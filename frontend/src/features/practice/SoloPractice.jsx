import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import PageShell from "../../components/layout/PageShell";
import { EmptyState, ErrorState, PageHeader, SkeletonList } from "../../components/ui/StateViews";
import api from "../../services/api";

function StatusIcon({ state, className = "h-4 w-4" }) {
  const paths = {
    done: <polyline points="20 6 9 17 4 12" />,
    locked: (
      <>
        <rect x="3" y="11" width="18" height="11" rx="2" />
        <path d="M7 11V7a5 5 0 0 1 10 0v4" />
      </>
    ),
    open: <path d="M16 18l6-6-6-6M8 6l-6 6 6 6" />,
  };
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {paths[state]}
    </svg>
  );
}

export default function SoloPractice() {
  const navigate = useNavigate();
  const [modules, setModules] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchModules = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get("/practice/modules");
      setModules(Array.isArray(response) ? response : []);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModules();
  }, [fetchModules]);

  return (
    <PageShell maxWidth="max-w-5xl">
      <PageHeader
        eyebrow="Practice"
        title="Solo Practice"
        description="Learn Python step by step. Complete each module to unlock the next one."
      />

      {error ? (
        <ErrorState error={error} resource="practice modules" onRetry={fetchModules} />
      ) : isLoading ? (
        <SkeletonList rows={3} className="h-40" />
      ) : modules.length === 0 ? (
        <EmptyState
          title="No practice modules available"
          message="Your instructors haven't published any practice modules yet. Check back later."
        />
      ) : (
        <ol className="space-y-6 pb-10">
          {modules.map((mod, index) => {
            const state = mod.is_completed ? "done" : mod.is_locked ? "locked" : "open";
            return (
              <li key={mod.module_id} className="relative flex gap-4">
                <div
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 ${
                    state === "done"
                      ? "border-emerald-700 bg-emerald-700 text-white"
                      : state === "locked"
                        ? "border-border-strong bg-bg-alt text-text-muted"
                        : "border-psu-maroon bg-psu-maroon text-white"
                  }`}
                  aria-hidden="true"
                >
                  <StatusIcon state={state} />
                </div>

                <section
                  className={`card min-w-0 flex-1 p-5 ${state === "locked" ? "bg-bg-alt/60" : ""}`}
                  aria-labelledby={`module-${mod.module_id}-title`}
                >
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <h2 id={`module-${mod.module_id}-title`} className="text-base font-semibold text-text-main">
                      Module {index + 1}: {mod.title}
                    </h2>
                    {state === "done" && <span className="badge badge-success">Completed</span>}
                    {state === "locked" && <span className="badge badge-neutral">Locked</span>}
                  </div>
                  {mod.description && <p className="mb-4 text-sm text-text-muted">{mod.description}</p>}
                  {state === "locked" && (
                    <p className="mb-4 text-xs text-text-muted">Complete the previous module to unlock these tasks.</p>
                  )}

                  {mod.tasks?.length ? (
                    <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
                      {mod.tasks.map((task, taskIndex) => {
                        const taskState = task.is_completed ? "done" : task.is_locked ? "locked" : "open";
                        return (
                          <button
                            key={task.task_id}
                            type="button"
                            disabled={task.is_locked}
                            onClick={() => navigate(`/student/practice/workspace?task=${task.task_id}`)}
                            className={`flex flex-col items-start gap-1.5 rounded-lg border p-3.5 text-left transition-colors ${
                              taskState === "done"
                                ? "border-emerald-600/25 bg-emerald-600/[0.04] hover:bg-emerald-600/[0.08]"
                                : taskState === "locked"
                                  ? "cursor-not-allowed border-border-subtle bg-bg-alt text-text-muted"
                                  : "border-border-subtle bg-bg-panel hover:border-psu-maroon/40 hover:bg-selected"
                            }`}
                          >
                            <span className="flex w-full items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                              Task {taskIndex + 1}
                              <span
                                className={
                                  taskState === "done"
                                    ? "text-text-emerald"
                                    : taskState === "locked"
                                      ? "text-text-muted"
                                      : "text-text-brand"
                                }
                              >
                                <StatusIcon state={taskState} />
                                <span className="sr-only">
                                  {taskState === "done" ? "Completed" : taskState === "locked" ? "Locked" : "Available"}
                                </span>
                              </span>
                            </span>
                            <span className="line-clamp-2 text-sm font-medium text-text-main">{task.title}</span>
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-xs text-text-muted">This module has no tasks yet.</p>
                  )}
                </section>
              </li>
            );
          })}
        </ol>
      )}
    </PageShell>
  );
}
