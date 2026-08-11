import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";
import { useAuth } from "../../features/auth/AuthContext";

import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";

function BookOpenIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
  );
}

function CodeIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
  );
}

export default function SoloPractice() {
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
  const [practiceActivities, setPracticeActivities] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchPracticeActivities = async () => {
      try {
        // Fetch all activities across all enrolled classes
        const activitiesRes = await api.get("/activities/");
        
        // Filter out graded activities to only show practice modules
        const practices = activitiesRes.filter(task => task.is_graded === false);
        setPracticeActivities(practices);
      } catch (err) {
        console.error("Failed to load practice activities:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPracticeActivities();
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main">
      <div className="hidden lg:flex h-full">
        <Sidebar user={user} activeItem="Solo Practice" />
      </div>

      <div className="flex min-w-0 flex-1 flex-col animate-page-fade">
        <main className="flex-1 overflow-y-auto px-6 py-6 sm:px-8">
          <div className="w-full">
            <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-border-subtle pb-6">
              <div>
                <h1 className="text-2xl font-bold flex items-center gap-3">
                  <CodeIcon className="h-6 w-6 text-violet-500" />
                  Solo Practice
                </h1>
                <p className="mt-1 text-sm text-text-muted">
                  Independent coding sandbox for practice lessons and ungraded modules. AST structural analysis is fully supported.
                </p>
              </div>
            </header>

            {isLoading ? (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex flex-col overflow-hidden rounded-2xl border border-white/[0.05] bg-bg-glass p-6 animate-pulse">
                    <div className="mb-4 h-10 w-10 rounded-xl bg-white/[0.05]"></div>
                    <div className="mb-2 h-6 w-3/4 rounded-md bg-white/[0.05]"></div>
                    <div className="mb-6 h-4 w-full rounded-md bg-white/[0.05]"></div>
                    <div className="mt-auto border-t border-white/[0.05] pt-4">
                      <div className="h-4 w-1/2 rounded-md bg-white/[0.05]"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : practiceActivities.length > 0 ? (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {practiceActivities.map((activity) => (
                  <div
                    key={activity.task_id}
                    onClick={() => navigate(`/student/workspace?activity=${activity.task_id}`)}
                    className="group relative flex cursor-pointer flex-col overflow-hidden rounded-2xl border border-white/[0.05] bg-bg-glass p-6 transition-all hover:-translate-y-1 hover:border-violet-500/30 hover:bg-violet-500/[0.04] hover:shadow-2xl hover:shadow-violet-500/10"
                  >
                    <div className="absolute -right-10 -top-10 opacity-5 transition-opacity group-hover:opacity-20">
                      <CodeIcon className="h-40 w-40 text-violet-500" />
                    </div>

                    <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/20 text-text-violet">
                      <BookOpenIcon className="h-5 w-5" />
                    </div>
                    
                    <h3 className="mb-2 text-lg font-semibold text-text-main/90 line-clamp-2">
                      {activity.title}
                    </h3>
                    
                    <p className="mb-6 flex-1 text-sm text-text-muted line-clamp-3">
                      {activity.description || "No description provided."}
                    </p>
                    
                    <div className="mt-auto flex items-center justify-between border-t border-white/[0.05] pt-4">
                      <span className="text-xs font-medium text-text-muted">
                        {activity.activity_type === "laboratory" ? "Laboratory Practice" : "Homework Practice"}
                      </span>
                      <button className="text-xs font-semibold text-text-violet opacity-0 transition-opacity group-hover:opacity-100">
                        Start Coding &rarr;
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border-subtle bg-white/[0.01] px-6 py-24 text-center transition-all hover:bg-bg-glass">
                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-violet-500/10 text-text-violet ring-4 ring-violet-500/5">
                  <CodeIcon className="h-8 w-8" />
                </div>
                <h3 className="mb-2 text-xl font-semibold text-text-main/90">No Practice Modules Yet</h3>
                <p className="max-w-md text-sm text-text-muted">
                  You don't have any practice lessons available at the moment. When instructors publish ungraded modules in your classes, they will appear here.
                </p>
              </div>
            )}
          </div>
        </main>

        <Statusbar
          sessionStatus="unknown"
          studentName={userName}
          pythonVersion="Python 3"
        />
      </div>
    </div>
  );
}
