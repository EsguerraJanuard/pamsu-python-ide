import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../services/api";
import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";

export default function SubmissionDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [submission, setSubmission] = useState(null);

  // Mock data falling back to reference design screenshot if backend fails or for id=3
  const defaultData = {
    id: id || "3",
    activityTitle: "Lab Activity 3 — Fibonacci Sequence",
    submittedAt: "Submitted Jan 15, 2026 at 14:47",
    filename: "fibonacci.py",
    lineCount: 24,
    astScore: 72,
    behaviorScore: 91,
    combinedScore: 81.5,
    advancementLevel: "Developing",
    studentName: "Juan, Miguel D.",
    studentInitials: "JD",
    astConstructs: [
      { id: 1, label: "Function defined:", code: "fibonacci()", status: "met", type: "required" },
      { id: 2, label: "for loop present", status: "met", type: "required" },
      { id: 3, label: "if/else conditional present", status: "met", type: "required" },
      { id: 4, label: "Type annotations used", status: "met", type: "required" },
      { id: 5, label: "List comprehension used", status: "met", type: "required" },
      { 
        id: 6, 
        label: "Missing: while loop (required)", 
        subtext: "Task requires a while-loop variant in addition to for", 
        status: "missing", 
        type: "required" 
      },
    ],
    astWarnings: [
      { id: 1, title: "Missing docstring on is_even()", description: "Document all public functions" },
      { id: 2, title: "No input validation for n < 0", description: "Add a bounds check before processing" },
    ],
    behavioralLogs: {
      sessionDuration: "01:14:32",
      activeCodingTime: "58:14",
      idleTime: "16:18",
      runAttempts: 18,
      runtimeErrors: 4,
      tabSwitches: "3x",
      tabSwitchLabel: "Logged — visible to instructor",
      pasteEventsBlocked: 0,
      pasteLabel: "No copy-paste attempted",
      behaviorScore: "91 / 100",
    },
    sessionTimeline: [
      { time: "14:10:02", title: "Session Initialized", type: "system", desc: "Workspace environment loaded." },
      { time: "14:22:15", title: "Run Attempt #1", type: "run", desc: "Output: IndentationError on line 12." },
      { time: "14:31:00", title: "Tab Switch Detected", type: "warning", desc: "Focused out of workspace for 42s." },
      { time: "14:45:10", title: "Run Attempt #18", type: "success", desc: "All local test cases passed." },
      { time: "14:47:00", title: "Official Code Submission", type: "submission", desc: "Submitted fibonacci.py (24 lines)." },
    ],
  };

  useEffect(() => {
    let isMounted = true;
    const fetchSubmissionDetails = async () => {
      if (!id) return;
      setLoading(true);
      try {
        const response = await api.get(`/submissions/${id}`);
        if (isMounted && response) {
          setSubmission({
            ...defaultData,
            ...response,
            astScore: response.ast_score ?? defaultData.astScore,
            behaviorScore: response.behavior_score ?? defaultData.behaviorScore,
            combinedScore: response.grade ?? response.calculated_score ?? defaultData.combinedScore,
          });
        }
      } catch (err) {
        if (isMounted) {
          setSubmission(defaultData);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchSubmissionDetails();
    return () => { isMounted = false; };
  }, [id]);

  const data = submission || defaultData;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0a0c14] text-slate-200">
      <Sidebar />

      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Context Navigation Bar */}
        <header className="flex h-14 items-center justify-between border-b border-slate-800/80 bg-[#0d101d] px-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded border border-cyan-500/30 bg-cyan-500/10 px-2 py-1 text-xs font-mono font-bold text-cyan-400">
              <span>&gt;_</span>
              <span>Python</span>
            </div>
            <span className="text-sm font-medium text-slate-300">
              Lab Activity 3 — Results
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate("/student/dashboard")}
              className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-1.5 text-xs font-medium text-slate-300 hover:border-slate-700 hover:bg-slate-800 hover:text-white transition"
            >
              <span>←</span> Back to Dashboard
            </button>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 font-mono text-xs font-bold text-white shadow-inner">
              {data.studentInitials}
            </div>
          </div>
        </header>

        {/* Scrollable Dashboard Content */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Hero Activity Summary & Score Card */}
          <div className="rounded-xl border border-slate-800/90 bg-[#111424] p-6 shadow-xl relative overflow-hidden">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              <div>
                <h1 className="text-xl font-bold text-white tracking-wide">
                  {data.activityTitle}
                </h1>
                <p className="mt-1 text-xs text-slate-400">
                  {data.submittedAt} · <span className="font-mono text-slate-300">{data.filename}</span> · {data.lineCount} lines
                </p>

                {/* Score Formula Equation */}
                <div className="mt-6 flex flex-wrap items-baseline gap-4 font-mono">
                  <div className="text-center">
                    <div className="text-3xl font-extrabold text-cyan-400">{data.astScore}</div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider mt-0.5">/ 100 Skills (AST)</div>
                  </div>
                  <div className="text-xl text-slate-500 font-bold">+</div>
                  <div className="text-center">
                    <div className="text-3xl font-extrabold text-emerald-400">{data.behaviorScore}</div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider mt-0.5">/ 100 Behavior</div>
                  </div>
                  <div className="text-xl text-slate-500 font-bold">=</div>
                  <div className="text-center">
                    <div className="text-4xl font-black text-sky-300">{data.combinedScore}</div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider mt-0.5">Calculated score</div>
                  </div>
                </div>
              </div>

              {/* Advancement Badge & Resubmit Button */}
              <div className="flex flex-col items-end justify-between gap-4">
                <div className="rounded-lg border border-blue-500/30 bg-blue-500/10 px-4 py-2 text-right">
                  <div className="text-xs font-bold text-blue-400 tracking-wide uppercase">
                    {data.advancementLevel}
                  </div>
                  <div className="text-[10px] text-slate-400">Level of Advancement</div>
                </div>

                <button
                  onClick={() => navigate("/student/workspace")}
                  className="rounded-lg bg-blue-600 px-5 py-2 text-xs font-semibold text-white shadow-lg hover:bg-blue-500 transition active:scale-95"
                >
                  Resubmit
                </button>
              </div>
            </div>

            {/* Secondary Math Formula Pill */}
            <div className="mt-6 rounded-lg border border-slate-800 bg-slate-950/60 px-4 py-2 flex items-center gap-3 text-xs font-mono text-slate-400">
              <span className="text-cyan-400 font-bold">{data.astScore}</span>
              <span>AST Score</span>
              <span>+</span>
              <span className="text-emerald-400 font-bold">{data.behaviorScore}</span>
              <span>Behavior</span>
              <span>÷ 2 =</span>
              <span className="text-sky-300 font-bold">{data.combinedScore}</span>
              <span>Combined</span>
              <span>→</span>
              <span className="text-blue-400 font-semibold">{data.advancementLevel} Level</span>
            </div>
          </div>

          {/* Two-Column Details Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column: AST Structure Breakdown */}
            <div className="rounded-xl border border-slate-800/90 bg-[#111424] p-5 shadow-lg space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
                <span className="text-cyan-400 font-mono font-bold">&lt;&gt;</span>
                <h2 className="text-sm font-bold text-white tracking-wide">
                  AST Structure Breakdown
                </h2>
              </div>

              {/* Required Constructs */}
              <div className="space-y-2">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Required Constructs
                </div>

                <div className="space-y-2 font-mono text-xs">
                  {data.astConstructs.map((item) => (
                    <div
                      key={item.id}
                      className={`rounded-lg px-3.5 py-2.5 border transition ${
                        item.status === "met"
                          ? "border-emerald-500/30 bg-emerald-950/20 text-emerald-300"
                          : "border-rose-500/30 bg-rose-950/25 text-rose-300"
                      }`}
                    >
                      <div className="flex items-center gap-2 font-medium">
                        {item.status === "met" ? (
                          <span className="text-emerald-400 font-bold">✓</span>
                        ) : (
                          <span className="text-rose-400 font-bold">✕</span>
                        )}
                        <span>{item.label}</span>
                        {item.code && (
                          <span className="text-amber-400">{item.code}</span>
                        )}
                      </div>
                      {item.subtext && (
                        <p className="mt-1 text-[11px] font-sans text-rose-300/80 pl-5">
                          {item.subtext}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Warnings */}
              <div className="space-y-2 pt-2">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Warnings
                </div>

                <div className="space-y-2">
                  {data.astWarnings.map((warn) => (
                    <div
                      key={warn.id}
                      className="rounded-lg border border-amber-500/30 bg-amber-950/20 p-3 text-xs"
                    >
                      <div className="flex items-center gap-2 font-semibold text-amber-300">
                        <span>⚠️</span>
                        <span>{warn.title}</span>
                      </div>
                      <p className="mt-1 text-[11px] text-amber-200/70 pl-6">
                        {warn.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column: Behavioral Log Summary */}
            <div className="rounded-xl border border-slate-800/90 bg-[#111424] p-5 shadow-lg space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
                <span className="text-emerald-400 font-mono font-bold">👁</span>
                <h2 className="text-sm font-bold text-white tracking-wide">
                  Behavioral Log Summary
                </h2>
              </div>

              <div className="divide-y divide-slate-800/60 text-xs">
                <div className="flex justify-between py-2.5">
                  <span className="text-slate-400">Session duration</span>
                  <span className="font-mono font-bold text-cyan-400">{data.behavioralLogs.sessionDuration}</span>
                </div>
                <div className="flex justify-between py-2.5">
                  <span className="text-slate-400">Active coding time</span>
                  <span className="font-mono font-semibold text-slate-200">{data.behavioralLogs.activeCodingTime}</span>
                </div>
                <div className="flex justify-between py-2.5">
                  <span className="text-slate-400">Idle time</span>
                  <span className="font-mono font-semibold text-amber-400">{data.behavioralLogs.idleTime}</span>
                </div>
                <div className="flex justify-between py-2.5">
                  <span className="text-slate-400">Run attempts</span>
                  <span className="font-mono font-semibold text-slate-200">{data.behavioralLogs.runAttempts}</span>
                </div>
                <div className="flex justify-between py-2.5">
                  <span className="text-slate-400">Runtime errors</span>
                  <span className="font-mono font-semibold text-rose-400">{data.behavioralLogs.runtimeErrors}</span>
                </div>
                <div className="flex justify-between py-2.5 items-center">
                  <span className="text-slate-400">Tab switches</span>
                  <div className="text-right">
                    <span className="font-mono font-bold text-amber-400">{data.behavioralLogs.tabSwitches}</span>
                    <span className="ml-2 text-[10px] text-amber-300/70">{data.behavioralLogs.tabSwitchLabel}</span>
                  </div>
                </div>
                <div className="flex justify-between py-2.5 items-center">
                  <span className="text-slate-400">Paste events blocked</span>
                  <div className="text-right">
                    <span className="font-mono font-bold text-emerald-400">{data.behavioralLogs.pasteEventsBlocked}</span>
                    <span className="ml-2 text-[10px] text-emerald-300/70">{data.behavioralLogs.pasteLabel}</span>
                  </div>
                </div>
                <div className="flex justify-between py-3 items-center font-bold text-sm pt-4">
                  <span className="text-white">Behavior score</span>
                  <span className="font-mono text-emerald-400">{data.behavioralLogs.behaviorScore}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Session Timeline Panel */}
          <div className="rounded-xl border border-slate-800/90 bg-[#111424] p-5 shadow-lg space-y-3">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
              <span className="text-blue-400 font-mono font-bold">⏱</span>
              <h2 className="text-sm font-bold text-white tracking-wide">
                Session Timeline
              </h2>
            </div>

            <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
              {data.sessionTimeline.map((evt, idx) => (
                <div key={idx} className="relative flex items-start gap-3 text-xs">
                  <div className="absolute -left-6 top-0.5 h-3 w-3 rounded-full border-2 border-[#111424] bg-blue-500" />
                  <span className="font-mono text-[11px] text-slate-400 w-16 shrink-0">{evt.time}</span>
                  <div>
                    <span className="font-semibold text-white">{evt.title}</span>
                    <p className="text-[11px] text-slate-400 mt-0.5">{evt.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </main>

        {/* Status bar */}
        <Statusbar
          sessionStatus="active"
          courseCode="Python Lab Activity 3"
          courseName="Submitted"
          studentName={`${data.combinedScore} / 100 — ${data.studentName}`}
        />
      </div>
    </div>
  );
}
