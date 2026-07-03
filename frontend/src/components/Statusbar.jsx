/**
 * StatusBar.jsx
 * The fixed bottom bar shown on all student pages.
 *
 * HOW TO USE:
 *   <StatusBar />
 *
 * TODO (Backend): get real session status from GET /api/student/session
 * TODO (Frontend): if session is expired, show red dot instead of green
 */

const MOCK_STUDENT = {
  name: "Juan, Miguel D.",
  course: "CCS101",
  courseName: "Introduction to Programming",
};

export default function StatusBar() {
  return (
    <div
      className="fixed bottom-0 left-0 right-0 h-9 flex items-center justify-between px-4 border-t border-white/[0.06] z-50"
      style={{ background: "#0d0f18" }}
    >
      <div className="flex items-center gap-2">
        {/* Green dot = session active. TODO: turn red if session expires */}
        <div className="w-1.5 h-1.5 rounded-full bg-[#22c55e]" />
        <span className="text-[10px] text-[#22c55e] font-mono select-none">
          Session active · {MOCK_STUDENT.course} — {MOCK_STUDENT.courseName}
        </span>
      </div>
      <span className="text-[10px] text-white/25 font-mono select-none">
        Python 3.12 · {MOCK_STUDENT.name}
      </span>
    </div>
  );
}