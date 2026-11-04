import { useCallback, useEffect, useState } from "react";

import PageShell from "../components/layout/PageShell";
import CustomSelect from "../components/ui/CustomSelect";
import Pagination from "../components/ui/Pagination";
import { EmptyState, ErrorState, PageHeader, SkeletonList } from "../components/ui/StateViews";
import api from "../services/api";
import { formatDateTime, humanize } from "../utils/format";
import Icon from "../components/ui/Icon";

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
            <Icon name="refresh" className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
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
        <div className="card overflow-clip">
          <table className="data-table table-fixed">
            <caption className="sr-only">Audit events, newest first</caption>
            <thead>
              <tr>
                <th scope="col" className="hidden w-48 sm:table-cell">When</th>
                <th scope="col">Event</th>
                <th scope="col" className="hidden w-56 md:table-cell">Resource</th>
                <th scope="col" className="w-28 text-right sm:w-32">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => {
                const resource = (
                  <span className="inline-flex max-w-full items-center gap-1.5 rounded-md border border-border-subtle bg-bg-alt px-2 py-0.5 text-xs font-medium text-text-muted">
                    <span className="truncate">{humanize(log.resource_type)}</span>
                    {log.resource_id ? <span className="font-mono">#{String(log.resource_id).slice(0, 8)}</span> : null}
                  </span>
                );
                return (
                  <tr key={log.audit_id}>
                    <td className="hidden whitespace-nowrap text-xs tabular-nums text-text-muted sm:table-cell">
                      <time dateTime={log.occurred_at}>{formatDateTime(log.occurred_at)}</time>
                    </td>
                    <td>
                      <p className="font-medium text-text-main">{humanize(log.action_type)}</p>
                      {/* Narrow screens hide When (below sm) and Resource (below md); show them here instead. */}
                      <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 md:hidden">
                        <time dateTime={log.occurred_at} className="text-xs tabular-nums text-text-muted sm:hidden">
                          {formatDateTime(log.occurred_at)}
                        </time>
                        {resource}
                      </div>
                    </td>
                    <td className="hidden md:table-cell">{resource}</td>
                    <td className="text-right">
                      <span className={`badge ${OUTCOME_BADGE[log.outcome] || "badge-neutral"}`}>{humanize(log.outcome)}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <Pagination
            page={page}
            totalPages={totalPages}
            totalItems={totalItems}
            pageSize={PAGE_SIZE}
            onPageChange={setPage}
            disabled={isLoading}
            noun={totalItems === 1 ? "event" : "events"}
          />
        </div>
      )}
    </PageShell>
  );
}
