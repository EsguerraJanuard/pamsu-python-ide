import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import PageShell from "../../components/layout/PageShell";
import { EmptyState, ErrorState, InlineAlert, PageHeader } from "../../components/ui/StateViews";
import api from "../../services/api";

function percent(part, whole) {
  return whole > 0 ? Math.round((part / whole) * 100) : 0;
}

function ProgressBar({ value, label }) {
  return (
    <div
      className="h-1.5 w-full overflow-hidden rounded-full bg-bg-alt"
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
    >
      <div className="h-full rounded-full bg-psu-maroon transition-all duration-700" style={{ width: `${value}%` }} />
    </div>
  );
}

export default function Analytics() {
  const [metrics, setMetrics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalytics = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setMetrics(await api.get("/practice/analytics/growth"));
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const score = Math.max(0, Math.min(100, metrics?.overall_growth_score ?? 0));
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const hasActivity = (metrics?.total_attempts ?? 0) > 0;

  return (
    <PageShell>
      <PageHeader
        eyebrow="Progress"
        title="My Analytics"
        description="Your Solo Practice progress: tasks completed, attempts and accuracy."
      />

      {error ? (
        <ErrorState error={error} resource="your analytics" onRetry={fetchAnalytics} />
      ) : isLoading ? (
        <div className="space-y-5" role="status" aria-label="Loading analytics">
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="card h-48 animate-pulse" />
            ))}
          </div>
          <div className="card h-56 animate-pulse" />
        </div>
      ) : (
        <div className="space-y-5">
          {!hasActivity && (
            <InlineAlert tone="info">
              You haven&apos;t attempted any practice tasks yet. Your figures will update as you work through{" "}
              <Link to="/student/practice" className="font-semibold underline">
                Solo Practice
              </Link>
              .
            </InlineAlert>
          )}

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
            <article className="card flex flex-col items-center justify-center p-6 text-center">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-text-muted">Growth score</h2>
              <div className="relative my-4 h-36 w-36">
                <svg className="h-full w-full -rotate-90" viewBox="0 0 140 140" aria-hidden="true">
                  <circle cx="70" cy="70" r={radius} fill="none" stroke="var(--color-bg-alt)" strokeWidth="12" />
                  <circle
                    cx="70"
                    cy="70"
                    r={radius}
                    fill="none"
                    stroke="var(--color-psu-maroon)"
                    strokeWidth="12"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={circumference - (score / 100) * circumference}
                    className="transition-all duration-700"
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-4xl font-bold tracking-tight">
                  {score}
                </span>
              </div>
              <p className="max-w-[220px] text-xs text-text-muted">
                Calculated by the server from practice task completion and solution accuracy.
              </p>
            </article>

            <article className="card flex flex-col justify-center p-6">
              <h2 className="text-sm font-medium text-text-muted">Tasks completed</h2>
              <p className="mt-1 text-3xl font-bold tracking-tight">
                {metrics?.completed_tasks ?? 0}
                <span className="text-lg font-medium text-text-muted"> / {metrics?.total_tasks ?? 0}</span>
              </p>
              <div className="mt-4">
                <ProgressBar value={percent(metrics?.completed_tasks ?? 0, metrics?.total_tasks ?? 0)} label="Tasks completed" />
              </div>
            </article>

            <article className="card flex flex-col justify-center p-6">
              <h2 className="text-sm font-medium text-text-muted">Solution accuracy</h2>
              <p className="mt-1 text-3xl font-bold tracking-tight">
                {hasActivity ? `${percent(metrics.successful_attempts, metrics.total_attempts)}%` : "—"}
              </p>
              <p className="mt-3 text-xs text-text-muted">
                {metrics?.successful_attempts ?? 0} of {metrics?.total_attempts ?? 0} attempts passed.
              </p>
            </article>
          </div>

          <section className="card overflow-hidden" aria-labelledby="module-progress-heading">
            <div className="border-b border-border-subtle px-5 py-4">
              <h2 id="module-progress-heading" className="text-sm font-semibold">
                Module progress
              </h2>
            </div>
            <div className="p-5">
              {metrics?.module_breakdown?.length ? (
                <ul className="space-y-4">
                  {metrics.module_breakdown.map((mod) => (
                    <li key={mod.module_title}>
                      <div className="mb-1.5 flex items-baseline justify-between gap-3">
                        <span className="text-sm font-medium text-text-main">{mod.module_title}</span>
                        <span className="shrink-0 text-xs text-text-muted">
                          {mod.completed_tasks}/{mod.total_tasks} tasks · {mod.attempts_count}{" "}
                          {mod.attempts_count === 1 ? "attempt" : "attempts"}
                        </span>
                      </div>
                      <ProgressBar value={percent(mod.completed_tasks, mod.total_tasks)} label={`${mod.module_title} progress`} />
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState
                  className="border-0 py-8"
                  title="No practice modules yet"
                  message="Practice modules will appear here once your instructors publish them."
                />
              )}
            </div>
          </section>
        </div>
      )}
    </PageShell>
  );
}
