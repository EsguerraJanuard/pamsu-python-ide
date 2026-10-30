import { useCallback, useEffect, useState } from "react";

import PageShell from "../components/layout/PageShell";
import CustomSelect from "../components/ui/CustomSelect";
import { EmptyState, ErrorState, PageHeader, SkeletonList } from "../components/ui/StateViews";
import api from "../services/api";
import { formatDateTime, humanize } from "../utils/format";

const PAGE_SIZE = 15;

const RESOURCE_FILTERS = [
  { value: "all", label: "All events" },
  { value: "user", label: "Account & sign-in" },
  { value: "classroom", label: "Classrooms" },
  { value: "enrollment", label: "Enrollments" },
  { value: "task", label: "Activities" },
  { value: "submission", label: "Submissions" },
  { value: "grade", label: "Grades" },
];

const OUTCOME_BADGE = {
  succeeded: "badge-success",
  denied: "badge-gold",
  failed: "badge-danger",
};

export default function AuditLogsPage({ role = "student" }) {
  const [logs, setLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [resourceFilter, setResourceFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  const fetchAuditLogs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      let url = `/audit-records/?page=${page}&page_size=${PAGE_SIZE}`;
      if (resourceFilter !== "all") url += `&resource_type=${resourceFilter}`;
      const response = await api.get(url);
      setLogs(response?.items || []);
      setTotalPages(Math.max(1, response?.total_pages || 1));
      setTotalItems(response?.total ?? response?.total_items ?? 0);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [page, resourceFilter]);

  useEffect(() => {
    fetchAuditLogs();
  }, [fetchAuditLogs]);

  return (
    <PageShell role={role}>
      <PageHeader
        eyebrow="Account"
        title={role === "instructor" ? "Audit Logs" : "Audit History"}
        description="A record of security and academic events on your account."
        actions={
          <button type="button" onClick={fetchAuditLogs} disabled={isLoading} className="btn-secondary btn-sm">
            {isLoading ? "Refreshing…" : "Refresh"}
          </button>
        }
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="w-full sm:w-60">
          <CustomSelect
            value={resourceFilter}
            onChange={(value) => {
              setResourceFilter(value);
              setPage(1);
            }}
            options={RESOURCE_FILTERS}
            ariaLabel="Filter audit events"
          />
        </div>
        {!error && !isLoading && (
          <p className="text-xs text-text-muted">
            {totalItems} {totalItems === 1 ? "event" : "events"}
          </p>
        )}
      </div>

      {error ? (
        <ErrorState error={error} resource="your audit history" onRetry={fetchAuditLogs} />
      ) : isLoading ? (
        <SkeletonList rows={5} className="h-14" />
      ) : logs.length === 0 ? (
        <EmptyState
          icon="search"
          title="No audit events"
          message={resourceFilter === "all" ? "No events have been recorded yet." : "No events match this filter."}
        />
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead className="border-b border-border-subtle bg-bg-alt text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                <tr>
                  <th scope="col" className="px-4 py-3">When</th>
                  <th scope="col" className="px-4 py-3">Event</th>
                  <th scope="col" className="px-4 py-3">Resource</th>
                  <th scope="col" className="px-4 py-3 text-right">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {logs.map((log) => (
                  <tr key={log.audit_id} className="hover:bg-bg-alt/60">
                    <td className="whitespace-nowrap px-4 py-3 text-xs text-text-muted">{formatDateTime(log.occurred_at)}</td>
                    <td className="px-4 py-3 font-medium text-text-main">{humanize(log.action_type)}</td>
                    <td className="px-4 py-3 text-text-muted">
                      {humanize(log.resource_type)}
                      {log.resource_id ? <span className="ml-1 font-mono text-xs">#{log.resource_id.slice(0, 8)}</span> : null}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className={`badge ${OUTCOME_BADGE[log.outcome] || "badge-neutral"}`}>{humanize(log.outcome)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-border-subtle px-4 py-3 text-xs text-text-muted">
              <span>
                Page {page} of {totalPages}
              </span>
              <div className="flex gap-2">
                <button type="button" className="btn-secondary btn-sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  Previous
                </button>
                <button type="button" className="btn-secondary btn-sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </PageShell>
  );
}
