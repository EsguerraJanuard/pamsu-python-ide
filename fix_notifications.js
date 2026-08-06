
const fs = require("fs");
const file = "frontend/src/pages/NotificationsPage.jsx";
let content = fs.readFileSync(file, "utf8");

const replacement = `  const [selectedNotification, setSelectedNotification] = useState(null);

  const fetchNotifications = async (currentPage = 1) => {`;

content = content.replace(`  const fetchNotifications = async (currentPage = 1) => {`, replacement);

const handleMarkAsReadReplacement = `  const handleMarkAsRead = async (id) => {
    try {
      await api.patch(\`/notifications/\${id}/read\`);
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

  const handleNotificationClick = (notif) => {
    setSelectedNotification(notif);
    if (!notif.is_read) {
      handleMarkAsRead(notif.id);
    }
  };`;

content = content.replace(/  const handleMarkAsRead = async.*?};/s, handleMarkAsReadReplacement);

const listUI = `              <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-160px)]">
                {/* Left Column: List */}
                <div className="flex-1 flex flex-col overflow-hidden">
                  {error && (
                    <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300 mb-4 shrink-0">
                      {error}
                    </div>
                  )}

                  {loading ? (
                    <div className="py-12 text-center text-xs text-slate-500 animate-pulse">
                      Loading notifications...
                    </div>
                  ) : notifications.length === 0 ? (
                    <div className="rounded-xl border border-white/[0.06] bg-[#1a1d27] p-12 text-center text-xs text-slate-400">
                      No notifications found.
                    </div>
                  ) : (
                    <div className="space-y-3 overflow-y-auto pr-2 pb-4 flex-1">
                      {notifications.map((notif) => (
                        <div
                          key={notif.id}
                          onClick={() => handleNotificationClick(notif)}
                          className={\`rounded-xl border p-4 transition cursor-pointer \${
                            selectedNotification?.id === notif.id
                              ? "border-emerald-500/50 bg-emerald-500/10"
                              : !notif.is_read
                              ? "border-blue-500/40 bg-blue-950/20 shadow-md hover:border-blue-500/60"
                              : "border-white/[0.06] bg-[#1a1d27] hover:bg-slate-800/50"
                          }\`}
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                {!notif.is_read && (
                                  <span className="h-2 w-2 rounded-full bg-blue-400 shrink-0" />
                                )}
                                <h2 className={\`text-sm font-bold \${selectedNotification?.id === notif.id ? "text-emerald-400" : !notif.is_read ? "text-white" : "text-slate-300"}\`}>
                                  {notif.title}
                                </h2>
                              </div>
                              <p className="text-xs text-slate-400 pl-4 line-clamp-1">{notif.message}</p>
                            </div>

                            <span className="text-[11px] font-mono text-slate-500 shrink-0 mt-1">
                              {new Date(notif.created_at || Date.now()).toLocaleDateString("en-US", {
                                month: "short",
                                day: "numeric",
                              })}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="flex justify-between items-center pt-4 text-xs font-mono text-slate-400 shrink-0 border-t border-white/[0.06] mt-2">
                      <span>Page {page} of {totalPages}</span>
                      <div className="flex gap-2">
                        <button
                          disabled={page <= 1}
                          onClick={() => setPage((p) => p - 1)}
                          className="rounded border border-slate-800 px-3 py-1 bg-slate-900 disabled:opacity-40 hover:bg-slate-800 transition"
                        >
                          Previous
                        </button>
                        <button
                          disabled={page >= totalPages}
                          onClick={() => setPage((p) => p + 1)}
                          className="rounded border border-slate-800 px-3 py-1 bg-slate-900 disabled:opacity-40 hover:bg-slate-800 transition"
                        >
                          Next
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Right Column: Details Pane */}
                <div className="flex-1 rounded-xl border border-white/[0.06] bg-[#1a1d27] hidden lg:flex flex-col">
                  {selectedNotification ? (
                    <div className="p-6 h-full flex flex-col">
                      <div className="flex items-center justify-between mb-6">
                        <span className="rounded-full bg-slate-800 border border-slate-700 px-3 py-1 text-[10px] font-mono text-slate-300 uppercase tracking-widest">
                          {selectedNotification.type || "System Alert"}
                        </span>
                        <span className="text-xs font-mono text-slate-400">
                          {new Date(selectedNotification.created_at || Date.now()).toLocaleString()}
                        </span>
                      </div>
                      
                      <h2 className="text-xl font-bold text-white mb-4">
                        {selectedNotification.title}
                      </h2>
                      
                      <div className="bg-black/20 rounded-xl p-5 border border-white/[0.02] mb-6 flex-1">
                        <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                          {selectedNotification.message}
                        </p>
                      </div>

                      <div className="pt-6 border-t border-white/[0.06] shrink-0">
                        <p className="text-xs text-slate-500 mb-4 uppercase tracking-wide font-semibold">Suggested Actions</p>
                        <div className="flex gap-3">
                          {selectedNotification.type === "classroom" && (
                            <button className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg px-4 py-2.5 text-sm font-medium transition-colors shadow-lg shadow-emerald-500/20">
                              Review Request
                            </button>
                          )}
                          {selectedNotification.type === "grade" && (
                            <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-2.5 text-sm font-medium transition-colors shadow-lg shadow-blue-500/20">
                              View Submission Details
                            </button>
                          )}
                          <button className="flex-1 bg-slate-800 hover:bg-slate-700 text-white rounded-lg px-4 py-2.5 text-sm font-medium transition-colors border border-slate-700">
                            Dismiss Alert
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-slate-500 p-8 text-center">
                      <div className="w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mb-4 border border-white/[0.02]">
                        <svg className="w-8 h-8 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                        </svg>
                      </div>
                      <p className="text-sm font-medium text-slate-400">No notification selected</p>
                      <p className="text-xs mt-2 max-w-[250px] leading-relaxed">Select a notification from the list to view its full details and available actions.</p>
                    </div>
                  )}
                </div>
              </div>`;

content = content.replace(/              <div className="space-y-4">.*?(?=            <\/div>\n          <\/main>)/s, listUI + "\n");

fs.writeFileSync(file, content);
console.log("Updated NotificationsPage.jsx!");
