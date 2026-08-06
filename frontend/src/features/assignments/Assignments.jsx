import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";

import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";

const PREVIEW_ACTIVITIES = [
  {
    id: 1,
    title: "Lab Activity 3 — Fibonacci Sequence",
    activityType: "Laboratory",
    courseCode: "CCS101",
    dueLabel: "Due today, 11:59 PM",
    tags: ["Loops", "Functions"],
    status: "due_today",
    progress: 70,
    note: "A draft is available. Continue working before the deadline.",
    actionLabel: "Continue",
    latestSubmission: null,
    instructorGrade: null,
  },
  {
    id: 2,
    title: "Homework 2 — Lists and File Processing",
    activityType: "Homework",
    courseCode: "CCS101",
    dueLabel: "Due Jan 18, 11:59 PM",
    tags: ["Lists", "File I/O"],
    status: "in_progress",
    progress: 30,
    note: "Draft saved. No official submission has been recorded.",
    actionLabel: "Open",
    latestSubmission: null,
    instructorGrade: null,
  },
  {
    id: 3,
    title: "Lab Activity 2 — Control Flow and Functions",
    activityType: "Laboratory",
    courseCode: "CCS101",
    dueLabel: "Due Jan 10",
    tags: ["Conditionals", "Functions"],
    status: "submitted",
    progress: 100,
    note: "Latest official submission is awaiting instructor review.",
    actionLabel: "View submission",
    latestSubmission: {
      attemptNumber: 2,
      submittedLabel: "Submitted Jan 10",
      isOfficial: true,
    },
    instructorGrade: null,
  },
  {
    id: 4,
    title: "Lab Activity 1 — Variables and Data Types",
    activityType: "Laboratory",
    courseCode: "CCS101",
    dueLabel: "Due Jan 5",
    tags: ["Variables", "Data Types"],
    status: "graded",
    progress: 100,
    note: "The latest official submission has been graded by the instructor.",
    actionLabel: "View result",
    latestSubmission: {
      attemptNumber: 1,
      submittedLabel: "Submitted Jan 5",
      isOfficial: true,
    },
    instructorGrade: {
      score: 92,
      maximum: 100,
    },
  },
];

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
      "bg-blue-600 text-white hover:bg-blue-500",
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
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white">
      <Sidebar assignmentCount={activities.filter(a => !isSubmittedActivity(a)).length} />

      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <main className="assignments-page flex-1 overflow-y-auto px-5 py-6 sm:px-8">
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

          <div className="mx-auto max-w-5xl">
            <header className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h1 className="text-2xl font-bold leading-tight">
                  Assignments
                </h1>

                <p className="mt-1 text-sm text-white/40">
                  {activities.filter(a => !isSubmittedActivity(a)).length} active · {activities.filter(isSubmittedActivity).length} submitted
                </p>
              </div>

              <span className="w-fit rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-[11px] font-medium text-amber-300">
                Preview data
              </span>
            </header>

            <section className="mb-6 rounded-xl border border-blue-500/20 bg-blue-500/[0.07] px-4 py-3">
              <p className="text-xs leading-relaxed text-blue-200/80">
                You may submit an activity more than once while
                submissions remain open. The latest accepted submission
                becomes the official version for instructor review.
              </p>
            </section>

            <div
              className="mb-6 flex w-fit gap-1 rounded-lg border border-white/[0.06] bg-[#1a1d27] p-1"
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
                    className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                      isSelected
                        ? "bg-white text-[#0f1117]"
                        : "text-white/40 hover:bg-white/[0.04] hover:text-white/80"
                    }`}
                  >
                    {filterOption.label}
                  </button>
                );
              })}
            </div>

            <section
              className="space-y-3"
              aria-label="Activity list"
            >
              {filteredActivities.map((activity, index) => {
                const status =
                  STATUS_CONFIG[activity.status] ??
                  STATUS_CONFIG.in_progress;

                return (
                  <article
                    key={activity.id}
                    className={`assignment-card rounded-xl border border-l-[3px] border-white/[0.06] bg-[#1a1d27] p-4 ${status.accentClass}`}
                    style={{
                      animation: `assignmentsFadeUp 400ms ease ${
                        index * 70
                      }ms both`,
                    }}
                  >
                    <div className="mb-3 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="mb-1 flex flex-wrap items-center gap-2">
                          <h2 className="text-sm font-semibold">
                            {activity.title}
                          </h2>

                          <span
                            className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${status.badgeClass}`}
                          >
                            {status.label}
                          </span>

                          <span className="rounded-full border border-white/[0.08] bg-white/[0.03] px-2 py-0.5 text-[10px] text-white/40">
                            {activity.activityType}
                          </span>
                        </div>

                        <div className="flex flex-wrap items-center gap-3 text-[11px] text-white/35">
                          <span>{activity.courseCode}</span>

                          <span className="flex items-center gap-1">
                            <ClockIcon />
                            {activity.dueLabel}
                          </span>

                          {activity.tags.length > 0 && (
                            <span className="flex items-center gap-1">
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
                        className={`shrink-0 rounded-lg px-3 py-1.5 text-xs font-semibold transition duration-150 hover:-translate-y-px active:translate-y-0 active:scale-[0.98] ${status.buttonClass}`}
                      >
                        {activity.actionLabel}
                      </button>
                    </div>

                    {activity.latestSubmission && (
                      <div className="mb-3 flex flex-wrap items-center gap-3 rounded-lg border border-green-500/10 bg-green-500/[0.05] px-3 py-2 text-[11px] text-green-300/80">
                        <span className="flex items-center gap-1">
                          <SubmissionIcon />
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
                          <span className="rounded-full bg-green-500/10 px-2 py-0.5 text-[10px] font-medium text-green-400">
                            Latest official submission
                          </span>
                        )}
                      </div>
                    )}

                    <div className="mb-3 rounded-lg border-l-2 border-white/[0.08] bg-white/[0.03] px-3 py-2 font-mono text-[11px] text-white/45">
                      <span className="text-white/25">
                        Activity status:{" "}
                      </span>
                      {activity.note}
                    </div>

                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                      <span className="shrink-0 text-[10px] text-white/30">
                        Activity progress
                      </span>

                      <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
                        <div
                          className={`h-full rounded-full ${status.progressClass}`}
                          style={{
                            width: `${activity.progress}%`,
                          }}
                        />
                      </div>

                      <span className="shrink-0 text-[10px] text-white/40">
                        {activity.progress}%
                      </span>

                      {activity.instructorGrade && (
                        <span className="shrink-0 rounded-full border border-violet-500/20 bg-violet-500/10 px-2.5 py-1 text-[10px] font-semibold text-violet-300">
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
                <div className="rounded-xl border border-dashed border-white/[0.08] py-16 text-center">
                  <p className="text-sm text-white/30">
                    No activities found for this filter.
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
