import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";

import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";
import JoinClassModal from "../../components/modals/JoinClassModal";

const DEFAULT_USER = {
  name: "Student",
  initials: "ST",
  courseCode: "No active class",
  courseName: "",
};

const PREVIEW_STATS = [
  {
    value: "2",
    label: "Active activities",
    description: "Laboratory and homework tasks",
    progress: 50,
    color: "#3b82f6",
  },
  {
    value: "8 / 11",
    label: "Activities completed",
    description: "Based on submitted activities",
    progress: 73,
    color: "#22c55e",
  },
  {
    value: "68%",
    label: "AST indicators met",
    description: "Across recent checked code",
    progress: 68,
    color: "#f59e0b",
  },
  {
    value: "84%",
    label: "Test cases passed",
    description: "Across recent runs and checks",
    progress: 84,
    color: "#a78bfa",
  },
];

const PREVIEW_ACTIVITIES = [
  {
    id: 1,
    title: "Lab Activity 3 — Fibonacci Sequence",
    courseCode: "CCS101",
    dueLabel: "Due today, 11:59 PM",
    status: "due_today",
    progress: 70,
    note: "A saved draft is available.",
    actionLabel: "Continue",
  },
  {
    id: 2,
    title: "Homework 2 — Lists and File Processing",
    courseCode: "CCS101",
    dueLabel: "Due in 3 days",
    status: "in_progress",
    progress: 30,
    note: "No official submission has been recorded.",
    actionLabel: "Open",
  },
  {
    id: 3,
    title: "Lab Activity 2 — Control Flow and Functions",
    courseCode: "CCS101",
    dueLabel: "Submission closed",
    status: "submitted",
    progress: 100,
    note: "Attempt 2 is the latest official submission.",
    actionLabel: "View submission",
  },
];

const PREVIEW_ACTIVITY_LOG = [
  {
    id: 1,
    message: "Python execution completed successfully",
    time: "Recently",
    type: "run",
  },
  {
    id: 2,
    message: "AST check identified a missing required loop",
    time: "Recently",
    type: "analysis",
  },
  {
    id: 3,
    message: "Lab Activity 2 was submitted as Attempt 2",
    time: "Yesterday",
    type: "submission",
  },
  {
    id: 4,
    message: "Instructor grade posted for Lab Activity 1",
    time: "Earlier",
    type: "grade",
  },
];

const STATUS_CONFIG = {
  due_today: {
    label: "Due today",
    badgeClass: "border-amber-500/30 bg-amber-500/10 text-amber-400",
    accentClass: "border-l-amber-500",
    progressClass: "bg-amber-500",
    buttonClass: "bg-amber-500 text-[#0f1117] hover:bg-amber-400",
  },
  in_progress: {
    label: "In progress",
    badgeClass: "border-blue-500/30 bg-blue-500/10 text-blue-400",
    accentClass: "border-l-blue-500",
    progressClass: "bg-blue-500",
    buttonClass: "bg-blue-600 text-white hover:bg-blue-500",
  },
  submitted: {
    label: "Submitted",
    badgeClass: "border-green-500/30 bg-green-500/10 text-green-400",
    accentClass: "border-l-green-500",
    progressClass: "bg-green-500",
    buttonClass: "border border-blue-500/40 bg-transparent text-blue-400 hover:bg-blue-500/10",
  },
};

function getStoredUser() {
  try {
    const storedUser = sessionStorage.getItem("user");

    if (!storedUser) {
      return DEFAULT_USER;
    }

    const user = JSON.parse(storedUser);
    const name =
      user.name ||
      user.fullName ||
      user.full_name ||
      DEFAULT_USER.name;

    const generatedInitials = name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("");

    return {
      name,
      initials:
        user.initials ||
        generatedInitials ||
        DEFAULT_USER.initials,
      courseCode:
        user.courseCode ||
        user.course_code ||
        user.course ||
        DEFAULT_USER.courseCode,
      courseName:
        user.courseName ||
        user.course_name ||
        DEFAULT_USER.courseName,
    };
  } catch {
    return DEFAULT_USER;
  }
}

function getGreeting() {
  const hour = new Date().getHours();

  if (hour < 12) {
    return "Good morning";
  }

  if (hour < 18) {
    return "Good afternoon";
  }

  return "Good evening";
}

function getFirstName(name) {
  const firstPart = name.includes(",")
    ? name.split(",")[1]?.trim()
    : name.trim();

  return firstPart?.split(/\s+/)[0] || "Student";
}

function getActivityColor(type) {
  const colors = {
    run: "#22c55e",
    analysis: "#f59e0b",
    submission: "#3b82f6",
    grade: "#a78bfa",
  };

  return colors[type] ?? "#64748b";
}

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

export default function StudentDashboard() {
  const navigate = useNavigate();
  const user = getStoredUser();
  
  const [isJoinModalOpen, setIsJoinModalOpen] = useState(false);
  const [classrooms, setClassrooms] = useState([]);
  const [activities, setActivities] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const [classRes, activityRes] = await Promise.all([
        api.get("/classrooms/mine"),
        api.get("/activities/")
      ]);
      setClassrooms(classRes);
      
      const classMap = {};
      classRes.forEach(c => {
        classMap[c.classroom.class_id] = c.classroom.subject_code;
      });

      const mappedActivities = activityRes.map(task => {
        // Map backend task to the dashboard format
        const due = task.due_at ? new Date(task.due_at) : null;
        let status = "in_progress";
        let dueLabel = "No due date";
        if (due) {
          dueLabel = `Due: ${due.toLocaleDateString()}`;
          if (due < new Date()) {
            status = "submitted"; // or past_due
            dueLabel = "Submission closed";
          } else {
             // simplified logic
             status = "in_progress";
          }
        }
        
        return {
          id: task.task_id,
          title: task.title,
          courseCode: classMap[task.class_id] || "Unknown",
          dueLabel: dueLabel,
          status: status,
          progress: 0,
          note: task.activity_type === "laboratory" ? "Laboratory activity" : "Homework",
          actionLabel: status === "submitted" ? "View" : "Open",
        };
      });
      setActivities(mappedActivities);
    } catch (err) {
      console.error("Failed to load dashboard data", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const activeActivities = activities.filter(
    (activity) => activity.status !== "submitted",
  );

  const dueTodayCount = activities.filter(
    (activity) => activity.status === "due_today",
  ).length;

  const handleOpenActivity = (activity) => {
    if (activity.status === "graded" || activity.status === "submitted") {
      navigate(`/student/submissions/${activity.id}`);
      return;
    }

    navigate(`/student/workspace?activity=${activity.id}`);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white">
      <Sidebar
        user={{
          name: user.name,
          initials: user.initials,
          role: "Student",
          course: user.courseCode,
        }}
        assignmentCount={activeActivities.length}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="dashboard-page min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
            <style>
              {`
                @keyframes dashboardFadeUp {
                  from {
                    opacity: 0;
                    transform: translateY(10px);
                  }

                  to {
                    opacity: 1;
                    transform: translateY(0);
                  }
                }

                .dashboard-page {
                  animation:
                    dashboardFadeUp 450ms
                    cubic-bezier(0.25, 0.46, 0.45, 0.94)
                    both;
                }

                @media (prefers-reduced-motion: reduce) {
                  .dashboard-page,
                  .dashboard-card {
                    animation: none !important;
                  }
                }
              `}
            </style>

            <div className="mx-auto max-w-6xl">
              <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="mb-2 font-mono text-xs text-white/30">
                    {user.courseCode}
                    {user.courseName
                      ? ` — ${user.courseName}`
                      : ""}
                  </p>

                  <h1 className="text-2xl font-bold">
                    {getGreeting()}, {getFirstName(user.name)}
                  </h1>

                  <p className="mt-1 text-sm text-white/40">
                    You have {activeActivities.length} active{" "}
                    {activeActivities.length === 1
                      ? "activity"
                      : "activities"}{" "}
                    and {dueTodayCount} due today.
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setIsJoinModalOpen(true)}
                    className="rounded-lg bg-[#3b82f6] px-4 py-2 text-xs font-semibold text-white transition hover:bg-[#2563eb]"
                  >
                    + Join Class
                  </button>

                  <span className="rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-[11px] font-medium text-amber-300">
                    Preview data
                  </span>

                  <div
                    className="flex h-9 w-9 items-center justify-center rounded-full bg-[#3b82f6] text-xs font-bold"
                    aria-label={`Signed in as ${user.name}`}
                  >
                    {user.initials}
                  </div>
                </div>
              </header>

              <section className="mb-6 rounded-xl border border-blue-500/20 bg-blue-500/[0.07] px-4 py-3">
                <p className="text-xs leading-relaxed text-blue-200/80">
                  Dashboard indicators support learning reflection.
                  AST checks, test results, and activity progress are
                  not automatic grades. Official grades are assigned
                  by the instructor.
                </p>
              </section>

              <section
                className="mb-8 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4"
                aria-label="Student progress summary"
              >
                {PREVIEW_STATS.map((stat, index) => (
                  <article
                    key={stat.label}
                    className="dashboard-card rounded-xl border border-white/[0.06] bg-[#1a1d27] p-4"
                    style={{
                      animation: `dashboardFadeUp 400ms ease ${
                        index * 70
                      }ms both`,
                    }}
                  >
                    <p
                      className="mb-1 text-3xl font-bold"
                      style={{ color: stat.color }}
                    >
                      {stat.value}
                    </p>

                    <h2 className="text-xs font-medium text-white/70">
                      {stat.label}
                    </h2>

                    <p className="mb-3 text-[10px] text-white/30">
                      {stat.description}
                    </p>

                    <div className="h-1 overflow-hidden rounded-full bg-white/[0.06]">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${stat.progress}%`,
                          backgroundColor: stat.color,
                        }}
                      />
                    </div>
                  </article>
                ))}
              </section>

              <section>
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-semibold">
                      Recent Activities
                    </h2>

                    <p className="mt-1 text-[11px] text-white/30">
                      Continue active work or review your latest
                      submission.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => navigate("/student/assignments")}
                    className="text-xs text-[#3b82f6] transition-colors hover:text-[#60a5fa]"
                  >
                    View all
                  </button>
                </div>

                <div className="space-y-3">
                  {activities.length === 0 && !isLoading && (
                    <div className="text-sm text-white/40 text-center py-8">
                      No activities found. Join a class to see your assignments.
                    </div>
                  )}
                  {activities.map(
                    (activity, index) => {
                      const status =
                        STATUS_CONFIG[activity.status] ??
                        STATUS_CONFIG.in_progress;

                      return (
                        <article
                          key={activity.id}
                          className={`dashboard-card rounded-xl border border-l-[3px] border-white/[0.06] bg-[#1a1d27] p-4 ${status.accentClass}`}
                          style={{
                            animation: `dashboardFadeUp 400ms ease ${
                              200 + index * 70
                            }ms both`,
                          }}
                        >
                          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                            <div className="min-w-0 flex-1">
                              <div className="mb-1 flex flex-wrap items-center gap-2">
                                <h3 className="text-sm font-semibold">
                                  {activity.title}
                                </h3>

                                <span
                                  className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${status.badgeClass}`}
                                >
                                  {status.label}
                                </span>
                              </div>

                              <div className="mb-3 flex flex-wrap items-center gap-3 text-[11px] text-white/35">
                                <span>
                                  {activity.courseCode}
                                </span>

                                <span className="flex items-center gap-1">
                                  <ClockIcon />
                                  {activity.dueLabel}
                                </span>
                              </div>

                              <p className="rounded-lg border-l-2 border-white/[0.08] bg-white/[0.03] px-3 py-2 font-mono text-[11px] text-white/45">
                                {activity.note}
                              </p>
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

                          <div className="mt-3 flex items-center gap-3">
                            <span className="shrink-0 text-[10px] text-white/30">
                              Progress
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
                          </div>
                        </article>
                      );
                    },
                  )}
                </div>
              </section>
            </div>
          </main>

          <aside className="hidden w-[300px] shrink-0 overflow-y-auto border-l border-white/[0.06] px-5 py-6 xl:block">
            <section className="mb-6">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-xs font-semibold">
                    Personal Progress
                  </h2>

                  <p className="mt-1 text-[10px] text-white/30">
                    Compared with your earlier work
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => navigate("/analytics")}
                  className="text-[10px] text-[#3b82f6] transition-colors hover:text-[#60a5fa]"
                >
                  Details
                </button>
              </div>

              <div className="flex flex-col items-center rounded-xl border border-white/[0.06] bg-[#1a1d27] px-4 py-6">
                <div className="relative h-32 w-32">
                  <svg
                    viewBox="0 0 120 120"
                    className="h-full w-full -rotate-90"
                    aria-label="Learning progress 72 percent"
                  >
                    <circle
                      cx="60"
                      cy="60"
                      r="48"
                      fill="none"
                      stroke="rgba(255,255,255,0.06)"
                      strokeWidth="10"
                    />

                    <circle
                      cx="60"
                      cy="60"
                      r="48"
                      fill="none"
                      stroke="#3b82f6"
                      strokeWidth="10"
                      strokeLinecap="round"
                      strokeDasharray="217.14 301.59"
                    />
                  </svg>

                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-bold">
                      72%
                    </span>

                    <span className="text-[10px] text-white/30">
                      progress
                    </span>
                  </div>
                </div>

                <p className="mt-3 text-sm font-semibold">
                  Improving
                </p>

                <p className="mt-1 text-center text-[10px] leading-relaxed text-white/35">
                  Based on your activity completion, AST indicators,
                  and test results.
                </p>
              </div>
            </section>

            <div className="mb-5 h-px bg-white/[0.06]" />

            <section>
              <h2 className="mb-4 text-xs font-semibold">
                Recent Learning Activity
              </h2>

              <ul className="space-y-4">
                {PREVIEW_ACTIVITY_LOG.map((item) => (
                  <li
                    key={item.id}
                    className="flex items-start gap-2.5"
                  >
                    <span
                      className="mt-1 h-2 w-2 shrink-0 rounded-full"
                      style={{
                        backgroundColor: getActivityColor(
                          item.type,
                        ),
                      }}
                      aria-hidden="true"
                    />

                    <div>
                      <p className="text-[11px] leading-snug text-white/60">
                        {item.message}
                      </p>

                      <p className="mt-0.5 text-[10px] text-white/25">
                        {item.time}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          </aside>
        </div>

        <Statusbar
          courseCode={user.courseCode}
          courseName={user.courseName}
          studentName={user.name}
        />
      </div>

      <JoinClassModal 
        isOpen={isJoinModalOpen} 
        onClose={() => setIsJoinModalOpen(false)}
        onSuccess={() => {
          console.log("Successfully joined class!");
          fetchDashboardData();
        }}
      />
    </div>
  );
}