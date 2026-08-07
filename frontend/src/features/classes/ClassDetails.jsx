import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../../services/api";
import { useAuth } from "../../features/auth/AuthContext";

import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";



function ArrowLeftIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
  );
}

function ClockIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
  );
}

function MegaphoneIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="m3 11 18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/></svg>
  );
}

export default function ClassDetails() {
  const { id } = useParams();
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

  const [isLoading, setIsLoading] = useState(true);
  const [classroom, setClassroom] = useState(null);
  const [activities, setActivities] = useState([]);
  const [totalActivitiesCount, setTotalActivitiesCount] = useState(0);
  const [membersCount, setMembersCount] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [classRes, activityRes, membersRes] = await Promise.all([
          api.get("/classrooms/mine"),
          api.get("/activities/"),
          api.get(`/classrooms/${id}/members`).catch(() => [])
        ]);
        
        const currentClass = classRes.find(c => String(c.classroom.class_id) === String(id));
        if (currentClass) {
          setClassroom(currentClass.classroom);
        }
        
        // Members count includes instructor + students (or just students). We can just show the total array length.
        setMembersCount(membersRes.length);

        const activeCount = activityRes.filter(task => {
          if (!task.due_at) return true;
          return new Date(task.due_at) >= new Date();
        }).length;
        setTotalActivitiesCount(activeCount);

        const classActivities = activityRes
          .filter(task => String(task.class_id) === String(id))
          .map(task => {
            const due = task.due_at ? new Date(task.due_at) : null;
            let status = "in_progress";
            let dueLabel = "No due date";
            if (due) {
              dueLabel = `Due: ${due.toLocaleDateString()}`;
              if (due < new Date()) {
                status = "submitted";
                dueLabel = "Submission closed";
              }
            }
            return {
              id: task.task_id,
              title: task.title,
              dueLabel: dueLabel,
              status: status,
              note: task.activity_type === "laboratory" ? "Laboratory activity" : "Homework",
              actionLabel: status === "submitted" ? "View" : "Open",
            };
          });

        setActivities(classActivities);

      } catch (err) {
        console.error("Failed to load class details", err);
        // Fallback preview
        if (!classroom) {
          setClassroom({
            class_id: id,
            subject_code: "CCS101",
            subject_name: "Computer Programming 1",
            instructor_name: "Dr. Maria Santos",
            section: "BSCS-1A",
          });
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [id]);

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
        assignmentCount={totalActivitiesCount}
      />

      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
            <div className="mx-auto max-w-6xl">
              
              <button 
                onClick={() => navigate("/student/classes")}
                className="mb-6 flex items-center gap-2 text-sm text-white/50 hover:text-white transition-colors"
              >
                <ArrowLeftIcon className="h-4 w-4" />
                Back to My Classes
              </button>

              {isLoading ? (
                <div className="animate-pulse">
                  <div className="h-24 w-full bg-[#1a1d27] rounded-xl border border-white/[0.06] mb-8"></div>
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2 h-64 bg-[#1a1d27] rounded-xl border border-white/[0.06]"></div>
                    <div className="h-64 bg-[#1a1d27] rounded-xl border border-white/[0.06]"></div>
                  </div>
                </div>
              ) : !classroom ? (
                <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-white/[0.1] bg-white/[0.02] py-20 px-6 text-center">
                  <h3 className="text-lg font-semibold text-white">Classroom Not Found</h3>
                  <p className="mt-2 text-sm text-white/40 mb-6">
                    We couldn't find the details for this classroom. You may not be enrolled.
                  </p>
                </div>
              ) : (
                <>
                  <header className="mb-8 relative overflow-hidden rounded-xl border border-blue-500/20 bg-[#1a1d27] p-8">
                    <div className="absolute top-0 right-0 p-16 opacity-5 pointer-events-none">
                      <MegaphoneIcon className="w-64 h-64 text-blue-500 transform rotate-[-15deg] translate-x-12 -translate-y-12" />
                    </div>
                    <div className="relative z-10">
                      <div className="mb-3 flex flex-wrap items-center gap-3">
                        <span className="inline-flex items-center rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-sm font-semibold text-blue-400">
                          {classroom.subject_code}
                        </span>
                        <span className="rounded-full border border-white/[0.1] bg-white/[0.03] px-3 py-1 text-sm font-medium text-white/70">
                          {classroom.section}
                        </span>
                      </div>
                      <h1 className="text-3xl font-bold text-white mb-2">{classroom.subject_name || "Classroom"}</h1>
                      {classroom.instructor_name && (
                        <p className="text-sm font-medium text-white/50">
                          Instructor: <span className="text-white/80">{classroom.instructor_name}</span>
                        </p>
                      )}
                    </div>
                  </header>

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left Column: Activities */}
                    <div className="lg:col-span-2 space-y-4">
                      <h2 className="text-lg font-semibold mb-4 border-b border-white/[0.06] pb-3">Class Activities</h2>
                      {activities.length === 0 ? (
                        <div className="rounded-xl border border-white/[0.06] bg-[#1a1d27]/50 p-8 text-center">
                          <p className="text-sm text-white/40">No activities assigned for this class yet.</p>
                        </div>
                      ) : (
                        activities.map((activity, index) => {
                          const isSubmitted = activity.status === "submitted";
                          return (
                            <div
                              key={activity.id}
                              className="group flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-white/[0.06] bg-[#1a1d27] p-5 hover:border-blue-500/30 transition-all duration-300"
                              style={{ animation: `dashboardFadeUp 400ms ease ${index * 70}ms both` }}
                            >
                              <div className="min-w-0">
                                <div className="flex items-center gap-3 mb-1">
                                  <h3 className="text-base font-semibold truncate">{activity.title}</h3>
                                  {isSubmitted ? (
                                    <span className="shrink-0 rounded-full border border-green-500/30 bg-green-500/10 px-2 py-0.5 text-[10px] font-semibold text-green-400">Submitted</span>
                                  ) : (
                                    <span className="shrink-0 rounded-full border border-blue-500/30 bg-blue-500/10 px-2 py-0.5 text-[10px] font-semibold text-blue-400">Active</span>
                                  )}
                                </div>
                                <div className="flex items-center gap-3 text-xs text-white/40">
                                  <span className="flex items-center gap-1.5"><ClockIcon className="h-3 w-3" /> {activity.dueLabel}</span>
                                  <span className="text-white/20">•</span>
                                  <span>{activity.note}</span>
                                </div>
                              </div>
                              <button
                                onClick={() => handleOpenActivity(activity)}
                                className={`shrink-0 rounded-lg px-4 py-2 text-sm font-semibold transition ${isSubmitted ? "border border-blue-500/40 text-blue-400 hover:bg-blue-500/10" : "bg-blue-600 text-white hover:bg-blue-500"}`}
                              >
                                {activity.actionLabel}
                              </button>
                            </div>
                          );
                        })
                      )}
                    </div>

                    {/* Right Column: Static Announcements */}
                    <div className="space-y-4">
                      <h2 className="text-lg font-semibold mb-4 border-b border-white/[0.06] pb-3">Announcements</h2>
                      <div className="rounded-xl border border-amber-500/20 bg-amber-500/[0.03] p-5 relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-1 h-full bg-amber-500/50"></div>
                        <div className="flex items-start gap-3 mb-3">
                          <MegaphoneIcon className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
                          <div>
                            <h3 className="text-sm font-semibold text-white">Welcome to the class!</h3>
                            <p className="text-[10px] text-white/40 mt-0.5">Posted by {classroom.instructor_name || "Instructor"}</p>
                          </div>
                        </div>
                        <p className="text-xs leading-relaxed text-white/70">
                          Welcome to the laboratory component! All coding activities for this course will be completed and graded here. Make sure to check the active assignments board regularly. Good luck!
                        </p>
                      </div>
                      
                      <div className="rounded-xl border border-white/[0.06] bg-[#1a1d27]/50 p-5">
                        <h3 className="text-sm font-semibold text-white mb-2">Class Information</h3>
                        <div className="space-y-2 mt-4">
                          <div className="flex justify-between text-xs">
                            <span className="text-white/40">Class ID</span>
                            <span className="font-mono text-white/80">{classroom.class_id}</span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-white/40">Instructor</span>
                            <span className="text-white/80">{classroom.instructor_name}</span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-white/40">Classmates</span>
                            <span className="text-white/80">{membersCount > 0 ? membersCount - 1 : 0} student{membersCount - 1 === 1 ? '' : 's'}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                  </div>
                </>
              )}
            </div>
          </main>
        </div>

        <Statusbar
          courseCode={user.courseCode}
          courseName={user.courseName}
          studentName={user.name}
        />
      </div>
    </div>
  );
}
