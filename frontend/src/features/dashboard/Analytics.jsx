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
  if (value >= 80) return "#22c55e"; // green
  if (value >= 60) return "#f59e0b"; // yellow
  return "#ef4444"; // red
}

export default function Analytics() {
  const [metrics, setMetrics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await api.get("/practice/analytics/growth");
        setMetrics(response);
      } catch (err) {
        console.error("Failed to load analytics data", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  // SVG Ring calculation
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const score = metrics?.overall_growth_score || 0;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  const ringColor = getProgressColor(score);

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main">
      <Sidebar />

      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <main className="flex-1 overflow-y-auto px-6 py-6 sm:px-8">
          <header className="mb-8 border-b border-border-subtle pb-6">
            <p className="mb-1 font-mono text-xs text-text-blue">PROGRESS</p>
            <h1 className="text-2xl font-bold flex items-center gap-3">
              <LineChartIcon className="h-6 w-6 text-blue-500" />
              My Analytics & Growth
            </h1>
            <p className="mt-1 text-sm text-text-muted">
              Track your structural logic understanding, problem-solving accuracy, and overall growth curve.
            </p>
          </header>

          {isLoading ? (
            <div className="animate-pulse space-y-6">
              <div className="h-64 w-full bg-bg-glass rounded-xl border border-border-subtle" />
              <div className="h-48 w-full bg-bg-glass rounded-xl border border-border-subtle" />
            </div>
          ) : (
            <div className="space-y-6">
              {/* Top Row: Growth Ring & Attempt Ratios */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Gamified Growth Ring */}
                <article className="lg:col-span-1 rounded-xl border border-border-subtle bg-bg-glass p-6 flex flex-col items-center justify-center relative overflow-hidden shadow-sm">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 pointer-events-none" />
                  <h2 className="text-sm font-semibold text-text-muted mb-4 uppercase tracking-wider">Overall Growth Score</h2>
                  
                  <div className="relative w-40 h-40 flex items-center justify-center">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 140 140">
                      {/* Background Track */}
                      <circle 
                        cx="70" cy="70" r={radius} 
                        fill="transparent" 
                        stroke="currentColor" 
                        strokeWidth="12" 
                        className="text-border-subtle/50" 
                      />
                      {/* Animated Progress Ring */}
                      <circle 
                        cx="70" cy="70" r={radius} 
                        fill="transparent" 
                        stroke={ringColor} 
                        strokeWidth="12" 
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={strokeDashoffset}
                        className="transition-all duration-1000 ease-out drop-shadow-md" 
                      />
                    </svg>
                    <div className="absolute flex flex-col items-center justify-center">
                      <span className="text-4xl font-bold font-mono tracking-tighter" style={{ color: ringColor }}>
                        {score}
                      </span>
                    </div>
                  </div>
                  <p className="mt-4 text-xs text-center text-text-muted max-w-[200px]">
                    Your synthetic rating based on task completion and solution accuracy.
                  </p>
                </article>

                {/* Metrics Cards */}
                <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-6">
                  
                  {/* Task Completion */}
                  <article className="rounded-xl border border-border-subtle bg-bg-glass p-6 flex flex-col justify-center">
                    <div className="mb-2 flex items-center gap-2">
                      <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      </div>
                      <h2 className="text-sm font-medium text-text-muted">Tasks Mastered</h2>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-4xl font-bold text-text-main">{metrics?.completed_tasks || 0}</span>
                      <span className="text-lg text-text-muted">/ {metrics?.total_tasks || 0}</span>
                    </div>
                    <div className="mt-4 h-1.5 w-full bg-border-subtle rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full" style={{ width: `${(metrics?.completed_tasks / Math.max(metrics?.total_tasks || 1, 1)) * 100}%` }} />
                    </div>
                  </article>

                  {/* Accuracy */}
                  <article className="rounded-xl border border-border-subtle bg-bg-glass p-6 flex flex-col justify-center">
                    <div className="mb-2 flex items-center gap-2">
                      <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                      </div>
                      <h2 className="text-sm font-medium text-text-muted">Solution Accuracy</h2>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-4xl font-bold text-text-main">
                        {metrics?.total_attempts ? Math.round((metrics.successful_attempts / metrics.total_attempts) * 100) : 0}%
                      </span>
                    </div>
                    <p className="mt-3 text-xs text-text-muted">
                      Passed <strong>{metrics?.successful_attempts || 0}</strong> out of <strong>{metrics?.total_attempts || 0}</strong> execution attempts.
                    </p>
                  </article>

                </div>
              </div>

              {/* Module Breakdown Table */}
              <section className="rounded-xl border border-border-subtle bg-bg-glass overflow-hidden">
                <div className="border-b border-border-subtle bg-bg-base/50 px-6 py-4">
                  <h3 className="font-semibold text-text-main">Module Progression</h3>
                </div>
                <div className="p-6">
                  {metrics?.module_breakdown && metrics.module_breakdown.length > 0 ? (
                    <div className="grid gap-4">
                      {metrics.module_breakdown.map((mod, idx) => (
                        <div key={idx} className="flex items-center justify-between p-4 rounded-lg border border-border-subtle/50 bg-bg-base/30">
                          <div>
                            <h4 className="font-medium text-text-main">{mod.module_title}</h4>
                            <p className="text-xs text-text-muted mt-1">
                              {mod.attempts_count} total code executions
                            </p>
                          </div>
                          <div className="text-right">
                            <span className="text-sm font-bold text-text-main">{mod.completed_tasks} <span className="text-text-muted font-normal">/ {mod.total_tasks}</span></span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-text-muted text-center py-4">No practice data available yet.</p>
                  )}
                </div>
              </section>

            </div>
          )}
        </main>
        <Statusbar />
      </div>
    </div>
  );
}
