import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import PageShell from "../../../components/layout/PageShell";
import Icon from "../../../components/ui/Icon";
import { EmptyState, ErrorState, PageHeader } from "../../../components/ui/StateViews";
import api from "../../../services/api";
import { cachedGet } from "../../../services/queryClient";
import ProgressMeter from "./ProgressMeter";

const toReview = (counts) => (counts ? (counts.submitted || 0) + (counts.awaiting_review || 0) : 0);
const reviewed = (counts) => (counts ? (counts.graded || 0) + (counts.rejected || 0) : 0);

export default function GradingBenchRoot() {
  const [classes, setClasses] = useState([]);
  const [counts, setCounts] = useState(null);
  // Per-class queue counts, keyed by class_id. Loaded after the cards show;
  // a class whose request fails simply shows no counts.
  const [classCounts, setClassCounts] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchClasses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [classRes, queueRes] = await Promise.all([
        cachedGet("/classrooms/"),
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

  useEffect(() => {
    if (classes.length === 0) return undefined;
    let cancelled = false;
    Promise.all(
      classes.map((cls) =>
        api
          .get(`/instructors/review-queue?class_id=${cls.class_id}&page_size=1`)
          .then((res) => [cls.class_id, res?.counts || null])
          .catch(() => [cls.class_id, null]),
      ),
    ).then((entries) => {
      if (!cancelled) setClassCounts(Object.fromEntries(entries));
    });
    return () => {
      cancelled = true;
    };
  }, [classes]);

  const pending = counts ? toReview(counts) : null;

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
            <div key={i} className="card h-44 animate-pulse" />
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
          {classes.map((cls) => {
            const classCount = classCounts[cls.class_id];
            const loaded = cls.class_id in classCounts;
            const waiting = toReview(classCount);
            return (
              <li key={cls.class_id}>
                <Link
                  to={`/instructor/bench/${cls.class_id}`}
                  className="card group flex h-full flex-col p-5 transition-[border-color,box-shadow] hover:border-psu-maroon/30 hover:shadow-md"
                >
                  {/* Meta badges wrap among themselves on the left; the review count stays top-right. */}
                  <div className="mb-2 flex items-start justify-between gap-3">
                    <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1.5">
                      {cls.subject_code && <span className="badge badge-brand whitespace-nowrap">{cls.subject_code}</span>}
                      {cls.section && <span className="badge badge-neutral whitespace-nowrap">Section {cls.section}</span>}
                      {!cls.is_active && <span className="badge badge-neutral whitespace-nowrap">Archived</span>}
                    </div>
                    {waiting > 0 && (
                      <span className="badge badge-gold shrink-0 whitespace-nowrap">
                        <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
                        {waiting} to review
                      </span>
                    )}
                  </div>
                  <h2 className="text-base font-semibold text-text-main">{cls.name}</h2>

                  <div className="mt-4 min-h-[2.375rem]">
                    {!loaded ? (
                      <div className="space-y-2" aria-hidden="true">
                        <div className="h-3 w-2/3 animate-pulse rounded bg-bg-alt" />
                        <div className="h-1.5 animate-pulse rounded-full bg-bg-alt" />
                      </div>
                    ) : classCount && classCount.total > 0 ? (
                      <ProgressMeter label="Submissions reviewed" value={reviewed(classCount)} max={classCount.total} />
                    ) : classCount ? (
                      <p className="text-xs text-text-muted">No submissions yet.</p>
                    ) : null}
                  </div>

                  <p className="mt-auto inline-flex items-center gap-1 pt-4 text-xs font-semibold text-text-brand">
                    Review activities
                    <Icon name="arrowRight" className="h-3.5 w-3.5 transition-transform duration-150 group-hover:translate-x-0.5" />
                  </p>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </PageShell>
  );
}
