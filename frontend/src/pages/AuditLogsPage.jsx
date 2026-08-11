import { useState, useEffect } from "react";
import { useAuth } from "../features/auth/AuthContext";
import api from "../services/api";
import Sidebar from "../components/layout/Sidebar";
import InstructorSidebar from "../components/layout/InstructorSidebar";
import Statusbar from "../components/layout/Statusbar";

function ShieldIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/></svg>
  );
}

export default function AuditLogsPage({ role: propRole }) {
  const auth = useAuth() || {};
  const activeRole = propRole || auth.role || "student";
  const isInstructor = activeRole === "instructor";

  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [actionFilter, setActionFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState("");



  const fetchAuditLogs = async (currentPage = 1, currentFilter = "all") => {
    setLoading(true);
    setError("");
    try {
      let url = `/audit-records/?page=${currentPage}&page_size=15`;
      if (currentFilter === "login") url += "&resource_type=user";
      else if (currentFilter === "submission") url += "&resource_type=submission";
      else if (currentFilter === "classroom") url += "&resource_type=classroom";

      const response = await api.get(url);
      if (response && Array.isArray(response.items)) {
        setLogs(response.items);
        setTotalPages(response.total_pages || 1);
      } else {
        setLogs([]);
      }
    } catch (err) {
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs(page, actionFilter);
  }, [page, actionFilter]);

  const filteredLogs = logs.filter((log) => {
    const matchesQuery =
      (log.action || log.action_type || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (log.resource || log.resource_type || log.resource_id || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (log.ip_address || log.audit_data?.ip_address || "127.0.0.1").toLowerCase().includes(searchQuery.toLowerCase());

    return matchesQuery;
  });

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
      {isInstructor ? <InstructorSidebar /> : <Sidebar />}

      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-6 py-6 sm:px-8">
            <div className="w-full">
              <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-border-subtle pb-6">
                <div>
                  <h1 className="text-2xl font-bold flex items-center gap-3 tracking-wide">
                    <ShieldIcon className="h-6 w-6 text-text-emerald" />
                    {isInstructor ? "System Audit Logs" : "Audit History"}
                  </h1>
                  <p className="mt-1 text-sm text-text-muted">
                    Review system events and security logs.
                  </p>
                </div>

                <button
                  onClick={() => fetchAuditLogs(page, actionFilter)}
                  disabled={loading}
                  className="rounded-lg border border-border-subtle bg-bg-glass px-3.5 py-1.5 text-xs font-medium text-text-muted hover:bg-bg-glass-hover transition"
                >
                  {loading ? "Refreshing..." : "↻ Refresh Audit Trail"}
                </button>
              </header>

              <div className="space-y-6">
                {/* Controls Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-border-subtle bg-bg-glass p-4">
                  <div className="flex items-center gap-3 flex-1">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search by action, resource, or IP address..."
                      className="w-full sm:w-80 rounded-lg border border-border-subtle bg-bg-glass px-3.5 py-2 text-xs text-text-main placeholder:text-text-muted focus:border-emerald-500/50 focus:outline-none transition"
                    />
                  </div>

                  <div className="flex items-center gap-3">
                    <label className="text-xs font-medium text-text-muted">Action Type:</label>
                    <select
                      value={actionFilter}
                      onChange={(e) => {
                        setActionFilter(e.target.value);
                        setPage(1); // Reset page on filter change
                      }}
                      className="rounded-lg border border-border-subtle bg-bg-glass px-3 py-2 text-xs text-text-main focus:border-emerald-500/50 focus:outline-none transition"
                    >
                      <option value="all">All Actions</option>
                      <option value="login">Login Events</option>
                      <option value="submission">Submissions</option>
                      <option value="classroom">Classroom Events</option>
                    </select>
                  </div>
                </div>

                {/* Audit Data Table */}
                <div className="rounded-xl border border-border-subtle bg-bg-glass shadow-xl overflow-hidden">
                  {loading ? (
                    <div className="divide-y divide-white/[0.06] w-full text-left text-xs font-mono">
                      {[1, 2, 3, 4, 5].map(i => (
                        <div key={i} className="flex px-4 py-3.5 animate-pulse items-center">
                          <div className="w-1/4 h-3 rounded bg-white/[0.06] mr-4"></div>
                          <div className="w-1/5 h-3 rounded bg-white/[0.06] mr-4"></div>
                          <div className="w-1/5 h-3 rounded bg-white/[0.06] mr-4"></div>
                          <div className="w-1/6 h-3 rounded bg-white/[0.06] mr-4"></div>
                          <div className="w-1/12 h-4 rounded bg-white/[0.06] ml-auto"></div>
                        </div>
                      ))}
                    </div>
                  ) : filteredLogs.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 px-6 text-center transition-all hover:bg-bg-glass">
                      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-slate-500/10 text-text-muted ring-4 ring-slate-500/5">
                        <ShieldIcon className="h-7 w-7" />
                      </div>
                      <h3 className="mb-2 text-lg font-semibold text-text-main">No Audit Records Found</h3>
                      <p className="text-xs text-text-muted max-w-sm">
                        No security events or actions match your current search criteria.
                      </p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="border-b border-border-subtle bg-bg-glass text-text-muted font-semibold uppercase tracking-wider">
                            <th className="py-3.5 px-4">Timestamp</th>
                            <th className="py-3.5 px-4">Action Type</th>
                            <th className="py-3.5 px-4">Target Resource</th>
                            <th className="py-3.5 px-4 font-mono">IP Address</th>
                            <th className="py-3.5 px-4 text-right">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/[0.06] font-mono">
                          {filteredLogs.map((log) => (
                            <tr key={log.id} className="hover:bg-bg-glass-hover transition">
                              <td className="py-3.5 px-4 text-text-muted whitespace-nowrap">
                                {new Date(log.timestamp || log.occurred_at || log.created_at || Date.now()).toLocaleString()}
                              </td>
                              <td className="py-3.5 px-4 font-semibold text-text-main font-sans">
                                {log.action || log.action_type}
                              </td>
                              <td className="py-3.5 px-4 text-text-muted">
                                {log.resource || log.resource_type || log.resource_id || "N/A"}
                              </td>
                              <td className="py-3.5 px-4 text-text-blue">
                                {log.ip_address || log.audit_data?.ip_address || "127.0.0.1"}
                              </td>
                              <td className="py-3.5 px-4 text-right font-sans">
                                <span
                                  className={`rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide border ${
                                    (log.status === "SUCCESS" || log.outcome === "succeeded")
                                      ? "border-emerald-500/30 bg-emerald-500/10 text-text-emerald"
                                      : "border-rose-500/30 bg-rose-500/10 text-text-rose"
                                  }`}
                                >
                                  {log.status || log.outcome || "SUCCESS"}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex justify-between items-center pt-2 text-xs font-mono text-text-muted">
                    <span>Page {page} of {totalPages}</span>
                    <div className="flex gap-2">
                      <button
                        disabled={page <= 1}
                        onClick={() => setPage((p) => p - 1)}
                        className="rounded border border-border-subtle px-3 py-1 bg-bg-glass disabled:opacity-40"
                      >
                        Previous
                      </button>
                      <button
                        disabled={page >= totalPages}
                        onClick={() => setPage((p) => p + 1)}
                        className="rounded border border-border-subtle px-3 py-1 bg-bg-glass disabled:opacity-40"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
