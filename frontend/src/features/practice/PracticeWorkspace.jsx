import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import MonacoEditor from "@monaco-editor/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import Statusbar from "../../components/layout/Statusbar";
import { EmptyState, ErrorState, LoadingState } from "../../components/ui/StateViews";
import { useBehaviorTracking } from "../../hooks/useBehaviorTracking";
import { useEditorSettings } from "../../hooks/useEditorSettings";
import api, { getErrorMessage, NETWORK_ERROR_STATUS, TIMEOUT_ERROR_STATUS } from "../../services/api";
import { useTheme } from "../theme/ThemeContext";
import ThemeToggle from "../theme/ThemeToggle";
import { defineEditorThemes, editorThemeFor } from "../workspace/editorThemes";

// The server saves the attempt and answers at once with status "pending";
// Judge0 runs the code in the background and the page polls the attempt
// until it is "completed" or "failed". The server closes an attempt that has
// waited 2 minutes, so polling always ends. Servers from before this change
// still run Judge0 inside the submit request (up to 15 s) and answer with the
// verdict and no status, so the request keeps a longer timeout.
const PRACTICE_SUBMIT_TIMEOUT_MS = 45000;
const ATTEMPT_POLL_INTERVAL_MS = 1500;
const ATTEMPT_MAX_WAIT_MS = 130000;
const NOT_CHECKED_MESSAGE = "Your code could not be checked this time. It does not count as a try — please run it again.";

// After a failed submission the server writes an AI Tutor hint in the
// background and answers "processing" until it is ready. Poll at this pace
// and give up after about 80 s: the server retries Gemini when it is busy,
// for at most 70 s (ai_tutor_service.worst_case_generation_seconds).
const HINT_POLL_INTERVAL_MS = 2000;
const HINT_MAX_POLLS = 40;

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function BackToModules() {
  return (
    <Link to="/student/practice" className="btn-ghost btn-sm">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      Modules
    </Link>
  );
}

function CenteredFrame({ children }) {
  return (
    <div className="flex h-screen flex-col bg-bg-base text-text-main">
      <header className="flex h-14 shrink-0 items-center border-b border-border-subtle bg-bg-panel px-4">
        <BackToModules />
      </header>
      <main className="flex flex-1 items-start justify-center overflow-y-auto p-6">
        <div className="w-full max-w-xl pt-6">{children}</div>
      </main>
    </div>
  );
}

export default function PracticeWorkspace() {
  const [searchParams] = useSearchParams();
  const taskId = searchParams.get("task");
  if (!taskId || !/^\d+$/.test(taskId)) {
    return (
      <CenteredFrame>
        <EmptyState
          title="Choose a practice task"
          message="Open a task from Solo Practice to start coding."
          action={
            <Link to="/student/practice" className="btn-primary">
              Go to Solo Practice
            </Link>
          }
        />
      </CenteredFrame>
    );
  }
  return <PracticeTask key={taskId} taskId={Number(taskId)} />;
}

function PracticeTask({ taskId }) {
  const navigate = useNavigate();
  const { settings } = useEditorSettings();
  const { tabSwitchCount, mouseLeaveCount, blockedPasteCount, setBlockedPasteCount } = useBehaviorTracking({ sessionId: null });
  const isMounted = useRef(true);

  const [state, setState] = useState({ status: "loading" });
  const [viewMode, setViewMode] = useState("lesson");
  const [code, setCode] = useState("");
  const { effectiveTheme } = useTheme();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [submitError, setSubmitError] = useState("");
  const [pasteNotice, setPasteNotice] = useState(false);
  // null | { status: "loading" } | { status: "ready", hint } | { status: "error", message, attemptId, retry? }
  const [tutor, setTutor] = useState(null);
  // Bumped for every submission, so polling for an older attempt stops.
  const hintRun = useRef(0);
  const submitRun = useRef(0);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const loadTask = useCallback(async () => {
    setState({ status: "loading" });
    try {
      const modules = await api.get("/practice/modules");
      const allTasks = (Array.isArray(modules) ? modules : []).flatMap((m) => (m.tasks || []).map((t) => ({ ...t, module: m })));
      const index = allTasks.findIndex((t) => t.task_id === taskId);
      if (index === -1) {
        setState({ status: "not_found" });
        return;
      }
      const task = allTasks[index];
      if (task.is_locked) {
        setState({ status: "locked", task });
        return;
      }
      setCode(task.starter_code || "");
      setState({ status: "ready", task, nextTaskId: allTasks[index + 1]?.task_id ?? null });
    } catch (err) {
      setState({ status: "error", error: err });
    }
  }, [taskId]);

  useEffect(() => {
    loadTask();
  }, [loadTask]);

  const recordBlockedPaste = () => {
    setBlockedPasteCount((c) => c + 1);
    setPasteNotice(true);
  };

  // retry: ask the server to start over after it reported `unavailable`.
  const fetchHint = useCallback(async (attemptId, { retry = false } = {}) => {
    const run = ++hintRun.current;
    const isCurrent = () => isMounted.current && hintRun.current === run;
    setTutor({ status: "loading" });
    try {
      for (let poll = 0; poll <= HINT_MAX_POLLS; poll += 1) {
        if (poll > 0) await wait(HINT_POLL_INTERVAL_MS);
        if (!isCurrent()) return;
        const query = retry && poll === 0 ? "?retry=true" : "";
        const result = await api.post(`/practice/attempts/${attemptId}/ai-hint${query}`);
        if (!isCurrent()) return;
        if (result?.unavailable) {
          setTutor({ status: "error", attemptId, retry: true, message: "The AI Tutor is busy right now. Try again in a moment." });
          return;
        }
        if (result?.status === "completed" && result.ai_hint) {
          setTutor({ status: "ready", hint: result.ai_hint });
          return;
        }
      }
      setTutor({ status: "error", attemptId, message: "The AI Tutor is taking longer than usual." });
    } catch (err) {
      if (!isCurrent()) return;
      setTutor({
        status: "error",
        attemptId,
        message:
          err?.status === 429
            ? "You've asked for many hints in a short time. Wait a few minutes and try again."
            : "The AI Tutor is unavailable right now. Review the output and try again.",
      });
    }
  }, []);

  // Polls a pending attempt until Judge0's verdict is recorded. Returns null
  // when the page moved on (unmounted or a newer submission started).
  const waitForVerdict = async (attemptId, run) => {
    const isCurrent = () => isMounted.current && submitRun.current === run;
    const deadline = Date.now() + ATTEMPT_MAX_WAIT_MS;
    let failedPolls = 0;
    while (Date.now() < deadline) {
      await wait(ATTEMPT_POLL_INTERVAL_MS);
      if (!isCurrent()) return null;
      let attempt;
      try {
        attempt = await api.get(`/practice/attempts/${attemptId}`);
        failedPolls = 0;
      } catch (err) {
        // The attempt is saved and keeps running: ride out a brief outage.
        failedPolls += 1;
        if (failedPolls >= 3) throw err;
        continue;
      }
      if (!isCurrent()) return null;
      if (attempt?.status !== "pending") return attempt;
    }
    return { status: "still_pending" };
  };

  const handleSubmit = async () => {
    if (isSubmitting) return;
    const run = ++submitRun.current;
    setIsSubmitting(true);
    setFeedback(null);
    setSubmitError("");
    hintRun.current += 1;
    setTutor(null);
    try {
      let result = await api.post(`/practice/tasks/${taskId}/submit`, { code }, {}, PRACTICE_SUBMIT_TIMEOUT_MS);
      if (!isMounted.current) return;
      // Older servers answer with the verdict itself (no status field).
      if (result?.status === "pending") {
        result = await waitForVerdict(result.attempt_id, run);
        if (!result) return;
      }
      if (result?.status === "still_pending") {
        setSubmitError("Your code is still being checked. Wait a moment, then run it again.");
        return;
      }
      if (result?.status === "failed") {
        setSubmitError(NOT_CHECKED_MESSAGE);
        return;
      }
      setFeedback(result);
      // An older backend sends no attempt_id; it has no tutor to ask.
      if (result && !result.is_successful && Number.isInteger(result.attempt_id)) fetchHint(result.attempt_id);
    } catch (err) {
      if (!isMounted.current || submitRun.current !== run) return;
      if (err?.status === NETWORK_ERROR_STATUS) setSubmitError("Could not reach the server. Your code was not evaluated.");
      else if (err?.status === TIMEOUT_ERROR_STATUS) setSubmitError("The evaluator took too long to respond. The code runner may be offline — please try again.");
      else if (err?.status === 429) setSubmitError("You're submitting too quickly. Wait a few seconds and try again.");
      else if (err?.status === 503) setSubmitError("The code runner is unavailable right now. Your code was not evaluated — please try again shortly.");
      else setSubmitError(getErrorMessage(err, "Your code could not be evaluated."));
    } finally {
      if (isMounted.current) setIsSubmitting(false);
    }
  };

  if (state.status === "loading") {
    return (
      <CenteredFrame>
        <LoadingState label="Loading practice task…" />
      </CenteredFrame>
    );
  }
  if (state.status === "error") {
    return (
      <CenteredFrame>
        <ErrorState error={state.error} resource="this practice task" onRetry={loadTask} />
      </CenteredFrame>
    );
  }
  if (state.status === "not_found") {
    return (
      <CenteredFrame>
        <EmptyState icon="search" title="Practice task not found" message="This task doesn't exist or is no longer published." />
      </CenteredFrame>
    );
  }
  if (state.status === "locked") {
    return (
      <CenteredFrame>
        <EmptyState
          icon="lock"
          title="This task is locked"
          message="Complete the earlier tasks in Solo Practice to unlock it."
          action={
            <Link to="/student/practice" className="btn-primary">
              Back to modules
            </Link>
          }
        />
      </CenteredFrame>
    );
  }

  const { task, nextTaskId } = state;

  if (viewMode === "lesson") {
    return (
      <div className="flex h-screen flex-col overflow-hidden bg-bg-base text-text-main">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-border-subtle bg-bg-panel px-4">
          <BackToModules />
          <span className="truncate text-xs text-text-muted">{task.module?.title}</span>
        </header>
        <main className="min-w-0 flex-1 overflow-y-auto px-5 py-10">
          <article className="mx-auto w-full max-w-3xl">
            <span className="badge badge-gold mb-3">Lesson</span>
            <h1 className="mb-6 text-3xl font-bold tracking-tight">{task.title}</h1>
            <div className="markdown-body mb-10">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{task.instructions || "No lesson content was provided."}</ReactMarkdown>
            </div>
            <div className="flex justify-end border-t border-border-subtle pb-16 pt-6">
              <button type="button" onClick={() => setViewMode("coding")} className="btn-primary px-6 py-3 text-base">
                Start coding challenge
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </button>
            </div>
          </article>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-bg-base text-text-main">
      <header className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-b border-border-subtle bg-bg-panel px-3 py-2 sm:px-4">
        <div className="flex min-w-0 items-center gap-2">
          <BackToModules />
          <div className="min-w-0">
            <h1 className="truncate text-sm font-semibold">{task.title}</h1>
            <p className="truncate text-[11px] text-text-muted">{task.module?.title}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Same student theme preference as the sidebar (this view has no sidebar). */}
          <div className="w-9 shrink-0">
            <ThemeToggle collapsed tooltipSide="bottom" />
          </div>
          {feedback?.is_successful && nextTaskId && (
            <button
              type="button"
              onClick={() => navigate(`/student/practice/workspace?task=${nextTaskId}`)}
              className="btn-secondary btn-sm"
            >
              Next task →
            </button>
          )}
          <button type="button" onClick={handleSubmit} disabled={isSubmitting} className="btn-primary btn-sm">
            {isSubmitting && (
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" aria-hidden="true" />
            )}
            {isSubmitting ? "Checking…" : "Run & check"}
          </button>
        </div>
      </header>

      {pasteNotice && (
        <div className="flex shrink-0 items-center justify-between gap-3 border-b border-psu-maroon/15 bg-selected px-4 py-1.5 text-xs text-text-brand" role="status">
          <span>Pasting from outside the editor is blocked during practice. Type your solution instead.</span>
          <button type="button" onClick={() => setPasteNotice(false)} className="font-semibold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden md:flex-row">
        <section className="flex max-h-[40vh] w-full flex-col overflow-y-auto border-b border-border-subtle bg-bg-panel md:max-h-none md:w-2/5 md:border-b-0 md:border-r lg:w-1/3" aria-label="Instructions and feedback">
          <div className="p-5">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 className="text-sm font-semibold">Instructions</h2>
              <button type="button" onClick={() => setViewMode("lesson")} className="text-xs font-semibold text-text-brand hover:underline">
                Read full lesson
              </button>
            </div>
            <div className="markdown-body markdown-compact">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{task.instructions || ""}</ReactMarkdown>
            </div>

            {submitError && (
              <p className="mt-6 rounded-lg border border-psu-red/20 bg-psu-red/[0.05] p-3 text-sm text-text-rose" role="alert">
                {submitError}
              </p>
            )}

            {feedback && (
              <div
                className={`mt-6 rounded-xl border p-4 ${
                  feedback.is_successful ? "border-emerald-600/25 bg-emerald-600/[0.05]" : "border-psu-red/20 bg-psu-red/[0.04]"
                }`}
                role="status"
                aria-live="polite"
              >
                <h3 className={`text-sm font-bold ${feedback.is_successful ? "text-text-emerald" : "text-text-rose"}`}>
                  {feedback.is_successful ? "Passed" : "Not passed yet"}
                </h3>
                <p className="mt-1 text-sm text-text-main">{feedback.message}</p>
                {feedback.ast_feedback?.length > 0 && (
                  <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-text-main">
                    {feedback.ast_feedback.map((msg, idx) => (
                      <li key={idx}>{msg}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {tutor && feedback && !feedback.is_successful && (
              <div className="mt-4 rounded-xl border border-psu-gold/40 bg-psu-gold/[0.08] p-4" aria-live="polite" aria-busy={tutor.status === "loading"}>
                <h3 className="flex items-center gap-2 text-sm font-bold text-text-amber">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z" />
                  </svg>
                  AI Tutor hint
                </h3>
                {tutor.status === "loading" && (
                  <p className="mt-2 flex items-center gap-2 text-sm text-text-muted">
                    <span className="h-3.5 w-3.5 shrink-0 animate-spin rounded-full border-2 border-psu-gold/30 border-t-psu-gold" aria-hidden="true" />
                    Looking at your code…
                  </p>
                )}
                {tutor.status === "ready" && (
                  <div className="markdown-body markdown-compact mt-2">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{tutor.hint}</ReactMarkdown>
                  </div>
                )}
                {tutor.status === "error" && (
                  <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-sm text-text-muted">
                    <span>{tutor.message}</span>
                    <button type="button" onClick={() => fetchHint(tutor.attemptId, { retry: tutor.retry })} className="font-semibold text-text-brand hover:underline">
                      Try again
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </section>

        <section className="flex min-h-0 min-w-0 flex-1 flex-col" aria-label="Code editor">
          <div
            className="min-h-0 flex-1"
            onPasteCapture={(event) => {
              event.preventDefault();
              event.stopPropagation();
              recordBlockedPaste();
            }}
          >
            <MonacoEditor
              height="100%"
              language="python"
              theme={editorThemeFor(effectiveTheme)}
              beforeMount={defineEditorThemes}
              value={code}
              onChange={(value) => setCode(value ?? "")}
              loading={<LoadingState label="Starting editor…" />}
              options={{
                minimap: { enabled: Boolean(settings.minimap) },
                fontSize: settings.fontSize,
                tabSize: settings.tabSize,
                wordWrap: settings.wordWrap,
                fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
                automaticLayout: true,
                scrollBeyondLastLine: false,
                contextmenu: false,
              }}
            />
          </div>
          <div className="flex h-44 shrink-0 flex-col border-t border-border-subtle bg-bg-panel">
            <div className="border-b border-border-subtle px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-text-muted">
              Output
            </div>
            <pre className="min-h-0 flex-1 overflow-auto whitespace-pre-wrap p-4 font-mono text-xs text-text-main">
              {isSubmitting ? (
                <span className="text-text-muted">Running your code in the sandbox…</span>
              ) : (
                feedback?.execution_feedback || (
                  <span className="text-text-muted">Select Run &amp; check to evaluate your solution. Its output appears here.</span>
                )
              )}
            </pre>
          </div>
        </section>
      </div>

      <Statusbar contextLabel={`Practice · ${tabSwitchCount} tab switches · ${blockedPasteCount} blocked pastes · ${mouseLeaveCount} pointer exits`} />
    </div>
  );
}
