import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";

const DEFAULT_CODE = `# Fibonacci Sequence
# Write your solution below.

def fibonacci(n):
    sequence = []

    # TODO: implement the solution

    return sequence


n = int(input())
print(fibonacci(n))
`;

const PREVIEW_ACTIVITY = {
  courseCode: "CCS101",
  title: "Lab Activity 3 — Fibonacci Sequence",
  fileName: "main.py",
  activityType: "Graded laboratory",
  dueLabel: "Preview activity",
  description:
    "Write a Python program that generates the first n Fibonacci numbers.",
  requirements: [
    "Define and call a function",
    "Use a loop",
    "Accept input using input()",
    "Display the generated sequence",
  ],
  expectedOutput: "[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]",
};

const EXECUTION_STATUS = {
  idle: {
    label: "Ready",
    dotClass: "bg-white/30",
    textClass: "text-white/40",
  },
  unavailable: {
    label: "Backend not connected",
    dotClass: "bg-amber-500",
    textClass: "text-amber-400",
  },
};

function loadDraft(storageKey) {
  try {
    return localStorage.getItem(storageKey) || DEFAULT_CODE;
  } catch {
    return DEFAULT_CODE;
  }
}

function formatEventTime() {
  return new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function Workspace() {
  const [searchParams] = useSearchParams();
  const activityId = searchParams.get("activity") || "preview";
  const draftStorageKey = `pamsu-workspace-draft-${activityId}`;

  const editorRef = useRef(null);

  const [code, setCode] = useState(() =>
    loadDraft(draftStorageKey),
  );
  const [standardInput, setStandardInput] = useState("10");
  const [output, setOutput] = useState(
    "The editor is ready. Code execution will appear here after the sandbox API is connected.",
  );
  const [activePanel, setActivePanel] = useState("output");
  const [executionStatus, setExecutionStatus] =
    useState("idle");
  const [notice, setNotice] = useState("");
  const [internalClipboard, setInternalClipboard] =
    useState("");
  const [blockedPasteCount, setBlockedPasteCount] =
    useState(0);
  const [lastBlockedPasteAt, setLastBlockedPasteAt] =
    useState("");
  const [tabSwitchCount, setTabSwitchCount] = useState(0);
  const [showBehaviorNotice, setShowBehaviorNotice] =
    useState(false);

  const [showProblemPanel, setShowProblemPanel] = useState(
    () => window.matchMedia("(min-width: 1280px)").matches,
  );
  const [showReviewPanel, setShowReviewPanel] =
    useState(false);

  const lineCount = code.split("\n").length;
  const status =
    EXECUTION_STATUS[executionStatus] ??
    EXECUTION_STATUS.idle;

  useEffect(() => {
    const autosaveTimer = window.setTimeout(() => {
      try {
        localStorage.setItem(draftStorageKey, code);
      } catch {
        // Keep the editor usable when browser storage is unavailable.
      }
    }, 500);

    return () => {
      window.clearTimeout(autosaveTimer);
    };
  }, [code, draftStorageKey]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        return;
      }

      setTabSwitchCount((currentCount) => currentCount + 1);
      setShowBehaviorNotice(true);
    };

    document.addEventListener(
      "visibilitychange",
      handleVisibilityChange,
    );

    return () => {
      document.removeEventListener(
        "visibilitychange",
        handleVisibilityChange,
      );
    };
  }, []);

  useEffect(() => {
    const desktopQuery = window.matchMedia(
      "(min-width: 1280px)",
    );

    const handleScreenChange = (event) => {
      if (event.matches) {
        setShowProblemPanel(true);
        return;
      }

      setShowProblemPanel(false);
      setShowReviewPanel(false);
    };

    desktopQuery.addEventListener(
      "change",
      handleScreenChange,
    );

    return () => {
      desktopQuery.removeEventListener(
        "change",
        handleScreenChange,
      );
    };
  }, []);

  const updateCodeAndSelection = (
    replacement,
    selectionStart,
    selectionEnd,
  ) => {
    const updatedCode =
      code.slice(0, selectionStart) +
      replacement +
      code.slice(selectionEnd);

    const nextCursorPosition =
      selectionStart + replacement.length;

    setCode(updatedCode);

    window.requestAnimationFrame(() => {
      const editor = editorRef.current;

      if (!editor) {
        return;
      }

      editor.focus();
      editor.setSelectionRange(
        nextCursorPosition,
        nextCursorPosition,
      );
    });
  };

  const copySelectionToInternalBuffer = () => {
    const editor = editorRef.current;

    if (!editor) {
      return;
    }

    const { selectionStart, selectionEnd } = editor;

    if (selectionStart === selectionEnd) {
      setNotice("Select code before copying.");
      return;
    }

    setInternalClipboard(
      code.slice(selectionStart, selectionEnd),
    );
    setNotice("Selection copied to the internal IDE buffer.");
  };

  const cutSelectionToInternalBuffer = () => {
    const editor = editorRef.current;

    if (!editor) {
      return;
    }

    const { selectionStart, selectionEnd } = editor;

    if (selectionStart === selectionEnd) {
      setNotice("Select code before cutting.");
      return;
    }

    setInternalClipboard(
      code.slice(selectionStart, selectionEnd),
    );

    updateCodeAndSelection(
      "",
      selectionStart,
      selectionEnd,
    );

    setNotice("Selection moved to the internal IDE buffer.");
  };

  const pasteFromInternalBuffer = () => {
    const editor = editorRef.current;

    if (!editor) {
      return;
    }

    if (!internalClipboard) {
      setNotice("The internal IDE buffer is empty.");
      return;
    }

    updateCodeAndSelection(
      internalClipboard,
      editor.selectionStart,
      editor.selectionEnd,
    );

    setNotice("Code pasted from the internal IDE buffer.");
  };

  const recordBlockedPaste = () => {
    setBlockedPasteCount(
      (currentCount) => currentCount + 1,
    );
    setLastBlockedPasteAt(formatEventTime());
    setShowBehaviorNotice(true);
    setNotice(
      "External clipboard paste was blocked. Use the internal IDE buffer.",
    );
  };

  const handleNativeCopy = (event) => {
    event.preventDefault();
    copySelectionToInternalBuffer();
  };

  const handleNativeCut = (event) => {
    event.preventDefault();
    cutSelectionToInternalBuffer();
  };

  const handleNativePaste = (event) => {
    event.preventDefault();
    recordBlockedPaste();
  };

  const handleEditorKeyDown = (event) => {
    const editor = editorRef.current;

    if (!editor) {
      return;
    }

    if (event.key === "Tab") {
      event.preventDefault();

      updateCodeAndSelection(
        "    ",
        editor.selectionStart,
        editor.selectionEnd,
      );

      return;
    }

    if (
      (event.ctrlKey || event.metaKey) &&
      event.key.toLowerCase() === "s"
    ) {
      event.preventDefault();

      try {
        localStorage.setItem(draftStorageKey, code);
        setNotice("Draft saved locally.");
      } catch {
        setNotice("Browser storage is unavailable.");
      }
    }
  };

  const handleRun = () => {
    setExecutionStatus("unavailable");
    setActivePanel("output");

    setOutput(
      [
        "Execution request was not sent.",
        "",
        "The isolated Python sandbox API is not connected yet.",
        "Student code will not be executed directly in React or FastAPI.",
        "",
        `Standard input prepared: ${
          standardInput || "(empty)"
        }`,
      ].join("\n"),
    );
  };

  const handleCheck = () => {
    setExecutionStatus("unavailable");
    setActivePanel("analysis");
    setNotice(
      "AST checking requires the authenticated backend analysis endpoint.",
    );
  };

  const handleSubmit = () => {
    setExecutionStatus("unavailable");
    setNotice(
      "Submission is not connected yet. Your code remains saved as a local draft.",
    );
  };

  const handleResetDraft = () => {
    const confirmed = window.confirm(
      "Reset this draft to the starter code?",
    );

    if (!confirmed) {
      return;
    }

    setCode(DEFAULT_CODE);
    setOutput("Draft reset to the starter code.");
    setExecutionStatus("idle");
    setNotice("Draft reset successfully.");
  };

  const toggleProblemPanel = () => {
    const willOpen = !showProblemPanel;

    setShowProblemPanel(willOpen);

    if (willOpen && window.innerWidth < 1536) {
      setShowReviewPanel(false);
    }
  };

  const toggleReviewPanel = () => {
    const willOpen = !showReviewPanel;

    setShowReviewPanel(willOpen);

    if (willOpen && window.innerWidth < 1536) {
      setShowProblemPanel(false);
    }
  };

  const closeMobilePanels = () => {
    setShowProblemPanel(false);
    setShowReviewPanel(false);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white">
      <div className="hidden lg:flex">
        <Sidebar />
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex min-h-14 shrink-0 flex-wrap items-center justify-between gap-3 border-b border-white/[0.08] px-3 py-2 sm:px-4">
          <div className="flex min-w-0 items-center gap-2">
            <button
              type="button"
              onClick={toggleProblemPanel}
              aria-pressed={showProblemPanel}
              className={`rounded-md border px-2.5 py-1.5 text-[10px] font-medium transition-colors ${
                showProblemPanel
                  ? "border-blue-500/30 bg-blue-500/10 text-blue-400"
                  : "border-white/[0.08] text-white/40 hover:text-white/70"
              }`}
            >
              Problem
            </button>

            <button
              type="button"
              onClick={toggleReviewPanel}
              aria-pressed={showReviewPanel}
              className={`rounded-md border px-2.5 py-1.5 text-[10px] font-medium transition-colors ${
                showReviewPanel
                  ? "border-violet-500/30 bg-violet-500/10 text-violet-400"
                  : "border-white/[0.08] text-white/40 hover:text-white/70"
              }`}
            >
              Session Review
            </button>

            <div className="hidden min-w-0 sm:block">
              <p className="truncate text-[9px] uppercase tracking-widest text-white/30">
                {PREVIEW_ACTIVITY.courseCode} ·{" "}
                {PREVIEW_ACTIVITY.activityType}
              </p>

              <h1 className="truncate text-xs font-semibold">
                {PREVIEW_ACTIVITY.title}
              </h1>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div
              className={`hidden items-center gap-2 rounded-md border border-white/[0.06] bg-white/[0.03] px-2.5 py-1.5 text-[10px] sm:flex ${status.textClass}`}
              role="status"
              aria-live="polite"
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${status.dotClass}`}
                aria-hidden="true"
              />

              {status.label}
            </div>

            <button
              type="button"
              onClick={handleCheck}
              className="rounded-md border border-blue-500/30 bg-blue-500/10 px-2.5 py-1.5 text-[10px] font-semibold text-blue-400 transition-colors hover:bg-blue-500/20 sm:px-3 sm:text-xs"
            >
              Check
            </button>

            <button
              type="button"
              onClick={handleRun}
              className="flex items-center gap-1.5 rounded-md border border-green-500/30 bg-green-500/10 px-2.5 py-1.5 text-[10px] font-semibold text-green-400 transition-colors hover:bg-green-500/20 sm:px-3 sm:text-xs"
            >
              <svg
                width="10"
                height="10"
                viewBox="0 0 24 24"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M5 3l14 9-14 9V3z" />
              </svg>

              Run
            </button>

            <button
              type="button"
              onClick={handleSubmit}
              className="rounded-md bg-violet-500 px-2.5 py-1.5 text-[10px] font-bold text-[#0f1117] transition-colors hover:bg-violet-400 sm:px-3 sm:text-xs"
            >
              Submit
            </button>
          </div>
        </header>

        {showBehaviorNotice && (
          <div
            className="flex shrink-0 items-center justify-between gap-3 border-b border-amber-500/20 bg-amber-500/[0.07] px-4 py-2 text-[10px] text-amber-300"
            role="status"
          >
            <span className="truncate">
              Recorded: {tabSwitchCount} tab{" "}
              {tabSwitchCount === 1 ? "switch" : "switches"} and{" "}
              {blockedPasteCount} blocked paste{" "}
              {blockedPasteCount === 1 ? "attempt" : "attempts"}.
              Clipboard contents are not stored.
            </span>

            <button
              type="button"
              onClick={() => setShowBehaviorNotice(false)}
              className="shrink-0 text-amber-300 hover:text-white"
            >
              Dismiss
            </button>
          </div>
        )}

        {notice && (
          <div
            className="flex shrink-0 items-center justify-between gap-3 border-b border-blue-500/10 bg-blue-500/[0.04] px-4 py-2 text-[10px] text-blue-300"
            role="status"
            aria-live="polite"
          >
            <span className="truncate">{notice}</span>

            <button
              type="button"
              onClick={() => setNotice("")}
              className="shrink-0 text-blue-300/60 hover:text-blue-200"
              aria-label="Dismiss notice"
            >
              ×
            </button>
          </div>
        )}

        {(showProblemPanel || showReviewPanel) && (
          <button
            type="button"
            onClick={closeMobilePanels}
            className="fixed inset-0 z-40 bg-black/60 xl:hidden"
            aria-label="Close workspace panel"
          />
        )}

        <div className="flex min-h-0 flex-1 overflow-hidden">
          <aside
            className={`fixed inset-y-0 left-0 z-50 w-[88vw] max-w-[300px] flex-col overflow-hidden border-r border-white/[0.08] bg-[#0f1117] xl:static xl:z-auto xl:w-[240px] xl:max-w-none ${
              showProblemPanel ? "flex" : "hidden"
            }`}
          >
            <div className="flex items-start justify-between gap-3 border-b border-white/[0.08] p-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-widest text-white/40">
                  Problem
                </span>

                <h2 className="mt-2 text-sm font-semibold">
                  {PREVIEW_ACTIVITY.title}
                </h2>
              </div>

              <button
                type="button"
                onClick={() => setShowProblemPanel(false)}
                className="rounded px-2 py-1 text-white/30 hover:bg-white/[0.05] hover:text-white xl:hidden"
                aria-label="Close problem panel"
              >
                ×
              </button>
            </div>

            <div className="flex-1 space-y-6 overflow-y-auto p-4">
              <span className="inline-block rounded border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-[9px] text-amber-400">
                {PREVIEW_ACTIVITY.dueLabel}
              </span>

              <section>
                <h3 className="mb-2 text-xs font-semibold text-white/70">
                  Instructions
                </h3>

                <p className="text-[11px] leading-relaxed text-white/50">
                  {PREVIEW_ACTIVITY.description}
                </p>
              </section>

              <section>
                <h3 className="mb-3 text-xs font-semibold text-white/70">
                  Requirements
                </h3>

                <ul className="space-y-2">
                  {PREVIEW_ACTIVITY.requirements.map(
                    (requirement) => (
                      <li
                        key={requirement}
                        className="flex items-start gap-2 text-[11px] text-white/50"
                      >
                        <span
                          className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-400"
                          aria-hidden="true"
                        />

                        {requirement}
                      </li>
                    ),
                  )}
                </ul>
              </section>

              <section>
                <h3 className="mb-2 text-xs font-semibold text-white/70">
                  Expected output
                </h3>

                <pre className="overflow-x-auto rounded-lg border border-white/[0.08] bg-[#1a1d27] p-3 font-mono text-[10px] text-green-400">
                  {PREVIEW_ACTIVITY.expectedOutput}
                </pre>
              </section>

              <section className="rounded-lg border border-blue-500/15 bg-blue-500/[0.05] p-3">
                <h3 className="text-[11px] font-semibold text-blue-300">
                  Paste policy
                </h3>

                <p className="mt-1 text-[10px] leading-relaxed text-white/40">
                  Native clipboard paste is blocked. Use the internal
                  IDE copy, cut, and paste controls.
                </p>
              </section>
            </div>
          </aside>

          <main className="flex min-w-0 flex-1 flex-col bg-[#0f1117]">
            <div className="flex shrink-0 items-center justify-between border-b border-white/[0.08] bg-[#11141c]">
              <div className="flex items-center gap-2 border-t-2 border-t-amber-500 bg-[#1a1d27] px-4 py-2 text-xs">
                <span className="text-amber-400">
                  {PREVIEW_ACTIVITY.fileName}
                </span>

                <span
                  className="h-1.5 w-1.5 rounded-full bg-amber-500"
                  title="Local draft"
                />
              </div>

              <div className="flex items-center gap-0.5 overflow-x-auto px-2">
                <button
                  type="button"
                  onClick={copySelectionToInternalBuffer}
                  className="rounded px-2 py-1 text-[9px] text-white/40 hover:bg-white/[0.05] hover:text-white/80"
                >
                  Copy
                </button>

                <button
                  type="button"
                  onClick={cutSelectionToInternalBuffer}
                  className="rounded px-2 py-1 text-[9px] text-white/40 hover:bg-white/[0.05] hover:text-white/80"
                >
                  Cut
                </button>

                <button
                  type="button"
                  onClick={pasteFromInternalBuffer}
                  className="whitespace-nowrap rounded px-2 py-1 text-[9px] text-white/40 hover:bg-white/[0.05] hover:text-white/80"
                >
                  Paste internal
                </button>

                <button
                  type="button"
                  onClick={handleResetDraft}
                  className="rounded px-2 py-1 text-[9px] text-red-400/70 hover:bg-red-500/[0.08] hover:text-red-400"
                >
                  Reset
                </button>
              </div>
            </div>

            <div className="relative min-h-0 flex-1">
              <textarea
                ref={editorRef}
                value={code}
                onChange={(event) => setCode(event.target.value)}
                onKeyDown={handleEditorKeyDown}
                onCopy={handleNativeCopy}
                onCut={handleNativeCut}
                onPaste={handleNativePaste}
                spellCheck="false"
                aria-label="Python code editor"
                className="h-full w-full resize-none overflow-auto bg-[#0f1117] p-4 font-mono text-[12px] leading-6 text-white/80 outline-none sm:p-5 sm:text-[13px]"
                style={{
                  caretColor: "#f59e0b",
                  tabSize: 4,
                }}
              />

              <div className="pointer-events-none absolute bottom-2 right-3 rounded bg-black/30 px-2 py-1 font-mono text-[9px] text-white/25">
                {lineCount} {lineCount === 1 ? "line" : "lines"} ·
                autosave
              </div>
            </div>

            <section className="flex h-[clamp(170px,26vh,230px)] shrink-0 flex-col border-t border-white/[0.08]">
              <div className="flex shrink-0 items-center overflow-x-auto border-b border-white/[0.08] px-2">
                {[
                  { id: "output", label: "Output" },
                  { id: "analysis", label: "Structure" },
                  { id: "input", label: "Standard Input" },
                ].map((panel) => (
                  <button
                    key={panel.id}
                    type="button"
                    onClick={() => setActivePanel(panel.id)}
                    className={`whitespace-nowrap border-b-2 px-3 py-2 text-[10px] transition-colors ${
                      activePanel === panel.id
                        ? "border-white text-white"
                        : "border-transparent text-white/40 hover:text-white/70"
                    }`}
                  >
                    {panel.label}
                  </button>
                ))}
              </div>

              <div className="min-h-0 flex-1 overflow-auto p-3 sm:p-4">
                {activePanel === "output" && (
                  <pre className="whitespace-pre-wrap font-mono text-[11px] leading-5 text-white/60">
                    {output}
                  </pre>
                )}

                {activePanel === "analysis" && (
                  <div className="space-y-2">
                    <div className="rounded-lg border border-amber-500/15 bg-amber-500/[0.05] p-3">
                      <h3 className="text-xs font-semibold text-amber-300">
                        AST analysis not connected
                      </h3>

                      <p className="mt-1 text-[10px] leading-relaxed text-white/40">
                        Verified structure results must come from the
                        backend AST service.
                      </p>
                    </div>

                    {PREVIEW_ACTIVITY.requirements.map(
                      (requirement) => (
                        <div
                          key={requirement}
                          className="flex items-center justify-between gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2"
                        >
                          <span className="text-[10px] text-white/50">
                            {requirement}
                          </span>

                          <span className="shrink-0 text-[9px] text-white/25">
                            Not checked
                          </span>
                        </div>
                      ),
                    )}
                  </div>
                )}

                {activePanel === "input" && (
                  <div className="h-full">
                    <label
                      htmlFor="standard-input"
                      className="mb-2 block text-[10px] font-medium text-white/50"
                    >
                      Input supplied to the Python program
                    </label>

                    <textarea
                      id="standard-input"
                      value={standardInput}
                      onChange={(event) =>
                        setStandardInput(event.target.value)
                      }
                      spellCheck="false"
                      placeholder="Example: 10"
                      className="h-[120px] w-full resize-none rounded-lg border border-white/[0.08] bg-[#11141c] p-3 font-mono text-[11px] text-white/70 outline-none placeholder-white/20 focus:border-blue-500/40"
                    />
                  </div>
                )}
              </div>
            </section>
          </main>

          <aside
            className={`fixed inset-y-0 right-0 z-50 w-[88vw] max-w-[320px] flex-col overflow-hidden border-l border-white/[0.08] bg-[#0f1117] xl:static xl:z-auto xl:w-[260px] xl:max-w-none ${
              showReviewPanel ? "flex" : "hidden"
            }`}
          >
            <div className="flex items-center justify-between border-b border-white/[0.08] p-4">
              <h2 className="text-[10px] font-bold uppercase tracking-widest text-white/40">
                Session Review
              </h2>

              <button
                type="button"
                onClick={() => setShowReviewPanel(false)}
                className="rounded px-2 py-1 text-white/30 hover:bg-white/[0.05] hover:text-white"
                aria-label="Close session review"
              >
                ×
              </button>
            </div>

            <div className="flex-1 space-y-5 overflow-y-auto p-4">
              <section>
                <h3 className="mb-3 text-xs font-semibold text-white/70">
                  Execution status
                </h3>

                <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
                  <div className="flex items-center gap-2">
                    <span
                      className={`h-2 w-2 rounded-full ${status.dotClass}`}
                      aria-hidden="true"
                    />

                    <span
                      className={`text-[11px] font-medium ${status.textClass}`}
                    >
                      {status.label}
                    </span>
                  </div>

                  <p className="mt-2 text-[10px] leading-relaxed text-white/30">
                    Execution states will include queued, running,
                    completed, runtime error, timeout, output limit,
                    and memory limit.
                  </p>
                </div>
              </section>

              <section>
                <h3 className="mb-3 text-xs font-semibold text-white/70">
                  Activity indicators
                </h3>

                <div className="space-y-2">
                  <div className="flex items-center justify-between rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2">
                    <span className="text-[11px] text-white/45">
                      Tab switches
                    </span>

                    <span className="font-mono text-xs text-amber-400">
                      {tabSwitchCount}
                    </span>
                  </div>

                  <div className="flex items-center justify-between rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2">
                    <span className="text-[11px] text-white/45">
                      Blocked pastes
                    </span>

                    <span className="font-mono text-xs text-amber-400">
                      {blockedPasteCount}
                    </span>
                  </div>

                  <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2">
                    <p className="text-[11px] text-white/45">
                      Last blocked paste
                    </p>

                    <p className="mt-1 font-mono text-[10px] text-white/25">
                      {lastBlockedPasteAt || "None recorded"}
                    </p>
                  </div>
                </div>

                <p className="mt-3 text-[10px] leading-relaxed text-white/25">
                  These events are review indicators, not automatic
                  behavior scores or proof of misconduct.
                </p>
              </section>

              <section className="rounded-lg border border-green-500/15 bg-green-500/[0.05] p-3">
                <h3 className="text-[11px] font-semibold text-green-300">
                  Privacy boundary
                </h3>

                <p className="mt-1 text-[10px] leading-relaxed text-white/35">
                  Clipboard contents, browsing history, screen,
                  webcam, microphone, and every keystroke are not
                  collected.
                </p>
              </section>
            </div>
          </aside>
        </div>

        <Statusbar pythonVersion="Python 3" />
      </div>
    </div>
  );
}
