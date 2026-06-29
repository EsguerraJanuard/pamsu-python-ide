/**
 * Analytics.jsx
 * Shows the student's performance analytics over time.
 *
 * TODO (Backend): GET /api/student/analytics
 * Response: { stats, weeklyScores, astBreakdown, behaviorBreakdown }
 * TODO (Frontend): replace mock data with real API data
 * TODO (Frontend): add date range filter (This Week, This Month, All Time)
 */

import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import StatusBar from "../components/StatusBar";

// ─── Mock data ────────────────────────────────────────────────────────────────
const MOCK_STATS = [
  { value: 72,  label: "Level of Advancement", sublabel: "Skills + Behavior",    color: "#3b82f6", max: 100 },
  { value: 68,  label: "Avg. AST Score",        sublabel: "Across all tasks",     color: "#f59e0b", max: 100 },
  { value: 91,  label: "Behavior Score",         sublabel: "This week average",    color: "#a78bfa", max: 100 },
  { value: 8,   label: "Tasks Completed",        sublabel: "of 11 assigned",       color: "#22c55e", max: 11  },
];

// Weekly scores — used to draw a simple bar chart
const MOCK_WEEKLY = [
  { week: "Week 1", ast: 75, behavior: 88 },
  { week: "Week 2", ast: 80, behavior: 85 },
  { week: "Week 3", ast: 65, behavior: 92 },
  { week: "Week 4", ast: 68, behavior: 91 },
];

// AST breakdown — which constructs were detected in submissions
const MOCK_AST = [
  { label: "Loops (for/while)", score: 85, max: 100 },
  { label: "Conditionals",      score: 90, max: 100 },
  { label: "Functions",         score: 70, max: 100 },
  { label: "File I/O",          score: 55, max: 100 },
  { label: "Exception handling",score: 40, max: 100 },
];

// Behavior breakdown
const MOCK_BEHAVIOR = [
  { label: "Tab-switch events",    value: 4,   note: "lower is better", good: false },
  { label: "Copy-paste attempts",  value: 0,   note: "no violations",   good: true  },
  { label: "Execution attempts",   value: 12,  note: "avg per session",  good: true  },
  { label: "Idle time",            value: "3m", note: "avg per session", good: true  },
];

export default function Analytics() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const maxBar = Math.max(...MOCK_WEEKLY.map(w => Math.max(w.ast, w.behavior)));

  return (
    <div
      className="flex min-h-screen bg-[#0f1117] text-white select-none cursor-default"
      style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.4s ease" }}
    >
      <Sidebar activePage="My Analytics" />

      <main className="flex-1 overflow-y-auto px-8 py-6 pb-12">

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">My Analytics</h1>
          <p className="text-sm text-white/40 mt-1">Your performance across all coding sessions.</p>
        </div>

        {/* Stat cards */}
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
              <p className="text-3xl font-bold mb-1" style={{ color: stat.color }}>{stat.value}</p>
              <p className="text-xs text-white/70 font-medium">{stat.label}</p>
              <p className="text-[10px] text-white/30 mb-3">{stat.sublabel}</p>
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

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 max-w-5xl">

          {/* Weekly score bar chart
              Simple SVG bar chart — no chart library needed
              TODO (Frontend): replace with real weekly data from API
          */}
          <div className="bg-[#1a1d27] border border-white/[0.06] rounded-xl p-5">
            <h2 className="text-sm font-semibold text-white mb-1">Weekly Scores</h2>
            <p className="text-[11px] text-white/30 mb-4">AST vs Behavior score per week</p>

            <div className="flex items-end gap-4 h-32">
              {MOCK_WEEKLY.map((w, i) => (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full flex items-end gap-1 h-24">
                    {/* AST bar */}
                    <div className="flex-1 rounded-t-sm" style={{
                      height: `${(w.ast / maxBar) * 100}%`,
                      background: "#f59e0b",
                      transition: `height 0.8s cubic-bezier(0.25,0.46,0.45,0.94) ${i * 0.1}s`,
                    }} />
                    {/* Behavior bar */}
                    <div className="flex-1 rounded-t-sm" style={{
                      height: `${(w.behavior / maxBar) * 100}%`,
                      background: "#a78bfa",
                      transition: `height 0.8s cubic-bezier(0.25,0.46,0.45,0.94) ${i * 0.1 + 0.05}s`,
                    }} />
                  </div>
                  <span className="text-[9px] text-white/25">{w.week}</span>
                </div>
              ))}
            </div>

            {/* Legend */}
            <div className="flex items-center gap-4 mt-3">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-sm bg-[#f59e0b]" />
                <span className="text-[10px] text-white/40">AST Score</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-sm bg-[#a78bfa]" />
                <span className="text-[10px] text-white/40">Behavior Score</span>
              </div>
            </div>
          </div>

          {/* AST construct breakdown
              Shows which programming constructs the student used correctly
              TODO (Frontend): replace with real AST data from API
          */}
          <div className="bg-[#1a1d27] border border-white/[0.06] rounded-xl p-5">
            <h2 className="text-sm font-semibold text-white mb-1">AST Construct Breakdown</h2>
            <p className="text-[11px] text-white/30 mb-4">How well you used each programming concept</p>
            <div className="space-y-3">
              {MOCK_AST.map((item, i) => (
                <div key={i}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] text-white/60">{item.label}</span>
                    <span className="text-[11px] font-semibold" style={{
                      color: item.score >= 80 ? "#22c55e" : item.score >= 60 ? "#f59e0b" : "#ef4444"
                    }}>
                      {item.score}%
                    </span>
                  </div>
                  <div className="h-1 w-full bg-white/[0.06] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${item.score}%`,
                        background: item.score >= 80 ? "#22c55e" : item.score >= 60 ? "#f59e0b" : "#ef4444",
                        transition: `width 0.8s cubic-bezier(0.25,0.46,0.45,0.94) ${i * 0.1}s`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Behavior breakdown
              Shows behavioral tracking stats
              TODO (Frontend): replace with real behavior data from API
              TODO (Backend): GET /api/student/behavior returns behavior logs summary
          */}
          <div className="bg-[#1a1d27] border border-white/[0.06] rounded-xl p-5 xl:col-span-2">
            <h2 className="text-sm font-semibold text-white mb-1">Behavior Summary</h2>
            <p className="text-[11px] text-white/30 mb-4">Behavioral tracking data from your coding sessions</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {MOCK_BEHAVIOR.map((item, i) => (
                <div
                  key={i}
                  className="rounded-lg p-3 border"
                  style={{
                    background: "rgba(255,255,255,0.02)",
                    borderColor: "rgba(255,255,255,0.06)",
                  }}
                >
                  <p className="text-xl font-bold mb-0.5" style={{ color: item.good ? "#22c55e" : "#f59e0b" }}>
                    {item.value}
                  </p>
                  <p className="text-[11px] text-white/60 font-medium">{item.label}</p>
                  <p className="text-[10px] text-white/30 mt-0.5">{item.note}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      <StatusBar />
    </div>
  );
}