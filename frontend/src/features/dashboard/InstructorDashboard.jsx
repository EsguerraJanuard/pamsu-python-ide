import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthContext";
import api from "../../services/api";
import InstructorSidebar from "../../components/layout/InstructorSidebar";
import CreateClassModal from "../../components/modals/CreateClassModal";

const PREVIEW_STATS = [
  {
    value: "4",
    label: "Active classes",
    description: "Enrolled laboratory sections",
    progress: 100,
    color: "#10b981", 
  },
  {
    value: "142",
    label: "Students monitored",
    description: "Across active laboratory sessions",
    progress: 88,
    color: "#3b82f6",
  },
  {
    value: "12",
    label: "Activities authored",
    description: "Published programming labs",
    progress: 75,
    color: "#f59e0b",
  },
  {
    value: "91%",
    label: "Submission compliance",
    description: "Passing automated test thresholds",
    progress: 91,
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
    progress: 82,
    note: "114 / 138 submissions received.",
    actionLabel: "Grade Bench",
  },
  {
    id: 2,
    title: "Homework 2 — Lists and File Processing",
    courseCode: "CCS101",
    dueLabel: "Due in 3 days",
    status: "in_progress",
    progress: 45,
    note: "Published to section A and B.",
    actionLabel: "Manage",
  },
  {
    id: 3,
    title: "Lab Activity 2 — Control Flow and Functions",
    courseCode: "CCS101",
    dueLabel: "Grading closed",
    status: "submitted",
    progress: 100,
    note: "All official grades posted.",
    actionLabel: "View Roster",
  },
];



const STATUS_CONFIG = {
  due_today: {
    label: "Active deadline",
    badgeClass: "border-amber-500/30 bg-amber-500/10 text-amber-400",
    accentClass: "border-l-amber-500",
    progressClass: "bg-amber-500",
    buttonClass: "bg-amber-500 text-[#0f1117] hover:bg-amber-400",
  },
  in_progress: {
    label: "Published",
    badgeClass: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
    accentClass: "border-l-emerald-500",
    progressClass: "bg-emerald-500",
    buttonClass: "bg-emerald-600 text-white hover:bg-emerald-500",
  },
  submitted: {
    label: "Completed",
    badgeClass: "border-blue-500/30 bg-blue-500/10 text-blue-400",
    accentClass: "border-l-blue-500",
    progressClass: "bg-blue-500",
    buttonClass: "border border-emerald-500/40 bg-transparent text-emerald-400 hover:bg-emerald-500/10",
  },
};

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function getFirstName(name) {
  const firstPart = name.includes(",") ? name.split(",")[1]?.trim() : name.trim();
  return firstPart?.split(/\s+/)[0] || "Instructor";
}

function getActivityColor(type) {
  const colors = {
    run: "#10b981",
    analysis: "#f59e0b",
    submission: "#3b82f6",
    grade: "#a78bfa",
  };
  return colors[type] ?? "#64748b";
}

function ClockIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M8 5v3.5l2 1.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function InstructorDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Data State
  const [classes, setClasses] = useState([]);
  const [activities, setActivities] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reviewQueue, setReviewQueue] = useState([]);

  // Modal State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const [classRes, tasksRes, reviewRes] = await Promise.all([
        api.get("/classrooms/"),
        api.get("/instructors/tasks/"),
        api.get("/instructors/review-queue")
      ]);
      setClasses(classRes || []);
      setActivities(tasksRes || []);
      const parsedReview = Array.isArray(reviewRes) ? reviewRes : (reviewRes?.items || []);
      setReviewQueue(parsedReview);
      setError(null);
    } catch (err) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const instructorName = user?.name || user?.fullName || "Faculty Member";
  
  // Use the first active class for the header context, or a fallback
  const primaryClass = classes.find((c) => c.is_active) || classes[0];
  const courseCode = primaryClass ? primaryClass.subject_code : "Faculty";
  const courseName = primaryClass ? primaryClass.name : "Dashboard";

  // Compute stats
  const activeClassesCount = classes.filter((c) => c.is_active).length;
  const activitiesAuthoredCount = activities.length;

  const dynamicStats = useMemo(() => [
    {
      value: activeClassesCount.toString(),
      label: "Active classes",
      description: "Enrolled laboratory sections",
      progress: activeClassesCount > 0 ? 100 : 0,
      color: "#10b981", 
    },
    {
      value: reviewQueue.length.toString(),
      label: "Pending Reviews",
      description: "Submissions awaiting grade",
      progress: reviewQueue.length > 0 ? 100 : 0,
      color: "#3b82f6",
    },
    {
      value: activitiesAuthoredCount.toString(),
      label: "Activities authored",
      description: "Published programming labs",
      progress: activitiesAuthoredCount > 0 ? 100 : 0,
      color: "#f59e0b",
    },
    {
      value: "0%",
      label: "Submission compliance",
      description: "Passing automated test thresholds",
      progress: 0,
      color: "#a78bfa",
    },
  ], [activeClassesCount, activitiesAuthoredCount]);

  // Map activities to UI format
  const auditLogs = useMemo(() => {
    return reviewQueue.slice(0, 5).map((sub) => {
      const time = new Date(sub.submitted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      return {
        id: sub.sub_id,
        message: `New submission from ${sub.student?.name || 'Unknown'} for ${sub.activity?.title || 'Unknown'}`,
        time: time,
        type: "submission"
      };
    });
  }, [reviewQueue]);

  const mappedActivities = useMemo(() => {
    return activities.map((act) => {
      // Find associated class
      const cls = classes.find(c => c.class_id === act.class_id);
      
      // Determine status
      let status = "in_progress";
      let actionLabel = "Manage";
      let dueLabel = "No deadline";

      if (act.due_at) {
        const dueDate = new Date(act.due_at);
        const now = new Date();
        dueLabel = `Due ${dueDate.toLocaleDateString()}`;
        
        if (dueDate < now) {
          status = "submitted";
          actionLabel = "View Roster";
          dueLabel = "Grading closed";
        } else if (dueDate.toDateString() === now.toDateString()) {
          status = "due_today";
          actionLabel = "Grade Bench";
          dueLabel = "Due today";
        }
      }

      if (!act.is_published) {
         dueLabel = "Draft";
      }

      return {
        id: act.task_id,
        title: act.title,
        courseCode: cls ? `${cls.subject_code} - ${cls.section}` : "Global",
        dueLabel,
        status,
        progress: act.is_published ? 50 : 0, // Placeholder progress
        note: act.is_published ? "Published to students." : "Currently hidden from students.",
        actionLabel,
      };
    });
  }, [activities, classes]);

  const activeActivitiesCount = mappedActivities.filter((a) => a.status !== "submitted").length;

  const handleOpenActivity = (activity) => {
    // This now correctly routes to the ClassRosterView we just added to App.jsx!
    if (activity.status === "submitted") {
      navigate(`/instructor/classes/${activity.id}`);
      return;
    }
    navigate(`/instructor/submissions?activity=${activity.id}`);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white select-none">
      <InstructorSidebar />

      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
            

            <div className="mx-auto max-w-6xl">
              <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="mb-1 font-mono text-xs text-emerald-400">
                    MANAGEMENT
                  </p>
                  <h1 className="text-2xl font-bold">
                    {getGreeting()}, {getFirstName(instructorName)}
                  </h1>
                  <p className="mt-1 text-sm text-white/40">
                    You have {activeActivitiesCount} active laboratory activities and active live sessions running.
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <button 
                    onClick={() => setIsCreateModalOpen(true)}
                    className="whitespace-nowrap rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-emerald-500"
                  >
                    + Create Class
                  </button>
                  <span className="whitespace-nowrap rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-[11px] font-medium text-emerald-300">
                    Faculty Portal
                  </span>
                  <div
                    className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-600 text-xs font-bold"
                    aria-label={`Signed in as ${instructorName}`}
                  >
                    {instructorName.split(/\s+/).map((p) => p[0]?.toUpperCase()).join("").slice(0, 2)}
                  </div>
                </div>
              </header>

              <section className="mb-6 rounded-xl border border-emerald-500/20 bg-emerald-500/[0.07] px-4 py-3">
                <p className="text-xs leading-relaxed text-emerald-200/80">
                  Faculty Control Center: Real-time AST compliance flags, execution metrics, and monitoring controls are active. Official student records sync automatically.
                </p>
              </section>

              <section className="mb-8 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Faculty summary metrics">
                {dynamicStats.map((stat, index) => (
                  <article
                    key={stat.label}
                    className="dashboard-card rounded-xl border border-white/[0.06] bg-[#1a1d27] p-4"
                    style={{ animation: `dashboardFadeUp 400ms ease ${index * 70}ms both` }}
                  >
                    <p className="mb-1 text-3xl font-bold" style={{ color: stat.color }}>
                      {stat.value}
                    </p>
                    <h2 className="text-xs font-medium text-white/70">{stat.label}</h2>
                    <p className="mb-3 text-[10px] text-white/30">{stat.description}</p>
                    <div className="h-1 overflow-hidden rounded-full bg-white/[0.06]">
                      <div className="h-full rounded-full" style={{ width: `${stat.progress}%`, backgroundColor: stat.color }} />
                    </div>
                  </article>
                ))}
              </section>

              <section>
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-semibold">Managed Activities</h2>
                    <p className="mt-1 text-[11px] text-white/30">Review submissions, grade outputs, or update parameters.</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => navigate("/instructor/activities")}
                    className="text-xs text-emerald-400 transition-colors hover:text-emerald-300"
                  >
                    Author new activity
                  </button>
                </div>

                <div className="space-y-3">
                  {isLoading ? (
                    <div className="flex h-32 items-center justify-center rounded-xl border border-white/[0.06] bg-[#1a1d27]">
                      <p className="text-sm text-white/40">Loading activities...</p>
                    </div>
                  ) : error ? (
                    <div className="flex h-32 items-center justify-center rounded-xl border border-red-500/20 bg-red-500/10">
                      <p className="text-sm text-red-400">{error}</p>
                    </div>
                  ) : mappedActivities.length === 0 ? (
                    <div className="flex h-32 flex-col items-center justify-center rounded-xl border border-white/[0.06] bg-[#1a1d27]">
                      <p className="text-sm text-white/40">No activities found.</p>
                      <button 
                        onClick={() => navigate("/instructor/activities")}
                        className="mt-2 text-xs text-emerald-400 hover:text-emerald-300"
                      >
                        Create your first activity
                      </button>
                    </div>
                  ) : mappedActivities.map((activity, index) => {
                    const status = STATUS_CONFIG[activity.status] ?? STATUS_CONFIG.in_progress;
                    return (
                      <article
                        key={activity.id}
                        className={`dashboard-card rounded-xl border border-l-[3px] border-white/[0.06] bg-[#1a1d27] p-4 ${status.accentClass}`}
                        style={{ animation: `dashboardFadeUp 400ms ease ${200 + index * 70}ms both` }}
                      >
                        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                          <div className="min-w-0 flex-1">
                            <div className="mb-1 flex flex-wrap items-center gap-2">
                              <h3 className="text-sm font-semibold">{activity.title}</h3>
                              <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${status.badgeClass}`}>
                                {status.label}
                              </span>
                            </div>
                            <div className="mb-3 flex flex-wrap items-center gap-3 text-[11px] text-white/35">
                              <span>{activity.courseCode}</span>
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
                            onClick={() => handleOpenActivity(activity)}
                            className={`shrink-0 rounded-lg px-3 py-1.5 text-xs font-semibold transition duration-150 hover:-translate-y-px active:translate-y-0 active:scale-[0.98] ${status.buttonClass}`}
                          >
                            {activity.actionLabel}
                          </button>
                        </div>

                        <div className="mt-3 flex items-center gap-3">
                          <span className="shrink-0 text-[10px] text-white/30">Completion Rate</span>
                          <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
                            <div className={`h-full rounded-full ${status.progressClass}`} style={{ width: `${activity.progress}%` }} />
                          </div>
                          <span className="shrink-0 text-[10px] text-white/40">{activity.progress}%</span>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </section>
            </div>
          </main>

          <aside className="hidden w-[300px] shrink-0 overflow-y-auto border-l border-white/[0.06] px-5 py-6 xl:block">
            {/* Sidebar content omitted for brevity, it remains identical to before */}
            <section className="mb-6">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-xs font-semibold">Live Monitoring Feed</h2>
                  <p className="mt-1 text-[10px] text-white/30">Active lab session activity</p>
                </div>
                <button
                  type="button"
                  onClick={() => navigate("/instructor/monitoring")}
                  className="text-[10px] text-emerald-400 transition-colors hover:text-emerald-300"
                >
                  Live View
                </button>
              </div>

              <div className="flex flex-col items-center rounded-xl border border-white/[0.06] bg-[#1a1d27] px-4 py-6">
                <div className="relative h-32 w-32">
                  <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90" aria-label="Class online 88 percent">
                    <circle cx="60" cy="60" r="48" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
                    <circle cx="60" cy="60" r="48" fill="none" stroke="#10b981" strokeWidth="10" strokeLinecap="round" strokeDasharray={`${Math.min(reviewQueue.length * 10, 301.59)} 301.59`} />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-bold">{reviewQueue.length}</span>
                    <span className="text-[10px] text-white/30">new</span>
                  </div>
                </div>
                <p className="mt-3 text-sm font-semibold">Submissions Active</p>
                <p className="mt-1 text-center text-[10px] leading-relaxed text-white/35">
                  Recent activities in your lab sessions.
                </p>
              </div>
            </section>

            <div className="mb-5 h-px bg-white/[0.06]" />

            <section>
              <h2 className="mb-4 text-xs font-semibold">System Audit Trail</h2>
              <ul className="space-y-4">
                {auditLogs.map((item) => (
                  <li key={item.id} className="flex items-start gap-2.5">
                    <span
                      className="mt-1 h-2 w-2 shrink-0 rounded-full"
                      style={{ backgroundColor: getActivityColor(item.type) }}
                      aria-hidden="true"
                    />
                    <div>
                      <p className="text-[11px] leading-snug text-white/60">{item.message}</p>
                      <p className="mt-0.5 text-[10px] text-white/25">{item.time}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          </aside>
        </div>
      </div>

      <CreateClassModal 
        isOpen={isCreateModalOpen} 
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={() => {
          console.log("Class created successfully!");
          fetchDashboardData();
        }}
      />
    </div>
  );
}