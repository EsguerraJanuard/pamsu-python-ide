import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import PageShell from "../../../components/layout/PageShell";
import { EmptyState, ErrorState, PageHeader, SkeletonList } from "../../../components/ui/StateViews";
import api from "../../../services/api";
import { classLabel, formatDateTime } from "../../../utils/format";
import ProgressMeter from "./ProgressMeter";

export default function GradingClassView() {
  const { classId } = useParams();
  const [classroom, setClassroom] = useState(null);
  const [activities, setActivities] = useState([]);
  // Enrolled students (null if the roster could not be loaded) and per-activity
  // queue counts keyed by task_id, loaded after the list shows.
  const [enrolledCount, setEnrolledCount] = useState(null);
  const [taskCounts, setTaskCounts] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [classRes, tasksRes, members] = await Promise.all([
        api.get(`/classrooms/${classId}`),
        api.get(`/instructors/tasks/?class_id=${classId}`),
        api.get(`/classrooms/${classId}/members`).catch(() => null),
      ]);
      setClassroom(classRes);
      setActivities((Array.isArray(tasksRes) ? tasksRes : []).filter((t) => String(t.class_id) === String(classId)));
      setEnrolledCount(Array.isArray(members) ? members.filter((m) => m.status !== "removed").length : null);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [classId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    const published = activities.filter((task) => task.is_published);
    if (published.length === 0) return undefined;
    let cancelled = false;
    Promise.all(
      published.map((task) =>
        api
          .get(`/instructors/review-queue?task_id=${task.task_id}&page_size=1`)
          .then((res) => [task.task_id, res?.counts || null])
          .catch(() => [task.task_id, null]),
      ),
    ).then((entries) => {
      if (!cancelled) setTaskCounts(Object.fromEntries(entries));
    });
    return () => {
      cancelled = true;
    };
  }, [activities]);

  return (
    <PageShell role="instructor" statusContext={classroom?.name}>
      <Link
        to="/instructor/bench"
        className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-text-muted transition-colors hover:text-text-main"
      >
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        All classes
      </Link>

      {error ? (
        <ErrorState error={error} resource="this class" onRetry={fetchData} />
      ) : isLoading ? (
        <SkeletonList rows={3} />
      ) : (
        <>
          <PageHeader eyebrow={classLabel(classroom)} title={classroom.name} description="Choose an activity to review its submissions." />
          {activities.length === 0 ? (
            <EmptyState
              title="No activities in this class"
              message="Create and publish an activity to start receiving submissions."
              action={
                <Link to={`/instructor/activities/create?class=${classId}`} className="btn-primary">
                  New activity
                </Link>
              }
            />
          ) : (
            <ul className="space-y-3">
              {activities.map((task) => {
                const counts = taskCounts[task.task_id];
                const loaded = task.task_id in taskCounts;
                const waiting = counts ? (counts.submitted || 0) + (counts.awaiting_review || 0) : 0;
                return (
                  <li key={task.task_id} className="card flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5">
                    <div className="min-w-0 flex-1">
                      <div className="mb-1 flex flex-wrap items-center gap-2">
                        <h2 className="text-sm font-semibold text-text-main">{task.title}</h2>
                        <span className={`badge ${task.is_published ? "badge-success" : "badge-neutral"}`}>
                          {task.is_published ? "Published" : "Draft"}
                        </span>
                        {waiting > 0 && (
                          <span className="badge badge-gold">
                            <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
                            {waiting} to review
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-text-muted">{task.due_at ? `Due ${formatDateTime(task.due_at)}` : "No due date"}</p>
                      {task.is_published && (
                        <div className="mt-3 sm:max-w-sm">
                          {!loaded ? (
                            <div className="h-1.5 animate-pulse rounded-full bg-bg-alt" aria-hidden="true" />
                          ) : counts && enrolledCount !== null ? (
                            // One official attempt per student who submitted.
                            <ProgressMeter label="Students submitted" value={Math.min(counts.official || 0, enrolledCount)} max={enrolledCount} />
                          ) : null}
                        </div>
                      )}
                    </div>
                    {task.is_published ? (
                      <Link to={`/instructor/bench/${classId}/${task.task_id}`} className="btn-primary btn-sm shrink-0">
                        Review submissions
                      </Link>
                    ) : (
                      <Link to={`/instructor/activities/${task.task_id}`} className="btn-secondary btn-sm shrink-0">
                        Publish to receive submissions
                      </Link>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </>
      )}
    </PageShell>
  );
}
