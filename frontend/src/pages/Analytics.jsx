import Sidebar from "../components/Sidebar";
import Statusbar from "../components/Statusbar";

const SUMMARY_CARDS = [
  {
    value: "72%",
    label: "Learning Progress",
    description: "Based on your completed activities",
    progress: 72,
    color: "#3b82f6",
  },
  {
    value: "68%",
    label: "AST Indicators Met",
    description: "Across checked submissions",
    progress: 68,
    color: "#f59e0b",
  },
  {
    value: "84%",
    label: "Test Cases Passed",
    description: "Across recent runs and checks",
    progress: 84,
    color: "#22c55e",
  },
  {
    value: "8 / 11",
    label: "Activities Completed",
    description: "Laboratory and homework activities",
    progress: 73,
    color: "#a78bfa",
  },
];

const WEEKLY_PROGRESS = [
  { week: "Week 1", ast: 55, tests: 62 },
  { week: "Week 2", ast: 61, tests: 70 },
  { week: "Week 3", ast: 65, tests: 78 },
  { week: "Week 4", ast: 68, tests: 84 },
];

const CONCEPT_PROGRESS = [
  {
    label: "Variables and expressions",
    value: 92,
  },
  {
    label: "Conditional statements",
    value: 86,
  },
  {
    label: "Loops",
    value: 78,
  },
  {
    label: "Functions",
    value: 70,
  },
  {
    label: "Lists and collections",
    value: 64,
  },
  {
    label: "Exception handling",
    value: 42,
  },
];

const RECENT_GROWTH = [
  {
    title: "AST indicators",
    current: "68%",
    previous: "61%",
    change: "+7%",
    positive: true,
  },
  {
    title: "Test cases passed",
    current: "84%",
    previous: "76%",
    change: "+8%",
    positive: true,
  },
  {
    title: "Average run attempts",
    current: "6",
    previous: "8",
    change: "-2",
    positive: true,
  },
];

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
  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <main className="analytics-page flex-1 overflow-y-auto px-5 py-6 sm:px-8">
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

          <div className="mx-auto max-w-6xl">
            <header className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h1 className="text-2xl font-bold text-white">
                  My Learning Progress
                </h1>

                <p className="mt-1 text-sm text-white/40">
                  Review your activity completion, structural indicators,
                  test results, and personal improvement.
                </p>
              </div>

              <span className="w-fit rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-[11px] font-medium text-amber-300">
                Preview data
              </span>
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

            <section
              className="mb-8 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4"
              aria-label="Progress summary"
            >
              {SUMMARY_CARDS.map((card) => (
                <article
                  key={card.label}
                  className="rounded-xl border border-white/[0.06] bg-[#1a1d27] p-4"
                >
                  <p
                    className="mb-1 text-3xl font-bold"
                    style={{ color: card.color }}
                  >
                    {card.value}
                  </p>

                  <h2 className="text-xs font-medium text-white/70">
                    {card.label}
                  </h2>

                  <p className="mb-3 text-[10px] text-white/30">
                    {card.description}
                  </p>

                  <div className="h-1 overflow-hidden rounded-full bg-white/[0.06]">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${card.progress}%`,
                        backgroundColor: card.color,
                      }}
                    />
                  </div>
                </article>
              ))}
            </section>

            <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
              <section className="rounded-xl border border-white/[0.06] bg-[#1a1d27] p-5">
                <h2 className="text-sm font-semibold text-white">
                  Weekly Progress
                </h2>

                <p className="mb-5 mt-1 text-[11px] text-white/30">
                  AST indicators and passed test cases from recent activities
                </p>

                <div
                  className="flex h-40 items-end gap-4"
                  aria-label="Weekly progress chart"
                >
                  {WEEKLY_PROGRESS.map((item) => (
                    <div
                      key={item.week}
                      className="flex flex-1 flex-col items-center gap-2"
                    >
                      <div className="flex h-28 w-full items-end gap-1">
                        <div
                          className="flex-1 rounded-t-sm bg-[#f59e0b]"
                          style={{ height: `${item.ast}%` }}
                          title={`${item.week} AST indicators: ${item.ast}%`}
                        />

                        <div
                          className="flex-1 rounded-t-sm bg-[#22c55e]"
                          style={{ height: `${item.tests}%` }}
                          title={`${item.week} test cases passed: ${item.tests}%`}
                        />
                      </div>

                      <span className="text-[9px] text-white/30">
                        {item.week}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-4">
                  <div className="flex items-center gap-1.5">
                    <span
                      className="h-2 w-2 rounded-sm bg-[#f59e0b]"
                      aria-hidden="true"
                    />

                    <span className="text-[10px] text-white/40">
                      AST indicators
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <span
                      className="h-2 w-2 rounded-sm bg-[#22c55e]"
                      aria-hidden="true"
                    />

                    <span className="text-[10px] text-white/40">
                      Test cases passed
                    </span>
                  </div>
                </div>
              </section>

              <section className="rounded-xl border border-white/[0.06] bg-[#1a1d27] p-5">
                <h2 className="text-sm font-semibold text-white">
                  Programming Concept Progress
                </h2>

                <p className="mb-5 mt-1 text-[11px] text-white/30">
                  Structural concepts detected in your checked code
                </p>

                <div className="space-y-4">
                  {CONCEPT_PROGRESS.map((item) => {
                    const color = getProgressColor(item.value);

                    return (
                      <div key={item.label}>
                        <div className="mb-1.5 flex items-center justify-between gap-4">
                          <span className="text-[11px] text-white/60">
                            {item.label}
                          </span>

                          <span
                            className="font-mono text-[11px] font-semibold"
                            style={{ color }}
                          >
                            {item.value}%
                          </span>
                        </div>

                        <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${item.value}%`,
                              backgroundColor: color,
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>

              <section className="rounded-xl border border-white/[0.06] bg-[#1a1d27] p-5 xl:col-span-2">
                <h2 className="text-sm font-semibold text-white">
                  Growth Compared with Previous Activities
                </h2>

                <p className="mb-5 mt-1 text-[11px] text-white/30">
                  Your recent results compared with your own earlier
                  performance
                </p>

                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  {RECENT_GROWTH.map((item) => (
                    <article
                      key={item.title}
                      className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-4"
                    >
                      <h3 className="text-[11px] font-medium text-white/60">
                        {item.title}
                      </h3>

                      <div className="mt-3 flex items-end justify-between gap-3">
                        <div>
                          <p className="text-2xl font-bold text-white">
                            {item.current}
                          </p>

                          <p className="text-[10px] text-white/30">
                            Previous: {item.previous}
                          </p>
                        </div>

                        <span
                          className={`rounded-full px-2 py-1 text-[10px] font-semibold ${
                            item.positive
                              ? "bg-green-500/10 text-green-400"
                              : "bg-red-500/10 text-red-400"
                          }`}
                        >
                          {item.change}
                        </span>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            </div>
          </div>
        </main>

        <Statusbar />
      </div>
    </div>
  );
}
