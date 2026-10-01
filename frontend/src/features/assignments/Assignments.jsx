import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";

import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";

// Mock icons
function ClipboardListIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
  );
}

function ClockIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
  );
}

function TagIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg>
  );
}

function SubmissionIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
  );
}

const FILTERS = [
  {
    label: "All",
    value: "all",
  },
  {
    label: "Active",
    value: "active",
  },
  {
    label: "Submitted",
    value: "submitted",
  },
];

const STATUS_CONFIG = {
  due_today: {
    label: "Due today",
    badgeClass: "border-psu-red/30 bg-psu-red/10 text-psu-red",
    accentClass: "border-l-psu-red",
    progressClass: "bg-psu-red",
    buttonClass: "border border-psu-red/40 bg-transparent text-psu-red hover:bg-psu-red/10",
  },
  in_progress: {
    label: "In progress",
    badgeClass: "border-border-strong bg-bg-glass text-text-muted",
    accentClass: "border-l-border-strong",
    progressClass: "bg-border-strong",
    buttonClass: "border border-border-strong bg-transparent text-text-muted hover:bg-bg-glass hover:text-text-main",
  },
  submitted: {
    label: "Submitted",
    badgeClass: "border-psu-maroon/30 bg-psu-maroon/10 text-text-brand dark:border-psu-gold/30 ",
    accentClass: "border-l-psu-maroon dark:border-l-psu-gold",
    progressClass: "bg-psu-maroon dark:bg-psu-gold",
    buttonClass: "border border-psu-maroon/40 bg-transparent text-text-brand hover:bg-psu-maroon/10 dark:border-psu-gold/40 dark:hover:bg-psu-gold/10",
  },
  graded: {
    label: "Graded",
    badgeClass: "border-psu-maroon bg-psu-maroon text-white dark:border-psu-gold dark:bg-psu-gold dark:text-black",
    accentClass: "border-l-psu-maroon dark:border-l-psu-gold",
    progressClass: "bg-psu-maroon dark:bg-psu-gold",
    buttonClass: "border border-psu-maroon bg-transparent text-text-brand hover:bg-psu-maroon/10 dark:border-psu-gold dark:hover:bg-psu-gold/10",
  },
};

export default function Assignments() {
  const navigate = useNavigate();
  const [activities, setActivities] = useState([]);
  const [filter, setFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchActivities = async () => {
    try {
      // Add your API call here if needed: const response = await api.get('/activities');
      // setActivities(response.data);
      setActivities([]); // placeholder
    } catch (error) {
      console.error("Failed to fetch activities", error);
    }
  };

  useEffect(() => {
    fetchActivities();
  }, []);

  const isSubmittedActivity = (activity) => {
    return activity.status === "graded" || activity.status === "submitted";
  };

  const handleOpenActivity = (activity) => {
    if (activity.status === "graded" || activity.status === "submitted") {
      navigate(`/student/submissions/task/${activity.id}`);
      return;
    }

    navigate(`/student/workspace?activity=${activity.id}`);
  };

  const filteredActivities = activities.filter((activity) => {
    const matchesSearch =
      activity.title
        .toLowerCase()
        .includes(searchQuery.toLowerCase()) ||
      activity.courseCode
        .toLowerCase()
        .includes(searchQuery.toLowerCase());

    let matchesFilter = true;
    if (filter === "active") {
      matchesFilter = activity.status !== "graded" && activity.status !== "submitted";
    } else if (filter === "submitted") {
      matchesFilter = activity.status === "graded" || activity.status === "submitted";
    }

    return matchesSearch && matchesFilter;
  });

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main">
      <Sidebar assignmentCount={activities.filter(a => !isSubmittedActivity(a)).length} />

      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <main className="assignments-page flex-1 overflow-y-auto px-6 py-6 sm:px-8">
          <style>
            {`
              @keyframes assignmentsFadeUp {
                from {
                  opacity: 0;
                  transform: translateY(10px);
                }

                to {
                  opacity: 1;
                  transform: translateY(0);
                }
              }

              .assignments-page {
                animation:
                  assignmentsFadeUp 450ms
                  cubic-bezier(0.25, 0.46, 0.45, 0.94)
                  both;
              }

              @media (prefers-reduced-motion: reduce) {
                .assignments-page,
                .assignment-card {
                  animation: none !important;
                }
              }
            `}
          </style>

          <div className="w-full">
            <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-border-subtle pb-6">
              <div>
                <p className="mb-1 font-mono text-xs text-text-brand">MAIN</p>
                <h1 className="text-2xl font-bold flex items-center gap-3">
                  <ClipboardListIcon className="h-6 w-6 text-text-brand" />
                  Assignments
                </h1>
                <p className="mt-1 text-sm text-text-muted">
                  {activities.filter(a => !isSubmittedActivity(a)).length} active · {activities.filter(isSubmittedActivity).length} submitted
                </p>
              </div>
            </header>

            <section className="mb-6 rounded-xl border border-psu-maroon/20 bg-psu-maroon/[0.07] px-4 py-3">
              <p className="text-xs leading-relaxed text-text-brand">
                You may submit an activity more than once while
                submissions remain open. The latest accepted submission
                becomes the official version for instructor review.
              </p>
            </section>

            <div
              className="mb-6 flex w-fit gap-1 rounded-lg border border-border-subtle bg-bg-glass shadow-inner p-1"
              role="tablist"
              aria-label="Activity filters"
            >
              {FILTERS.map((filterOption) => {
                const isSelected =
                  filter === filterOption.value;

                return (
                  <button
                    key={filterOption.value}
                    type="button"
                    role="tab"
                    aria-selected={isSelected}
                    onClick={() =>
                      setFilter(filterOption.value)
                    }
                    className={`rounded-md px-4 py-1.5 text-sm font-medium transition-all duration-200 ${
                      isSelected
                        ? "bg-white text-[#0f1117] shadow-sm"
                        : "text-text-muted hover:bg-bg-glass-hover hover:text-text-main"
                    }`}
                  >
                    {filterOption.label}
                  </button>
                );
              })}
            </div>

            <section
              className="space-y-4"
              aria-label="Activity list"
            >
              {filteredActivities.map((activity, index) => {
                const status =
                  STATUS_CONFIG[activity.status] ??
                  STATUS_CONFIG.in_progress;

                return (
                  <article
                    key={activity.id}
                    className={`assignment-card rounded-xl border border-l-[3px] border-border-subtle bg-bg-glass p-5 shadow-inner transition-all hover:bg-bg-glass-hover hover:border-border-strong hover:shadow-lg hover:shadow-border-strong group ${status.accentClass}`}
                    style={{
                      animation: `assignmentsFadeUp 400ms ease ${
                        index * 70
                      }ms both`,
                    }}
                  >
                    <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="mb-2 flex flex-wrap items-center gap-2">
                          <h2 className="text-sm font-semibold text-text-main transition-colors group-hover:text-text-main">
                            {activity.title}
                          </h2>

                          <span
                            className={`rounded-full border px-2 py-0.5 text-[10px] font-bold tracking-wide ${status.badgeClass}`}
                          >
                            {status.label}
                          </span>

                          <span className="rounded-full border border-border-subtle bg-bg-glass px-2 py-0.5 text-[10px] font-medium text-text-muted shadow-sm">
                            {activity.activityType}
                          </span>
                        </div>

                        <div className="flex flex-wrap items-center gap-3 text-[11px] font-medium text-text-muted">
                          <span className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-bg-glass border border-border-subtle">
                            <ClipboardListIcon className="h-3 w-3 text-text-brand" />
                            {activity.courseCode}
                          </span>

                          <span className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-bg-glass border border-border-subtle">
                            <ClockIcon className="h-3 w-3" />
                            {activity.dueLabel}
                          </span>

                          {activity.tags.length > 0 && (
                            <span className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-bg-glass border border-border-subtle">
                              <TagIcon />
                              {activity.tags.join(" · ")}
                            </span>
                          )}
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={() =>
                          handleOpenActivity(activity)
                        }
                        className={`shrink-0 rounded-lg px-5 py-2 text-xs font-semibold shadow-sm transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98] ${status.buttonClass}`}
                      >
                        {activity.actionLabel}
                      </button>
                    </div>

                    {activity.latestSubmission && (
                      <div className="mb-4 flex flex-wrap items-center gap-3 rounded-lg border border-psu-maroon/20 bg-psu-maroon/5 px-3 py-2 text-[11px] text-text-brand shadow-inner">
                        <span className="flex items-center gap-1.5 font-medium">
                          <SubmissionIcon className="h-3 w-3" />
                          Attempt{" "}
                          {activity.latestSubmission.attemptNumber}
                        </span>

                        <span>
                          {
                            activity.latestSubmission
                              .submittedLabel
                          }
                        </span>

                        {activity.latestSubmission.isOfficial && (
                          <span className="rounded-full bg-psu-maroon/10 px-2 py-0.5 text-[10px] font-bold tracking-wide text-text-brand">
                            Latest official submission
                          </span>
                        )}
                      </div>
                    )}

                    <div className="mb-4 rounded-lg border-l-2 border-border-subtle bg-bg-glass px-3 py-2.5 font-mono text-[11px] text-text-muted shadow-inner">
                      <span className="text-text-muted uppercase tracking-wider text-[9px] mr-2">
                        Activity status:
                      </span>
                      {activity.note}
                    </div>

                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                      <span className="shrink-0 text-[10px] font-medium uppercase tracking-wider text-text-muted">
                        Activity progress
                      </span>

                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.06] shadow-inner">
                        <div
                          className={`h-full rounded-full transition-all duration-1000 ease-out ${status.progressClass}`}
                          style={{
                            width: `${activity.progress}%`,
                          }}
                        />
                      </div>

                      <span className="shrink-0 text-[10px] font-bold text-text-muted">
                        {activity.progress}%
                      </span>

                      {activity.instructorGrade && (
                        <span className="shrink-0 rounded-full border border-violet-500/20 bg-violet-500/10 px-2.5 py-1 text-[10px] font-bold tracking-wide text-text-violet shadow-sm ml-auto">
                          Instructor grade:{" "}
                          {activity.instructorGrade.score} /{" "}
                          {activity.instructorGrade.maximum}
                        </span>
                      )}
                    </div>
                  </article>
                );
              })}

              {filteredActivities.length === 0 && (
                <div className="rounded-2xl border border-dashed border-border-subtle bg-bg-glass shadow-inner py-20 text-center transition-all hover:bg-bg-glass hover:border-border-strong">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-bg-glass mb-4 text-text-muted ring-4 ring-white/[0.02]">
                    <ClipboardListIcon className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-semibold text-text-main">No Activities Found</h3>
                  <p className="mt-1 text-sm text-text-muted">
                    No activities match the current filter.
                  </p>
                </div>
              )}
            </section>
          </div>
        </main>

        <Statusbar />
      </div>
    </div>
  );
}
