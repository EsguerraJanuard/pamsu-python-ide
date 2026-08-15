import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";

import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";


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
    badgeClass:
      "border-amber-500/30 bg-amber-500/10 text-amber-400",
    accentClass: "border-l-amber-500",
    progressClass: "bg-amber-500",
    buttonClass:
      "bg-amber-500 text-[#0f1117] hover:bg-amber-400",
  },
  in_progress: {
    label: "In progress",
    badgeClass:
      "border-blue-500/30 bg-blue-500/10 text-blue-400",
    accentClass: "border-l-blue-500",
    progressClass: "bg-blue-500",
    buttonClass:
      "bg-blue-600 text-text-main hover:bg-blue-500",
  },
  submitted: {
    label: "Submitted",
    badgeClass:
      "border-green-500/30 bg-green-500/10 text-green-400",
    accentClass: "border-l-green-500",
    progressClass: "bg-green-500",
    buttonClass:
      "border border-blue-500/40 bg-transparent text-blue-400 hover:bg-blue-500/10",
  },
  graded: {
    label: "Graded",
    badgeClass:
      "border-violet-500/30 bg-violet-500/10 text-violet-400",
    accentClass: "border-l-violet-500",
    progressClass: "bg-violet-500",
    buttonClass:
      "border border-violet-500/40 bg-transparent text-violet-400 hover:bg-violet-500/10",
  },
};

function ClockIcon() {
  return (
    <svg
      width="11"
      height="11"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
    >
      <circle
        cx="8"
        cy="8"
        r="6.5"
        stroke="currentColor"
        strokeWidth="1.3"
      />
      <path
        d="M8 5v3.5l2 1.5"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function TagIcon() {
  return (
    <svg
      width="11"
      height="11"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M2 2h5.5l6.5 6.5-5.5 5.5L2 7.5V2z"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinejoin="round"
      />
      <circle cx="5" cy="5" r="1" fill="currentColor" />
    </svg>
  );
}

function SubmissionIcon() {
  return (
    <svg
      width="11"
      height="11"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M3 8l4 4 6-7"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function isSubmittedActivity(activity) {
  return (
    activity.status === "submitted" ||
    activity.status === "graded"
  );
}

function ClipboardListIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/></svg>
  );
}

export default function Assignments() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [activities, setActivities] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchActivities = async () => {
    setIsLoading(true);
    try {
      const [classRes, activityRes] = await Promise.all([
        api.get("/classrooms/mine"),
        api.get("/activities/")
      ]);
      
      const classMap = {};
      classRes.forEach(c => {
        classMap[c.classroom.class_id] = c.classroom.subject_code;
      });

      const mappedActivities = activityRes.map(task => {
        const due = task.due_at ? new Date(task.due_at) : null;
        let status = "in_progress";
        let dueLabel = "No due date";
        if (due) {
          dueLabel = `Due: ${due.toLocaleDateString()}`;
          if (due < new Date()) {
            status = "submitted"; 
            dueLabel = "Submission closed";
          } else {
             status = "in_progress";
          }
        }
        
        return {
          id: task.task_id,
          title: task.title,
          activityType: task.activity_type === "laboratory" ? "Laboratory" : "Homework",
          courseCode: classMap[task.class_id] || "Unknown",
          dueLabel: dueLabel,
          tags: [], 
          status: status,
          progress: 0,
          note: "No official submission has been recorded.",
          actionLabel: status === "submitted" ? "View submission" : "Open",
          latestSubmission: null,
          instructorGrade: null,
        };
      });
      setActivities(mappedActivities);
    } catch (err) {
      console.error("Failed to load activities", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchActivities();
  }, []);

  const handleOpenActivity = (activity) => {
    if (activity.status === "graded" || activity.status === "submitted") {
      navigate(`/student/submissions/${activity.id}`);
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
                <h1 className="text-2xl font-bold flex items-center gap-3">
                  <ClipboardListIcon className="h-6 w-6 text-blue-500" />
                  Assignments
                </h1>
                <p className="mt-1 text-sm text-text-muted">
                  {activities.filter(a => !isSubmittedActivity(a)).length} active · {activities.filter(isSubmittedActivity).length} submitted
                </p>
              </div>
            </header>

            <section className="mb-6 rounded-xl border border-blue-500/20 bg-blue-500/[0.07] px-4 py-3">
              <p className="text-xs leading-relaxed text-text-blue">
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
                            <ClipboardListIcon className="h-3 w-3 text-text-blue" />
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
                      <div className="mb-4 flex flex-wrap items-center gap-3 rounded-lg border border-green-500/10 bg-green-500/[0.05] px-3 py-2 text-[11px] text-text-emerald shadow-inner">
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
                          <span className="rounded-full bg-green-500/10 px-2 py-0.5 text-[10px] font-bold tracking-wide text-text-emerald">
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
