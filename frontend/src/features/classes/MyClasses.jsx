import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
function UsersIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
  );
}

function PlusIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
  );
}

function BookOpenIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
  );
}

function ChevronRightIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><polyline points="9 18 15 12 9 6"/></svg>
  );
}
import api from "../../services/api";
import { useAuth } from "../../features/auth/AuthContext";

import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";
import JoinClassModal from "../../components/modals/JoinClassModal";



export default function MyClasses() {
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
  const [isLoading, setIsLoading] = useState(true);

  // We fetch dashboard data to get the accurate assignmentCount for Sidebar, and the classrooms
  const [activeActivitiesCount, setActiveActivitiesCount] = useState(0);

  const fetchClassesData = async () => {
    setIsLoading(true);
    try {
      const [classRes, activityRes] = await Promise.all([
        api.get("/classrooms/mine"),
        api.get("/activities/")
      ]);
      
      // Parse activities to get active count
      const activeCount = activityRes.filter(task => {
        if (!task.due_at) return true; // no due date = active
        return new Date(task.due_at) >= new Date(); // not past due
      }).length;
      
      setActiveActivitiesCount(activeCount);
      setClassrooms(classRes);
    } catch (err) {
      console.error("Failed to load classes data", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchClassesData();
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white">
      <Sidebar
        user={{
          name: user.name,
          initials: user.initials,
          role: "Student",
          course: user.courseCode,
        }}
        assignmentCount={activeActivitiesCount}
      />

      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-6 py-6 sm:px-8">
            <div className="w-full">
              
              <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-white/[0.06] pb-6">
                <div>
                  <h1 className="text-2xl font-bold flex items-center gap-3">
                    <UsersIcon className="h-6 w-6 text-blue-500" />
                    My Classes
                  </h1>
                  <p className="mt-1 text-sm text-white/40">
                    View your enrolled classrooms and access specific lab activities.
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setIsJoinModalOpen(true)}
                    className="flex items-center gap-2 rounded-lg bg-[#3b82f6] px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-[#2563eb]"
                  >
                    <PlusIcon className="h-4 w-4" />
                    Join a Class
                  </button>
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-full bg-[#1a1d27] border border-white/[0.06] text-xs font-bold shadow-sm"
                  >
                    {user.initials}
                  </div>
                </div>
              </header>

              <div className="space-y-6">
                {isLoading ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="flex flex-col rounded-xl border border-white/[0.06] bg-[#1a1d27] p-6 animate-pulse">
                        <div className="mb-4 h-5 w-16 bg-white/[0.06] rounded-full"></div>
                        <div className="mb-2 h-6 w-3/4 bg-white/[0.06] rounded-md"></div>
                        <div className="mb-6 h-4 w-1/2 bg-white/[0.06] rounded-md"></div>
                        <div className="mt-auto border-t border-white/[0.06] pt-4 flex gap-2">
                          <div className="h-6 w-1/3 bg-white/[0.06] rounded-md"></div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : classrooms.length === 0 ? (
                  <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/[0.1] bg-white/[0.01] py-24 px-6 text-center transition-all hover:bg-white/[0.02]">
                    <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-500/10 mb-4 ring-4 ring-blue-500/5 text-blue-400">
                      <BookOpenIcon className="h-8 w-8" />
                    </div>
                    <h3 className="text-xl font-semibold text-white/90">No Active Classes</h3>
                    <p className="mt-2 max-w-md text-sm text-white/50 mb-6">
                      You haven't joined any classrooms yet. Use the 6-character code provided by your instructor to join one.
                    </p>
                    <button
                      onClick={() => setIsJoinModalOpen(true)}
                      className="rounded-lg bg-[#1a1d27] border border-white/[0.1] px-6 py-2.5 text-sm font-medium hover:bg-white/[0.05] transition"
                    >
                      Enter class code
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {classrooms.map((cls, idx) => (
                      <div 
                        key={cls.classroom.class_id || idx}
                        onClick={() => navigate(`/student/classes/${cls.classroom.class_id}`)}
                        className="group relative flex flex-col rounded-xl border border-white/[0.08] bg-[#1a1d27] hover:border-blue-500/30 hover:bg-[#1f2330] hover:shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:-translate-y-1 transition-all duration-300 overflow-hidden cursor-pointer cursor-pointer"
                        style={{
                          animation: `dashboardFadeUp 400ms ease ${idx * 70}ms both`,
                        }}
                      >
                        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                        
                        <div className="p-6 flex-1">
                          <div className="flex justify-between items-start mb-4">
                            <span className="inline-flex items-center rounded-full border border-blue-500/20 bg-blue-500/10 px-2.5 py-0.5 text-xs font-medium text-blue-400">
                              {cls.classroom.subject_code}
                            </span>
                          </div>
                          
                          <h3 className="text-lg font-bold text-white mb-1 line-clamp-1">
                            {cls.classroom.subject_name || 'Classroom'}
                          </h3>
                          
                          <div className="flex items-center gap-2 mb-6">
                            <span className="text-sm font-medium text-white/70">
                              {cls.classroom.section}
                            </span>
                            {cls.classroom.instructor_name && (
                              <>
                                <span className="text-white/20">•</span>
                                <span className="text-sm text-white/50">
                                  {cls.classroom.instructor_name}
                                </span>
                              </>
                            )}
                          </div>
                          
                          <div className="flex items-center gap-4 border-t border-white/[0.06] pt-4 mt-auto">
                            <div className="flex flex-col">
                              <span className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Status</span>
                              <span className="text-xs font-medium text-emerald-400 flex items-center gap-1.5">
                                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
                                Enrolled
                              </span>
                            </div>
                            <div className="h-6 w-px bg-white/[0.06]"></div>
                            <div className="flex flex-col">
                              <span className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Joined</span>
                              <span className="text-xs font-medium text-white/60">
                                {cls.joined_at ? new Date(cls.joined_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric'}) : 'Recently'}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </main>
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
          fetchClassesData();
        }}
      />
    </div>
  );
}
