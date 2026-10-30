import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import PageShell from "../../components/layout/PageShell";
import CreateClassModal from "../../components/modals/CreateClassModal";
import { EmptyState, ErrorState, PageHeader, SkeletonList } from "../../components/ui/StateViews";
import api from "../../services/api";
import { cachedGet } from "../../services/queryClient";
import { classLabel, formatDateTime } from "../../utils/format";
import { useAuth } from "../auth/AuthContext";

function activityState(task) {
  if (!task.is_published) {
    return task.scheduled_publish_at
      ? { label: `Scheduled · ${formatDateTime(task.scheduled_publish_at)}`, badge: "badge-gold" }
      : { label: "Draft", badge: "badge-neutral" };
  }
  if (task.due_at && new Date(task.due_at) < new Date()) return { label: "Closed", badge: "badge-neutral" };
  return { label: "Published", badge: "badge-success" };
}

function StatLink({ to, value, label, description }) {
  return (
    <Link to={to} className="card block p-5 transition hover:border-psu-maroon/30 hover:shadow-md">
      <p className="text-3xl font-bold tracking-tight text-text-main">{value}</p>
      <p className="mt-1 text-sm font-semibold text-text-main">{label}</p>
      <p className="text-xs text-text-muted">{description}</p>
    </Link>
  );
}

export default function InstructorDashboard() {
  const { user } = useAuth();
  const [classes, setClasses] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [queue, setQueue] = useState({ items: [], counts: null });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const fetchDashboardData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [classRes, tasksRes, reviewRes] = await Promise.all([
        cachedGet("/classrooms/"),
        cachedGet("/instructors/tasks/"),
        // The review queue changes as students submit: always fetched fresh.
        api.get("/instructors/review-queue?page_size=5"),
      ]);
      setClasses(Array.isArray(classRes) ? classRes : []);
      setTasks(Array.isArray(tasksRes) ? tasksRes : []);
      setQueue({ items: reviewRes?.items || [], counts: reviewRes?.counts || null });
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const classMap = useMemo(() => Object.fromEntries(classes.map((c) => [c.class_id, c])), [classes]);
  const activeClasses = classes.filter((c) => c.is_active).length;
  const publishedCount = tasks.filter((t) => t.is_published).length;
  const pendingReviews = queue.counts ? (queue.counts.submitted || 0) + (queue.counts.awaiting_review || 0) : 0;
  const recentTasks = [...tasks].sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at)).slice(0, 6);

  return (
    <PageShell role="instructor">
      <PageHeader
        eyebrow="Faculty overview"
        title={user?.name ? `Welcome, ${user.name}` : "Welcome"}
        description="Your classes, activities and submissions awaiting review."
        actions={
          <>
            <Link to="/instructor/activities/create" className="btn-secondary">
              New activity
            </Link>
            <button type="button" onClick={() => setIsCreateModalOpen(true)} className="btn-primary">
              Create class
            </button>
          </>
        }
      />

      {error ? (
        <ErrorState error={error} resource="your dashboard" onRetry={fetchDashboardData} />
      ) : (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_300px]">
          <div className="min-w-0 space-y-6">
            <section className="grid grid-cols-1 gap-4 sm:grid-cols-3" aria-label="Summary">
              {isLoading ? (
                [0, 1, 2].map((i) => <div key={i} className="card h-[108px] animate-pulse" />)
              ) : (
                <>
                  <StatLink to="/instructor/classes" value={activeClasses} label="Active classes" description={`${classes.length} total`} />
                  <StatLink to="/instructor/bench" value={pendingReviews} label="Awaiting review" description="Submitted, not yet graded" />
                  <StatLink
                    to="/instructor/bench"
                    value={publishedCount}
                    label="Published activities"
                    description={`${tasks.length - publishedCount} draft or scheduled`}
                  />
                </>
              )}
            </section>

            <section aria-labelledby="activities-heading">
              <div className="mb-3 flex items-end justify-between">
                <div>
                  <h2 id="activities-heading" className="text-base font-semibold">
                    Recent activities
                  </h2>
                  <p className="text-xs text-text-muted">Most recently created or updated.</p>
                </div>
              </div>
              {isLoading ? (
                <SkeletonList rows={3} />
              ) : classes.length === 0 ? (
                <EmptyState
                  title="Create your first class"
                  message="Classes generate an enrollment code for students. Activities are assigned to classes."
                  action={
                    <button type="button" className="btn-primary" onClick={() => setIsCreateModalOpen(true)}>
                      Create class
                    </button>
                  }
                />
              ) : tasks.length === 0 ? (
                <EmptyState
                  title="No activities yet"
                  message="Author a laboratory or homework activity and assign it to your classes."
                  action={
                    <Link to="/instructor/activities/create" className="btn-primary">
                      New activity
                    </Link>
                  }
                />
              ) : (
                <ul className="space-y-3">
                  {recentTasks.map((task) => {
                    const state = activityState(task);
                    return (
                      <li key={task.task_id} className="card p-4">
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                          <div className="min-w-0">
                            <div className="mb-1 flex flex-wrap items-center gap-2">
                              <h3 className="text-sm font-semibold text-text-main">{task.title}</h3>
                              <span className={`badge ${state.badge}`}>{state.label}</span>
                            </div>
                            <p className="text-xs text-text-muted">
                              {[classLabel(classMap[task.class_id]), task.due_at ? `Due ${formatDateTime(task.due_at)}` : "No due date"].join(" · ")}
                            </p>
                          </div>
                          <div className="flex shrink-0 gap-2">
                            <Link to={`/instructor/activities/${task.task_id}`} className="btn-secondary btn-sm">
                              Manage
                            </Link>
                            {task.is_published && (
                              <Link to={`/instructor/bench/${task.class_id}/${task.task_id}`} className="btn-ghost btn-sm">
                                Grade
                              </Link>
                            )}
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>
          </div>

          <aside className="space-y-4">
            <section className="card p-5" aria-labelledby="recent-submissions-heading">
              <div className="mb-3 flex items-center justify-between">
                <h2 id="recent-submissions-heading" className="text-sm font-semibold">
                  Latest submissions
                </h2>
                <Link to="/instructor/bench" className="text-xs font-semibold text-text-brand hover:underline">
                  Grading bench
                </Link>
              </div>
              {isLoading ? (
                <div className="space-y-2">
                  {[0, 1, 2].map((i) => (
                    <div key={i} className="h-10 animate-pulse rounded-lg bg-bg-alt" />
                  ))}
                </div>
              ) : queue.items.length === 0 ? (
                <p className="text-xs text-text-muted">No submissions yet.</p>
              ) : (
                <ul className="space-y-1">
                  {queue.items.map((item) => (
                    <li key={item.sub_id}>
                      <Link
                        to={item.activity?.class_id ? `/instructor/bench/${item.activity.class_id}/${item.activity.task_id}` : "/instructor/bench"}
                        className="block rounded-lg px-2.5 py-2 transition-colors hover:bg-bg-alt"
                      >
                        <p className="truncate text-sm font-medium text-text-main">{item.student?.name || "Student"}</p>
                        <p className="truncate text-xs text-text-muted">
                          {item.activity?.title} · {formatDateTime(item.submitted_at)}
                        </p>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="card p-5">
              <h2 className="text-sm font-semibold">Live monitoring</h2>
              <p className="mt-1 text-xs text-text-muted">See which students currently have an open coding session.</p>
              <Link to="/instructor/monitoring" className="btn-secondary btn-sm mt-4 w-full">
                Open live view
              </Link>
            </section>
          </aside>
        </div>
      )}

      <CreateClassModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={fetchDashboardData}
      />
    </PageShell>
  );
}
