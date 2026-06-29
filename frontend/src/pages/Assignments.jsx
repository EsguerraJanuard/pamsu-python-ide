/**
 * Assignments.jsx
 * Shows all assignments for the student — active, submitted, and upcoming.
 *
 * TODO (Backend): GET /api/student/assignments
 * Response: [{ id, title, due, tags, feedback, progress, status, action, astScore, behaviorScore, finalScore, submittedDate }]
 * TODO (Frontend): replace MOCK_ASSIGNMENTS with real API data
 * TODO (Frontend): add filter buttons (All, Active, Submitted) that filter the list
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import StatusBar from "../components/StatusBar";

const MOCK_ASSIGNMENTS = [
  {
    id: 1,
    title: "Lab Activity 3 — Fibonacci Sequence",
    due: "Jan 15, 11:59 PM",
    tags: ["Python", "Loops", "Functions"],
    feedback: "Missing while loop variant — task requires both for and while implementations",
    progress: 70,
    status: "due_today",
    action: "Continue",
  },
  {
    id: 2,
    title: "Lab Activity 4 — List Comprehensions & File I/O",
    due: "Jan 18, 11:59 PM",
    tags: ["Python", "Lists", "File I/O"],
    feedback: "Good structure — add exception handling for file operations",
    progress: 30,
    status: "in_progress",
    action: "Open",
  },
  {
    id: 3,
    title: "Lab Activity 2 — Control Flow & Functions",
    due: "Jan 10",
    tags: [],
    feedback: "All structural requirements met. Excellent behavioral consistency throughout the session.",
    progress: 100,
    status: "submitted",
    action: "View report",
    submittedDate: "Jan 10",
    astScore: 85,
    behaviorScore: 94,
    finalScore: 88,
  },
  {
    id: 4,
    title: "Lab Activity 1 — Variables & Data Types",
    due: "Jan 5",
    tags: [],
    feedback: "All requirements met. Good use of type conversion.",
    progress: 100,
    status: "submitted",
    action: "View report",
    submittedDate: "Jan 5",
    astScore: 90,
    behaviorScore: 96,
    finalScore: 92,
  },
];

const FILTERS = ["All", "Active", "Submitted"];

function getBadge(status) {
  if (status === "due_today")  return { label: "Due today",   bg: "rgba(245,158,11,0.15)", color: "#f59e0b", border: "rgba(245,158,11,0.3)" };
  if (status === "in_progress") return { label: "In progress", bg: "rgba(59,130,246,0.15)", color: "#3b82f6", border: "rgba(59,130,246,0.3)" };
  if (status === "submitted")  return { label: "Submitted",   bg: "rgba(34,197,94,0.15)",  color: "#22c55e", border: "rgba(34,197,94,0.3)" };
}

function getActionStyle(status) {
  if (status === "due_today")  return { bg: "#f59e0b",     color: "#0f1117" };
  if (status === "in_progress") return { bg: "#3b82f6",    color: "#ffffff" };
  if (status === "submitted")  return { bg: "transparent", color: "#3b82f6", border: "1px solid rgba(59,130,246,0.4)" };
}

function ClockIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.3"/>
      <path d="M8 5v3.5l2 1.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function TagIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 16 16" fill="none">
      <path d="M2 2h5.5l6.5 6.5-5.5 5.5L2 7.5V2z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round"/>
      <circle cx="5" cy="5" r="1" fill="currentColor"/>
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 16 16" fill="none">
      <path d="M3 8l4 4 6-7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

export default function Assignments() {
  const [mounted, setMounted] = useState(false);
  const [filter, setFilter] = useState("All");
  const navigate = useNavigate();

  useEffect(() => {
    setMounted(true);
  }, []);

  // Filter assignments based on selected tab
  const filtered = MOCK_ASSIGNMENTS.filter((a) => {
    if (filter === "Active") return a.status !== "submitted";
    if (filter === "Submitted") return a.status === "submitted";
    return true;
  });

  return (
    <div
      className="flex min-h-screen bg-[#0f1117] text-white select-none cursor-default"
      style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.4s ease" }}
    >
      <Sidebar activePage="Assignments" />

      <main className="flex-1 overflow-y-auto px-8 py-6 pb-12">

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Assignments</h1>
          <p className="text-sm text-white/40 mt-1">
            {MOCK_ASSIGNMENTS.filter(a => a.status !== "submitted").length} active · {MOCK_ASSIGNMENTS.filter(a => a.status === "submitted").length} submitted
          </p>
        </div>

        {/* Filter tabs
            TODO (Frontend): wire filter to real API query param when backend is ready
        */}
        <div className="flex gap-1 mb-6 bg-[#1a1d27] p-1 rounded-lg border border-white/[0.06] w-fit">
          {FILTERS.map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className="px-4 py-1.5 rounded-md text-sm font-medium"
              style={{
                background: filter === f ? "#ffffff" : "transparent",
                color: filter === f ? "#0f1117" : "rgba(255,255,255,0.4)",
                transition: "background 0.2s ease, color 0.2s ease",
              }}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Assignment list */}
        <div className="space-y-3 max-w-3xl">
          {filtered.map((assignment, i) => {
            const badge = getBadge(assignment.status);
            const actionStyle = getActionStyle(assignment.status);
            return (
              <div
                key={assignment.id}
                className="bg-[#1a1d27] border border-white/[0.06] rounded-xl p-4"
                style={{
                  borderLeft: assignment.status === "due_today" ? "3px solid #f59e0b"
                    : assignment.status === "submitted" ? "3px solid #22c55e"
                    : "3px solid #3b82f6",
                  opacity: mounted ? 1 : 0,
                  transform: mounted ? "translateY(0)" : "translateY(8px)",
                  transition: `opacity 0.4s ease ${i * 0.07}s, transform 0.4s ease ${i * 0.07}s`,
                }}
              >
                <div className="flex items-start justify-between gap-4 mb-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <h3 className="text-sm font-semibold text-white">{assignment.title}</h3>
                      <span
                        className="text-[10px] font-semibold px-2 py-0.5 rounded-full border"
                        style={{ background: badge.bg, color: badge.color, borderColor: badge.border }}
                      >
                        {badge.label}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-white/35 flex-wrap">
                      <span className="flex items-center gap-1"><ClockIcon />Due: {assignment.due}</span>
                      {assignment.tags.length > 0 && (
                        <span className="flex items-center gap-1"><TagIcon />{assignment.tags.join(" · ")}</span>
                      )}
                      {assignment.status === "submitted" && (
                        <span className="flex items-center gap-1">
                          <CheckIcon />
                          Submitted {assignment.submittedDate} · AST: {assignment.astScore}/100 · Behavior: {assignment.behaviorScore}/100
                        </span>
                      )}
                    </div>
                  </div>

                  <button
                    type="button"
                    className="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer"
                    style={{
                      background: actionStyle.bg,
                      color: actionStyle.color,
                      border: actionStyle.border || "none",
                      transition: "opacity 0.15s ease, transform 0.15s ease",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.opacity = "0.8";
                      e.currentTarget.style.transform = "translateY(-1px)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.opacity = "1";
                      e.currentTarget.style.transform = "translateY(0)";
                    }}
                    onClick={() => {
                      if (assignment.status === "submitted") navigate(`/submissions/${assignment.id}`);
                      else navigate(`/workspace?task=${assignment.id}`);
                    }}
                  >
                    {assignment.action}
                  </button>
                </div>

                {/* Feedback */}
                <div
                  className="text-[11px] font-mono px-3 py-2 rounded-lg mb-3"
                  style={{
                    background: "rgba(255,255,255,0.03)",
                    borderLeft: "2px solid rgba(255,255,255,0.08)",
                    color: "rgba(255,255,255,0.45)",
                  }}
                >
                  <span className="text-white/25">Last feedback: </span>
                  {assignment.feedback}
                </div>

                {/* Progress */}
                <div className="flex items-center gap-3">
                  <span className="text-[10px] text-white/30 flex-shrink-0">
                    {assignment.status === "submitted" ? "Final score" : "Progress"}
                  </span>
                  <div className="flex-1 h-1 bg-white/[0.06] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${assignment.progress}%`,
                        background: assignment.status === "due_today" ? "#f59e0b"
                          : assignment.status === "submitted" ? "#22c55e"
                          : "#3b82f6",
                        transition: "width 0.8s cubic-bezier(0.25,0.46,0.45,0.94)",
                      }}
                    />
                  </div>
                  {assignment.status === "submitted"
                    ? <span className="text-[10px] font-semibold text-[#22c55e] flex-shrink-0">{assignment.finalScore} / 100</span>
                    : <span className="text-[10px] text-white/30 flex-shrink-0">{assignment.progress}%</span>
                  }
                </div>
              </div>
            );
          })}

          {filtered.length === 0 && (
            <div className="text-center py-16 text-white/25 text-sm">
              No {filter.toLowerCase()} assignments.
            </div>
          )}
        </div>
      </main>

      <StatusBar />
    </div>
  );
}