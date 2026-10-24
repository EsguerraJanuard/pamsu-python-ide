import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import MonacoEditor from "@monaco-editor/react";

import PageShell from "../../components/layout/PageShell";
import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";
import ConfirmationModal from "../../components/modals/ConfirmationModal";
import { EmptyState, ErrorState, LoadingState } from "../../components/ui/StateViews";
import { useEditorSettings } from "../../hooks/useEditorSettings";
import { requiredRuleIds, ruleLabel, ruleMinCount } from "../../utils/astRules";
import { useBehaviorTracking } from "../../hooks/useBehaviorTracking";
import { useAuth } from "../auth/AuthContext";
import api, { getErrorMessage, NETWORK_ERROR_STATUS, TIMEOUT_ERROR_STATUS } from "../../services/api";
import { classLabel, formatDateTime } from "../student/studentData";
import { useTheme } from "../theme/ThemeContext";
import ThemeToggle from "../theme/ThemeToggle";
import { draftKeyFor, readDraft, saveDraft } from "./draftStorage";
import { defineEditorThemes, editorThemeFor } from "./editorThemes";

const BLANK_TEMPLATE = "# Write your solution below.\n";
const POLL_INTERVAL_MS = 1500;
const MAX_POLLS = 20;
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

  const [internalClipboard, setInternalClipboard] = useState("");
  // Opens (or resumes) this activity's coding session and keeps its counts in
  // sync, so Live Monitoring and the grading bench can show them.
  const tracking = useBehaviorTracking({ taskId: activityId });
  const { tabSwitchCount, blockedPasteCount, mouseLeaveCount } = tracking;
  // Fallbacks for when no session could be opened.
  const [localRunCount, setLocalRunCount] = useState(0);
  const [lastBlockedPasteIso, setLastBlockedPasteIso] = useState(null);
  const runAttemptCount = tracking.session ? tracking.session.run_attempt_count : localRunCount;

  const [showProblemPanel, setShowProblemPanel] = useState(() => window.matchMedia("(min-width: 1280px)").matches);
  const [showReviewPanel, setShowReviewPanel] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

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
      });
      setSampleCases(cases);

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

  // Autosave the draft locally (debounced).
  useEffect(() => {
    if (!activity || !draftStorageKey) return undefined;
    const timer = window.setTimeout(() => saveDraft(draftStorageKey, code), 500);
    return () => window.clearTimeout(timer);
  }, [code, draftStorageKey, activity]);

  useEffect(() => {
    const desktopQuery = window.matchMedia("(min-width: 1280px)");
    const handleScreenChange = (event) => {
      setShowProblemPanel(event.matches);
      if (!event.matches) setShowReviewPanel(false);
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

  // ── Internal clipboard ───────────────────────────────────────────────
  const getSelectionText = () => {
    const editor = editorRef.current;
    if (!editor) return { editor: null, selection: null, text: "" };
    const selection = editor.getSelection();
    return { editor, selection, text: editor.getModel().getValueInRange(selection) };
  };

  const copySelection = () => {
    const { text } = getSelectionText();
    if (!text) return showNotice("Select code before copying.");
    setInternalClipboard(text);
    showNotice("Copied to the workspace clipboard.");
  };

  const cutSelection = () => {
    const { editor, selection, text } = getSelectionText();
    if (!text) return showNotice("Select code before cutting.");
    setInternalClipboard(text);
    editor.executeEdits("internal-cut", [{ range: selection, text: "", forceMoveMarkers: true }]);
    editor.focus();
    showNotice("Moved to the workspace clipboard.");
  };

  const pasteInternal = () => {
    if (activity?.pasteDisabled) return showNotice("Pasting is turned off for this activity.");
    const editor = editorRef.current;
    if (!editor) return;
    if (!internalClipboard) return showNotice("The workspace clipboard is empty.");
    editor.executeEdits("internal-paste", [{ range: editor.getSelection(), text: internalClipboard, forceMoveMarkers: true }]);
    editor.focus();
  };

  const recordBlockedPaste = () => {
    tracking.recordBlockedPaste();
    setLastBlockedPasteIso(new Date().toISOString());
    showNotice("Pasting from outside the workspace is blocked. Use the workspace Copy / Paste buttons.");
  };

  // ── Execution ────────────────────────────────────────────────────────
  const pollExecution = async (executionId) => {
    for (let attempt = 0; attempt < MAX_POLLS; attempt += 1) {
      await delay(POLL_INTERVAL_MS);
      if (!isMounted.current) return null;
      const result = await api.get(`/execution/requests/${executionId}`);
      if (TERMINAL_STATES.includes(result.status)) return result;
      setExecutionStatus(result.status === "queued" ? "queued" : "running");
    }
    return null;
  };

  const handleRun = async () => {
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

  const submitSolution = async () => {
    if (isSubmitting) return;
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
      navigate(`/student/submissions/${submission.sub_id}`, { state: { justSubmitted: true } });
    } catch (err) {
      setConfirmAction(null);
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

  const resetDraft = () => {
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

  const panelToggle = (pressed) =>
    `flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold transition-colors ${
      pressed ? "bg-psu-maroon text-white" : "text-text-muted hover:bg-bg-alt hover:text-text-main"
    }`;

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
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </Link>
            <div className="flex items-center gap-1 rounded-lg border border-border-subtle bg-bg-alt p-0.5">
              <button
                type="button"
                onClick={() => {
                  setShowProblemPanel((v) => !v);
                  if (window.innerWidth < 1536) setShowReviewPanel(false);
                }}
                aria-pressed={showProblemPanel}
                className={panelToggle(showProblemPanel)}
              >
                Problem
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowReviewPanel((v) => !v);
                  if (window.innerWidth < 1536) setShowProblemPanel(false);
                }}
                aria-pressed={showReviewPanel}
                className={panelToggle(showReviewPanel)}
              >
                Session
              </button>
            </div>
            <div className="hidden min-w-0 sm:block">
              <p className="truncate text-sm font-semibold text-text-main">{activity.title}</p>
              <p className="truncate text-[11px] text-text-muted">{activity.classLabel}</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="hidden items-center gap-2 rounded-lg border border-border-subtle px-2.5 py-1 text-xs md:flex" role="status" aria-live="polite">
              <span className={`h-2 w-2 rounded-full ${status.dot}`} aria-hidden="true" />
              <span className="text-text-muted">{status.label}</span>
            </div>
            {/* Below lg the navigation rail (and its theme control) is hidden. */}
            <div className="w-9 shrink-0 lg:hidden">
              <ThemeToggle collapsed tooltipSide="bottom" />
            </div>
            <button type="button" onClick={handleCheck} disabled={isBusy} className="btn-secondary btn-sm">
              Check structure
            </button>
            <button type="button" onClick={handleRun} disabled={isBusy} className="btn-secondary btn-sm">
              <svg width="11" height="11" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                <path d="M4 2.5v11l9-5.5-9-5.5z" />
              </svg>
              Run
            </button>
            <button
              type="button"
              onClick={() => setConfirmAction("submit")}
              disabled={isBusy || isSubmitting || !hasOwnCode}
              title={!hasOwnCode ? "Write your solution before submitting." : undefined}
              className="btn-primary btn-sm"
            >
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

        {(showProblemPanel || showReviewPanel) && (
          <button
            type="button"
            onClick={() => {
              setShowProblemPanel(false);
              setShowReviewPanel(false);
            }}
            className="fixed inset-0 z-40 bg-overlay xl:hidden"
            aria-label="Close side panel"
          />
        )}

        <div className="flex min-h-0 flex-1 overflow-hidden">
          {showProblemPanel && (
            <aside
              className="fixed inset-y-0 left-0 z-50 flex w-[88vw] max-w-[360px] flex-col overflow-hidden border-r border-border-subtle bg-bg-panel xl:static xl:z-auto xl:w-[340px]"
              aria-label="Problem statement"
            >
              <div className="flex items-start justify-between gap-3 border-b border-border-subtle p-4">
                <div className="min-w-0">
                  <p className="text-[11px] font-semibold uppercase tracking-widest text-text-brand">Problem</p>
                  <h2 className="mt-1 text-sm font-bold text-text-main">{activity.title}</h2>
                </div>
                <button
                  type="button"
                  onClick={() => setShowProblemPanel(false)}
                  className="btn-ghost btn-sm xl:hidden"
                  aria-label="Close problem panel"
                >
                  ✕
                </button>
              </div>

              <div className="flex-1 space-y-4 overflow-y-auto p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`badge ${pastDue ? "badge-danger" : "badge-gold"}`}>{pastDue ? `Past due · ${dueLabel.replace("Due ", "")}` : dueLabel}</span>
                  <span className="badge badge-neutral">{activity.activity_type === "homework" ? "Homework" : "Laboratory"}</span>
                </div>

                {activity.description && (
                  <section>
                    <h3 className="mb-1.5 text-sm font-bold text-text-main">Problem description</h3>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-text-muted">{activity.description}</p>
                  </section>
                )}

                {activity.scenario && (
                  <section>
                    <h3 className="mb-1.5 text-sm font-bold text-text-main">Real-world scenario</h3>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-text-muted">{activity.scenario}</p>
                  </section>
                )}

                {(activity.instructions || !activity.description) && (
                  <section>
                    <h3 className="mb-1.5 text-sm font-bold text-text-main">Instructions</h3>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-text-muted">
                      {activity.instructions || "No instructions were provided for this activity."}
                    </p>
                  </section>
                )}

                {activity.requirements.length > 0 && (
                  <section>
                    <h3 className="mb-1.5 text-sm font-bold text-text-main">Required structures</h3>
                    <ul className="space-y-1.5">
                      {activity.requirements.map((rule) => {
                        const count = ruleMinCount(activity.required_ast_rules[rule]);
                        return (
                          <li key={rule} className="flex items-center gap-2 text-sm text-text-muted">
                            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-psu-gold" aria-hidden="true" />
                            {ruleLabel(rule)}
                            {count > 1 ? ` (at least ${count})` : ""}
                          </li>
                        );
                      })}
                    </ul>
                  </section>
                )}

                <section>
                  <h3 className="mb-1.5 text-xs font-bold text-text-main">Sample cases</h3>
                  {sampleCases.length === 0 ? (
                    <p className="text-xs text-text-muted">No sample input/output was published for this activity.</p>
                  ) : (
                    <div className="space-y-3">
                      {sampleCases.map((sample) => (
                        <div key={sample.test_case_id} className="rounded-lg border border-border-subtle bg-bg-alt p-3">
                          <p className="mb-1.5 text-[11px] font-semibold text-text-main">{sample.name}</p>
                          {sample.standard_input && (
                            <>
                              <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">Input</p>
                              <pre className="mb-2 overflow-x-auto whitespace-pre-wrap font-mono text-[11px] text-text-main">{sample.standard_input}</pre>
                            </>
                          )}
                          <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">Expected output</p>
                          <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-[11px] text-text-main">{sample.expected_output}</pre>
                        </div>
                      ))}
                    </div>
                  )}
                </section>

                <section className="rounded-lg border border-psu-maroon/15 bg-selected p-3">
                  <h3 className="text-xs font-bold text-text-brand">Clipboard policy</h3>
                  <p className="mt-1 text-xs leading-relaxed text-text-muted">
                    {activity.pasteDisabled
                      ? "Pasting is turned off for this activity. Type your solution in the editor."
                      : "Pasting from outside the workspace is blocked. Use the Copy, Cut and Paste buttons above the editor to move code within it."}
                  </p>
                </section>
              </div>
            </aside>
          )}

          <main className="flex min-w-0 flex-1 flex-col">
            <div className="flex shrink-0 items-center justify-between gap-2 border-b border-border-subtle bg-bg-panel px-3 py-1.5">
              <span className="font-mono text-xs font-semibold text-text-main">main.py</span>
              <div className="flex items-center gap-1.5">
                <button type="button" onClick={copySelection} className="btn-ghost btn-sm" title="Copy selection to workspace clipboard">
                  Copy
                </button>
                <button type="button" onClick={cutSelection} className="btn-ghost btn-sm" title="Cut selection to workspace clipboard">
                  Cut
                </button>
                <button
                  type="button"
                  onClick={pasteInternal}
                  disabled={activity.pasteDisabled}
                  className="btn-ghost btn-sm"
                  title={activity.pasteDisabled ? "Pasting is turned off for this activity" : "Paste from workspace clipboard"}
                >
                  Paste
                </button>
                <span className="mx-1 h-4 w-px bg-border-subtle" aria-hidden="true" />
                <button type="button" onClick={() => setConfirmAction("reset")} className="btn-ghost btn-sm text-text-rose hover:text-text-rose">
                  Reset
                </button>
              </div>
            </div>

            <div className="relative min-h-0 flex-1">
              <div
                className="h-full w-full"
                onPasteCapture={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  recordBlockedPaste();
                }}
                onCopyCapture={(e) => {
                  e.preventDefault();
                  copySelection();
                }}
                onCutCapture={(e) => {
                  e.preventDefault();
                  cutSelection();
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

          {showReviewPanel && (
            <aside
              className="fixed inset-y-0 right-0 z-50 flex w-[88vw] max-w-[320px] flex-col overflow-hidden border-l border-border-subtle bg-bg-panel xl:static xl:z-auto xl:w-[270px]"
              aria-label="Session indicators"
            >
              <div className="flex items-center justify-between border-b border-border-subtle p-4">
                <h2 className="text-[11px] font-semibold uppercase tracking-widest text-text-muted">Session</h2>
                <button type="button" onClick={() => setShowReviewPanel(false)} className="btn-ghost btn-sm" aria-label="Close session panel">
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
          pastDue
            ? "This activity is past its due date. A late submission is accepted only if your instructor allowed you another attempt."
            : "Your current code becomes your latest attempt. You can submit again while the activity is open; the latest accepted attempt is the official one."
        }
        confirmText="Submit"
        loadingText="Submitting…"
        isLoading={isSubmitting}
        onConfirm={submitSolution}
        onCancel={() => setConfirmAction(null)}
      />
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
