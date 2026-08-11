import { useEffect, useRef, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import MonacoEditor from "@monaco-editor/react";
import api from "../../services/api";

import Sidebar from "../../components/layout/Sidebar";
import { ThemeToggle } from "../theme/ThemeToggle";
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
    textClass: "text-text-muted",
  },
  running: {
    label: "Running...",
    dotClass: "bg-blue-500 animate-pulse",
    textClass: "text-blue-400",
  },
  completed: {
    label: "Execution complete",
    dotClass: "bg-green-500",
    textClass: "text-green-400",
  },
  failed: {
    label: "Execution failed",
    dotClass: "bg-red-500",
    textClass: "text-red-400",
  },
  unavailable: {
    label: "Backend not connected",
    dotClass: "bg-amber-500",
    textClass: "text-amber-400",
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
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const activityId = searchParams.get("activity") || "preview";
  const draftStorageKey = `pamsu-workspace-draft-${activityId}`;

  const editorRef = useRef(null);
  
  const [activity, setActivity] = useState(PREVIEW_ACTIVITY);
  const [testCases, setTestCases] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (activityId === "preview") {
      setIsLoading(false);
      return;
    }

    const loadActivity = async () => {
      try {
        const [activityRes, testCasesRes] = await Promise.all([
          api.get(`/activities/${activityId}`),
          api.get(`/activities/${activityId}/sample-test-cases`)
        ]);

        const due = activityRes.due_at ? new Date(activityRes.due_at) : null;
        let dueLabel = "No due date";
        if (due) {
          dueLabel = `Due: ${due.toLocaleDateString()}`;
        }

        setActivity({
          courseCode: `Class ${activityRes.class_id}`, // In a real app we'd fetch class details
          title: activityRes.title,
          fileName: "main.py",
          activityType: activityRes.activity_type === "laboratory" ? "Graded laboratory" : "Homework",
          dueLabel: dueLabel,
          description: activityRes.description || "",
          requirements: Object.keys(activityRes.required_ast_rules || {}),
          expectedOutput: testCasesRes.length > 0 ? testCasesRes[0].expected_output : "No expected output provided.",
        });
        setTestCases(testCasesRes);
        
        // If draft is empty but there's starter code, use starter code
        const savedDraft = loadDraft(draftStorageKey);
        if (savedDraft === DEFAULT_CODE && activityRes.starter_code) {
          setCode(activityRes.starter_code);
        }

        if (testCasesRes.length > 0 && testCasesRes[0].standard_input) {
          setStandardInput(testCasesRes[0].standard_input.trim());
        }

      } catch (err) {
        console.error("Failed to load activity", err);
        setNotice("Failed to load activity details.");
      } finally {
        setIsLoading(false);
      }
    };

    loadActivity();
  }, [activityId]);

  const [code, setCode] = useState(() =>
    loadDraft(draftStorageKey),
  );
  const [standardInput, setStandardInput] = useState("10");
  const [output, setOutput] = useState(
    "The editor is ready. Code execution will appear here after the sandbox API is connected.",
  );
  const [activePanel, setActivePanel] = useState("output");
  const [executionStatus, setExecutionStatus] = useState("idle");
  const [notice, setNotice] = useState("");
  const [visibleNotice, setVisibleNotice] = useState("");
  const [isFadingOut, setIsFadingOut] = useState(false);

  // Silky-smooth auto-dismiss fade animation for notice message
  useEffect(() => {
    if (!notice) return;

    setVisibleNotice(notice);
    setIsFadingOut(false);

    const fadeTimer = setTimeout(() => {
      setIsFadingOut(true);
    }, 2500);

    const clearTimer = setTimeout(() => {
      setVisibleNotice("");
      setNotice("");
      setIsFadingOut(false);
    }, 3000);

    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(clearTimer);
    };
  }, [notice]);
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

  // Resizable Problem Panel State
  const [panelWidth, setPanelWidth] = useState(() => {
    const saved = localStorage.getItem("pamsu_problem_panel_width");
    return saved ? parseInt(saved, 10) : 320;
  });
  const [isResizing, setIsResizing] = useState(false);

  const startResizing = (mouseDownEvent) => {
    mouseDownEvent.preventDefault();
    setIsResizing(true);

    const handleMouseMove = (moveEvent) => {
      const sidebarWidth = document.querySelector("aside")?.getBoundingClientRect().width || 64;
      const newWidth = Math.max(200, Math.min(650, moveEvent.clientX - sidebarWidth));
      setPanelWidth(newWidth);
      localStorage.setItem("pamsu_problem_panel_width", String(newWidth));
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
  };

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
    setBlockedPasteCount((currentCount) => currentCount + 1);
    setLastBlockedPasteAt(formatEventTime());
    setNotice("External clipboard paste was blocked. Use the internal IDE copy/paste controls.");
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

  const handleRun = async () => {
    if (activityId === "preview") {
      setExecutionStatus("unavailable");
      setActivePanel("output");
      setOutput("Preview mode: Backend isolated.");
      return;
    }

    setExecutionStatus("running");
    setActivePanel("output");
    setOutput("Sending execution request...");

    try {
      const execRes = await api.post("/execution/requests/", {
        request_kind: "run",
        task_id: parseInt(activityId),
        source_code: code,
        standard_input: standardInput || ""
      });

      // Poll for result
      pollExecution(execRes.execution_id);
    } catch (err) {
      setExecutionStatus("failed");
      setOutput(`Failed to start execution: ${err.message || err.detail || 'Unknown error'}`);
    }
  };

  const handleCheck = async () => {
    if (activityId === "preview") {
      setExecutionStatus("unavailable");
      setActivePanel("analysis");
      setNotice("AST checking requires the authenticated backend analysis endpoint.");
      return;
    }

    setExecutionStatus("running");
    setActivePanel("analysis");
    
    try {
      const execRes = await api.post("/execution/requests/", {
        request_kind: "check",
        task_id: parseInt(activityId),
        source_code: code,
        standard_input: standardInput || ""
      });

      pollExecution(execRes.execution_id, true);
    } catch (err) {
      setExecutionStatus("failed");
      setNotice(`Failed to start AST check: ${err.message || err.detail || 'Unknown error'}`);
    }
  };

  const pollExecution = async (executionId, isCheck = false) => {
    let pollCount = 0;
    const poll = setInterval(async () => {
      try {
        pollCount++;
        const statusRes = await api.get(`/execution/requests/${executionId}`);
        if (["completed", "syntax_error", "runtime_error", "timed_out", "memory_limit", "output_limit", "process_limit", "failed"].includes(statusRes.status)) {
          clearInterval(poll);
          if (statusRes.status === "completed") {
            setExecutionStatus("completed");
          } else {
            setExecutionStatus("failed");
          }

          if (isCheck) {
            setNotice(`Check finished with status: ${statusRes.status}`);
          } else {
            setOutput(statusRes.execution_output || "No output returned.");
          }
        } else if (pollCount >= 5) {
          // If the worker isn't running in dev, time it out locally
          clearInterval(poll);
          setExecutionStatus("unavailable");
          const msg = "Execution request was successfully queued, but the backend Python sandbox is not connected. Student code will not be executed directly in React or FastAPI.";
          if (isCheck) {
            setNotice(msg);
          } else {
            setOutput(msg);
          }
        }
      } catch (err) {
        clearInterval(poll);
        setExecutionStatus("failed");
        if (isCheck) setNotice("Polling failed.");
        else setOutput("Polling failed.");
      }
    }, 1000);
  };

  const handleSubmit = async () => {
    if (activityId === "preview") {
      setExecutionStatus("unavailable");
      setNotice("Cannot submit in preview mode.");
      return;
    }

    try {
      await api.post("/submissions/", {
        task_id: parseInt(activityId),
        raw_code: code,
      });
      setNotice("Code submitted successfully!");
      // Optionally navigate away or update state
      setTimeout(() => navigate("/student/assignments"), 1500);
    } catch (err) {
      setNotice(`Submission failed: ${err.message || err.detail || 'Unknown error'}`);
    }
  };

  const handleResetDraft = () => {
    const confirmed = window.confirm(
      "Reset this draft to the starter code?",
    );

    if (!confirmed) {
      return;
    }

    // Attempt to use activity starter code if available
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
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main">
      <div className="hidden lg:flex h-full">
        <Sidebar />
      </div>

      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <header className="flex min-h-13 shrink-0 flex-wrap items-center justify-between gap-3 border-b border-border-subtle bg-bg-glass shadow-inner backdrop-blur-md px-5 sm:px-6 py-2 select-none">
          {/* Left: Section Segment Control & Activity Info */}
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex items-center gap-1 rounded-lg bg-bg-glass shadow-inner p-1 border border-border-subtle">
              <button
                type="button"
                onClick={toggleProblemPanel}
                aria-pressed={showProblemPanel}
                className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold transition-all ${
                  showProblemPanel
                    ? "bg-[#3b82f6] text-text-main shadow-sm"
                    : "text-text-muted hover:bg-bg-glass-hover hover:text-text-main"
                }`}
              >
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                  <path d="M2 3h12M2 7h12M2 11h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
                Problem
              </button>

              <button
                type="button"
                onClick={toggleReviewPanel}
                aria-pressed={showReviewPanel}
                className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold transition-all ${
                  showReviewPanel
                    ? "bg-violet-600 text-text-main shadow-sm"
                    : "text-text-muted hover:bg-bg-glass-hover hover:text-text-main"
                }`}
              >
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                  <path d="M8 2v12M2 8h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
                Review
              </button>
            </div>
            <div className="hidden min-w-0 sm:block border-l border-border-subtle pl-3">
              <span className="rounded bg-blue-500/10 border border-blue-500/20 px-1.5 py-0.5 text-[9px] font-mono font-bold text-text-blue mr-2">
                {activity.courseCode}
              </span>
              <span className="truncate text-xs font-bold text-text-main tracking-wide">
                {activity.title}
              </span>
            </div>
          </div>

          {/* Right: Execution Status & Action Buttons */}
          <div className="flex items-center gap-2.5">
            {/* Status Indicator */}
            <div className="hidden sm:flex items-center gap-2 rounded-lg border border-border-subtle bg-bg-glass shadow-inner px-2.5 py-1 text-xs font-medium">
              <span className={`h-2 w-2 rounded-full ${status.dotClass}`} />
              <span className={status.textClass}>{status.label}</span>
            </div>

            <div className="mx-1 h-5 w-px bg-border-subtle" />
            <ThemeToggle />
            <div className="mx-1 h-5 w-px bg-border-subtle" />

            {/* Check Code Button */}
            <button
              type="button"
              onClick={handleCheck}
              disabled={executionStatus === "running"}
              className="flex items-center gap-1.5 rounded-lg border border-white/[0.12] bg-bg-glass px-3 py-1.5 text-xs font-semibold text-text-main transition-all hover:bg-bg-glass-hover hover:border-white/[0.2] active:scale-95 disabled:opacity-50 cursor-pointer"
            >
              <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M3 8l3 3 7-7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              Check
            </button>

            {/* Run Code Button */}
            <button
              type="button"
              onClick={handleRun}
              disabled={executionStatus === "running"}
              className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-bold text-text-main shadow-md shadow-emerald-600/20 transition-all hover:bg-emerald-500 hover:shadow-emerald-500/30 active:scale-95 disabled:opacity-50 cursor-pointer"
            >
              <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                <path d="M4 2.5v11l9-5.5-9-5.5z" />
              </svg>
              Run
            </button>

            {/* Submit Button */}
            <button
              type="button"
              onClick={handleSubmit}
              disabled={executionStatus === "running"}
              className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-1.5 text-xs font-bold text-text-main shadow-md shadow-blue-500/25 transition-all hover:from-blue-500 hover:to-indigo-500 hover:shadow-blue-500/40 active:scale-95 disabled:opacity-50 cursor-pointer"
            >
              Submit
            </button>
          </div>
        </header>

        {showBehaviorNotice && (
          <div
            className="flex shrink-0 items-center justify-between gap-3 border-b border-amber-500/20 bg-amber-500/[0.07] px-4 py-2 text-[10px] text-text-amber select-none"
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
              className="shrink-0 font-semibold text-text-amber hover:text-text-main transition-colors cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {visibleNotice && (
          <div
            className={`flex shrink-0 items-center justify-between gap-3 border-b border-blue-500/20 bg-blue-500/[0.06] px-4 py-1.5 text-xs text-text-blue select-none transition-all duration-500 ease-out ${
              isFadingOut ? "opacity-0 -translate-y-1" : "opacity-100 translate-y-0"
            }`}
            role="status"
            aria-live="polite"
          >
            <span className="truncate text-[11px] font-medium">{visibleNotice}</span>
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
            style={{ width: showProblemPanel ? `${panelWidth}px` : "0px" }}
            className={`fixed inset-y-0 left-0 z-50 flex-col overflow-hidden border-r border-border-subtle bg-bg-glass shadow-inner backdrop-blur-xl xl:static xl:z-auto transition-[width] duration-75 ${
              showProblemPanel ? "flex" : "hidden"
            }`}
          >
            <div className="flex items-start justify-between gap-3 border-b border-border-subtle p-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">
                  Problem Statement
                </span>

                <h2 className="mt-1 text-sm font-bold text-text-main tracking-tight">
                  {activity.title}
                </h2>
              </div>

              <button
                type="button"
                onClick={() => setShowProblemPanel(false)}
                className="rounded px-2 py-1 text-text-muted hover:bg-bg-glass-hover hover:text-text-main xl:hidden"
                aria-label="Close problem panel"
              >
                ×
              </button>
            </div>

            <div className="flex-1 space-y-5 overflow-y-auto p-4 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
              <div className="flex items-center justify-between">
                <span className="inline-block rounded-md border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-[10px] font-semibold text-text-amber">
                  {activity.dueLabel}
                </span>
                <span className="rounded bg-bg-glass border border-border-subtle px-2 py-0.5 text-[10px] font-mono text-text-muted">
                  Python 3
                </span>
              </div>

              <section className="rounded-lg border border-border-subtle bg-bg-glass shadow-inner p-4">
                <h3 className="mb-1.5 text-xs font-bold text-text-main">
                  Instructions
                </h3>

                <p className="text-xs leading-relaxed text-text-muted">
                  {activity.description}
                </p>
              </section>

              <section className="rounded-lg border border-border-subtle bg-bg-glass shadow-inner p-4">
                <h3 className="mb-2 text-xs font-bold text-text-main">
                  Requirements Checklist
                </h3>

                <ul className="space-y-2">
                  {activity.requirements.map((requirement) => (
                    <li
                      key={requirement}
                      className="flex items-center gap-2 text-xs text-text-muted font-medium"
                    >
                      <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded bg-blue-500/15 text-[10px] font-bold text-text-blue border border-blue-500/20">
                        ✓
                      </span>
                      {requirement}
                    </li>
                  ))}
                </ul>
              </section>

              <section className="rounded-lg border border-border-subtle bg-bg-glass shadow-inner p-4">
                <h3 className="mb-1.5 text-xs font-bold text-text-main">
                  Expected Output
                </h3>

                <pre className="overflow-x-auto rounded-md border border-emerald-500/20 bg-bg-glass shadow-inner p-3 font-mono text-[11px] text-text-emerald">
                  {activity.expectedOutput}
                </pre>
              </section>

              <section className="rounded-lg border border-blue-500/15 bg-blue-500/[0.02] shadow-inner p-4">
                <h3 className="text-xs font-bold text-text-blue">
                  Clipboard Policy
                </h3>

                <p className="mt-1 text-[11px] leading-relaxed text-text-muted">
                  Native paste is restricted for academic integrity. Use internal IDE copy/paste controls.
                </p>
              </section>
            </div>
          </aside>

          {/* Draggable Resizer Handle Bar */}
          {showProblemPanel && (
            <div
              onMouseDown={startResizing}
              title="Drag to resize Problem Panel"
              className={`group relative z-30 hidden w-1.5 shrink-0 cursor-col-resize select-none bg-transparent hover:bg-blue-500/40 active:bg-blue-500 transition-colors xl:flex items-center justify-center ${
                isResizing ? "bg-blue-500" : ""
              }`}
            >
              <div className="h-8 w-1 rounded-full bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          )}

          <main className="flex min-w-0 flex-1 flex-col bg-bg-base">
            <div className="flex shrink-0 items-center justify-between border-b border-border-subtle bg-bg-glass shadow-inner px-3 py-1 backdrop-blur-md">
              <div className="flex items-center gap-2 border-t-2 border-t-blue-500 bg-bg-glass shadow-[0_-2px_10px_rgba(0,0,0,0.2)] px-3 py-1.5 text-xs font-semibold rounded-t-md">
                <span className="text-text-blue">
                  {activity.fileName}
                </span>

                <span
                  className="h-1.5 w-1.5 rounded-full bg-blue-400"
                  title="Local draft"
                />
              </div>

              <div className="flex items-center gap-1.5 px-1">
                <button
                  type="button"
                  onClick={copySelectionToInternalBuffer}
                  className="flex items-center gap-1 rounded-md border border-border-subtle bg-bg-glass px-2 py-1 text-[10px] font-medium text-text-muted transition-all hover:bg-bg-glass-hover hover:text-text-main active:scale-95 cursor-pointer"
                  title="Copy selection"
                >
                  <svg width="11" height="11" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <rect x="5" y="5" width="8" height="9" rx="1" stroke="currentColor" strokeWidth="1.3" />
                    <path d="M3 11V3h8" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
                  </svg>
                  Copy
                </button>

                <button
                  type="button"
                  onClick={cutSelectionToInternalBuffer}
                  className="flex items-center gap-1 rounded-md border border-border-subtle bg-bg-glass px-2 py-1 text-[10px] font-medium text-text-muted transition-all hover:bg-bg-glass-hover hover:text-text-main active:scale-95 cursor-pointer"
                  title="Cut selection"
                >
                  <svg width="11" height="11" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <circle cx="5" cy="5" r="2" stroke="currentColor" strokeWidth="1.3" />
                    <circle cx="5" cy="11" r="2" stroke="currentColor" strokeWidth="1.3" />
                    <path d="M7 6l6 6M7 10l6-6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
                  </svg>
                  Cut
                </button>

                <button
                  type="button"
                  onClick={pasteFromInternalBuffer}
                  className="flex items-center gap-1 rounded-md border border-border-subtle bg-bg-glass px-2 py-1 text-[10px] font-medium text-text-muted transition-all hover:bg-bg-glass-hover hover:text-text-main active:scale-95 cursor-pointer"
                  title="Paste selection"
                >
                  <svg width="11" height="11" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <rect x="3" y="3" width="10" height="11" rx="1" stroke="currentColor" strokeWidth="1.3" />
                    <path d="M6 1h4v2H6V1z" stroke="currentColor" strokeWidth="1.3" />
                  </svg>
                  Paste
                </button>

                <div className="h-3.5 w-px bg-white/[0.08] mx-0.5" />

                <button
                  type="button"
                  onClick={handleResetDraft}
                  className="flex items-center gap-1 rounded-md border border-red-500/20 bg-red-500/5 px-2 py-1 text-[10px] font-medium text-text-rose/80 transition-all hover:bg-red-500/15 hover:text-text-rose active:scale-95 cursor-pointer"
                  title="Reset code draft"
                >
                  <svg width="11" height="11" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <path d="M2.5 8a5.5 5.5 0 111.6 3.9M2.5 4v4h4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
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
                className="h-full w-full resize-none overflow-auto bg-bg-base p-4 font-mono text-[12px] leading-6 text-text-main outline-none sm:p-5 sm:text-[13px]"
                style={{
                  caretColor: "#f59e0b",
                  tabSize: 4,
                }}
              />

              <div className="pointer-events-none absolute bottom-2 right-3 rounded bg-black/30 px-2 py-1 font-mono text-[9px] text-text-main/25">
                {lineCount} {lineCount === 1 ? "line" : "lines"} ·
                autosave
              </div>
            </div>

            <section className="flex h-[clamp(170px,26vh,230px)] shrink-0 flex-col border-t border-border-subtle">
              <div className="flex shrink-0 items-center overflow-x-auto border-b border-border-subtle px-2">
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
                        ? "border-white text-text-main"
                        : "border-transparent text-text-muted hover:text-text-muted"
                    }`}
                  >
                    {panel.label}
                  </button>
                ))}
              </div>

              <div className="min-h-0 flex-1 overflow-auto p-3 sm:p-4">
                {activePanel === "output" && (
                  <pre className="whitespace-pre-wrap font-mono text-[11px] leading-5 text-text-muted">
                    {output}
                  </pre>
                )}

                {activePanel === "analysis" && (
                  <div className="space-y-2">
                    <div className="rounded-lg border border-amber-500/15 bg-amber-500/[0.05] p-3">
                      <h3 className="text-xs font-semibold text-text-amber">
                        AST analysis not connected
                      </h3>

                      <p className="mt-1 text-[10px] leading-relaxed text-text-muted">
                        Verified structure results must come from the
                        backend AST service.
                      </p>
                    </div>

                    {activity.requirements.map(
                      (requirement) => (
                        <div
                          key={requirement}
                          className="flex items-center justify-between gap-3 rounded-lg border border-border-subtle bg-bg-glass px-3 py-2"
                        >
                          <span className="text-[10px] text-text-muted">
                            {requirement}
                          </span>

                          <span className="shrink-0 text-[9px] text-text-main/25">
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
                      className="mb-2 block text-[10px] font-medium text-text-muted"
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
                      className="h-[120px] w-full resize-none rounded-lg border border-border-subtle bg-bg-glass p-3 font-mono text-[11px] text-text-muted outline-none placeholder:text-text-muted focus:border-blue-500/40"
                    />
                  </div>
                )}
              </div>
            </section>
          </main>

          <aside
            className={`fixed inset-y-0 right-0 z-50 w-[88vw] max-w-[320px] flex-col overflow-hidden border-l border-border-subtle bg-bg-glass shadow-inner backdrop-blur-xl xl:static xl:z-auto xl:w-[260px] xl:max-w-none ${
              showReviewPanel ? "flex" : "hidden"
            }`}
          >
            <div className="flex items-center justify-between border-b border-border-subtle p-4">
              <h2 className="text-[10px] font-bold uppercase tracking-widest text-text-muted">
                Session Review
              </h2>

              <button
                type="button"
                onClick={() => setShowReviewPanel(false)}
                className="rounded px-2 py-1 text-text-muted hover:bg-bg-glass-hover hover:text-text-main"
                aria-label="Close session review"
              >
                ×
              </button>
            </div>

            <div className="flex-1 space-y-5 overflow-y-auto p-4">
              <section>
                <h3 className="mb-3 text-xs font-semibold text-text-muted">
                  Execution status
                </h3>

                <div className="rounded-lg border border-border-subtle bg-bg-glass shadow-inner p-4">
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

                  <p className="mt-2 text-[10px] leading-relaxed text-text-muted">
                    Execution states will include queued, running,
                    completed, runtime error, timeout, output limit,
                    and memory limit.
                  </p>
                </div>
              </section>

              <section>
                <h3 className="mb-3 text-xs font-semibold text-text-muted">
                  Activity indicators
                </h3>

                <div className="space-y-3">
                  <div className="flex items-center justify-between rounded-lg border border-border-subtle bg-bg-glass shadow-inner px-4 py-2.5">
                    <span className="text-[11px] text-text-muted">
                      Tab switches
                    </span>

                    <span className="font-mono text-xs text-text-amber">
                      {tabSwitchCount}
                    </span>
                  </div>

                  <div className="flex items-center justify-between rounded-lg border border-border-subtle bg-bg-glass shadow-inner px-4 py-2.5">
                    <span className="text-[11px] text-text-muted">
                      Blocked pastes
                    </span>

                    <span className="font-mono text-xs text-text-amber">
                      {blockedPasteCount}
                    </span>
                  </div>

                  <div className="rounded-lg border border-border-subtle bg-bg-glass shadow-inner px-4 py-2.5">
                    <p className="text-[11px] text-text-muted">
                      Last blocked paste
                    </p>

                    <p className="mt-1 font-mono text-[10px] text-text-main/25">
                      {lastBlockedPasteAt || "None recorded"}
                    </p>
                  </div>
                </div>

                <p className="mt-3 text-[10px] leading-relaxed text-text-main/25">
                  These events are review indicators, not automatic
                  behavior scores or proof of misconduct.
                </p>
              </section>

              <section className="rounded-lg border border-green-500/15 bg-green-500/[0.02] shadow-inner p-4">
                <h3 className="text-[11px] font-semibold text-green-300">
                  Privacy boundary
                </h3>

                <p className="mt-1 text-[10px] leading-relaxed text-text-main/35">
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
