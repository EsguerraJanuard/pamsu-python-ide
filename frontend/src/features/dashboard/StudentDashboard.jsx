import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import PageShell from "../../components/layout/PageShell";
import JoinClassModal from "../../components/modals/JoinClassModal";
import { EmptyState, ErrorState, InlineAlert, PageHeader, SkeletonList } from "../../components/ui/StateViews";
import { useAuth } from "../auth/AuthContext";
import ActivityCard from "../student/ActivityCard";
import { classLabel, isActiveActivity, loadStudentActivities } from "../student/studentData";

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function getFirstName(name) {
  if (!name) return "";
  const firstPart = name.includes(",") ? name.split(",")[1]?.trim() : name.trim();
  return firstPart?.split(/\s+/)[0] || "";
}

function StatCard({ value, label, description, progress }) {
  return (
    <article className="card p-5">
      <p className="text-3xl font-bold tracking-tight text-text-main">{value}</p>
      <h2 className="mt-1 text-sm font-semibold text-text-main">{label}</h2>
      <p className="text-xs text-text-muted">{description}</p>
      {progress !== undefined && (
        <div
          className="mt-4 h-1.5 overflow-hidden rounded-full bg-bg-alt"
          role="progressbar"
          aria-valuenow={Math.round(progress)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={label}
        >
          <div className="h-full rounded-full bg-psu-maroon transition-all duration-700" style={{ width: `${progress}%` }} />
        </div>
      )}
    </article>
  );
}

export default function StudentDashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isJoinModalOpen, setIsJoinModalOpen] = useState(false);
  const [joinedMessage, setJoinedMessage] = useState("");

  const fetchDashboardData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setData(await loadStudentActivities());
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const activities = data?.activities || [];
  const activeClassrooms = (data?.classrooms || []).filter((c) => c.enrollment_status === "active");
  const openActivities = activities.filter(isActiveActivity);
  const dueSoonCount = activities.filter((a) => a.status === "due_soon").length;
  const submittedCount = activities.filter((a) => a.isSubmitted).length;
  const completion = activities.length > 0 ? (submittedCount / activities.length) * 100 : 0;
  const firstName = getFirstName(user?.name);

  return (
    <PageShell assignmentCount={openActivities.length}>
      <PageHeader
        eyebrow="Dashboard"
        title={`${getGreeting()}${firstName ? `, ${firstName}` : ""}`}
        description={
          data
            ? `You have ${openActivities.length} open ${openActivities.length === 1 ? "activity" : "activities"}${
                dueSoonCount ? `, ${dueSoonCount} due within 24 hours` : ""
              }.`
            : "Your activities and classes at a glance."
        }
        actions={
          <button type="button" onClick={() => setIsJoinModalOpen(true)} className="btn-primary">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
            Join a class
          </button>
        }
      />

      {joinedMessage && (
        <InlineAlert tone="success" onDismiss={() => setJoinedMessage("")} className="mb-5">
          {joinedMessage}
        </InlineAlert>
      )}

      {error ? (
        <ErrorState error={error} resource="your dashboard" onRetry={fetchDashboardData} />
      ) : (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_280px]">
          <div className="min-w-0 space-y-6">
            <section className="grid grid-cols-1 gap-4 sm:grid-cols-3" aria-label="Progress summary">
              {isLoading ? (
                [0, 1, 2].map((i) => <div key={i} className="card h-[120px] animate-pulse" />)
              ) : (
                <>
                  <StatCard value={openActivities.length} label="Open activities" description="Not yet submitted" />
                  <StatCard
                    value={`${submittedCount}/${activities.length}`}
                    label="Submitted"
                    description="Activities with at least one attempt"
                    progress={completion}
                  />
                  <StatCard value={activeClassrooms.length} label="Classes" description="Active enrollments" />
                </>
              )}
            </section>

            <InlineAlert tone="info">
              AST checks, test results and activity indicators support your learning. They are not automatic
              grades — official grades are assigned and released by your instructor.
            </InlineAlert>

            <section aria-labelledby="recent-activities-heading">
              <div className="mb-3 flex items-end justify-between gap-3">
                <div>
                  <h2 id="recent-activities-heading" className="text-base font-semibold">
                    Upcoming &amp; recent activities
                  </h2>
                  <p className="text-xs text-text-muted">Open work first, then your latest submissions.</p>
                </div>
                {activities.length > 0 && (
                  <Link to="/student/assignments" className="text-xs font-semibold text-text-brand hover:underline">
                    View all
                  </Link>
                )}
              </div>

              {isLoading ? (
                <SkeletonList rows={3} />
              ) : (data?.classrooms || []).length === 0 ? (
                <EmptyState
                  icon="inbox"
                  title="You're not enrolled in any class yet"
                  message="Ask your instructor for a class code, then join to see your activities here."
                  action={
                    <button type="button" className="btn-primary" onClick={() => setIsJoinModalOpen(true)}>
                      Enter class code
                    </button>
                  }
                />
              ) : activities.length === 0 ? (
                <EmptyState
                  title="No activities yet"
                  message="Your instructors haven't published any activities for your classes. New work will appear here."
                />
              ) : (
                <div className="space-y-3">
                  {activities.slice(0, 5).map((activity) => (
                    <ActivityCard key={activity.id} activity={activity} />
                  ))}
                </div>
              )}
            </section>
          </div>

          <aside className="space-y-4" aria-label="My classes">
            <section className="card p-5">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold">My classes</h2>
                <Link to="/student/classes" className="text-xs font-semibold text-text-brand hover:underline">
                  Manage
                </Link>
              </div>
              {isLoading ? (
                <div className="space-y-2">
                  {[0, 1].map((i) => (
                    <div key={i} className="h-10 animate-pulse rounded-lg bg-bg-alt" />
                  ))}
                </div>
              ) : activeClassrooms.length === 0 ? (
                <p className="text-xs text-text-muted">No active enrollments.</p>
              ) : (
                <ul className="space-y-1">
                  {activeClassrooms.map((enrollment) => (
                    <li key={enrollment.enrollment_id}>
                      <Link
                        to={`/student/classes/${enrollment.classroom.class_id}`}
                        className="block rounded-lg px-2.5 py-2 transition-colors hover:bg-bg-alt"
                      >
                        <p className="truncate text-sm font-medium text-text-main">{enrollment.classroom.name}</p>
                        <p className="truncate text-xs text-text-muted">
                          {classLabel(enrollment.classroom)}
                          {enrollment.classroom.instructor_name ? ` · ${enrollment.classroom.instructor_name}` : ""}
                        </p>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="card p-5">
              <h2 className="text-sm font-semibold">Practice &amp; growth</h2>
              <p className="mt-1 text-xs text-text-muted">
                Build skills with self-paced practice modules and track your growth over time.
              </p>
              <div className="mt-4 flex flex-col gap-2">
                <Link to="/student/practice" className="btn-secondary btn-sm">
                  Open solo practice
                </Link>
                <Link to="/student/analytics" className="btn-ghost btn-sm">
                  View my analytics
                </Link>
              </div>
            </section>
          </aside>
        </div>
      )}

      <JoinClassModal
        isOpen={isJoinModalOpen}
        onClose={() => setIsJoinModalOpen(false)}
        onSuccess={() => {
          setJoinedMessage("You joined the class. Its activities now appear on your dashboard.");
          fetchDashboardData();
        }}
      />
    </PageShell>
  );
}
