import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import PageShell from "../../../components/layout/PageShell";
import { EmptyState, ErrorState, PageHeader, SkeletonList } from "../../../components/ui/StateViews";
import api from "../../../services/api";
import { classLabel, formatDateTime } from "../../../utils/format";

export default function GradingClassView() {
  const { classId } = useParams();
  const [classroom, setClassroom] = useState(null);
  const [activities, setActivities] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [classRes, tasksRes] = await Promise.all([
        api.get(`/classrooms/${classId}`),
        api.get(`/instructors/tasks/?class_id=${classId}`),
      ]);
      setClassroom(classRes);
      setActivities((Array.isArray(tasksRes) ? tasksRes : []).filter((t) => String(t.class_id) === String(classId)));
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [classId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

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
              {activities.map((task) => (
                <li key={task.task_id} className="card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <div className="mb-1 flex flex-wrap items-center gap-2">
                      <h2 className="text-sm font-semibold text-text-main">{task.title}</h2>
                      <span className={`badge ${task.is_published ? "badge-success" : "badge-neutral"}`}>
                        {task.is_published ? "Published" : "Draft"}
                      </span>
                    </div>
                    <p className="text-xs text-text-muted">{task.due_at ? `Due ${formatDateTime(task.due_at)}` : "No due date"}</p>
                  </div>
                  {task.is_published ? (
                    <Link to={`/instructor/bench/${classId}/${task.task_id}`} className="btn-primary btn-sm">
                      Review submissions
                    </Link>
                  ) : (
                    <Link to={`/instructor/activities/${task.task_id}`} className="btn-secondary btn-sm">
                      Publish to receive submissions
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </PageShell>
  );
}
