import { useCallback, useEffect, useEffectEvent, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import MonacoEditor from "@monaco-editor/react";

import PageShell from "../../components/layout/PageShell";
import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";
import AlertModal from "../../components/modals/AlertModal";
import ConfirmationModal from "../../components/modals/ConfirmationModal";
import { EmptyState, ErrorState, LoadingState } from "../../components/ui/StateViews";
import { useEditorSettings } from "../../hooks/useEditorSettings";
import { requiredRuleIds, ruleLabel, ruleMinCount } from "../../utils/astRules";
import { pollDelay } from "../../utils/polling";
import { useBehaviorTracking } from "../../hooks/useBehaviorTracking";
import { useAuth } from "../auth/AuthContext";
import api, { getErrorMessage, NETWORK_ERROR_STATUS, TIMEOUT_ERROR_STATUS } from "../../services/api";
import { classLabel, formatDateTime } from "../student/studentData";
import { useTheme } from "../theme/ThemeContext";
import ThemeToggle from "../theme/ThemeToggle";
import { draftKeyFor, readDraft, saveDraft } from "./draftStorage";
import { defineEditorThemes, editorThemeFor } from "./editorThemes";
import ActivityTimer, { toClientTimer } from "./ActivityTimer";
import Icon from "../../components/ui/Icon";

const BLANK_TEMPLATE = "# Write your solution below.\n";

/*
 * Copy and cut inside the editor keep the code in the workspace clipboard
 * (React state) and put only this marker on the system clipboard: a random
 * token under a private type, never readable text. A later Ctrl+V that carries
 * the current token is the student's own copy, pasted from the workspace
 * clipboard and not counted. Any paste that carries outside text is blocked
 * and counted as a blocked paste.
 */
const WORKSPACE_CLIPBOARD_TYPE = "application/x-pamsu-workspace-clipboard";
const newClipboardToken = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;

const WORKSPACE_VIEWS = [
  { id: "problem", label: "Problem", icon: "M2 3h4a2 2 0 012 2v9a2 2 0 00-2-2H2V3zM14 3h-4a2 2 0 00-2 2v9a2 2 0 012-2h4V3z" },
  { id: "session", label: "Session", icon: "M5 5L2 8l3 3M11 5l3 3-3 3M9 3l-2 10" },
];
// Checks for the run result follow utils/polling.js and stop after 30 s.
const POLL_MAX_WAIT_MS = 30000;
const SUBMIT_TIMEOUT_MS = 45000;
// Longest a submit waits to send the last indicator counts first.
const FLUSH_WAIT_MS = 5000;

const TERMINAL_STATES = ["completed", "syntax_error", "runtime_error", "timed_out", "memory_limit", "output_limit", "process_limit", "cancelled", "failed"];

const RESULT_LABELS = {
  completed: "Finished",
  syntax_error: "Syntax error",
  runtime_error: "Runtime error",
  timed_out: "Time limit exceeded",
  memory_limit: "Memory limit exceeded",
  output_limit: "Output limit exceeded",
  process_limit: "Process limit exceeded",
  cancelled: "Cancelled",
  failed: "Execution failed",
};

const STATUS_DISPLAY = {
  idle: { label: "Ready", dot: "bg-text-muted/40" },
  running: { label: "Running…", dot: "bg-psu-gold animate-pulse" },
  queued: { label: "Waiting for sandbox", dot: "bg-psu-gold" },
  completed: { label: "Finished", dot: "bg-emerald-600" },
  error: { label: "Finished with errors", dot: "bg-psu-red" },
  unavailable: { label: "Sandbox unavailable", dot: "bg-psu-red" },
};

function connectionMessage(err, action) {
  if (err?.status === NETWORK_ERROR_STATUS) return `Could not reach the server to ${action}. Check your connection and try again.`;
  if (err?.status === TIMEOUT_ERROR_STATUS) return `The server took too long to ${action}. The code runner may be busy or offline.`;
  return getErrorMessage(err, `Could not ${action}.`);
}

function useDelay() {
  const timers = useRef(new Set());
  useEffect(() => {
    const active = timers.current;
    return () => active.forEach((t) => window.clearTimeout(t));
  }, []);
  return useCallback((ms) => new Promise((resolve) => {
    const t = window.setTimeout(() => {
      timers.current.delete(t);
      resolve();
    }, ms);
    timers.current.add(t);
  }), []);
}

/** Workspace route without an activity: point the student to their assignments. */
function NoActivitySelected() {
  return (
    <PageShell>
      <EmptyState
        className="mt-10"
        icon="inbox"
        title="Choose an activity to start coding"
        message="The workspace opens from an assignment. Pick an open activity to load its instructions and editor."
        action={
          <Link to="/student/assignments" className="btn-primary">
            Go to assignments
          </Link>
        }
      />
    </PageShell>
  );
}

export default function Workspace() {
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const activityId = searchParams.get("activity");
  if (!activityId || !/^\d+$/.test(activityId)) return <NoActivitySelected />;
  // Keyed by account too, so a different student never inherits editor state.
  return <ActivityWorkspace key={`${user?.user_id}-${activityId}`} activityId={activityId} userId={user?.user_id} />;
}

function ActivityWorkspace({ activityId, userId }) {
  const navigate = useNavigate();
  const delay = useDelay();
  const { settings } = useEditorSettings();
  // No account id means no local draft: never share one between students.
  const draftStorageKey = userId ? draftKeyFor(userId, activityId) : null;
  const editorRef = useRef(null);
  const isMounted = useRef(true);

  const [activity, setActivity] = useState(null);
  const [sampleCases, setSampleCases] = useState([]);
  const [loadError, setLoadError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const [code, setCode] = useState(BLANK_TEMPLATE);
  const { effectiveTheme } = useTheme();
  const [standardInput, setStandardInput] = useState("");
  const [output, setOutput] = useState("");
  const [astResults, setAstResults] = useState(null);
  const [astError, setAstError] = useState("");
  const [activePanel, setActivePanel] = useState("output");
  const [executionStatus, setExecutionStatus] = useState("idle");
  const [notice, setNotice] = useState(null);

  // Workspace clipboard. A ref, not state: Ctrl+V right after Ctrl+C must see
  // the new text even before React re-renders.
  const internalClipboardRef = useRef("");
  // Marker of the latest copy/cut made in the editor (see WORKSPACE_CLIPBOARD_TYPE).
  const clipboardTokenRef = useRef(null);
  // Opens (or resumes) this activity's coding session and keeps its counts in
  // sync, so Live Monitoring and the grading bench can show them.
  const tracking = useBehaviorTracking({ taskId: activityId });
  const { tabSwitchCount, blockedPasteCount, mouseLeaveCount } = tracking;
  // Fallbacks for when no session could be opened.
  const [localRunCount, setLocalRunCount] = useState(0);
  const [lastBlockedPasteIso, setLastBlockedPasteIso] = useState(null);
  const runAttemptCount = tracking.session ? tracking.session.run_attempt_count : localRunCount;

  // "problem" is for reading only; code is written and run on "session".
  const [view, setView] = useState("problem");
  const isCoding = view === "session";
  // Below xl the session indicators open as an overlay; at xl they are docked.
  const [showIndicators, setShowIndicators] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Timed activities. The server owns the timer (GET/POST /activities/:id/timer);
  // this copy adds endsAtMs, the end on this device's clock.
  const [timer, setTimer] = useState(null);
  const [timeUp, setTimeUp] = useState(false);
  const [isStartingTimer, setIsStartingTimer] = useState(false);
  // Extra lines for the start warning, worked out when it opens.
  const [startTimerNotes, setStartTimerNotes] = useState([]);
  // Result of the automatic submit at 00:00: { kind: "submitted", subId } or { kind: "failed", message }.
  const [timeUpOutcome, setTimeUpOutcome] = useState(null);
  const autoSubmitStarted = useRef(false);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const loadActivity = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const [activityRes, casesRes, classesRes] = await Promise.allSettled([
        api.get(`/activities/${activityId}`),
        api.get(`/activities/${activityId}/sample-test-cases`),
        api.get("/classrooms/mine"),
      ]);
      if (activityRes.status === "rejected") throw activityRes.reason;

      const task = activityRes.value;
      // A timed activity cannot open without its timer: the editor must know
      // whether the student's time is running, over, or not started.
      const timerBody = task.is_timed ? await api.get(`/activities/${activityId}/timer`) : null;
      const cases = casesRes.status === "fulfilled" && Array.isArray(casesRes.value) ? casesRes.value : [];
      const enrollment =
        classesRes.status === "fulfilled"
          ? (classesRes.value || []).find((c) => c.classroom?.class_id === task.class_id)
          : null;

      setActivity({
        ...task,
        classLabel: enrollment ? classLabel(enrollment.classroom) : `Class ${task.class_id}`,
        requirements: requiredRuleIds(task.required_ast_rules),
        pasteDisabled: task.paste_policy === "disabled",
        // Timed and not started: the server sent no problem text, starter code,
        // required structures or sample cases (see revealProblem).
        contentWithheld: Boolean(task.content_withheld),
      });
      setSampleCases(cases);
      setTimer(timerBody ? toClientTimer(timerBody) : null);
      setTimeUp(Boolean(timerBody) && (timerBody.state === "expired" || timerBody.state === "closed"));

      const savedDraft = draftStorageKey ? readDraft(draftStorageKey) : null;
      setCode(savedDraft ?? (task.starter_code || BLANK_TEMPLATE));
      if (cases[0]?.standard_input) setStandardInput(cases[0].standard_input);
    } catch (err) {
      setLoadError(err);
    } finally {
      setIsLoading(false);
    }
  }, [activityId, draftStorageKey]);

  useEffect(() => {
    loadActivity();
  }, [loadActivity]);

  // Autosave the draft locally (debounced). Not while the problem is withheld:
  // the blank template saved then would later hide the starter code.
  useEffect(() => {
    if (!activity || !draftStorageKey || activity.contentWithheld) return undefined;
    const timer = window.setTimeout(() => saveDraft(draftStorageKey, code), 500);
    return () => window.clearTimeout(timer);
  }, [code, draftStorageKey, activity]);

  // Shrinking below xl must not leave the indicators overlay covering the editor.
  useEffect(() => {
    const desktopQuery = window.matchMedia("(min-width: 1280px)");
    const handleScreenChange = (event) => {
      if (!event.matches) setShowIndicators(false);
    };
    desktopQuery.addEventListener("change", handleScreenChange);
    return () => desktopQuery.removeEventListener("change", handleScreenChange);
  }, []);

  useEffect(() => {
    if (!notice) return undefined;
    const timer = window.setTimeout(() => setNotice(null), notice.tone === "error" ? 6000 : 3500);
    return () => window.clearTimeout(timer);
  }, [notice]);

  const showNotice = (text, tone = "info") => setNotice({ text, tone });

  const isTimed = Boolean(activity?.is_timed);
  const timerRunning = isTimed && timer?.state === "running" && !timeUp;
  // A timed activity can be edited, run and submitted only while its timer runs.
  const isLocked = isTimed && !timerRunning;
  const lockedMessage = "Your time for this activity is up, so the code can no longer be changed.";

  // ── Internal clipboard ───────────────────────────────────────────────
  const getSelectionText = () => {
    const editor = editorRef.current;
    if (!editor) return { editor: null, selection: null, text: "" };
    const selection = editor.getSelection();
    return { editor, selection, text: editor.getModel().getValueInRange(selection) };
  };

  /**
   * Replaces the system clipboard with a fresh workspace marker (no text), so
   * nothing readable leaves the workspace and the next Ctrl+V is recognised.
   * Ctrl+C / Ctrl+X pass their event's clipboardData; the toolbar buttons have
   * none, so a copy command is started to get one.
   */
  const markSystemClipboard = (clipboardData) => {
    const token = newClipboardToken();
    clipboardTokenRef.current = token;
    if (clipboardData) {
      clipboardData.setData(WORKSPACE_CLIPBOARD_TYPE, token);
      return;
    }
    const writeMarker = (event) => {
      event.clipboardData?.setData(WORKSPACE_CLIPBOARD_TYPE, token);
      event.preventDefault();
      event.stopImmediatePropagation();
    };
    document.addEventListener("copy", writeMarker, true);
    try {
      document.execCommand("copy");
    } catch {
      // Best effort: without it, a later Ctrl+V of older outside text is still blocked and counted.
    } finally {
      document.removeEventListener("copy", writeMarker, true);
    }
  };

  const copySelection = (clipboardData = null) => {
    const { text } = getSelectionText();
    if (!text) return showNotice("Select code before copying.");
    internalClipboardRef.current = text;
    markSystemClipboard(clipboardData);
    showNotice("Copied to the workspace clipboard.");
  };

  const cutSelection = (clipboardData = null) => {
    // executeEdits ignores Monaco's readOnly, so the lock is checked here.
    if (isLocked) return showNotice(lockedMessage);
    const { editor, selection, text } = getSelectionText();
    if (!text) return showNotice("Select code before cutting.");
    internalClipboardRef.current = text;
    markSystemClipboard(clipboardData);
    editor.executeEdits("internal-cut", [{ range: selection, text: "", forceMoveMarkers: true }]);
    editor.focus();
    showNotice("Moved to the workspace clipboard.");
  };

  const pasteInternal = () => {
    if (isLocked) return showNotice(lockedMessage);
    if (activity?.pasteDisabled) return showNotice("Pasting is turned off for this activity.");
    const editor = editorRef.current;
    if (!editor) return;
    const text = internalClipboardRef.current;
    if (!text) return showNotice("The workspace clipboard is empty.");
    editor.executeEdits("internal-paste", [{ range: editor.getSelection(), text, forceMoveMarkers: true }]);
    editor.focus();
  };

  const recordBlockedPaste = (message = "Pasting from outside the workspace is blocked. Copying and pasting inside the editor still works.") => {
    tracking.recordBlockedPaste();
    setLastBlockedPasteIso(new Date().toISOString());
    showNotice(message);
  };

  /**
   * Dropping text into the editor would bypass the paste block, so drops are
   * cancelled, and a drop that carries text counts as a blocked paste. Moving a
   * selection by dragging inside the editor is Monaco's own mouse handling and
   * is not affected.
   */
  const handleEditorDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (event.dataTransfer?.getData("text/plain")) {
      recordBlockedPaste("Dropping text from outside the workspace is blocked.");
    }
  };

  /**
   * Every browser paste into the editor lands here. The student's own copy
   * (current marker), or a paste with no text at all, goes through the
   * workspace clipboard and is not counted. Outside text is blocked and counted.
   */
  const handleEditorPaste = (event) => {
    // Monaco's find box: a search term never enters the code, so let it paste.
    if (event.target?.closest?.(".find-widget")) return;
    event.preventDefault();
    event.stopPropagation();
    const data = event.clipboardData;
    const isOwnCopy = Boolean(clipboardTokenRef.current) && data?.getData(WORKSPACE_CLIPBOARD_TYPE) === clipboardTokenRef.current;
    const outsideText = data?.getData("text/plain") || "";
    if (isOwnCopy || !outsideText) {
      pasteInternal();
      return;
    }
    recordBlockedPaste();
  };

  // ── Execution ────────────────────────────────────────────────────────
  const pollExecution = async (executionId) => {
    for (let waited = 0; waited < POLL_MAX_WAIT_MS; ) {
      const pause = pollDelay(waited);
      await delay(pause);
      waited += pause;
      if (!isMounted.current) return null;
      const result = await api.get(`/execution/requests/${executionId}`);
      if (TERMINAL_STATES.includes(result.status)) return result;
      setExecutionStatus(result.status === "queued" ? "queued" : "running");
    }
    return null;
  };

  const handleRun = async () => {
    if (!isCoding || isLocked) return;
    setActivePanel("output");
    setExecutionStatus("running");
    setOutput("Sending your code to the sandbox…");
    setLocalRunCount((c) => c + 1);
    try {
      const runBody = {
        request_kind: "run",
        task_id: Number(activityId),
        source_code: code,
        standard_input: standardInput || "",
      };
      const sessionId = tracking.sessionId;
      let request;
      try {
        // Linking the run lets the server count it on the coding session.
        request = await api.post("/execution/requests/", sessionId ? { ...runBody, coding_session_id: sessionId } : runBody);
      } catch (err) {
        // 404 is refused before anything is saved; if the session was the
        // cause, run without it rather than block the student.
        if (err?.status !== 404 || !sessionId) throw err;
        request = await api.post("/execution/requests/", runBody);
      }
      // Fetch the session's updated run count for the Session panel.
      tracking.flush();
      const result = await pollExecution(request.execution_id);
      if (!isMounted.current) return;
      if (!result) {
        setExecutionStatus("unavailable");
        setOutput(
          "Your run request was accepted but no result came back. The code runner may be offline or very busy.\nTry again in a moment; if this keeps happening, tell your instructor.",
        );
        return;
      }
      setExecutionStatus(result.status === "completed" ? "completed" : "error");
      const text = [result.stdout, result.stderr].filter(Boolean).join(result.stdout && result.stderr ? "\n" : "");
      const header = `[${RESULT_LABELS[result.status] || result.status}${
        typeof result.execution_time_ms === "number" ? ` · ${result.execution_time_ms} ms` : ""
      }]`;
      setOutput(`${header}\n${text || "(no output)"}${result.limit_reason ? `\n\n${result.limit_reason}` : ""}`);
    } catch (err) {
      if (!isMounted.current) return;
      setExecutionStatus(err?.status === NETWORK_ERROR_STATUS || err?.status === TIMEOUT_ERROR_STATUS ? "unavailable" : "error");
      setOutput(connectionMessage(err, "run your code"));
    }
  };

  const handleCheck = async () => {
    if (!isCoding || isLocked) return;
    setActivePanel("analysis");
    setExecutionStatus("running");
    setAstError("");
    try {
      const result = await api.post(`/activities/${activityId}/analyze-ast`, { source_code: code });
      if (!isMounted.current) return;
      setAstResults(result);
      setExecutionStatus("idle");
    } catch (err) {
      if (!isMounted.current) return;
      setAstResults(null);
      setAstError(connectionMessage(err, "check your code structure"));
      setExecutionStatus("idle");
    }
  };

  /**
   * Submits the current code. `auto` is the timed activity's submit at 00:00:
   * it runs whichever tab is open and whatever the code holds, and reports
   * through the time-up dialog instead of leaving the page.
   */
  const submitSolution = async ({ auto = false } = {}) => {
    if (isSubmitting) return;
    if (!auto && (!isCoding || isLocked)) return;
    setIsSubmitting(true);
    try {
      // Send the last counts first so the linked session is complete; never
      // hold up the submission for longer than FLUSH_WAIT_MS.
      const flushed = await Promise.race([tracking.flush(), delay(FLUSH_WAIT_MS).then(() => null)]);
      const linkedSession = flushed || tracking.session;
      const sessionId = linkedSession?.session_id ?? null;
      const submitBody = { task_id: Number(activityId), raw_code: code };

      // Submitting can take longer than other requests while the server queues evaluation.
      let submission;
      try {
        submission = await api.post(
          "/submissions/",
          sessionId ? { ...submitBody, coding_session_id: sessionId } : submitBody,
          {},
          SUBMIT_TIMEOUT_MS,
        );
      } catch (err) {
        // 404 is refused before anything is saved. If the session was the
        // cause, submit without it: indicators must never block a submission.
        if (err?.status !== 404 || !sessionId) throw err;
        submission = await api.post("/submissions/", submitBody, {}, SUBMIT_TIMEOUT_MS);
      }
      try {
        const lastBlockedPasteAt = linkedSession?.last_blocked_paste_at ?? lastBlockedPasteIso;
        await api.post("/logs/behavioral/", {
          sub_id: submission.sub_id,
          tab_switches_count: tabSwitchCount,
          blocked_paste_count: blockedPasteCount,
          mouseleave_count: mouseLeaveCount,
          run_attempt_count: runAttemptCount,
          idle_duration_seconds: 0,
          ...(lastBlockedPasteAt && { last_blocked_paste_at: lastBlockedPasteAt }),
        });
      } catch (logErr) {
        // The submission is already recorded; indicator sync is best-effort.
        console.warn("Activity indicator sync failed", logErr);
      }
      setConfirmAction(null);
      if (auto) {
        if (isMounted.current) setTimeUpOutcome({ kind: "submitted", subId: submission.sub_id });
        return;
      }
      navigate(`/student/submissions/${submission.sub_id}`, { state: { justSubmitted: true } });
    } catch (err) {
      setConfirmAction(null);
      if (auto) {
        if (isMounted.current) {
          setTimeUpOutcome({
            kind: "failed",
            message:
              err?.status === TIMEOUT_ERROR_STATUS
                ? "The server didn't confirm the submission in time. It may still have been recorded: check Submissions before trying again."
                : connectionMessage(err, "submit your code"),
          });
        }
        return;
      }
      if (err?.status === TIMEOUT_ERROR_STATUS) {
        // The request may have completed on the server even though no reply arrived.
        showNotice(
          "The server didn't confirm your submission in time. It may still have been recorded — check Submissions before submitting again.",
          "error",
        );
      } else {
        showNotice(`Your submission was not recorded. ${connectionMessage(err, "submit")}`, "error");
      }
    } finally {
      if (isMounted.current) setIsSubmitting(false);
    }
  };

  // ── Timed activity ───────────────────────────────────────────────────
  const refreshTimer = async () => {
    try {
      const body = await api.get(`/activities/${activityId}/timer`);
      if (!isMounted.current) return;
      setTimer(toClientTimer(body));
      setTimeUp(body.state === "expired" || body.state === "closed");
    } catch {
      // The state shown stays as it was; the server still enforces the time.
    }
  };

  /**
   * Loads the problem the server withheld until the timer started: text,
   * required structures, sample cases and starter code. Returns false when it
   * could not be loaded (the Problem tab then offers to try again).
   */
  const revealProblem = async () => {
    const [taskRes, casesRes] = await Promise.allSettled([
      api.get(`/activities/${activityId}`),
      api.get(`/activities/${activityId}/sample-test-cases`),
    ]);
    if (!isMounted.current) return false;
    if (taskRes.status === "rejected" || taskRes.value.content_withheld) {
      showNotice("Your timer is running, but the problem could not be loaded. Select “Load the problem” to try again.", "error");
      return false;
    }
    const task = taskRes.value;
    const cases = casesRes.status === "fulfilled" && Array.isArray(casesRes.value) ? casesRes.value : [];
    setActivity((prev) => ({
      ...prev,
      ...task,
      requirements: requiredRuleIds(task.required_ast_rules),
      pasteDisabled: task.paste_policy === "disabled",
      contentWithheld: false,
    }));
    setSampleCases(cases);
    if (cases[0]?.standard_input) setStandardInput(cases[0].standard_input);
    const savedDraft = draftStorageKey ? readDraft(draftStorageKey) : null;
    setCode(savedDraft ?? (task.starter_code || BLANK_TEMPLATE));
    return true;
  };

  const startTimer = async () => {
    if (isStartingTimer) return;
    setIsStartingTimer(true);
    try {
      const body = await api.post(`/activities/${activityId}/timer/start`);
      if (!isMounted.current) return;
      // Converted now: the problem requests below must not shift the clock correction.
      const clientTimer = toClientTimer(body);
      const revealed = body.state === "running" && activity?.contentWithheld ? await revealProblem() : true;
      if (!isMounted.current) return;
      setTimer(clientTimer);
      setTimeUp(body.state !== "running");
      setConfirmAction(null);
      if (body.state === "running" && revealed) {
        switchView("session");
        window.setTimeout(() => editorRef.current?.focus(), 0);
      }
    } catch (err) {
      if (!isMounted.current) return;
      setConfirmAction(null);
      showNotice(`The timer was not started. ${connectionMessage(err, "start the timer")}`, "error");
      // Refused (the deadline passed, the time was used): show the server's state.
      if (err?.status === 403) refreshTimer();
    } finally {
      if (isMounted.current) setIsStartingTimer(false);
    }
  };

  const handleTimerWarning = (secondsLeft) =>
    showNotice(
      secondsLeft >= 5 * 60
        ? "5 minutes left. Your code is submitted automatically when the timer reaches 00:00."
        : "1 minute left. Your code is submitted automatically when the timer reaches 00:00.",
    );

  // 00:00 on a timer that ran in this page: lock the editor (isLocked) and
  // submit. A timer that was already over when the page opened submits nothing.
  const submitAtTimeUp = useEffectEvent(() => {
    // A Submit already on its way counts as the student's final attempt.
    if (isSubmitting) return;
    setConfirmAction(null);
    submitSolution({ auto: true });
  });

  useEffect(() => {
    if (!timeUp || timer?.state !== "running" || autoSubmitStarted.current) return;
    autoSubmitStarted.current = true;
    submitAtTimeUp();
  }, [timeUp, timer]);

  const resetDraft = () => {
    if (isLocked) return showNotice(lockedMessage);
    const starter = activity?.starter_code || BLANK_TEMPLATE;
    setCode(starter);
    setOutput("");
    setAstResults(null);
    setExecutionStatus("idle");
    setConfirmAction(null);
    showNotice("Draft reset to the starter code.");
  };

  if (isLoading) {
    return (
      <PageShell>
        <LoadingState label="Loading workspace…" />
      </PageShell>
    );
  }

  if (loadError) {
    return (
      <PageShell>
        <ErrorState
          className="mt-6"
          error={loadError}
          resource="this activity"
          onRetry={loadActivity}
          action={
            <Link to="/student/assignments" className="btn-secondary">
              <Icon name="arrowLeft" className="h-4 w-4" />
              Back to assignments
            </Link>
          }
        />
      </PageShell>
    );
  }

  const status = STATUS_DISPLAY[executionStatus] || STATUS_DISPLAY.idle;
  const isBusy = executionStatus === "running" || executionStatus === "queued";
  const lineCount = code.split("\n").length;
  const dueLabel = activity.due_at ? `Due ${formatDateTime(activity.due_at)}` : "No due date";
  const pastDue = activity.due_at && new Date(activity.due_at) < new Date();
  // A submission needs code of the student's own: not just comments or the untouched starter code.
  const hasOwnCode =
    code.split("\n").some((line) => line.trim() && !line.trim().startsWith("#")) &&
    code.trim() !== (activity.starter_code || "").trim();

  const switchView = (next) => {
    setView(next);
    if (next !== "session") setShowIndicators(false);
  };

  const timerNotStarted = isTimed && timer?.state === "not_started";
  const timeLimitMinutes = timer?.time_limit_minutes ?? activity.time_limit_minutes;
  const minutesText = (minutes) => `${minutes} ${minutes === 1 ? "minute" : "minutes"}`;

  // Entering the Session tab of a timed activity starts its timer, so the
  // student confirms first ("Start Now"). Reading the problem never does.
  const openSession = () => {
    if (!timerNotStarted) {
      switchView("session");
      return;
    }
    const notes = [];
    if (timer.retake_available) notes.push("Your instructor allowed you another attempt. This starts a new timer.");
    if (activity.contentWithheld) notes.push("The problem, starter code and sample cases appear as soon as the timer starts.");
    if (activity.due_at) {
      const minutesToDeadline = Math.floor((new Date(activity.due_at).getTime() - Date.now()) / 60000);
      if (minutesToDeadline < timeLimitMinutes && !timer.retake_available) {
        notes.push(
          `The activity is due ${formatDateTime(activity.due_at)}, so your timer will end then: about ${minutesText(Math.max(minutesToDeadline, 0))} from now.`,
        );
      }
    }
    notes.push("When the timer reaches 00:00, the editor locks and your code is submitted automatically.");
    setStartTimerNotes(notes);
    setConfirmAction("start-timer");
  };

  // Tabs pattern: arrow keys (and Home/End) move between the two views.
  const handleViewKeyDown = (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const next = event.key === "Home" ? "problem" : event.key === "End" ? "session" : isCoding ? "problem" : "session";
    if (next === "session" && timerNotStarted) {
      openSession();
      return;
    }
    switchView(next);
    document.getElementById(`workspace-tab-${next}`)?.focus();
  };
  const notCodingHint = "Open the Session tab to run and submit your code.";
  const lockedHint = timeUp ? "Your time for this activity is up." : undefined;
  const startCodingButton = (
    <button type="button" onClick={openSession} className="btn-primary shrink-0">
      Start coding
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M3 8h10M9 4l4 4-4 4" />
      </svg>
    </button>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main">
      {/* Navigation rail on wide screens; smaller screens use the back link in the header. */}
      <div className="hidden h-full lg:flex">
        <Sidebar />
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-b border-border-subtle bg-bg-panel px-3 py-2 sm:px-4">
          <div className="flex min-w-0 items-center gap-2">
            <Link
              to="/student/assignments"
              className="btn-ghost btn-sm lg:hidden"
              aria-label="Back to assignments"
            >
              <Icon name="arrowLeft" className="h-3.5 w-3.5" />
            </Link>
            <div
              role="tablist"
              aria-label="Workspace view"
              onKeyDown={handleViewKeyDown}
              className="flex items-center gap-1 rounded-lg border border-border-subtle bg-bg-alt p-0.5"
            >
              {WORKSPACE_VIEWS.map((tab) => {
                const selected = view === tab.id;
                return (
                  <button
                    key={tab.id}
                    id={`workspace-tab-${tab.id}`}
                    type="button"
                    role="tab"
                    aria-selected={selected}
                    aria-controls={`workspace-view-${tab.id}`}
                    tabIndex={selected ? 0 : -1}
                    onClick={() => (tab.id === "session" ? openSession() : switchView(tab.id))}
                    className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold transition-colors ${
                      selected ? "bg-psu-maroon text-white shadow-sm" : "text-text-muted hover:bg-bg-panel hover:text-text-main"
                    }`}
                  >
                    <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d={tab.icon} />
                    </svg>
                    {tab.label}
                  </button>
                );
              })}
            </div>
            <div className="hidden min-w-0 sm:block">
              <p className="truncate text-sm font-semibold text-text-main">{activity.title}</p>
              <p className="truncate text-[11px] text-text-muted">{activity.classLabel}</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {isTimed && (
              <ActivityTimer
                limitMinutes={timeLimitMinutes}
                endsAtMs={timer?.endsAtMs ?? undefined}
                running={timerRunning}
                timeUp={timeUp}
                onExpire={() => setTimeUp(true)}
                onWarning={handleTimerWarning}
              />
            )}
            <div className="hidden items-center gap-2 rounded-lg border border-border-subtle px-2.5 py-1 text-xs md:flex" role="status" aria-live="polite">
              <span className={`h-2 w-2 rounded-full ${status.dot}`} aria-hidden="true" />
              <span className="text-text-muted">{status.label}</span>
            </div>
            {/* Below lg the navigation rail (and its theme control) is hidden. */}
            <div className="w-9 shrink-0 lg:hidden">
              <ThemeToggle collapsed tooltipSide="bottom" />
            </div>
            {/* Disabled rather than hidden on the Problem tab, so the header never shifts. */}
            <button
              type="button"
              onClick={handleCheck}
              disabled={!isCoding || isBusy || isLocked}
              title={!isCoding ? notCodingHint : lockedHint}
              className="btn-secondary btn-sm"
            >
              <Icon name="check" className="h-3.5 w-3.5" />
              Check structure
            </button>
            <button
              type="button"
              onClick={handleRun}
              disabled={!isCoding || isBusy || isLocked}
              title={!isCoding ? notCodingHint : lockedHint}
              className="btn-secondary btn-sm"
            >
              <svg width="11" height="11" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                <path d="M4 2.5v11l9-5.5-9-5.5z" />
              </svg>
              Run
            </button>
            <button
              type="button"
              onClick={() => setConfirmAction("submit")}
              disabled={!isCoding || isBusy || isSubmitting || !hasOwnCode || isLocked}
              title={!isCoding ? notCodingHint : isLocked ? lockedHint : !hasOwnCode ? "Write your solution before submitting." : undefined}
              className="btn-primary btn-sm"
            >
              <Icon name="send" className="h-3.5 w-3.5" />
              Submit
            </button>
          </div>
        </header>

        {notice && (
          <div
            role={notice.tone === "error" ? "alert" : "status"}
            aria-live="polite"
            className={`shrink-0 border-b px-4 py-1.5 text-xs font-medium ${
              notice.tone === "error"
                ? "border-psu-red/20 bg-psu-red/[0.06] text-text-rose"
                : "border-psu-maroon/15 bg-selected text-text-brand"
            }`}
          >
            {notice.text}
          </div>
        )}

        {isTimed && timeUp && (
          <div
            role="status"
            className="flex shrink-0 flex-wrap items-center gap-x-3 gap-y-1 border-b border-psu-red/20 bg-psu-red/[0.06] px-4 py-2 text-xs text-text-main"
          >
            <span className="flex items-center gap-1.5 font-semibold text-text-rose">
              <Icon name="clock" className="h-3.5 w-3.5" />
              {timer?.state === "closed" ? "Deadline passed" : "Time is up"}
            </span>
            <span className="text-text-muted">
              {timer?.state === "closed"
                ? "The deadline passed before you started this timed activity."
                : isSubmitting
                  ? "The editor is locked. Submitting your code…"
                  : timeUpOutcome?.kind === "submitted" || timer?.submitted_in_window
                    ? "The editor is locked. Your submission was recorded."
                    : timeUpOutcome?.kind === "failed"
                      ? "The editor is locked. Your code was not submitted."
                      : "The editor is locked. Nothing was submitted during your time."}
            </span>
            <Link to="/student/submissions" className="font-semibold text-text-brand underline">
              My submissions
            </Link>
          </div>
        )}

        {showIndicators && (
          <button
            type="button"
            onClick={() => setShowIndicators(false)}
            className="fixed inset-0 z-40 bg-overlay xl:hidden"
            aria-label="Close session indicators"
          />
        )}

        <div className="flex min-h-0 flex-1 overflow-hidden">
          {view === "problem" && (
            <section
              id="workspace-view-problem"
              role="tabpanel"
              aria-labelledby="workspace-tab-problem"
              className="min-h-0 flex-1 overflow-y-auto"
            >
              <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6 sm:py-8">
                <div className="flex flex-col gap-4 border-b border-border-subtle pb-5 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold uppercase tracking-widest text-text-brand">Problem</p>
                    <h1 className="mt-1 text-xl font-bold tracking-tight text-text-main sm:text-2xl">{activity.title}</h1>
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <span className={`badge ${pastDue ? "badge-danger" : "badge-gold"}`}>{pastDue ? `Past due · ${dueLabel.replace("Due ", "")}` : dueLabel}</span>
                      <span className="badge badge-neutral">{activity.activity_type === "homework" ? "Homework" : "Laboratory"}</span>
                      {isTimed && (
                        <span className="badge badge-brand inline-flex items-center gap-1">
                          <Icon name="clock" className="h-3 w-3" />
                          Timed · {timeLimitMinutes} min
                        </span>
                      )}
                    </div>
                  </div>
                  {startCodingButton}
                </div>

                <div className="mt-6 space-y-7">
                  {activity.contentWithheld ? (
                    <section
                      aria-labelledby="problem-withheld-heading"
                      className="rounded-xl border border-dashed border-border-strong bg-bg-panel px-5 py-8 text-center"
                    >
                      <span className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-psu-maroon/10 text-text-brand">
                        <Icon name="clock" className="h-5 w-5" />
                      </span>
                      {timerRunning ? (
                        <>
                          <h2 id="problem-withheld-heading" className="mt-3 text-base font-semibold text-text-main">
                            The problem did not load
                          </h2>
                          <p className="mx-auto mt-1.5 max-w-md text-sm leading-relaxed text-text-muted">
                            Your timer is running. Load the problem again; if it keeps failing, reload the page.
                          </p>
                          <button type="button" onClick={revealProblem} className="btn-primary mt-4">
                            <Icon name="refresh" className="h-4 w-4" />
                            Load the problem
                          </button>
                        </>
                      ) : (
                        <>
                          <h2 id="problem-withheld-heading" className="mt-3 text-base font-semibold text-text-main">
                            {timer?.state === "closed" ? "This timed activity was not started" : "The problem appears when you start"}
                          </h2>
                          <p className="mx-auto mt-1.5 max-w-md text-sm leading-relaxed text-text-muted">
                            {timer?.state === "closed"
                              ? "The deadline passed before you started, so the problem is not shown."
                              : `This is a timed activity. The problem, starter code and sample cases are shown once you start the timer. You will then have ${minutesText(timeLimitMinutes)}, and the timer cannot be paused.`}
                          </p>
                          {timer?.state !== "closed" && <div className="mt-4 flex justify-center">{startCodingButton}</div>}
                        </>
                      )}
                    </section>
                  ) : (
                  <>
                  {activity.description && (
                    <section>
                      <h2 className="mb-2 text-sm font-semibold text-text-main">Problem description</h2>
                      <p className="whitespace-pre-wrap text-[15px] leading-7 text-text-main">{activity.description}</p>
                    </section>
                  )}

                  {activity.scenario && (
                    <section>
                      <h2 className="mb-2 text-sm font-semibold text-text-main">Real-world scenario</h2>
                      <p className="whitespace-pre-wrap text-[15px] leading-7 text-text-main">{activity.scenario}</p>
                    </section>
                  )}

                  {(activity.instructions || !activity.description) && (
                    <section>
                      <h2 className="mb-2 text-sm font-semibold text-text-main">Instructions</h2>
                      <p className="whitespace-pre-wrap text-[15px] leading-7 text-text-main">
                        {activity.instructions || "No instructions were provided for this activity."}
                      </p>
                    </section>
                  )}

                  {activity.requirements.length > 0 && (
                    <section>
                      <h2 className="mb-2 text-sm font-semibold text-text-main">Required structures</h2>
                      <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                        {activity.requirements.map((rule) => {
                          const count = ruleMinCount(activity.required_ast_rules[rule]);
                          return (
                            <li key={rule} className="flex items-center gap-2.5 rounded-lg border border-border-subtle bg-bg-panel px-3 py-2 text-sm text-text-main">
                              <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-psu-gold" aria-hidden="true" />
                              {ruleLabel(rule)}
                              {count > 1 && <span className="text-xs text-text-muted">at least {count}</span>}
                            </li>
                          );
                        })}
                      </ul>
                    </section>
                  )}

                  <section>
                    <h2 className="mb-2 text-sm font-semibold text-text-main">Sample cases</h2>
                    {sampleCases.length === 0 ? (
                      <p className="text-sm text-text-muted">No sample input/output was published for this activity.</p>
                    ) : (
                      <div className="space-y-3">
                        {sampleCases.map((sample) => (
                          <div key={sample.test_case_id} className="overflow-hidden rounded-lg border border-border-subtle bg-bg-panel">
                            <p className="border-b border-border-subtle bg-bg-alt px-3 py-2 text-xs font-semibold text-text-main">{sample.name}</p>
                            <div className={`grid grid-cols-1 ${sample.standard_input ? "sm:grid-cols-2 sm:divide-x" : ""} divide-border-subtle`}>
                              {sample.standard_input && (
                                <div className="p-3">
                                  <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">Input</p>
                                  <pre className="mt-1 overflow-x-auto whitespace-pre-wrap font-mono text-xs text-text-main">{sample.standard_input}</pre>
                                </div>
                              )}
                              <div className="border-t border-border-subtle p-3 sm:border-t-0">
                                <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">Expected output</p>
                                <pre className="mt-1 overflow-x-auto whitespace-pre-wrap font-mono text-xs text-text-main">{sample.expected_output}</pre>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </section>
                  </>
                  )}

                  <section className="rounded-lg border border-psu-maroon/15 bg-selected p-4">
                    <h2 className="text-xs font-bold text-text-brand">Clipboard policy</h2>
                    <p className="mt-1 text-sm leading-relaxed text-text-muted">
                      {activity.pasteDisabled
                        ? "Pasting is turned off for this activity. Type your solution in the editor."
                        : "Pasting from outside the workspace is blocked. Use the Copy, Cut and Paste buttons above the editor to move code within it."}
                    </p>
                  </section>
                </div>

                {!activity.contentWithheld && (
                <div className="mt-8 flex flex-col gap-4 rounded-xl border border-border-subtle bg-bg-panel p-4 shadow-[var(--shadow-card)] sm:flex-row sm:items-center sm:justify-between sm:p-5">
                  <div>
                    <p className="text-sm font-semibold text-text-main">
                      {timeUp ? "Your time is up" : timerRunning ? "Your timer is running" : "Ready to write your solution?"}
                    </p>
                    <p className="mt-0.5 text-sm text-text-muted">
                      {!isTimed
                        ? "Switch to the Session tab to start coding. Your draft is kept when you come back to re-read the problem."
                        : timeUp
                          ? "The editor is locked. You can still open the Session tab to see your code."
                          : timerRunning
                            ? "The timer keeps running while you read. Switch to the Session tab to keep coding."
                            : `This is a timed activity: you have ${minutesText(timeLimitMinutes)} once you start coding, and the timer cannot be paused.`}
                    </p>
                  </div>
                  {startCodingButton}
                </div>
                )}
              </div>
            </section>
          )}

          {/* Hidden (not unmounted) on the Problem tab: the editor keeps the
              draft, undo history and last output for when the student returns. */}
          <main
            id="workspace-view-session"
            role="tabpanel"
            aria-labelledby="workspace-tab-session"
            className={`${isCoding ? "flex" : "hidden"} min-w-0 flex-1 flex-col`}
          >
            <div className="flex shrink-0 items-center justify-between gap-2 border-b border-border-subtle bg-bg-panel px-3 py-1.5">
              <span className="font-mono text-xs font-semibold text-text-main">main.py</span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setShowIndicators((open) => !open)}
                  aria-pressed={showIndicators}
                  aria-controls="workspace-indicators"
                  className="btn-ghost btn-sm px-2 sm:px-3 xl:hidden"
                  title="Show the session indicators your instructor sees"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M1.5 8h3l2-4.5 3 9 2-4.5h3" />
                  </svg>
                  {/* Icon only on phones, so the toolbar still fits next to Reset. */}
                  <span className="sr-only sm:not-sr-only">Indicators</span>
                </button>
                <span className="mx-1 h-4 w-px bg-border-subtle xl:hidden" aria-hidden="true" />
                <button type="button" onClick={() => copySelection()} className="btn-ghost btn-sm" title="Copy selection to workspace clipboard">
                  Copy
                </button>
                <button type="button" onClick={() => cutSelection()} disabled={isLocked} className="btn-ghost btn-sm" title="Cut selection to workspace clipboard">
                  Cut
                </button>
                <button
                  type="button"
                  onClick={pasteInternal}
                  disabled={activity.pasteDisabled || isLocked}
                  className="btn-ghost btn-sm"
                  title={activity.pasteDisabled ? "Pasting is turned off for this activity" : "Paste from workspace clipboard"}
                >
                  Paste
                </button>
                <span className="mx-1 h-4 w-px bg-border-subtle" aria-hidden="true" />
                <button
                  type="button"
                  onClick={() => setConfirmAction("reset")}
                  disabled={isLocked}
                  className="btn-ghost btn-sm text-text-rose hover:text-text-rose"
                >
                  Reset
                </button>
              </div>
            </div>

            <div className="relative min-h-0 flex-1">
              <div
                className="h-full w-full"
                onPasteCapture={handleEditorPaste}
                onDropCapture={handleEditorDrop}
                onCopyCapture={(e) => {
                  // stopPropagation keeps Monaco's own copy handler from writing the
                  // code as text to the system clipboard (no copy-out). Also inside
                  // the find box: Ctrl+F fills it with selected code.
                  e.preventDefault();
                  e.stopPropagation();
                  copySelection(e.clipboardData);
                }}
                onCutCapture={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  cutSelection(e.clipboardData);
                }}
              >
                <MonacoEditor
                  height="100%"
                  language="python"
                  theme={editorThemeFor(effectiveTheme)}
                  beforeMount={defineEditorThemes}
                  value={code}
                  onChange={(value) => setCode(value ?? "")}
                  onMount={(editor) => {
                    editorRef.current = editor;
                  }}
                  loading={<LoadingState label="Starting editor…" />}
                  options={{
                    // Guard in case focus lingers after switching to the Problem tab;
                    // a timed activity also locks when its time is up.
                    readOnly: !isCoding || isLocked,
                    readOnlyMessage: { value: isLocked ? lockedMessage : "Open the Session tab to edit your code." },
                    minimap: { enabled: Boolean(settings.minimap) },
                    fontSize: settings.fontSize,
                    tabSize: settings.tabSize,
                    wordWrap: settings.wordWrap,
                    fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    padding: { top: 14, bottom: 14 },
                    renderLineHighlight: "all",
                    quickSuggestions: false,
                    suggestOnTriggerCharacters: false,
                    snippetSuggestions: "none",
                    wordBasedSuggestions: "off",
                    hover: { enabled: false },
                    parameterHints: { enabled: false },
                    contextmenu: false,
                    // Outside text must not be dropped in (see handleEditorDrop).
                    dropIntoEditor: { enabled: false },
                    renderWhitespace: "selection",
                  }}
                />
              </div>
              <div className="pointer-events-none absolute bottom-2 right-3 rounded bg-bg-panel/90 px-2 py-0.5 font-mono text-xs text-text-muted shadow-sm">
                {lineCount} {lineCount === 1 ? "line" : "lines"} · draft saved in this browser
              </div>
            </div>

            <section className="flex h-[clamp(170px,28vh,260px)] shrink-0 flex-col border-t border-border-subtle bg-bg-panel" aria-label="Results">
              <div className="flex shrink-0 items-center overflow-x-auto border-b border-border-subtle px-2" role="tablist">
                {[
                  { id: "output", label: "Output" },
                  { id: "analysis", label: "Structure check" },
                  { id: "input", label: "Standard input" },
                ].map((panel) => (
                  <button
                    key={panel.id}
                    type="button"
                    role="tab"
                    aria-selected={activePanel === panel.id}
                    onClick={() => setActivePanel(panel.id)}
                    className={`whitespace-nowrap border-b-2 px-3 py-2 text-xs font-medium transition-colors ${
                      activePanel === panel.id ? "border-psu-maroon text-text-brand" : "border-transparent text-text-muted hover:text-text-main"
                    }`}
                  >
                    {panel.label}
                  </button>
                ))}
              </div>

              <div className="min-h-0 flex-1 overflow-auto p-3 sm:p-4" role="tabpanel">
                {activePanel === "output" && (
                  <pre className="whitespace-pre-wrap font-mono text-xs leading-5 text-text-main">
                    {output || <span className="text-text-muted">Run your code to see its output here.</span>}
                  </pre>
                )}

                {activePanel === "analysis" && (
                  <div className="space-y-2">
                    {astError ? (
                      <p className="rounded-lg border border-psu-red/20 bg-psu-red/[0.05] p-3 text-xs text-text-rose" role="alert">
                        {astError}
                      </p>
                    ) : !astResults ? (
                      <p className="text-xs text-text-muted">
                        Select <span className="font-semibold">Check structure</span> to compare your code with the required
                        structures. This is feedback only, not a grade.
                      </p>
                    ) : astResults.syntax_error ? (
                      <div className="rounded-lg border border-psu-red/20 bg-psu-red/[0.05] p-3">
                        <p className="text-xs font-semibold text-text-rose">Syntax error on line {astResults.syntax_error.line}</p>
                        <p className="mt-1 font-mono text-xs text-text-main">{astResults.syntax_error.message}</p>
                      </div>
                    ) : (
                      <>
                        <p className={`text-xs font-semibold ${astResults.passed ? "text-text-emerald" : "text-text-amber"}`}>
                          {activity.requirements.length === 0
                            ? "This activity has no required structures."
                            : astResults.passed
                              ? "All required structures were found."
                              : "Some required structures are missing."}
                        </p>
                        {(astResults.findings || []).map((finding) => (
                          <div
                            key={finding.rule}
                            className="flex items-center justify-between gap-3 rounded-lg border border-border-subtle px-3 py-2"
                          >
                            <span className="text-xs text-text-main">{finding.label || ruleLabel(finding.rule)}</span>
                            <span className={`badge ${finding.passed ? "badge-success" : "badge-gold"}`}>
                              {finding.passed ? "Found" : "Missing"}
                            </span>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                )}

                {activePanel === "input" && (
                  <div>
                    <label htmlFor="standard-input" className="field-label">
                      Input given to your program when you select Run
                    </label>
                    <textarea
                      id="standard-input"
                      value={standardInput}
                      onChange={(event) => setStandardInput(event.target.value)}
                      spellCheck="false"
                      placeholder="Example: 10"
                      className="input-field h-[110px] resize-none font-mono text-xs"
                    />
                  </div>
                )}
              </div>
            </section>
          </main>

          {/* Part of the Session tab: docked at xl, an overlay below it. */}
          {isCoding && (
            <aside
              id="workspace-indicators"
              className={`${showIndicators ? "flex" : "hidden"} fixed inset-y-0 right-0 z-50 w-[88vw] max-w-[320px] flex-col overflow-hidden border-l border-border-subtle bg-bg-panel xl:static xl:z-auto xl:flex xl:w-[270px]`}
              aria-label="Session indicators"
            >
              <div className="flex items-center justify-between border-b border-border-subtle p-4">
                <h2 className="text-[11px] font-semibold uppercase tracking-widest text-text-muted">Session indicators</h2>
                <button type="button" onClick={() => setShowIndicators(false)} className="btn-ghost btn-sm xl:hidden" aria-label="Close session indicators">
                  ✕
                </button>
              </div>
              <div className="flex-1 space-y-4 overflow-y-auto p-4 text-xs">
                <dl className="space-y-2">
                  {[
                    ["Tab switches", tabSwitchCount],
                    ["Blocked pastes", blockedPasteCount],
                    ["Pointer left window", mouseLeaveCount],
                    ["Runs this session", runAttemptCount],
                  ].map(([label, value]) => (
                    <div key={label} className="flex items-center justify-between rounded-lg border border-border-subtle px-3 py-2">
                      <dt className="text-text-muted">{label}</dt>
                      <dd className="font-mono font-semibold text-text-main">{value}</dd>
                    </div>
                  ))}
                </dl>
                <p className="leading-relaxed text-text-muted">
                  Your instructor sees these counts while you work on this activity and with your submission, as review
                  indicators. They are not scores and not proof of misconduct.
                </p>
                <p className="leading-relaxed text-text-muted">
                  Clipboard contents, keystrokes, browsing history, screen, camera and microphone are never collected.
                </p>
              </div>
            </aside>
          )}
        </div>

        <Statusbar contextLabel={activity.classLabel} />
      </div>

      <ConfirmationModal
        isOpen={confirmAction === "submit"}
        title="Submit this solution?"
        message={
          isTimed
            ? "Your current code becomes your latest attempt. You can submit again until your timer ends; the latest accepted attempt is the official one."
            : pastDue
              ? "This activity is past its due date. A late submission is accepted only if your instructor allowed you another attempt."
              : "Your current code becomes your latest attempt. You can submit again while the activity is open; the latest accepted attempt is the official one."
        }
        confirmText="Submit"
        loadingText="Submitting…"
        isLoading={isSubmitting}
        onConfirm={() => submitSolution()}
        onCancel={() => setConfirmAction(null)}
      />
      {isTimed && (
        <>
          <ConfirmationModal
            isOpen={confirmAction === "start-timer"}
            title="Start the timer?"
            message={`This is a timed activity. Once you proceed, a timer of ${minutesText(timeLimitMinutes)} will begin and cannot be paused. Are you ready?`}
            confirmText="Start Now"
            loadingText="Starting…"
            isLoading={isStartingTimer}
            onConfirm={startTimer}
            onCancel={() => setConfirmAction(null)}
          >
            <ul className="mt-3 space-y-1.5 text-sm leading-relaxed text-text-muted">
              {startTimerNotes.map((note) => (
                <li key={note} className="flex gap-2">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-psu-gold" aria-hidden="true" />
                  {note}
                </li>
              ))}
            </ul>
          </ConfirmationModal>
          <AlertModal
            isOpen={timeUpOutcome?.kind === "submitted"}
            title="Time is up"
            message="Time is up! Your code has been automatically submitted."
            onClose={() => navigate(`/student/submissions/${timeUpOutcome.subId}`, { state: { justSubmitted: true } })}
          />
          <ConfirmationModal
            isOpen={timeUpOutcome?.kind === "failed"}
            title="Time is up"
            message={`Your code could not be submitted automatically. ${timeUpOutcome?.message ?? ""}`}
            confirmText="Try again"
            cancelText="Close"
            loadingText="Submitting…"
            isLoading={isSubmitting}
            onConfirm={() => {
              setTimeUpOutcome(null);
              submitSolution({ auto: true });
            }}
            onCancel={() => setTimeUpOutcome(null)}
          />
        </>
      )}
      <ConfirmationModal
        isOpen={confirmAction === "reset"}
        title="Reset your draft?"
        message="Your current code will be replaced with the activity's starter code. This cannot be undone."
        confirmText="Reset draft"
        isDanger
        onConfirm={resetDraft}
        onCancel={() => setConfirmAction(null)}
      />
    </div>
  );
}
