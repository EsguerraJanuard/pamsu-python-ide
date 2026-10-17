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

  const handleSubmit = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setFeedback(null);
    setSubmitError("");
    try {
      const result = await api.post(`/practice/tasks/${taskId}/submit`, { code });
      if (isMounted.current) setFeedback(result);
    } catch (err) {
      if (!isMounted.current) return;
      if (err?.status === NETWORK_ERROR_STATUS) setSubmitError("Could not reach the server. Your code was not evaluated.");
      else if (err?.status === TIMEOUT_ERROR_STATUS) setSubmitError("The evaluator took too long to respond. The code runner may be offline — please try again.");
      else if (err?.status === 429) setSubmitError("You're submitting too quickly. Wait a few seconds and try again.");
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
            <ThemeToggle collapsed />
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
            {isSubmitting ? "Evaluating…" : "Run & check"}
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
              {feedback?.execution_feedback || (
                <span className="text-text-muted">Select Run &amp; check to evaluate your solution. Its output appears here.</span>
              )}
            </pre>
          </div>
        </section>
      </div>

      <Statusbar contextLabel={`Practice · ${tabSwitchCount} tab switches · ${blockedPasteCount} blocked pastes · ${mouseLeaveCount} pointer exits`} />
    </div>
  );
}
