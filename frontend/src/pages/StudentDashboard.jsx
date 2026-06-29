/**
 * StudentDashboard.jsx
 * This is the main dashboard page that students see after logging in.
 *
 * HOW IT WORKS:
 * - Shows the student's name, active assignments, scores, and recent activity
 * - Has a sidebar for navigation
 * - Has a right panel showing level of advancement and recent activity
 * - Has a bottom status bar showing session info
 *
 * LAYOUT:
 * - Left: Sidebar (fixed)
 * - Center: Main content (scrollable)
 * - Right: Advancement panel (fixed)
 * - Bottom: Status bar (fixed)
 *
 * TODO (Backend): fetch real student data from GET /api/student/dashboard
 * Response shape expected:
 * {
 *   student: { name, id, course },
 *   stats: { level, tasksCompleted, totalTasks, avgAstScore, behaviorScore },
 *   assignments: [{ id, title, dueDate, tags, lastFeedback, progress, status, score, astScore, behaviorScore }],
 *   recentActivity: [{ id, message, time, type }]
 * }
 *
 * TODO (Frontend): replace all mock data below with real API data when backend is ready
 * TODO (Frontend): add useEffect to fetch data on page load
 * TODO (Frontend): protect this route — if no token in sessionStorage, redirect to /login
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import StatusBar from "../components/StatusBar";

// ─── Mock data — replace with real API data when backend is ready ─────────────
const MOCK_STUDENT = {
  name: "Juan, Miguel D.",
  initials: "JD",
  role: "Student",
  course: "CCS101",
  courseName: "Introduction to Programming",
};

const MOCK_STATS = [
  {
    value: 72,
    label: "Level of Advancement",
    sublabel: "Skills + Behavior score",
    color: "#3b82f6",
    max: 100,
  },
  {
    value: 8,
    label: "Tasks completed",
    sublabel: "of 11 assigned",
    color: "#22c55e",
    max: 11,
  },
  {
    value: 68,
    label: "Avg. AST Score",
    sublabel: "Across all submissions",
    color: "#f59e0b",
    max: 100,
  },
  {
    value: 91,
    label: "Behavior Score",
    sublabel: "This week average",
    color: "#a78bfa",
    max: 100,
  },
];

const MOCK_ASSIGNMENTS = [
  {
    id: 1,
    title: "Lab Activity 3 — Fibonacci Sequence",
    due: "Jan 15, 11:59 PM",
    tags: ["Python", "Loops", "Functions"],
    feedback: "Missing while loop variant — task requires both for and while implementations",
    progress: 70,
    status: "due_today", // due_today | in_progress | submitted
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
];

const MOCK_ACTIVITY = [
  { id: 1, message: "Ran fibonacci.py — exit code 0", time: "2 mins ago", type: "run" },
  { id: 2, message: "AST feedback: missing while loop in Lab 3", time: "14 mins ago", type: "ast" },
  { id: 3, message: "Lab Activity 2 graded — 88 / 100", time: "Yesterday", type: "grade" },
  { id: 4, message: "Tab-switch warning recorded (×2)", time: "Jan 12", type: "warning" },
];

// ─── Nav links for the sidebar ────────────────────────────────────────────────
// TODO (Frontend): clicking these should navigate to the correct route
const NAV_SECTIONS = [
  {
    label: "MAIN",
    links: [
      { icon: "grid", label: "Dashboard", path: "/dashboard/student", active: true },
      { icon: "list", label: "Assignments", path: "/assignments", badge: 3 },
      { icon: "code", label: "Workspace", path: "/ide" },
    ],
  },
  {
    label: "PROGRESS",
    links: [
      { icon: "chart", label: "My Analytics", path: "/analytics" },
      { icon: "file", label: "Submissions", path: "/submissions" },
    ],
  },
  {
    label: "ACCOUNT",
    links: [
      { icon: "settings", label: "Settings", path: "/settings" },
    ],
  },
];

// ─── Helper: get badge style based on assignment status ───────────────────────
function getBadge(status) {
  if (status === "due_today") return { label: "Due today", bg: "rgba(245,158,11,0.15)", color: "#f59e0b", border: "rgba(245,158,11,0.3)" };
  if (status === "in_progress") return { label: "In progress", bg: "rgba(59,130,246,0.15)", color: "#3b82f6", border: "rgba(59,130,246,0.3)" };
  if (status === "submitted") return { label: "Submitted", bg: "rgba(34,197,94,0.15)", color: "#22c55e", border: "rgba(34,197,94,0.3)" };
}

// ─── Helper: get action button style ─────────────────────────────────────────
function getActionStyle(status) {
  if (status === "due_today") return { bg: "#f59e0b", color: "#0f1117" };
  if (status === "in_progress") return { bg: "#3b82f6", color: "#ffffff" };
  if (status === "submitted") return { bg: "transparent", color: "#3b82f6", border: "1px solid rgba(59,130,246,0.4)" };
}

// ─── Helper: get activity dot color ──────────────────────────────────────────
function getActivityColor(type) {
  if (type === "run") return "#22c55e";
  if (type === "ast") return "#f59e0b";
  if (type === "grade") return "#3b82f6";
  if (type === "warning") return "#ef4444";
}

// ─── Inline SVG icons ─────────────────────────────────────────────────────────
// We use inline SVGs only — no icon libraries
function Icon({ name, size = 16, className = "" }) {
  const icons = {
    grid: <svg width={size} height={size} viewBox="0 0 16 16" fill="none" className={className}><rect x="1" y="1" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.3"/><rect x="9" y="1" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.3"/><rect x="1" y="9" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.3"/><rect x="9" y="9" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.3"/></svg>,
    list: <svg width={size} height={size} viewBox="0 0 16 16" fill="none" className={className}><path d="M3 4h10M3 8h10M3 12h10" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>,
    code: <svg width={size} height={size} viewBox="0 0 16 16" fill="none" className={className}><path d="M5 5L2 8l3 3M11 5l3 3-3 3M9 3l-2 10" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>,
    chart: <svg width={size} height={size} viewBox="0 0 16 16" fill="none" className={className}><path d="M2 12l4-4 3 3 5-6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>,
    file: <svg width={size} height={size} viewBox="0 0 16 16" fill="none" className={className}><rect x="3" y="1" width="10" height="14" rx="1.5" stroke="currentColor" strokeWidth="1.3"/><path d="M6 5h4M6 8h4M6 11h2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>,
    settings: <svg width={size} height={size} viewBox="0 0 16 16" fill="none" className={className}><circle cx="8" cy="8" r="2.5" stroke="currentColor" strokeWidth="1.3"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M3.05 12.95l1.41-1.41M11.54 4.46l1.41-1.41" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>,
    clock: <svg width={size} height={size} viewBox="0 0 16 16" fill="none" className={className}><circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.3"/><path d="M8 5v3.5l2 1.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>,
    tag: <svg width={size} height={size} viewBox="0 0 16 16" fill="none" className={className}><path d="M2 2h5.5l6.5 6.5-5.5 5.5L2 7.5V2z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round"/><circle cx="5" cy="5" r="1" fill="currentColor"/></svg>,
    check: <svg width={size} height={size} viewBox="0 0 16 16" fill="none" className={className}><path d="M3 8l4 4 6-7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>,
    logout: <svg width={size} height={size} viewBox="0 0 16 16" fill="none" className={className}><path d="M6 2H3a1 1 0 00-1 1v10a1 1 0 001 1h3M10 11l3-3-3-3M13 8H6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>,
  };
  return icons[name] || null;
}

export default function StudentDashboard() {
  const [mounted, setMounted] = useState(false);
  const [activeNav, setActiveNav] = useState("Dashboard");
  const navigate = useNavigate();

  // TODO (Frontend): add loading and error states when connecting to backend
  // const [loading, setLoading] = useState(true);
  // const [error, setError] = useState(null);
  // const [data, setData] = useState(null);

  // Page load animation
  useEffect(() => {
    // TODO (Frontend): protect this route
    // const token = sessionStorage.getItem("token");
    // if (!token) { navigate("/login"); return; }

    // TODO (Frontend): fetch real data here
    // fetchDashboardData();

    setMounted(true);
  }, []);

  // TODO (Frontend): uncomment and fill this when backend is ready
  // const fetchDashboardData = async () => {
  //   try {
  //     const res = await fetch("/api/student/dashboard", {
  //       headers: { Authorization: `Bearer ${sessionStorage.getItem("token")}` },
  //     });
  //     if (!res.ok) throw new Error("Failed to load dashboard");
  //     const json = await res.json();
  //     setData(json);
  //   } catch (err) {
  //     setError(err.message);
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  // Sign out — clears token and goes back to login
  const handleSignOut = () => {
    sessionStorage.removeItem("token");
    navigate("/login");
  };

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <div
      className="flex flex-col min-h-screen bg-[#0f1117] text-white select-none cursor-default overflow-hidden"
      style={{
        opacity: mounted ? 1 : 0,
        transition: "opacity 0.4s ease",
      }}
    >
      {/* ── Main layout: sidebar + content + right panel ── */}
      <div className="flex flex-1 overflow-hidden" style={{ paddingBottom: "36px" }}>

        {/* ════════════════════════════════════════════════
            SIDEBAR
            - Fixed left panel
            - Shows logo, nav links, user info
            - TODO (Frontend): highlight active link based on current route
            - TODO (Frontend): show assignment badge count from API
        ════════════════════════════════════════════════ */}
        <aside className="w-[200px] flex-shrink-0 flex flex-col justify-between border-r border-white/[0.06] px-3 py-4 overflow-y-auto">

          {/* Top: logo + nav */}
          <div>
            {/* Logo */}
            <div className="flex items-center gap-2 px-2 mb-6">
              <div className="flex items-center justify-center w-7 h-7 rounded-md bg-[#3b82f6] text-white text-xs font-bold font-mono">
                &gt;_
              </div>
              <span className="font-semibold text-white text-sm tracking-wide">Python</span>
            </div>

            {/* User info */}
            <div className="flex items-center gap-2.5 px-2 mb-6 pb-4 border-b border-white/[0.06]">
              <div className="w-8 h-8 rounded-full bg-[#3b82f6] flex items-center justify-center text-xs font-bold flex-shrink-0">
                {MOCK_STUDENT.initials}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-white truncate">{MOCK_STUDENT.name}</p>
                <p className="text-[10px] text-white/40">{MOCK_STUDENT.role} · {MOCK_STUDENT.course}</p>
              </div>
            </div>

            {/* Nav sections */}
            {NAV_SECTIONS.map((section) => (
              <div key={section.label} className="mb-4">
                <p className="text-[10px] font-semibold text-white/25 uppercase tracking-widest px-2 mb-1">
                  {section.label}
                </p>
                {section.links.map((link) => (
                  <button
                    key={link.label}
                    type="button"
                    onClick={() => {
                      setActiveNav(link.label);
                      navigate(link.path);
                    }}
                    className="w-full flex items-center justify-between gap-2.5 px-2 py-2 rounded-lg text-sm mb-0.5"
                    style={{
                      background: activeNav === link.label ? "rgba(59,130,246,0.12)" : "transparent",
                      color: activeNav === link.label ? "#3b82f6" : "rgba(255,255,255,0.45)",
                      transition: "background 0.2s ease, color 0.2s ease",
                    }}
                    onMouseEnter={(e) => {
                      if (activeNav === link.label) return;
                      e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                      e.currentTarget.style.color = "rgba(255,255,255,0.8)";
                    }}
                    onMouseLeave={(e) => {
                      if (activeNav === link.label) return;
                      e.currentTarget.style.background = "transparent";
                      e.currentTarget.style.color = "rgba(255,255,255,0.45)";
                    }}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon name={link.icon} size={15} />
                      <span>{link.label}</span>
                    </div>
                    {/* Badge — shows number of pending assignments */}
                    {link.badge && (
                      <span className="text-[10px] font-semibold bg-[#3b82f6] text-white px-1.5 py-0.5 rounded-full">
                        {link.badge}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            ))}
          </div>

          {/* Bottom: sign out */}
          <button
            type="button"
            onClick={handleSignOut}
            className="flex items-center gap-2.5 px-2 py-2 rounded-lg text-sm text-white/30 w-full"
            style={{ transition: "color 0.2s ease, background 0.2s ease" }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "#ef4444";
              e.currentTarget.style.background = "rgba(239,68,68,0.08)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "rgba(255,255,255,0.3)";
              e.currentTarget.style.background = "transparent";
            }}
          >
            <Icon name="logout" size={15} />
            Sign out
          </button>
        </aside>

        {/* ════════════════════════════════════════════════
            MAIN CONTENT
            - Scrollable center area
            - Greeting, stat cards, assignment list
            - TODO (Frontend): replace MOCK_STATS and MOCK_ASSIGNMENTS with real API data
        ════════════════════════════════════════════════ */}
        <main className="flex-1 overflow-y-auto px-8 py-6 min-w-0">

          {/* Top bar — course name + avatar */}
          <div className="flex items-center justify-between mb-6">
            <span className="text-xs text-white/30 font-mono">
              {MOCK_STUDENT.course} — {MOCK_STUDENT.courseName}
            </span>
            <div className="w-7 h-7 rounded-full bg-[#3b82f6] flex items-center justify-center text-xs font-bold">
              {MOCK_STUDENT.initials}
            </div>
          </div>

          {/* Greeting */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-white">
              {greeting}, {MOCK_STUDENT.name.split(",")[1]?.trim().split(" ")[0] || "Student"} 👋
            </h1>
            <p className="text-sm text-white/40 mt-1">
              You have {MOCK_ASSIGNMENTS.filter(a => a.status !== "submitted").length} active assignments and {MOCK_ASSIGNMENTS.filter(a => a.status === "due_today").length} due today.
            </p>
          </div>

          {/* ── Stat cards ──
              4 cards showing key metrics.
              TODO (Frontend): replace values with real data from API
              Each card has: big number, label, sublabel, colored progress bar
          ── */}
          <div className="grid grid-cols-2 xl:grid-cols-4 gap-3 mb-8">
            {MOCK_STATS.map((stat, i) => (
              <div
                key={i}
                className="bg-[#1a1d27] border border-white/[0.06] rounded-xl p-4"
                style={{
                  opacity: mounted ? 1 : 0,
                  transform: mounted ? "translateY(0)" : "translateY(8px)",
                  transition: `opacity 0.4s ease ${i * 0.07}s, transform 0.4s ease ${i * 0.07}s`,
                }}
              >
                <p
                  className="text-3xl font-bold mb-1"
                  style={{ color: stat.color }}
                >
                  {stat.value}
                </p>
                <p className="text-xs text-white/70 font-medium">{stat.label}</p>
                <p className="text-[10px] text-white/30 mb-3">{stat.sublabel}</p>
                {/* Progress bar */}
                <div className="h-1 w-full bg-white/[0.06] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${(stat.value / stat.max) * 100}%`,
                      background: stat.color,
                      transition: "width 0.8s cubic-bezier(0.25,0.46,0.45,0.94)",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* ── Active Assignments ──
              Shows all assignments with status, feedback, and action button.
              TODO (Frontend): replace MOCK_ASSIGNMENTS with real API data
              TODO (Backend): GET /api/student/assignments returns list of assignments
              TODO (Frontend): clicking Continue/Open should navigate to /ide?task=ID
              TODO (Frontend): clicking View report should navigate to /submissions/ID
          ── */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-white">Active Assignments</h2>
            <button
              type="button"
              className="text-xs text-[#3b82f6] hover:text-[#60a5fa] transition-colors duration-150"
              onClick={() => navigate("/assignments")}>
              View all
            </button>
          </div>

          <div className="space-y-3">
            {MOCK_ASSIGNMENTS.map((assignment, i) => {
              const badge = getBadge(assignment.status);
              const actionStyle = getActionStyle(assignment.status);
              return (
                <div
                  key={assignment.id}
                  className="bg-[#1a1d27] border border-white/[0.06] rounded-xl p-4"
                  style={{
                    borderLeft: assignment.status === "due_today"
                      ? "3px solid #f59e0b"
                      : assignment.status === "submitted"
                      ? "3px solid #22c55e"
                      : "3px solid #3b82f6",
                    opacity: mounted ? 1 : 0,
                    transform: mounted ? "translateY(0)" : "translateY(8px)",
                    transition: `opacity 0.4s ease ${0.2 + i * 0.08}s, transform 0.4s ease ${0.2 + i * 0.08}s`,
                  }}
                >
                  {/* Assignment header */}
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <h3 className="text-sm font-semibold text-white">{assignment.title}</h3>
                        {/* Status badge */}
                        <span
                          className="text-[10px] font-semibold px-2 py-0.5 rounded-full border"
                          style={{ background: badge.bg, color: badge.color, borderColor: badge.border }}
                        >
                          {badge.label}
                        </span>
                      </div>

                      {/* Due date + tags */}
                      <div className="flex items-center gap-3 text-[11px] text-white/35">
                        <span className="flex items-center gap-1">
                          <Icon name="clock" size={11} />
                          Due: {assignment.due}
                        </span>
                        {assignment.tags.length > 0 && (
                          <span className="flex items-center gap-1">
                            <Icon name="tag" size={11} />
                            {assignment.tags.join(" · ")}
                          </span>
                        )}
                        {/* Submitted scores */}
                        {assignment.status === "submitted" && (
                          <span className="flex items-center gap-1">
                            <Icon name="check" size={11} />
                            Submitted {assignment.submittedDate} · AST Score: {assignment.astScore}/100 · Behavior: {assignment.behaviorScore}/100
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Action button */}
                    <button
                      type="button"
                      className="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold"
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
                        if (assignment.status === "submitted") {
                          navigate(`/submissions/${assignment.id}`);
                        } else {
                          navigate(`/ide?task=${assignment.id}`);
                        }
                      }}
                    >
                      {assignment.action}
                    </button>
                  </div>

                  {/* Last feedback */}
                  <div
                    className="text-[11px] font-mono px-3 py-2 rounded-lg mb-3"
                    style={{
                      background: "rgba(255,255,255,0.03)",
                      borderLeft: "2px solid rgba(255,255,255,0.08)",
                      color: assignment.status === "submitted" ? "rgba(255,255,255,0.5)" : "rgba(255,255,255,0.45)",
                    }}
                  >
                    <span className="text-white/25">Last feedback: </span>
                    {assignment.feedback}
                  </div>

                  {/* Progress bar */}
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] text-white/30 flex-shrink-0">
                      {assignment.status === "submitted" ? "Final score" : "Progress"}
                    </span>
                    <div className="flex-1 h-1 bg-white/[0.06] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${assignment.progress}%`,
                          background: assignment.status === "due_today"
                            ? "#f59e0b"
                            : assignment.status === "submitted"
                            ? "#22c55e"
                            : "#3b82f6",
                          transition: "width 0.8s cubic-bezier(0.25,0.46,0.45,0.94)",
                        }}
                      />
                    </div>
                    {assignment.status === "submitted" && (
                      <span className="text-[10px] font-semibold text-[#22c55e] flex-shrink-0">
                        {assignment.finalScore} / 100
                      </span>
                    )}
                    {assignment.status !== "submitted" && (
                      <span className="text-[10px] text-white/30 flex-shrink-0">
                        {assignment.progress}%
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </main>

        {/* ════════════════════════════════════════════════
            RIGHT PANEL
            - Level of Advancement donut chart
            - Recent activity feed
            - TODO (Frontend): replace mock data with real API data
            - TODO (Backend): GET /api/student/activity returns recent activity list
        ════════════════════════════════════════════════ */}
        <aside className="w-[280px] flex-shrink-0 border-l border-white/[0.06] px-4 py-6 overflow-y-auto">

          {/* Level of Advancement */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-semibold text-white">Level of Advancement</h3>
              <button
                type="button"
                className="text-[10px] text-[#3b82f6] hover:text-[#60a5fa] transition-colors duration-150"
                onClick={() => navigate("/analytics")}>
                Details
              </button>
            </div>

            {/* Donut chart — SVG based, no library needed */}
            <div className="flex flex-col items-center py-4">
              <div className="relative w-32 h-32">
                <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
                  {/* Background circle */}
                  <circle
                    cx="60" cy="60" r="48"
                    fill="none"
                    stroke="rgba(255,255,255,0.06)"
                    strokeWidth="10"
                  />
                  {/* Progress circle
                      The circumference of r=48 is 2*PI*48 ≈ 301.59
                      strokeDasharray = progress% * 301.59 then gap
                  */}
                  <circle
                    cx="60" cy="60" r="48"
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="10"
                    strokeLinecap="round"
                    strokeDasharray={`${(MOCK_STATS[0].value / 100) * 301.59} 301.59`}
                    style={{ transition: "stroke-dasharray 1s cubic-bezier(0.25,0.46,0.45,0.94)" }}
                  />
                </svg>
                {/* Center text */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-2xl font-bold text-white">{MOCK_STATS[0].value}</span>
                  <span className="text-[10px] text-white/30">/ 100</span>
                </div>
              </div>
              <p className="text-sm font-semibold text-white mt-2">Developing</p>
              <p className="text-[10px] text-white/35 mt-0.5">
                Skills {MOCK_STATS[0].value} + Behavior {MOCK_STATS[3].value} — combined
              </p>
            </div>
          </div>

          {/* Divider */}
          <div className="h-px bg-white/[0.06] mb-4" />

          {/* Recent activity */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-white">Recent activity</h3>
              <button
                type="button"
                className="text-[10px] text-[#3b82f6] hover:text-[#60a5fa] transition-colors duration-150"
                onClick={() => navigate("/activity")}>
                All
              </button>
            </div>

            <ul className="space-y-3">
              {MOCK_ACTIVITY.map((item) => (
                <li key={item.id} className="flex items-start gap-2.5">
                  {/* Colored dot */}
                  <div
                    className="w-2 h-2 rounded-full flex-shrink-0 mt-1"
                    style={{ background: getActivityColor(item.type) }}
                  />
                  <div>
                    <p className="text-[11px] text-white/60 leading-tight">{item.message}</p>
                    <p className="text-[10px] text-white/25 mt-0.5">{item.time}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </div>

      {/* ════════════════════════════════════════════════
          BOTTOM STATUS BAR
          - Fixed at the bottom
          - Shows session status on the left
          - Shows Python version + username on the right
          - TODO (Backend): get real session status from API
          - Green dot = active session, Red dot = disconnected
      ════════════════════════════════════════════════ */}
      <div
        className="fixed bottom-0 left-0 right-0 h-9 flex items-center justify-between px-4 border-t border-white/[0.06]"
        style={{ background: "#0d0f18" }}
      >
        <div className="flex items-center gap-2">
          {/* Green dot = session is active */}
          <div className="w-1.5 h-1.5 rounded-full bg-[#22c55e]" />
          <span className="text-[10px] text-[#22c55e] font-mono">
            Session active · {MOCK_STUDENT.course} — {MOCK_STUDENT.courseName}
          </span>
        </div>
        <span className="text-[10px] text-white/25 font-mono">
          Python 3.12 · {MOCK_STUDENT.name}
        </span>
      </div>
    </div>
  );
}