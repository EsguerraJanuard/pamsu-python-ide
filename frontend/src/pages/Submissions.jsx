/**
 * Submissions.jsx
 * Shows all submitted assignments with scores and reports.
 *
 * TODO (Backend): GET /api/student/submissions
 * Response: [{ id, title, submittedDate, astScore, behaviorScore, finalScore, feedback, similarity }]
 * TODO (Frontend): replace MOCK_SUBMISSIONS with real API data
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import StatusBar from "../components/StatusBar";

const MOCK_SUBMISSIONS = [
  {
    id: 3,
    title: "Lab Activity 2 — Control Flow & Functions",
    submittedDate: "Jan 10, 2026",
    astScore: 85,
    behaviorScore: 94,
    finalScore: 88,
    feedback: "All structural requirements met. Excellent behavioral consistency throughout the session.",
    similarity: 12,
  },
  {
    id: 4,
    title: "Lab Activity 1 — Variables & Data Types",
    submittedDate: "Jan 5, 2026",
    astScore: 90,
    behaviorScore: 96,
    finalScore: 92,
    feedback: "All requirements met. Good use of type conversion.",
    similarity: 8,
  },
];

export default function Submissions() {
  const [mounted, setMounted] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div
      className="flex min-h-screen bg-[#0f1117] text-white select-none cursor-default"
      style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.4s ease" }}
    >
      <Sidebar activePage="Submissions" />

      <main className="flex-1 overflow-y-auto px-8 py-6 pb-12">

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Submissions</h1>
          <p className="text-sm text-white/40 mt-1">{MOCK_SUBMISSIONS.length} submitted assignments</p>
        </div>

        <div className="space-y-4 max-w-3xl">
          {MOCK_SUBMISSIONS.map((sub, i) => (
            <div
              key={sub.id}
              className="bg-[#1a1d27] border border-white/[0.06] rounded-xl p-5"
              style={{
                borderLeft: "3px solid #22c55e",
                opacity: mounted ? 1 : 0,
                transform: mounted ? "translateY(0)" : "translateY(8px)",
                transition: `opacity 0.4s ease ${i * 0.08}s, transform 0.4s ease ${i * 0.08}s`,
              }}
            >
              {/* Title + date */}
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <h3 className="text-sm font-semibold text-white mb-0.5">{sub.title}</h3>
                  <p className="text-[11px] text-white/30">Submitted {sub.submittedDate}</p>
                </div>
                <span
                  className="text-[10px] font-semibold px-2 py-0.5 rounded-full border flex-shrink-0"
                  style={{ background: "rgba(34,197,94,0.15)", color: "#22c55e", borderColor: "rgba(34,197,94,0.3)" }}
                >
                  Submitted
                </span>
              </div>

              {/* Score breakdown */}
              <div className="grid grid-cols-3 gap-3 mb-3">
                {[
                  { label: "AST Score",      value: sub.astScore,      color: "#f59e0b" },
                  { label: "Behavior Score", value: sub.behaviorScore, color: "#a78bfa" },
                  { label: "Final Score",    value: sub.finalScore,    color: "#22c55e" },
                ].map((score, j) => (
                  <div
                    key={j}
                    className="rounded-lg p-3 text-center"
                    style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
                  >
                    <p className="text-lg font-bold" style={{ color: score.color }}>{score.value}</p>
                    <p className="text-[10px] text-white/40 mt-0.5">{score.label}</p>
                  </div>
                ))}
              </div>

              {/* Similarity score
                  Low = good. High = potential plagiarism flag.
                  TODO (Backend): this comes from the Jaccard Similarity algorithm result
              */}
              <div className="flex items-center gap-2 mb-3">
                <span className="text-[10px] text-white/30">Code similarity:</span>
                <span
                  className="text-[10px] font-semibold"
                  style={{ color: sub.similarity < 20 ? "#22c55e" : sub.similarity < 50 ? "#f59e0b" : "#ef4444" }}
                >
                  {sub.similarity}% — {sub.similarity < 20 ? "Original" : sub.similarity < 50 ? "Moderate" : "High risk"}
                </span>
              </div>

              {/* Feedback */}
              <div
                className="text-[11px] font-mono px-3 py-2 rounded-lg mb-3"
                style={{
                  background: "rgba(255,255,255,0.03)",
                  borderLeft: "2px solid rgba(255,255,255,0.08)",
                  color: "rgba(255,255,255,0.5)",
                }}
              >
                <span className="text-white/25">Feedback: </span>
                {sub.feedback}
              </div>

              {/* View full report button */}
              <button
                type="button"
                className="text-xs text-[#3b82f6] hover:text-[#60a5fa] transition-colors duration-150 cursor-pointer"
                onClick={() => navigate(`/submissions/${sub.id}`)}
              >
                View full report →
              </button>
            </div>
          ))}

          {MOCK_SUBMISSIONS.length === 0 && (
            <div className="text-center py-16 text-white/25 text-sm">
              No submissions yet.
            </div>
          )}
        </div>
      </main>

      <StatusBar />
    </div>
  );
}