/**
 * Workspace.jsx
 * This is the Student IDE page where students write and run Python code.
 *
 * This page is intentionally left as a placeholder for now.
 * The Monaco Editor and code execution will be wired up in the next sprint.
 *
 * TODO (Frontend): integrate Monaco Editor here
 * TODO (Frontend): read task ID from URL query param: ?task=ID
 * TODO (Backend): GET /api/student/tasks/:id — load the task details
 * TODO (Backend): POST /api/student/submit — submit the code for grading
 * TODO (Backend): POST /api/code/run — run code via Judge0 sandbox
 * TODO (Frontend): track tab switches and copy-paste events here (behavioral tracking)
 */

import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import StatusBar from "../components/StatusBar";

export default function Workspace() {
  const [mounted, setMounted] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const taskId = searchParams.get("task"); // gets the task ID from the URL

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div
      className="flex flex-col min-h-screen bg-[#0f1117] text-white select-none cursor-default"
      style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.4s ease" }}
    >
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-7 h-7 rounded-md bg-[#3b82f6] text-white text-xs font-bold font-mono">
            &gt;_
          </div>
          <span className="text-sm font-semibold text-white">Python IDE</span>
          {taskId && (
            <span className="text-xs text-white/30 font-mono">Task #{taskId}</span>
          )}
        </div>

        {/* Leave button — goes back to dashboard */}
        <button
          type="button"
          onClick={() => navigate("/dashboard/student")}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-white/50 border border-white/[0.08] cursor-pointer"
          style={{ transition: "color 0.2s ease, border-color 0.2s ease, transform 0.15s ease" }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = "rgba(255,255,255,0.9)";
            e.currentTarget.style.borderColor = "rgba(255,255,255,0.2)";
            e.currentTarget.style.transform = "translateY(-1px)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = "rgba(255,255,255,0.5)";
            e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
            e.currentTarget.style.transform = "translateY(0)";
          }}
        >
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
            <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Leave
        </button>
      </div>

      {/* Placeholder content — replace with Monaco Editor later */}
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl bg-[#1a1d27] border border-white/[0.06] flex items-center justify-center mx-auto mb-4">
            <svg width="28" height="28" viewBox="0 0 16 16" fill="none" className="text-white/20">
              <path d="M5 5L2 8l3 3M11 5l3 3-3 3M9 3l-2 10" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-white mb-2">Workspace coming soon</h2>
          <p className="text-sm text-white/35 mb-6 max-w-xs">
            The Monaco Editor and code execution will be integrated here in the next sprint.
          </p>
          <button
            type="button"
            onClick={() => navigate("/dashboard/student")}
            className="px-4 py-2 rounded-lg text-sm font-semibold text-white cursor-pointer"
            style={{
              background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
              transition: "opacity 0.15s ease, transform 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.opacity = "0.88";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = "1";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      <StatusBar />
    </div>
  );
}