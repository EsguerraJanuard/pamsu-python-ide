import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";
import { useAuth } from "../../features/auth/AuthContext";

import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";

function CodeIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
  );
}

function LockIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
  );
}

function UnlockIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/></svg>
  );
}

function CheckIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><polyline points="20 6 9 17 4 12"/></svg>
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
    courseCode: "Solo Practice",
    courseName: "",
  };
  
  const [modules, setModules] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchModules = async () => {
      try {
        const response = await api.get("/practice/modules");
        // Ensure response is an array before setting to prevent crash on 404 HTML responses
        if (Array.isArray(response)) {
          setModules(response);
        } else {
          console.error("Expected array but got:", typeof response);
          setModules([]);
        }
      } catch (err) {
        console.error("Failed to load practice modules:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchModules();
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main transition-colors duration-200">
      <div className="hidden lg:flex h-full">
        <Sidebar user={user} activeItem="Solo Practice" />
      </div>

      <div className="flex min-w-0 flex-1 flex-col animate-page-fade">
        <main className="flex-1 overflow-y-auto px-6 py-6 sm:px-8">
          <div className="mx-auto w-full max-w-5xl">
            <header className="mb-8 flex flex-col gap-4 border-b border-border-subtle pb-6">
              <div>
                <h1 className="text-3xl font-bold flex items-center gap-3">
                  <CodeIcon className="h-8 w-8 text-violet-500" />
                  Solo Practice Modules
                </h1>
                <p className="mt-2 text-sm text-text-muted">
                  Learn Python from the ground up. Complete modules sequentially to unlock the next levels.
                </p>
              </div>
            </header>

            {isLoading ? (
              <div className="flex justify-center py-20">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-border-subtle border-t-violet-500"></div>
              </div>
            ) : modules.length > 0 ? (
              <div className="space-y-12 pb-20">
                {modules.map((mod, index) => (
                  <section key={mod.module_id} className="relative">
                    {/* Connecting line between modules */}
                    {index !== modules.length - 1 && (
                      <div className="absolute left-[23px] top-[40px] bottom-[-48px] w-0.5 bg-border-subtle z-0"></div>
                    )}
                    
                    <div className="relative z-10 flex flex-col sm:flex-row gap-6">
                      {/* Module Icon Indicator */}
                      <div className={`shrink-0 flex h-12 w-12 items-center justify-center rounded-full border-4 border-bg-base shadow-sm
                        ${mod.is_completed ? "bg-emerald-500 text-white" : mod.is_locked ? "bg-bg-alt text-text-muted border-border-subtle" : "bg-violet-500 text-white"}`}
                      >
                        {mod.is_completed ? <CheckIcon className="h-6 w-6" /> : mod.is_locked ? <LockIcon className="h-5 w-5" /> : <UnlockIcon className="h-5 w-5" />}
                      </div>

                      {/* Module Content */}
                      <div className={`flex-1 rounded-2xl border p-6 transition-all duration-300
                        ${mod.is_locked ? "border-border-subtle bg-bg-base opacity-70" : "border-border-subtle bg-bg-glass shadow-sm hover:shadow-md"}`}
                      >
                        <h2 className="text-xl font-bold mb-2 flex items-center justify-between">
                          <span>Module {index + 1}: {mod.title}</span>
                          {mod.is_completed && <span className="text-xs font-semibold uppercase tracking-wider text-emerald-500 bg-emerald-500/10 px-3 py-1 rounded-full">Completed</span>}
                        </h2>
                        <p className="text-sm text-text-muted mb-6">{mod.description}</p>
                        
                        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                          {mod.tasks.map((task, tIndex) => (
                            <button
                              key={task.task_id}
                              disabled={task.is_locked}
                              onClick={() => navigate(`/student/practice/workspace?task=${task.task_id}`)}
                              className={`flex flex-col text-left items-start gap-2 rounded-xl border p-4 transition-all
                                ${task.is_completed 
                                  ? "border-emerald-500/30 bg-emerald-500/[0.03] hover:bg-emerald-500/[0.06]" 
                                  : task.is_locked 
                                    ? "border-border-subtle bg-bg-base cursor-not-allowed opacity-60" 
                                    : "border-border-subtle bg-bg-base hover:border-violet-500/40 hover:bg-violet-500/[0.04]"
                                }`}
                            >
                              <div className="flex w-full items-center justify-between">
                                <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                                  Task {tIndex + 1}
                                </span>
                                {task.is_completed ? (
                                  <CheckIcon className="h-4 w-4 text-emerald-500" />
                                ) : task.is_locked ? (
                                  <LockIcon className="h-4 w-4 text-text-muted" />
                                ) : (
                                  <CodeIcon className="h-4 w-4 text-violet-500" />
                                )}
                              </div>
                              <span className={`font-medium line-clamp-1 ${task.is_locked ? 'text-text-muted' : 'text-text-main'}`}>
                                {task.title}
                              </span>
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </section>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border-subtle py-24 text-center">
                <CodeIcon className="mb-4 h-12 w-12 text-text-muted opacity-50" />
                <h3 className="mb-2 text-xl font-semibold">No Modules Available</h3>
                <p className="text-sm text-text-muted">Practice modules have not been seeded yet.</p>
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
