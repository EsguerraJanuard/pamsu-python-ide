import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import PageShell from "../../components/layout/PageShell";
import { EmptyState, ErrorState, PageHeader, SkeletonList } from "../../components/ui/StateViews";
import ActivityCard from "../student/ActivityCard";
import { isActiveActivity, loadStudentActivities } from "../student/studentData";

function BackLink() {
  return (
    <Link
      to="/student/classes"
      className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-text-muted transition-colors hover:text-text-main"
    >
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      Back to My Classes
    </Link>
  );
}

export default function ClassDetails() {
  const { id } = useParams();
  const [enrollment, setEnrollment] = useState(null);
  const [activities, setActivities] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await loadStudentActivities();
      setEnrollment(data.classrooms.find((c) => String(c.classroom?.class_id) === String(id)) || null);
      setActivities(data.activities.filter((a) => String(a.classId) === String(id)));
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const classroom = enrollment?.classroom;

  return (
    <PageShell statusContext={classroom?.name}>
      <BackLink />

      {error ? (
        <ErrorState error={error} resource="this class" onRetry={fetchData} />
      ) : isLoading ? (
        <>
          <div className="card mb-6 h-28 animate-pulse" />
          <SkeletonList rows={3} />
        </>
      ) : !classroom ? (
        <EmptyState
          icon="search"
          title="Class not found"
          message="You are not enrolled in this class, or it no longer exists."
          action={
            <Link to="/student/classes" className="btn-secondary">
              View my classes
            </Link>
          }
        />
      ) : (
        <>
          <PageHeader
            eyebrow={[classroom.subject_code, classroom.section && `Section ${classroom.section}`].filter(Boolean).join(" · ") || "Class"}
            title={classroom.name}
            description={classroom.instructor_name ? `Instructor: ${classroom.instructor_name}` : undefined}
          />

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_260px]">
            <section aria-labelledby="class-activities-heading" className="min-w-0">
              <h2 id="class-activities-heading" className="mb-3 text-base font-semibold">
                Class activities
              </h2>
              {activities.length === 0 ? (
                <EmptyState
                  title="No activities published yet"
                  message="Your instructor hasn't published activities for this class. Check back later."
                />
              ) : (
                <div className="space-y-3">
                  {activities.map((activity) => (
                    <ActivityCard key={activity.id} activity={activity} showClass={false} />
                  ))}
                </div>
              )}
            </section>

            <aside className="card h-fit p-5" aria-label="Class information">
              <h2 className="mb-3 text-sm font-semibold">Class information</h2>
              <dl className="space-y-2.5 text-sm">
                {[
                  ["Instructor", classroom.instructor_name || "—"],
                  ["Subject code", classroom.subject_code || "—"],
                  ["Section", classroom.section || "—"],
                  ["Class code", classroom.class_code || "—"],
                  ["Open activities", activities.filter(isActiveActivity).length],
                  ["Status", classroom.is_active ? "Active" : "Archived"],
                ].map(([term, value]) => (
                  <div key={term} className="flex justify-between gap-3">
                    <dt className="text-text-muted">{term}</dt>
                    <dd className="text-right font-medium text-text-main">{value}</dd>
                  </div>
                ))}
              </dl>
            </aside>
          </div>
        </>
      )}
    </PageShell>
  );
}
