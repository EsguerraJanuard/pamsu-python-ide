import { useEffect, useRef, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import MonacoEditor from "@monaco-editor/react";
import { useEditorSettings } from "../../hooks/useEditorSettings";
import { useTheme } from "../theme/ThemeContext";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import api from "../../services/api";


import Statusbar from "../../components/layout/Statusbar";

function PlayIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><polygon points="5 3 19 12 5 21 5 3"/></svg>
  );
}

function ArrowLeftIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
  );
}

export default function PracticeWorkspace() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const taskId = searchParams.get("task");
  
  const { settings } = useEditorSettings();
  const { resolvedTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState("lesson");
  const [taskDetails, setTaskDetails] = useState(null);
  const [moduleDetails, setModuleDetails] = useState(null);
  const [nextTaskId, setNextTaskId] = useState(null);
  
  const [code, setCode] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [aiHint, setAiHint] = useState(null);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [triggerRun, setTriggerRun] = useState(0);
  const [output, setOutput] = useState("");

  useEffect(() => {
    // Monaco editor applies settings dynamically via the options prop.
  }, [settings]);

  useEffect(() => {
    if (!taskId) {
      navigate("/student/practice");
      return;
    }

    const fetchTask = async () => {
      try {
        const response = await api.get("/practice/modules");
        if (!Array.isArray(response)) {
            console.error("Expected array but got:", typeof response);
            setLoading(false);
            return;
          }
          let foundTask = null;
        let foundModule = null;
        let nTaskId = null;
        
        const allTasks = [];
        response.forEach(m => {
          m.tasks.forEach(t => allTasks.push(t));
        });

        for (let i = 0; i < allTasks.length; i++) {
          if (allTasks[i].task_id === parseInt(taskId)) {
            foundTask = allTasks[i];
            foundModule = response.find(m => m.module_id === foundTask.module_id);
            if (i + 1 < allTasks.length) {
              nTaskId = allTasks[i + 1].task_id;
            }
            break;
          }
        }

        if (foundTask) {
          if (foundTask.is_locked) {
            navigate("/student/practice"); // Prevent access to locked tasks
          } else {
            setTaskDetails(foundTask);
            setModuleDetails(foundModule);
            setNextTaskId(nTaskId);
            const draftStorageKey = `pamsu_saved_code_${taskId}`;
            try {
              const savedCode = localStorage.getItem(draftStorageKey);
              if (savedCode) {
                setCode(savedCode);
              } else {
                setCode(foundTask.starter_code || "");
              }
            } catch {
              setCode(foundTask.starter_code || "");
            }
          }
        } else {
          navigate("/student/practice");
        }
      } catch (err) {
        console.error("Failed to load task:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchTask();
  }, [taskId, navigate]);
  useEffect(() => {
    if (!taskId) return;
    const draftStorageKey = `pamsu_saved_code_${taskId}`;
    const autosaveTimer = window.setTimeout(() => {
      try {
        localStorage.setItem(draftStorageKey, code);
      } catch {}
    }, 2000);

    return () => {
      window.clearTimeout(autosaveTimer);
    };
  }, [code, taskId]);

  const [isRunCooldown, setIsRunCooldown] = useState(false);

  const handleSubmit = async () => {
    if (isRunCooldown) return;
    setIsRunCooldown(true);
    setTimeout(() => setIsRunCooldown(false), 3000);
    
    setIsSubmitting(true);
    setFeedback(null);
    setAiHint(null);
    setNextTaskId(null);

    // Also trigger InteractiveTerminal so student sees raw output
    setTriggerRun(prev => prev + 1);

    try {
      const res = await api.post(`/practice/tasks/${taskId}/submit`, { code });
      setFeedback(res);
      setOutput(res.execution_feedback || "Execution completed without output.");
      
      if (res.is_successful) {
        // Find next task id
        if (moduleDetails) {
          const tIndex = moduleDetails.tasks.findIndex(t => String(t.task_id) === String(taskId));
          if (tIndex !== -1 && tIndex < moduleDetails.tasks.length - 1) {
            setNextTaskId(moduleDetails.tasks[tIndex + 1].task_id);
          }
        }
      } else {
        // Fetch AI hint
        setIsAiLoading(true);
        try {
          const aiRes = await api.post(`/practice/attempts/${res.attempt_id}/ai-hint`);
          setAiHint(aiRes.ai_hint);
        } catch (aiErr) {
          console.error("AI hint fetch failed", aiErr);
          setAiHint("The AI Tutor is currently unavailable. Please check your syntax and try again.");
        } finally {
          setIsAiLoading(false);
        }
      }
    } catch (err) {
      console.error("Submission failed", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const monacoOptions = {
    minimap: { enabled: settings.minimap },
    fontSize: settings.fontSize,
    fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
    lineHeight: 1.5,
    fontLigatures: true,
    cursorBlinking: settings.cursorStyle,
    wordWrap: settings.wordWrap,
    automaticLayout: true,
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-bg-base">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-border-subtle border-t-blue-500"></div>
      </div>
    );
  }

  if (!taskDetails) {
    return (
      <div className="flex h-screen flex-col items-center justify-center bg-bg-base p-6 text-center">
        <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-bg-alt shadow-inner">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-text-muted">
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        <h2 className="mb-2 text-2xl font-bold text-text-main">Practice Task Not Found</h2>
        <p className="mb-8 max-w-md text-sm text-text-muted">
          We couldn't load this practice module. Either the task doesn't exist, it's locked, or the backend API is currently unavailable.
        </p>
        <button 
          onClick={() => navigate('/student/practice')}
          className="flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 font-semibold text-white shadow-lg transition-all hover:bg-blue-500 hover:shadow-blue-500/25"
        >
          <ArrowLeftIcon className="h-5 w-5" />
          Return to Modules
        </button>
      </div>
    );
  }


  if (viewMode === "lesson") {
    return (
      <div className="flex h-screen flex-col overflow-hidden bg-bg-base text-text-main">
        <header className="flex h-14 shrink-0 items-center border-b border-border-subtle bg-bg-base px-4">
          <button 
            onClick={() => navigate("/student/practice")}
            className="flex items-center gap-2 rounded-md px-2 py-1 text-sm font-medium text-text-muted hover:bg-bg-alt hover:text-text-main transition-colors"
          >
            <ArrowLeftIcon className="h-4 w-4" />
            Back to Modules
          </button>
        </header>

        <main className="flex-1 overflow-y-auto px-6 py-12 flex justify-center animate-fade-in">
          <div className="max-w-3xl w-full">
            <div className="mb-4 inline-flex items-center rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-600 dark:text-emerald-400 ring-1 ring-inset ring-emerald-500/20">
              Lesson
            </div>
            <h1 className="text-4xl font-extrabold mb-8 text-text-main tracking-tight">{taskDetails.title}</h1>
            
            <div className="prose prose-invert prose-emerald max-w-none mb-12">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{taskDetails.instructions || 'No instructions provided.'}</ReactMarkdown>
            </div>
            
            <div className="border-t border-border-subtle pt-8 flex justify-end pb-24">
              <button 
                onClick={() => setViewMode("coding")} 
                className="flex items-center gap-2 rounded-xl bg-blue-600 px-8 py-4 text-base font-semibold text-white shadow-lg shadow-blue-500/20 transition-all hover:bg-blue-500 hover:scale-[1.02]"
              >
                Start Coding Challenge
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-bg-base text-text-main">
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-border-subtle bg-bg-base px-4">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate("/student/practice")}
            className="flex items-center gap-2 rounded-md px-2 py-1 text-sm font-medium text-text-muted hover:bg-bg-alt hover:text-text-main transition-colors"
          >
            <ArrowLeftIcon className="h-4 w-4" />
            Back to Modules
          </button>
          <div className="h-4 w-px bg-border-subtle"></div>
          <div>
            <h1 className="text-sm font-bold text-text-main">{taskDetails.title}</h1>
            <p className="text-xs text-text-muted">{moduleDetails?.title}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {feedback?.is_successful && nextTaskId && (
            <button
              onClick={() => {
                setTaskDetails(null); // trigger re-fetch/loading
                setFeedback(null);
    setAiHint(null);
                setCode("");
                navigate(`/student/practice/workspace?task=${nextTaskId}`);
              }}
              className="flex items-center gap-2 rounded-md bg-emerald-600 px-4 py-1.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-emerald-500"
            >
              Next Task ?
            </button>
          )}
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || isRunCooldown}
            className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-1.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-white"></div>
            ) : (
              <PlayIcon className="h-4 w-4" />
            )}
            {isSubmitting ? "Evaluating..." : "Run & Submit"}
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel: Instructions & Feedback */}
        <div className="flex w-1/3 flex-col border-r border-border-subtle bg-bg-base overflow-y-auto">
          <div className="p-6">
            <div className="mb-4 flex items-center justify-between border-b border-border-subtle pb-2"><h2 className="text-lg font-bold text-text-main">Instructions</h2>
              <button onClick={() => setViewMode("lesson")} className="text-xs text-blue-400 hover:text-blue-300 font-medium">Read Full Lesson</button></div>
            <div className="prose prose-invert prose-sm max-w-none text-text-main">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{taskDetails.instructions || ''}</ReactMarkdown>
            </div>

            {feedback && (
              <div className={`mt-8 animate-fade-in rounded-xl border p-5 
                ${feedback.is_successful ? "border-emerald-500/30 bg-emerald-500/10" : "border-rose-500/30 bg-rose-500/10"}`}
              >
                <h3 className={`text-base font-bold flex items-center gap-2 mb-3
                  ${feedback.is_successful ? "text-emerald-500" : "text-rose-500"}`}
                >
                  {feedback.is_successful ? "Evaluation Passed!" : "Evaluation Failed"}
                </h3>
                
                
                <p className="text-sm font-medium mb-4 text-text-main">{feedback.message}</p>
                {feedback.is_successful && (
                  nextTaskId ? (
                    <button
                      onClick={() => {
                        setTaskDetails(null);
                        setFeedback(null);
                        setAiHint(null);
                        setCode("");
                        navigate(`/student/practice/workspace?task=${nextTaskId}`);
                      }}
                      className="mt-2 w-full flex justify-center items-center gap-2 rounded-md bg-emerald-600 px-6 py-2.5 text-sm font-bold text-white shadow-lg transition-all hover:bg-emerald-500 hover:-translate-y-0.5 active:translate-y-0"
                    >
                      Proceed to Next Task
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                    </button>
                  ) : (
                    <button
                      onClick={() => navigate('/student/practice')}
                      className="mt-2 w-full flex justify-center items-center gap-2 rounded-md bg-slate-700 px-6 py-2.5 text-sm font-bold text-white shadow-lg transition-all hover:bg-slate-600 hover:-translate-y-0.5 active:translate-y-0"
                    >
                      Module Complete! Return to Modules
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                    </button>
                  )
                )}
                {feedback.ast_feedback && feedback.ast_feedback.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold uppercase text-text-muted mb-1">Structural Feedback</h4>
                    <ul className="list-disc list-inside text-sm text-text-main space-y-1">
                      {feedback.ast_feedback.map((msg, idx) => (
                        <li key={idx} className={msg.startsWith("Missing") ? "text-rose-400" : "text-amber-400"}>
                          {msg}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Code Editor */}
        <div className="flex w-2/3 flex-col">
          <div className="flex-1 overflow-hidden">
             <MonacoEditor
              height="100%"
              language="python"
              theme={resolvedTheme === "dark" ? "vs-dark" : "light"}
              value={code}
              onChange={(value) => setCode(value || "")}
              options={monacoOptions}
            />
          </div>
          {/* Output Terminal */}
          <div className="h-56 border-t border-border-subtle bg-bg-base flex flex-col">
             <div className="flex items-center px-4 py-2 border-b border-white/5 bg-bg-panel">
                <span className="text-xs font-mono text-text-muted uppercase tracking-wider">Terminal Output</span>
             </div>
               <div className="flex-1 p-1 bg-transparent h-full relative">
                 <div className="w-full h-full min-h-[150px] bg-slate-900/50 p-4 rounded font-mono text-sm text-slate-300 whitespace-pre-wrap overflow-auto border border-slate-700/50">
                   {output || "Output will appear here..."}
                 </div>
               </div>
          </div>
        </div>
      </div>
      
      <Statusbar
        sessionStatus="active"
        studentName="Student"
        pythonVersion="Python 3"
      />
    </div>
  );
}

