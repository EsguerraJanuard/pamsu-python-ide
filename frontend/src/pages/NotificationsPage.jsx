import { useState, useEffect } from "react";
import { useAuth } from "../features/auth/AuthContext";
import api from "../services/api";
import Sidebar from "../components/layout/Sidebar";
import InstructorSidebar from "../components/layout/InstructorSidebar";
import Statusbar from "../components/layout/Statusbar";

export default function NotificationsPage({ role: propRole }) {
  const auth = useAuth() || {};
  const activeRole = propRole || auth.role || "student";
  const isInstructor = activeRole === "instructor";

  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [unreadCount, setUnreadCount] = useState(0);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");

  const mockNotifications = [
    {
      id: "notif-1",
      title: isInstructor ? "New Student Join Request" : "Lab Activity 3 Graded",
      message: isInstructor
        ? "Juan Dela Cruz requested to join CS101 — Intro to Programming."
        : "Instructor posted official AST and manual score evaluation for Fibonacci Sequence.",
      created_at: "2026-01-15T14:47:00Z",
      is_read: false,
      type: isInstructor ? "classroom" : "grade",
    },
    {
      id: "notif-2",
      title: isInstructor ? "Submission Threshold Alert" : "Classroom Enrollment Approved",
      message: isInstructor
        ? "82% of students submitted Lab Activity 3 before the deadline."
        : "You have been officially enrolled in CCS101 — Intro to Computer Science.",
      created_at: "2026-01-12T09:15:00Z",
      is_read: false,
      type: "system",
    },
    {
      id: "notif-3",
      title: "System Update Complete",
      message: "PAMSU IDE system maintenance completed successfully.",
      created_at: "2026-01-10T16:30:00Z",
      is_read: true,
      type: "system",
    },
  ];

  const fetchNotifications = async (currentPage = 1) => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get(`/notifications/?page=${currentPage}&page_size=10`);
      if (response && Array.isArray(response.items)) {
        setNotifications(response.items);
        setTotalPages(response.total_pages || 1);
        setUnreadCount(response.unread_count || response.items.filter((n) => !n.is_read).length);
      } else {
        setNotifications(mockNotifications);
        setUnreadCount(mockNotifications.filter((n) => !n.is_read).length);
      }
    } catch (err) {
      setNotifications(mockNotifications);
      setUnreadCount(mockNotifications.filter((n) => !n.is_read).length);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications(page);
  }, [page]);

  const handleMarkAllRead = async () => {
    setActionLoading(true);
    try {
      await api.patch("/notifications/read-all");
      setNotifications((prev) => prev.map((item) => ({ ...item, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      setNotifications((prev) => prev.map((item) => ({ ...item, is_read: true })));
      setUnreadCount(0);
    } finally {
      setActionLoading(false);
    }
  };

  const handleMarkAsRead = async (id) => {
    try {
      await api.patch(`/notifications/${id}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0a0c14] text-slate-200">
      {isInstructor ? <InstructorSidebar /> : <Sidebar />}

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 items-center justify-between border-b border-slate-800/80 bg-[#0d101d] px-6">
          <div className="flex items-center gap-3">
            <h1 className="text-base font-bold text-white tracking-wide">
              {isInstructor ? "Instructor System Alerts" : "Student Notifications"}
            </h1>
            {unreadCount > 0 && (
              <span className="rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-0.5 text-xs font-mono">
                {unreadCount} Unread
              </span>
            )}
          </div>

          <button
            onClick={handleMarkAllRead}
            disabled={actionLoading || unreadCount === 0}
            className="rounded-lg border border-slate-800 bg-slate-900 px-3.5 py-1.5 text-xs font-medium text-slate-300 hover:border-slate-700 hover:bg-slate-800 transition disabled:opacity-50"
          >
            {actionLoading ? "Updating..." : "✓ Mark all as read"}
          </button>
        </header>

        <main className="flex-1 overflow-y-auto p-6 space-y-4 max-w-4xl mx-auto w-full">
          {error && (
            <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
              {error}
            </div>
          )}

          {loading ? (
            <div className="py-12 text-center text-xs text-slate-500 animate-pulse">
              Loading notifications...
            </div>
          ) : notifications.length === 0 ? (
            <div className="rounded-xl border border-slate-800 bg-[#111424] p-12 text-center text-xs text-slate-400">
              No notifications found.
            </div>
          ) : (
            <div className="space-y-3">
              {notifications.map((notif) => (
                <div
                  key={notif.id}
                  onClick={() => !notif.is_read && handleMarkAsRead(notif.id)}
                  className={`rounded-xl border p-4 transition cursor-pointer ${
                    !notif.is_read
                      ? "border-blue-500/40 bg-blue-950/20 shadow-md"
                      : "border-slate-800 bg-[#111424]/60 hover:bg-[#111424]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        {!notif.is_read && (
                          <span className="h-2 w-2 rounded-full bg-blue-400 shrink-0" />
                        )}
                        <h2 className={`text-sm font-bold ${!notif.is_read ? "text-white" : "text-slate-300"}`}>
                          {notif.title}
                        </h2>
                      </div>
                      <p className="text-xs text-slate-400 pl-4">{notif.message}</p>
                    </div>

                    <span className="text-[11px] font-mono text-slate-500 shrink-0">
                      {new Date(notif.created_at || Date.now()).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-between items-center pt-4 text-xs font-mono text-slate-400">
              <span>Page {page} of {totalPages}</span>
              <div className="flex gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="rounded border border-slate-800 px-3 py-1 bg-slate-900 disabled:opacity-40"
                >
                  Previous
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="rounded border border-slate-800 px-3 py-1 bg-slate-900 disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </main>

        <Statusbar sessionStatus="active" courseCode={isInstructor ? "Instructor" : "Student"} courseName="Alert History" />
      </div>
    </div>
  );
}
