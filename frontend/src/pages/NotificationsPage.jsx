import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import PageShell from "../components/layout/PageShell";
import { EmptyState, ErrorState, InlineAlert, PageHeader, SkeletonList } from "../components/ui/StateViews";
import api, { getErrorMessage } from "../services/api";
import { formatDateTime } from "../utils/format";

const PAGE_SIZE = 10;

/** Maps a notification's resource to an in-app destination for the given role. */
function resourceLink(notification, role) {
  const { resource_type: type, resource_id: id } = notification;
  if (role === "instructor") {
    if (type === "classroom") return { to: `/instructor/classes/${id}`, label: "Open class" };
    if (type === "task") return { to: `/instructor/activities/${id}`, label: "Open activity" };
    if (type === "submission" || type === "grade") return { to: "/instructor/bench", label: "Open grading bench" };
    if (type === "enrollment") return { to: "/instructor/classes", label: "View classes" };
    return null;
  }
  if (type === "classroom") return { to: `/student/classes/${id}`, label: "Open class" };
  if (type === "task") return { to: `/student/workspace?activity=${id}`, label: "Open activity" };
  if (type === "submission") return { to: `/student/submissions/${id}`, label: "View submission" };
  if (type === "grade") return { to: "/student/submissions", label: "View grades" };
  if (type === "enrollment") return { to: "/student/classes", label: "View my classes" };
  return null;
}

export default function NotificationsPage({ role = "student" }) {
  const [notifications, setNotifications] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [unreadCount, setUnreadCount] = useState(0);
  const [readFilter, setReadFilter] = useState("all");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionError, setActionError] = useState("");
  const [isMarkingAll, setIsMarkingAll] = useState(false);
  const [selectedId, setSelectedId] = useState(null);

  const fetchNotifications = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get(`/notifications/?page=${page}&page_size=${PAGE_SIZE}&read_filter=${readFilter}`);
      setNotifications(response?.items || []);
      setTotalPages(Math.max(1, response?.total_pages || 1));
      setUnreadCount(response?.recipient_unread_count ?? 0);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [page, readFilter]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const selected = notifications.find((n) => n.notification_id === selectedId) || null;

  const markAsRead = async (notification) => {
    if (notification.is_read) return;
    try {
      await api.patch(`/notifications/${notification.notification_id}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === notification.notification_id ? { ...n, is_read: true } : n)),
      );
      setUnreadCount((count) => Math.max(0, count - 1));
    } catch (err) {
      setActionError(getErrorMessage(err, "This notification couldn't be marked as read."));
    }
  };

  const handleSelect = (notification) => {
    setActionError("");
    setSelectedId(notification.notification_id);
    markAsRead(notification);
  };

  const handleMarkAllRead = async () => {
    setIsMarkingAll(true);
    setActionError("");
    try {
      const result = await api.patch("/notifications/read-all");
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(result?.remaining_unread_count ?? 0);
    } catch (err) {
      setActionError(getErrorMessage(err, "Notifications couldn't be marked as read."));
    } finally {
      setIsMarkingAll(false);
    }
  };

  const link = selected ? resourceLink(selected, role) : null;

  return (
    <PageShell role={role}>
      <PageHeader
        eyebrow="Account"
        title="Notifications"
        description={error ? "Updates about your classes, activities and grades." : `${unreadCount} unread`}
        actions={
          <button
            type="button"
            onClick={handleMarkAllRead}
            disabled={isMarkingAll || unreadCount === 0 || Boolean(error)}
            className="btn-secondary btn-sm"
          >
            {isMarkingAll ? "Updating…" : "Mark all as read"}
          </button>
        }
      />

      {actionError && (
        <InlineAlert tone="error" onDismiss={() => setActionError("")} className="mb-4">
          {actionError}
        </InlineAlert>
      )}

      {error ? (
        <ErrorState error={error} resource="your notifications" onRetry={fetchNotifications} />
      ) : (
        <>
          <div className="mb-4 flex w-fit gap-1 rounded-lg border border-border-subtle bg-bg-panel p-1" role="tablist" aria-label="Filter notifications">
            {[
              ["all", "All"],
              ["unread", "Unread"],
              ["read", "Read"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                role="tab"
                aria-selected={readFilter === value}
                onClick={() => {
                  setReadFilter(value);
                  setPage(1);
                  setSelectedId(null);
                }}
                className={`rounded-md px-3.5 py-1.5 text-sm font-medium transition-colors ${
                  readFilter === value ? "bg-psu-maroon text-white shadow-sm" : "text-text-muted hover:bg-bg-alt hover:text-text-main"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
            <section className={`card overflow-hidden ${selected ? "hidden lg:block" : ""}`} aria-label="Notification list">
              {isLoading ? (
                <div className="p-4">
                  <SkeletonList rows={4} className="h-16" />
                </div>
              ) : notifications.length === 0 ? (
                <EmptyState
                  className="m-4 border-0"
                  title={readFilter === "unread" ? "No unread notifications" : "No notifications"}
                  message="You're all caught up. Updates about classes, activities and grades will appear here."
                />
              ) : (
                <ul className="divide-y divide-border-subtle">
                  {notifications.map((notification) => {
                    const isSelected = notification.notification_id === selectedId;
                    return (
                      <li key={notification.notification_id}>
                        <button
                          type="button"
                          onClick={() => handleSelect(notification)}
                          aria-current={isSelected ? "true" : undefined}
                          className={`flex w-full items-start gap-3 px-4 py-3.5 text-left transition-colors ${
                            isSelected ? "bg-psu-cream" : "hover:bg-bg-alt"
                          }`}
                        >
                          <span
                            className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${notification.is_read ? "bg-transparent" : "bg-psu-maroon"}`}
                            aria-hidden="true"
                          />
                          <span className="min-w-0 flex-1">
                            <span className={`block truncate text-sm ${notification.is_read ? "text-text-muted" : "font-semibold text-text-main"}`}>
                              {notification.title}
                              {!notification.is_read && <span className="sr-only"> (unread)</span>}
                            </span>
                            <span className="mt-0.5 line-clamp-2 block text-xs text-text-muted">{notification.message}</span>
                            <span className="mt-1 block text-[11px] text-text-muted">{formatDateTime(notification.occurred_at)}</span>
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}

              {totalPages > 1 && (
                <div className="flex items-center justify-between border-t border-border-subtle px-4 py-3 text-xs text-text-muted">
                  <span>
                    Page {page} of {totalPages}
                  </span>
                  <div className="flex gap-2">
                    <button type="button" className="btn-secondary btn-sm" disabled={page <= 1 || isLoading} onClick={() => setPage((p) => p - 1)}>
                      Previous
                    </button>
                    <button type="button" className="btn-secondary btn-sm" disabled={page >= totalPages || isLoading} onClick={() => setPage((p) => p + 1)}>
                      Next
                    </button>
                  </div>
                </div>
              )}
            </section>

            <section className={`card min-h-[240px] ${selected ? "" : "hidden lg:flex lg:items-center lg:justify-center"}`} aria-label="Notification details">
              {selected ? (
                <div className="p-6">
                  <button
                    type="button"
                    onClick={() => setSelectedId(null)}
                    className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-text-muted hover:text-text-main lg:hidden"
                  >
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                      <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    Back to list
                  </button>
                  <p className="text-xs text-text-muted">{formatDateTime(selected.occurred_at)}</p>
                  <h2 className="mt-1 text-xl font-bold tracking-tight">{selected.title}</h2>
                  <p className="mt-4 whitespace-pre-wrap text-sm leading-relaxed text-text-main">{selected.message}</p>
                  {link && (
                    <div className="mt-6 border-t border-border-subtle pt-5">
                      <Link to={link.to} className="btn-primary">
                        {link.label}
                      </Link>
                    </div>
                  )}
                </div>
              ) : (
                <p className="p-6 text-sm text-text-muted">Select a notification to read it.</p>
              )}
            </section>
          </div>
        </>
      )}
    </PageShell>
  );
}
