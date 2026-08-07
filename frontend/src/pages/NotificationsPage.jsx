import { useState, useEffect } from "react";
import { useAuth } from "../features/auth/AuthContext";
import api from "../services/api";
import Sidebar from "../components/layout/Sidebar";
import InstructorSidebar from "../components/layout/InstructorSidebar";
import { useNavigate } from "react-router-dom";

function BellIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>
  );
}

export default function NotificationsPage({ role: propRole }) {
  const auth = useAuth() || {};
  const activeRole = propRole || auth.role || "student";
  const isInstructor = activeRole === "instructor";
  const navigate = useNavigate();

  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [unreadCount, setUnreadCount] = useState(0);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedNotification, setSelectedNotification] = useState(null);

  const mockNotifications = [
    {
      id: "notif-1",
      title: "Submission received",
      message: "John Doe submitted Lab Activity 3 - Fibonacci Sequence, attempt 1.",
      created_at: new Date().toISOString(),
      is_read: false,
      type: "submission",
      reference_id: "123",
    },
    {
      id: "notif-2",
      title: isInstructor ? "New Student Join Request" : "Lab Activity 3 Graded",
      message: isInstructor
        ? "Juan Dela Cruz requested to join CS101 — Intro to Programming."
        : "Instructor posted official AST and manual score evaluation for Fibonacci Sequence.",
      created_at: new Date(Date.now() - 3600000).toISOString(),
      is_read: false,
      type: isInstructor ? "classroom" : "grade",
      reference_id: "456",
    },
    {
      id: "notif-3",
      title: isInstructor ? "Submission Threshold Alert" : "Classroom Enrollment Approved",
      message: isInstructor
        ? "82% of students submitted Lab Activity 3 before the deadline."
        : "You have been officially enrolled in CCS101 — Intro to Computer Science.",
      created_at: new Date(Date.now() - 86400000).toISOString(),
      is_read: false,
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
    } catch (err) {
      console.log("Mock mark all read");
    } finally {
      setNotifications((prev) => prev.map((item) => ({ ...item, is_read: true })));
      setUnreadCount(0);
      setActionLoading(false);
    }
  };

  const handleMarkAsRead = async (id) => {
    try {
      await api.patch(`/notifications/${id}/read`);
    } catch (err) {
       console.log("Mock mark read");
    } finally {
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    }
  };

  const handleNotificationClick = (notif) => {
    setSelectedNotification(notif);
    if (!notif.is_read) {
      handleMarkAsRead(notif.id);
    }
  };

  const handleAction = (type, refId) => {
    if (type === "submission") navigate(`/instructor/submissions/${refId || ""}`);
    else if (type === "classroom") navigate(`/instructor/classes/${refId || ""}`);
    else if (type === "grade") navigate(`/student/submissions/${refId || ""}`);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white select-none">
      {isInstructor ? <InstructorSidebar /> : <Sidebar />}

      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
            <div className="mx-auto max-w-6xl h-full flex flex-col">
              <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-white/[0.06] pb-6 shrink-0">
                <div>
                  <h1 className="text-2xl font-bold flex items-center gap-3 tracking-wide">
                    <BellIcon className="h-6 w-6 text-emerald-400" />
                    {isInstructor ? "System Alerts" : "Student Notifications"}
                  </h1>
                  <p className="mt-1 text-sm text-white/40">
                    View your recent alerts and system messages.
                  </p>
                </div>

                <button
                  onClick={handleMarkAllRead}
                  disabled={actionLoading || unreadCount === 0}
                  className="rounded-lg border border-white/[0.06] bg-[#1a1d27] px-4 py-2 text-xs font-semibold hover:bg-white/[0.03] transition disabled:opacity-50"
                >
                  {actionLoading ? "Updating..." : "✓ Mark all as read"}
                </button>
              </header>

              <div className="flex-1 flex gap-6 overflow-hidden pb-4">
                {/* Left Pane: Notification List */}
                <div className={`flex-col flex w-full lg:w-1/3 rounded-xl border border-white/[0.06] bg-[#1a1d27] overflow-hidden ${selectedNotification ? "hidden lg:flex" : "flex"}`}>
                  <div className="border-b border-white/[0.06] p-4 bg-[#1a1d27]">
                    <h2 className="text-sm font-semibold">Inbox</h2>
                  </div>
                  
                  <div className="flex-1 overflow-y-auto">
                    {loading ? (
                      <div className="p-8 text-center text-xs text-white/40 animate-pulse">Loading...</div>
                    ) : notifications.length === 0 ? (
                      <div className="p-8 text-center text-xs text-white/40">No notifications.</div>
                    ) : (
                      <div className="divide-y divide-white/[0.06]">
                        {notifications.map((notif) => {
                          const isSelected = selectedNotification?.id === notif.id;
                          return (
                            <div
                              key={notif.id}
                              onClick={() => handleNotificationClick(notif)}
                              className={`p-4 cursor-pointer transition-colors ${
                                isSelected 
                                  ? "bg-white/[0.04]" 
                                  : !notif.is_read 
                                    ? "bg-blue-500/[0.03] hover:bg-blue-500/[0.06]" 
                                    : "hover:bg-white/[0.02]"
                              }`}
                            >
                              <div className="flex items-start gap-3">
                                {!notif.is_read && (
                                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)]" />
                                )}
                                <div className={`min-w-0 flex-1 ${notif.is_read ? "ml-4.5" : ""}`}>
                                  <h3 className={`truncate text-sm ${!notif.is_read ? "font-semibold text-white" : "font-medium text-white/70"}`}>
                                    {notif.title}
                                  </h3>
                                  <p className="mt-1 line-clamp-2 text-xs text-white/40 leading-relaxed">
                                    {notif.message}
                                  </p>
                                  <p className="mt-2 text-[10px] font-mono text-white/30">
                                    {new Date(notif.created_at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                                  </p>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>

                {/* Right Pane: Notification Details */}
                <div className={`flex-col flex w-full lg:w-2/3 rounded-xl border border-white/[0.06] bg-[#1a1d27] overflow-hidden ${!selectedNotification ? "hidden lg:flex" : "flex"}`}>
                  {selectedNotification ? (
                    <div className="flex h-full flex-col">
                      <div className="border-b border-white/[0.06] p-4 bg-[#1a1d27] flex items-center gap-3">
                        <button 
                          className="lg:hidden rounded-lg p-1.5 hover:bg-white/[0.06]"
                          onClick={() => setSelectedNotification(null)}
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
                        </button>
                        <h2 className="text-sm font-semibold text-emerald-400">Notification Details</h2>
                      </div>
                      
                      <div className="flex-1 overflow-y-auto p-8">
                        <div className="mx-auto max-w-2xl">
                          <span className="inline-block rounded-full border border-white/[0.06] bg-white/[0.03] px-3 py-1 text-[10px] font-mono text-white/50 mb-4">
                            {new Date(selectedNotification.created_at).toLocaleString([], { weekday: "long", year: "numeric", month: "long", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                          </span>
                          
                          <h1 className="text-2xl font-bold mb-4">{selectedNotification.title}</h1>
                          
                          <div className="prose prose-invert prose-sm max-w-none text-white/70 mb-8">
                            <p className="leading-relaxed text-sm">
                              {selectedNotification.message}
                            </p>
                          </div>

                          <div className="border-t border-white/[0.06] pt-6">
                            <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-4">Suggested Actions</h3>
                            <div className="flex flex-wrap gap-3">
                              {selectedNotification.type === "submission" && (
                                <button onClick={() => handleAction("submission", selectedNotification.reference_id)} className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500 transition">
                                  Review Submission
                                </button>
                              )}
                              {selectedNotification.type === "classroom" && (
                                <button onClick={() => handleAction("classroom", selectedNotification.reference_id)} className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-xs font-semibold text-emerald-400 hover:bg-emerald-500/20 transition">
                                  Manage Classroom
                                </button>
                              )}
                              {selectedNotification.type === "grade" && (
                                <button onClick={() => handleAction("grade", selectedNotification.reference_id)} className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500 transition">
                                  View Grade
                                </button>
                              )}
                              <button 
                                onClick={() => setSelectedNotification(null)}
                                className="rounded-lg border border-white/[0.06] bg-transparent px-4 py-2 text-xs font-semibold text-white/70 hover:bg-white/[0.03] transition"
                              >
                                Dismiss
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex h-full flex-col items-center justify-center text-white/30">
                      <svg className="h-12 w-12 mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                      </svg>
                      <p className="text-sm">Select a notification to view details.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
