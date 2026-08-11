import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";

import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";
import JoinClassModal from "../../components/modals/JoinClassModal";
import { useAuth } from "../../features/auth/AuthContext";

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
    buttonClass: "bg-blue-600 text-text-main hover:bg-blue-500",
  },
  submitted: {
    label: "Submitted",
    badgeClass: "border-green-500/30 bg-green-500/10 text-green-400",
    accentClass: "border-l-green-500",
    progressClass: "bg-green-500",
    buttonClass: "border border-blue-500/40 bg-transparent text-blue-400 hover:bg-blue-500/10",
  },
};

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

function LayoutDashboardIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>
  );
}

export default function StudentDashboard() {
  const navigate = useNavigate();
  const { user: authUser } = useAuth();
  
  const userName = authUser?.name || "Student";
  const userInitials = userName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "ST";
    
  const user = {
    name: userName,
    initials: userInitials,
    courseCode: "No active class",
    courseName: "",
  };
  
  const [isJoinModalOpen, setIsJoinModalOpen] = useState(false);
  const [classrooms, setClassrooms] = useState([]);
  const [activities, setActivities] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [completedCount, setCompletedCount] = useState(0);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const [classRes, activityRes, subRes] = await Promise.all([
        api.get("/classrooms/mine"),
        api.get("/activities/"),
        api.get("/submissions/")
      ]);
      setClassrooms(classRes);
      
      const completed = subRes.filter(s => s.status === 'submitted' || s.status === 'graded').length;
      setCompletedCount(completed);
      
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
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main">
      <Sidebar
        user={{
          name: user.name,
          initials: user.initials,
          role: "Student",
          course: user.courseCode,
        }}
        assignmentCount={activeActivities.length}
      />

      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
            

            <div className="mx-auto max-w-6xl">
              <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-border-subtle pb-6">
                <div>
                  <h1 className="text-2xl font-bold flex items-center gap-3">
                    <LayoutDashboardIcon className="h-6 w-6 text-blue-500" />
                    {getGreeting()}, {getFirstName(user.name)}
                  </h1>
                  <p className="mt-1 text-sm text-text-muted">
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
                    className="flex items-center gap-2 rounded-lg bg-[#3b82f6] px-4 py-2.5 text-xs font-semibold text-text-main transition hover:bg-[#2563eb]"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    Join a Class
                  </button>

                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-full bg-bg-glass border border-border-subtle text-xs font-bold shadow-sm"
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
                className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2"
                aria-label="Student progress summary"
              >
                {isLoading ? (
                  <>
                    <article className="dashboard-card rounded-xl border border-border-subtle bg-bg-glass p-5 animate-pulse">
                      <div className="mb-2 h-8 w-16 bg-white/[0.06] rounded-md"></div>
                      <div className="mb-1 h-4 w-32 bg-white/[0.06] rounded-md"></div>
                      <div className="mb-4 h-3 w-40 bg-white/[0.06] rounded-md"></div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]"></div>
                    </article>
                    <article className="dashboard-card rounded-xl border border-border-subtle bg-bg-glass p-5 animate-pulse">
                      <div className="mb-2 h-8 w-24 bg-white/[0.06] rounded-md"></div>
                      <div className="mb-1 h-4 w-32 bg-white/[0.06] rounded-md"></div>
                      <div className="mb-4 h-3 w-40 bg-white/[0.06] rounded-md"></div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]"></div>
                    </article>
                  </>
                ) : (
                  <>
                  <article
                    className="dashboard-card relative overflow-hidden rounded-xl border border-border-subtle bg-bg-glass p-5 shadow-inner transition-all hover:bg-black/60 hover:border-white/[0.12] hover:shadow-lg hover:shadow-black/20 group"
                  >
                    <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-blue-500/10 blur-2xl transition-all group-hover:bg-blue-500/20"></div>
                    <p
                      className="mb-1 text-4xl font-bold text-text-main tracking-tight"
                    >
                      {activeActivities.length}
                    </p>

                    <h2 className="text-sm font-semibold text-white/90">
                      Active activities
                    </h2>

                    <p className="mb-4 text-[11px] text-text-muted font-medium">
                      Laboratory and homework tasks
                    </p>

                    <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06] shadow-inner">
                      <div
                        className="h-full rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)] transition-all duration-1000 ease-out"
                        style={{
                          width: `${activities.length > 0 ? (activeActivities.length / activities.length) * 100 : 0}%`,
                        }}
                      />
                    </div>
                  </article>
                  
                  <article
                    className="dashboard-card relative overflow-hidden rounded-xl border border-border-subtle bg-bg-glass p-5 shadow-inner transition-all hover:bg-black/60 hover:border-white/[0.12] hover:shadow-lg hover:shadow-black/20 group"
                  >
                    <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-emerald-500/10 blur-2xl transition-all group-hover:bg-emerald-500/20"></div>
                    <p
                      className="mb-1 text-4xl font-bold text-text-main tracking-tight flex items-baseline gap-1"
                    >
                      {completedCount} <span className="text-lg text-text-muted font-medium">/ {activities.length}</span>
                    </p>

                    <h2 className="text-sm font-semibold text-white/90">
                      Activities completed
                    </h2>

                    <p className="mb-4 text-[11px] text-text-muted font-medium">
                      Based on submitted activities
                    </p>

                    <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06] shadow-inner">
                      <div
                        className="h-full rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)] transition-all duration-1000 ease-out"
                        style={{
                          width: `${activities.length > 0 ? (completedCount / activities.length) * 100 : 0}%`,
                        }}
                      />
                    </div>
                  </article>
                  </>
                )}
              </section>

              <section>
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-semibold">
                      Recent Activities
                    </h2>

                    <p className="mt-1 text-[11px] text-text-muted">
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
                  {isLoading && (
                    [1, 2, 3].map(i => (
                      <article key={i} className="dashboard-card rounded-xl border border-border-subtle bg-bg-glass p-4 animate-pulse flex items-center justify-between">
                        <div className="space-y-2">
                          <div className="h-5 w-48 bg-white/[0.06] rounded-md"></div>
                          <div className="h-4 w-32 bg-white/[0.06] rounded-md"></div>
                        </div>
                        <div className="h-8 w-20 bg-white/[0.06] rounded-md"></div>
                      </article>
                    ))
                  )}
                  {activities.length === 0 && !isLoading && (
                    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border-subtle bg-white/[0.01] py-16 px-6 text-center transition-all hover:bg-bg-glass">
                      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/10 mb-3 ring-4 ring-blue-500/5 text-blue-400">
                        <LayoutDashboardIcon className="h-6 w-6" />
                      </div>
                      <h3 className="text-lg font-semibold text-white/90">No Activities Found</h3>
                      <p className="mt-1 text-sm text-text-muted">
                        Join a class to see your assignments and practice modules.
                      </p>
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
                          className={`dashboard-card rounded-xl border border-l-[3px] border-border-subtle bg-bg-glass p-5 shadow-inner transition-all hover:bg-black/60 hover:border-white/[0.12] hover:shadow-lg hover:shadow-black/20 ${status.accentClass} group`}
                          style={{
                            animation: `dashboardFadeUp 400ms ease ${
                              200 + index * 70
                            }ms both`,
                          }}
                        >
                          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                            <div className="min-w-0 flex-1">
                              <div className="mb-2 flex flex-wrap items-center gap-2">
                                <h3 className="text-sm font-semibold text-white/90 transition-colors group-hover:text-text-main">
                                  {activity.title}
                                </h3>

                                <span
                                  className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold tracking-wide ${status.badgeClass}`}
                                >
                                  {status.label}
                                </span>
                              </div>

                              <div className="mb-4 flex flex-wrap items-center gap-3 text-[11px] font-medium text-text-muted">
                                <span className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-bg-glass border border-white/[0.05]">
                                  <BookOpenIcon className="h-3 w-3 text-blue-400" />
                                  {activity.courseCode}
                                </span>

                                <span className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-bg-glass border border-white/[0.05]">
                                  <ClockIcon />
                                  {activity.dueLabel}
                                </span>
                              </div>

                              <p className="rounded-lg border-l-2 border-border-subtle bg-bg-glass px-3 py-2 font-mono text-[11px] text-text-muted shadow-inner">
                                {activity.note}
                              </p>
                            </div>

                            <button
                              type="button"
                              onClick={() =>
                                handleOpenActivity(activity)
                              }
                              className={`shrink-0 rounded-lg px-4 py-2 text-xs font-semibold shadow-sm transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98] ${status.buttonClass}`}
                            >
                              {activity.actionLabel}
                            </button>
                          </div>

                          <div className="mt-4 flex items-center gap-3">
                            <span className="shrink-0 text-[10px] font-medium uppercase tracking-wider text-text-muted">
                              Progress
                            </span>

                            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.06] shadow-inner">
                              <div
                                className={`h-full rounded-full transition-all duration-1000 ease-out ${status.progressClass}`}
                                style={{
                                  width: `${activity.progress}%`,
                                }}
                              />
                            </div>

                            <span className="shrink-0 text-[10px] text-text-muted">
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

          <aside className="hidden w-[300px] shrink-0 overflow-y-auto border-l border-border-subtle px-5 py-6 xl:block">
            <section className="mb-6">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-xs font-semibold">
                    Personal Progress
                  </h2>

                  <p className="mt-1 text-[10px] text-text-muted">
                    Compared with your earlier work
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => navigate("/student/analytics")}
                  className="text-[10px] text-[#3b82f6] transition-colors hover:text-[#60a5fa]"
                >
                  Details
                </button>
              </div>

              <div className="flex flex-col items-center rounded-xl border border-border-subtle bg-bg-glass px-4 py-6">
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
                      {activities.length > 0 ? Math.round((completedCount / activities.length) * 100) : 0}%
                    </span>

                    <span className="text-[10px] text-text-muted">
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

              <div className="flex items-center justify-center py-6 text-center">
                <p className="text-xs text-text-muted">
                  No recent activity logged yet.
                </p>
              </div>
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