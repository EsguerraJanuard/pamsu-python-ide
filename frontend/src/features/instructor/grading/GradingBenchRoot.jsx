import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import PageShell from "../../../components/layout/PageShell";
import { EmptyState, ErrorState, PageHeader } from "../../../components/ui/StateViews";
import api from "../../../services/api";

export default function GradingBenchRoot() {
  const [classes, setClasses] = useState([]);
  const [counts, setCounts] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchClasses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [classRes, queueRes] = await Promise.all([
        api.get("/classrooms/"),
        api.get("/instructors/review-queue?page_size=1"),
      ]);
      setClasses(Array.isArray(classRes) ? classRes : []);
      setCounts(queueRes?.counts || null);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchClasses();
  }, [fetchClasses]);

  const pending = counts ? (counts.submitted || 0) + (counts.awaiting_review || 0) : null;

  return (
    <PageShell role="instructor">
      <PageHeader
        eyebrow="Monitoring & grading"
        title="Grading Bench"
        description={
          pending === null ? "Choose a class to review submissions." : `${pending} submission${pending === 1 ? "" : "s"} awaiting review across your classes.`
        }
      />

      {error ? (
        <ErrorState error={error} resource="your classes" onRetry={fetchClasses} />
      ) : isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3" role="status" aria-label="Loading classes">
          {[0, 1, 2].map((i) => (
            <div key={i} className="card h-32 animate-pulse" />
          ))}
        </div>
      ) : classes.length === 0 ? (
        <EmptyState
          title="No classes yet"
          message="Create a class and publish an activity to start receiving submissions."
          action={
            <Link to="/instructor/classes" className="btn-primary">
              Go to classes
            </Link>
          }
        />
      ) : (
        <ul className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {classes.map((cls) => (
            <li key={cls.class_id}>
              <Link
                to={`/instructor/bench/${cls.class_id}`}
                className="card block h-full p-5 transition hover:border-psu-maroon/30 hover:shadow-md"
              >
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  {cls.subject_code && <span className="badge badge-brand">{cls.subject_code}</span>}
                  {cls.section && <span className="badge badge-neutral">Section {cls.section}</span>}
                  {!cls.is_active && <span className="badge badge-neutral">Archived</span>}
                </div>
                <h2 className="text-base font-semibold text-text-main">{cls.name}</h2>
                <p className="mt-3 text-xs font-semibold text-text-brand">Review activities →</p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </PageShell>
  );
}
