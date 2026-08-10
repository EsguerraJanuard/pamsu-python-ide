import { useState, useEffect } from "react";
import api from "../../services/api";
import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";

function LineChartIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
  );
}

function getProgressColor(value) {
  if (value >= 80) {
    return "#22c55e";
  }

  if (value >= 60) {
    return "#f59e0b";
  }

  return "#ef4444";
}

export default function Analytics() {
  const [metrics, setMetrics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const [subRes, actRes] = await Promise.all([
          api.get("/submissions/"),
          api.get("/activities/")
        ]);
        
        const completed = subRes.filter(s => s.status === 'submitted' || s.status === 'graded').length;
        const total = actRes.length;
        const progress = total > 0 ? Math.round((completed / total) * 100) : 0;
        
        setMetrics({
          learningProgress: progress,
          completedActivities: `${completed} / ${total}`,
          completionPercentage: progress,
        });
      } catch (err) {
        console.error("Failed to load analytics data", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white">
      <Sidebar />

      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <main className="analytics-page flex-1 overflow-y-auto px-6 py-6 sm:px-8">
          <style>
            {`
              @keyframes analyticsFadeUp {
                from {
                  opacity: 0;
                  transform: translateY(10px);
                }

                to {
                  opacity: 1;
                  transform: translateY(0);
                }
              }

              .analytics-page {
                animation:
                  analyticsFadeUp 450ms
                  cubic-bezier(0.25, 0.46, 0.45, 0.94)
                  both;
              }

              @media (prefers-reduced-motion: reduce) {
                .analytics-page {
                  animation: none;
                }
              }
            `}
          </style>

          <div className="w-full">
            <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-white/[0.06] pb-6">
              <div>
                <h1 className="text-2xl font-bold flex items-center gap-3">
                  <LineChartIcon className="h-6 w-6 text-blue-500" />
                  My Analytics
                </h1>
                <p className="mt-1 text-sm text-white/40">
                  Review your activity completion, structural indicators,
                  test results, and personal improvement.
                </p>
              </div>
            </header>

            <section
              className="mb-6 rounded-xl border border-blue-500/20 bg-blue-500/[0.07] px-4 py-3"
              aria-label="Analytics explanation"
            >
              <p className="text-xs leading-relaxed text-blue-200/80">
                These indicators support learning reflection and instructor
                review. They are not automatic grades. Official grades are
                assigned by your instructor.
              </p>
            </section>

            {isLoading ? (
              <section className="mb-8 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-2">
                <article className="rounded-xl border border-white/[0.06] bg-[#1a1d27] p-4 animate-pulse">
                  <div className="mb-1 h-8 w-20 bg-white/[0.06] rounded-md"></div>
                  <div className="mb-1 h-4 w-32 bg-white/[0.06] rounded-md"></div>
                  <div className="mb-3 h-3 w-40 bg-white/[0.06] rounded-md"></div>
                  <div className="h-1 overflow-hidden rounded-full bg-white/[0.06]"></div>
                </article>
                <article className="rounded-xl border border-white/[0.06] bg-[#1a1d27] p-4 animate-pulse">
                  <div className="mb-1 h-8 w-16 bg-white/[0.06] rounded-md"></div>
                  <div className="mb-1 h-4 w-32 bg-white/[0.06] rounded-md"></div>
                  <div className="mb-3 h-3 w-40 bg-white/[0.06] rounded-md"></div>
                  <div className="h-1 overflow-hidden rounded-full bg-white/[0.06]"></div>
                </article>
              </section>
            ) : (
            <section
              className="mb-8 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-2"
              aria-label="Progress summary"
            >
                <article
                  className="rounded-xl border border-white/[0.06] bg-[#1a1d27] p-4"
                >
                  <p
                    className="mb-1 text-3xl font-bold text-blue-500"
                  >
                    {metrics?.learningProgress || 0}%
                  </p>

                  <h2 className="text-xs font-medium text-white/70">
                    Learning Progress
                  </h2>

                  <p className="mb-3 text-[10px] text-white/30">
                    Based on your completed activities
                  </p>

                  <div className="h-1 overflow-hidden rounded-full bg-white/[0.06]">
                    <div
                      className="h-full rounded-full bg-blue-500"
                      style={{
                        width: `${metrics?.learningProgress || 0}%`
                      }}
                    />
                  </div>
                </article>

                <article
                  className="rounded-xl border border-white/[0.06] bg-[#1a1d27] p-4"
                >
                  <p
                    className="mb-1 text-3xl font-bold text-purple-400"
                  >
                    {metrics?.completedActivities || "0 / 0"}
                  </p>

                  <h2 className="text-xs font-medium text-white/70">
                    Activities Completed
                  </h2>

                  <p className="mb-3 text-[10px] text-white/30">
                    Laboratory and homework activities
                  </p>

                  <div className="h-1 overflow-hidden rounded-full bg-white/[0.06]">
                    <div
                      className="h-full rounded-full bg-purple-400"
                      style={{
                        width: `${metrics?.completionPercentage || 0}%`
                      }}
                    />
                  </div>
                </article>
            </section>
            )}

            {!isLoading && (
              <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
                <section className="rounded-xl border border-dashed border-white/[0.08] bg-transparent p-12 flex flex-col items-center justify-center text-center xl:col-span-2">
                   <h2 className="text-base font-semibold text-white/70 mb-2">More Analytics Coming Soon</h2>
                   <p className="text-xs text-white/40 max-w-md">Detailed programming concept progress, weekly tracking, and comparative growth charts require additional backend support. This feature will be available in a future update.</p>
                </section>
              </div>
            )}
          </div>
        </main>

        <Statusbar />
      </div>
    </div>
  );
}
