import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import PageShell from "../../components/layout/PageShell";
import CustomSelect from "../../components/ui/CustomSelect";
import { EmptyState, ErrorState, InlineAlert, PageHeader, SkeletonList } from "../../components/ui/StateViews";
import useApiQuery from "../../hooks/useApiQuery";
import useUrlFilters from "../../hooks/useUrlFilters";
import api from "../../services/api";
import { classLabel } from "../../utils/format";

const POLL_MS = 10000;
// Same window as LIVE_SESSION_WINDOW in backend/app/services/coding_session_service.py:
// an open workspace sends a heartbeat every 30 seconds.
const LIVE_WINDOW_MS = 3 * 60 * 1000;

// ?activity=12&class=BSIT%201A — kept in the URL so a reload keeps the view.
const FILTER_DEFAULTS = { activity: "all", class: "all" };

function isQuiet(session, now) {
  const quietFor = now - new Date(session.last_activity_at).getTime();
  return Number.isFinite(quietFor) && quietFor > LIVE_WINDOW_MS;
}

/**
 * Only live sessions are shown: never one that has ended, and never one whose
 * workspace sent nothing for three minutes (a tab closed without "end").
 * The server applies the same rule (live_only); this also covers a server
 * that predates it, and sessions that go quiet between two refreshes.
 */
function liveSessionsOnly(sessions, now) {
  const open = sessions.filter((session) => !session.ended_at);
  return Number.isFinite(now) ? open.filter((session) => !isQuiet(session, now)) : open;
}

function timeAgo(value) {
  if (!value) return "—";
  const seconds = Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  return new Date(value).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export default function LiveMonitoring() {
  const [filters, setFilters] = useUrlFilters(FILTER_DEFAULTS);
  const scope = filters.activity;
  const classFilter = filters.class;
  const setScope = (value) => setFilters({ activity: value });
  const setClassFilter = (value) => setFilters({ class: value });
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshError, setRefreshError] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  // student_id → name. The per-activity session list carries no names, so
  // they come from the class roster (as on the grading bench).
  const [rosterNames, setRosterNames] = useState({});
  const hasLoaded = useRef(false);

  // Filter lists come from the shared cache; they are optional, and the
  // session list reports its own errors.
  const classroomsQuery = useApiQuery("/classrooms/");
  const tasksQuery = useApiQuery("/instructors/tasks/");
  const classrooms = useMemo(() => (Array.isArray(classroomsQuery.data) ? classroomsQuery.data : []), [classroomsQuery.data]);
  const tasks = useMemo(() => (Array.isArray(tasksQuery.data) ? tasksQuery.data.filter((t) => t.is_published) : []), [tasksQuery.data]);

  const fetchSessions = useCallback(async () => {
    try {
      // live_only: not ended, heartbeat within three minutes. active_only is
      // the older server's closest filter (drops ended sessions).
      const url =
        scope === "all"
          ? "/instructors/coding-sessions/live"
          : `/instructors/tasks/${encodeURIComponent(scope)}/coding-sessions?live_only=true&active_only=true`;
      const response = await api.get(url);
      setSessions(Array.isArray(response) ? response : []);
      setLastUpdated(new Date());
      setError(null);
      setRefreshError(false);
      hasLoaded.current = true;
    } catch (err) {
      // Keep the last good list visible if a background refresh fails.
      if (hasLoaded.current) setRefreshError(true);
      else setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [scope]);

  useEffect(() => {
    hasLoaded.current = false;
    setIsLoading(true);
    setError(null);
    setSessions([]);
    fetchSessions();
    const interval = window.setInterval(() => {
      if (!document.hidden) fetchSessions();
    }, POLL_MS);
    return () => window.clearInterval(interval);
  }, [fetchSessions]);

  const selectedTask = scope === "all" ? null : tasks.find((t) => String(t.task_id) === scope);
  const selectedClassId = selectedTask?.class_id ?? null;

  useEffect(() => {
    if (!selectedClassId) return undefined;
    let cancelled = false;
    api
      .get(`/classrooms/${selectedClassId}/members`)
      .then((members) => {
        if (cancelled || !Array.isArray(members)) return;
        // Includes removed students, who may still have past sessions. Ids are
        // account ids, so names from earlier classes stay valid.
        setRosterNames((prev) => ({ ...prev, ...Object.fromEntries(members.map((m) => [m.student_id, m.name])) }));
      })
      .catch(() => {
        // Names are a convenience; cards fall back to the student number.
      });
    return () => {
      cancelled = true;
    };
  }, [selectedClassId]);

  const classMap = useMemo(() => Object.fromEntries(classrooms.map((c) => [c.class_id, c])), [classrooms]);
  const taskOptions = [
    { value: "all", label: "All active sessions" },
    ...tasks.map((t) => ({ value: String(t.task_id), label: `${t.title} — ${classLabel(classMap[t.class_id])}` })),
  ];
  const classOptions = [{ value: "all", label: "All classes" }, ...classrooms.map((c) => ({ value: c.name, label: c.name }))];

  const liveSessions = liveSessionsOnly(sessions, lastUpdated ? lastUpdated.getTime() : NaN);
  const visibleSessions =
    scope === "all" && classFilter !== "all" ? liveSessions.filter((s) => s.classroom_name === classFilter) : liveSessions;

  return (
    <PageShell role="instructor">
      <PageHeader
        eyebrow="Monitoring & grading"
        title="Live Monitoring"
        description="Students working right now. Ended sessions, and sessions with no activity for 3 minutes, drop off. Refreshes every 10 seconds while this tab is visible."
        actions={
          <button type="button" onClick={fetchSessions} className="btn-secondary btn-sm">
            Refresh now
          </button>
        }
      />

      <div className="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:max-w-3xl">
        <div>
          <label htmlFor="monitor-scope" className="field-label">
            Activity
          </label>
          <CustomSelect id="monitor-scope" value={scope} onChange={setScope} options={taskOptions} />
        </div>
        {scope === "all" && (
          <div>
            <label htmlFor="monitor-class" className="field-label">
              Class
            </label>
            <CustomSelect id="monitor-class" value={classFilter} onChange={setClassFilter} options={classOptions} />
          </div>
        )}
      </div>

      {refreshError && (
        <InlineAlert tone="warning" className="mb-4">
          The latest refresh failed. Showing data from {lastUpdated ? lastUpdated.toLocaleTimeString() : "the previous update"}.
        </InlineAlert>
      )}

      <InlineAlert tone="info" className="mb-5">
        Counts are review indicators only — they are not evidence of misconduct.
      </InlineAlert>

      {error ? (
        <ErrorState error={error} resource="live sessions" onRetry={fetchSessions} />
      ) : isLoading ? (
        <SkeletonList rows={3} className="h-24" />
      ) : visibleSessions.length === 0 ? (
        <EmptyState
          title="No active sessions"
          message={scope === "all" ? "No students currently have an open coding session in your classes." : "No students are currently working on this activity."}
        />
      ) : (
        <ul className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {visibleSessions.map((session) => {
            return (
              <li key={session.session_id} className="card p-5">
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h2 className="truncate text-sm font-semibold text-text-main">
                      {session.student_name || rosterNames[session.student_id] || `Student #${session.student_id}`}
                    </h2>
                    <p className="truncate text-xs text-text-muted">
                      {[
                        session.task_title || selectedTask?.title,
                        session.classroom_name || classMap[selectedTask?.class_id]?.name,
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </p>
                  </div>
                  <span className="badge badge-success">
                    <span className="mr-1 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-current" aria-hidden="true" />
                    Live
                  </span>
                </div>
                <dl className="grid grid-cols-3 gap-2 text-center">
                  {[
                    ["Tab switches", session.tab_switch_count],
                    ["Blocked pastes", session.blocked_paste_count],
                    ["Runs", session.run_attempt_count],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-lg bg-bg-alt px-2 py-2">
                      <dd className="text-base font-semibold text-text-main">{value ?? 0}</dd>
                      <dt className="text-xs text-text-muted">{label}</dt>
                    </div>
                  ))}
                </dl>
                <p className="mt-3 text-xs text-text-muted">Last activity {timeAgo(session.last_activity_at)}</p>
              </li>
            );
          })}
        </ul>
      )}
    </PageShell>
  );
}
