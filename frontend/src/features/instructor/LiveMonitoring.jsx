import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import InstructorSidebar from "../../components/layout/InstructorSidebar";

const LiveMonitoring = () => {
  const [mode, setMode] = useState('global'); // 'global' or 'task'
  const [taskIdInput, setTaskIdInput] = useState('');
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [classrooms, setClassrooms] = useState([]);
  const [selectedClassroom, setSelectedClassroom] = useState('All');

  useEffect(() => {
    const fetchClassrooms = async () => {
      try {
        const response = await api.get('/classrooms');
        setClassrooms(Array.isArray(response) ? response : response.items || []);
      } catch (err) {
        console.error('Error fetching classrooms:', err);
      }
    };
    fetchClassrooms();
  }, []);

  useEffect(() => {
    let intervalId;

    const fetchSessions = async () => {
      if (mode === 'task' && !activeTaskId) {
        setSessions([]);
        return;
      }
      
      try {
        const url = mode === 'global' 
          ? `/instructors/coding-sessions/live`
          : `/instructors/tasks/${activeTaskId}/coding-sessions`;
          
        const response = await api.get(url);
        // Handle both possible wrapper object or direct array
        const data = response?.sessions || response || [];
        setSessions(Array.isArray(data) ? data : []);
        setError(null);
      } catch (err) {
        console.error('Error fetching sessions:', err);
        setError(`Failed to fetch coding sessions. ${mode === 'task' ? 'Please check the Task ID.' : ''}`);
      }
    };

    if (mode === 'global' || (mode === 'task' && activeTaskId)) {
      setLoading(true);
      fetchSessions().finally(() => setLoading(false));
      intervalId = setInterval(fetchSessions, 5000);
    } else {
      setSessions([]);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [mode, activeTaskId]);

  const handleMonitor = (e) => {
    e.preventDefault();
    if (taskIdInput.trim()) {
      setActiveTaskId(taskIdInput.trim());
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
      <InstructorSidebar />
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
                        
            <div className="mx-auto max-w-6xl ">

        <div className="w-full">
          <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="mb-1 font-mono text-xs text-text-emerald">MONITORING & GRADING</p>
              <h1 className="text-2xl font-bold">Live Monitoring</h1>
              <p className="mt-1 text-sm text-text-muted">
                Monitor real-time student activity and execution metrics.
              </p>
            </div>
            
            <div className="flex flex-col items-end gap-3">
              <div className="flex bg-bg-glass rounded-lg p-1 border border-border-subtle">
                <button
                  onClick={() => setMode('global')}
                  className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors ${mode === 'global' ? 'bg-emerald-500/20 text-text-emerald' : 'text-text-muted hover:text-text-main'}`}
                >
                  All Active Students
                </button>
                <button
                  onClick={() => setMode('task')}
                  className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors ${mode === 'task' ? 'bg-emerald-500/20 text-text-emerald' : 'text-text-muted hover:text-text-main'}`}
                >
                  Specific Task
                </button>
              </div>
              
              <div className="flex items-center gap-3">
                {mode === 'global' && (
                  <select
                    value={selectedClassroom}
                    onChange={(e) => setSelectedClassroom(e.target.value)}
                    className="bg-bg-base border border-border-subtle text-text-main text-sm font-medium rounded-lg px-4 py-1.5 focus:outline-none focus:border-emerald-500 transition-colors"
                  >
                    <option value="All">All Classrooms</option>
                    {classrooms.map((c) => (
                      <option key={c.class_id || c.name} value={c.name}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                )}

                {(mode === 'global' || activeTaskId) && (
                  <div className="flex items-center gap-2 text-sm text-text-emerald bg-green-400/10 px-3 py-1.5 rounded-full border border-green-400/20">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    Live Updates Active
                  </div>
                )}
              </div>
            </div>
          </header>
        
        {mode === 'task' && (
          <div className="bg-bg-glass p-6 rounded-xl border border-border-subtle mb-8 shadow-sm">
            <form onSubmit={handleMonitor} className="flex gap-4 items-end">
              <div className="flex-1 max-w-md">
                <label htmlFor="taskId" className="block text-sm font-medium text-text-muted mb-2">
                  Task ID to Monitor
                </label>
                <input
                  type="text"
                  id="taskId"
                  value={taskIdInput}
                  onChange={(e) => setTaskIdInput(e.target.value)}
                  className="w-full bg-bg-base border border-border-subtle rounded-lg px-4 py-2.5 text-text-main focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                  placeholder="Enter Task ID (e.g., 123)"
                />
              </div>
              <button
                type="submit"
                disabled={!taskIdInput.trim()}
                className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-800/50 disabled:text-text-muted text-white font-semibold py-2.5 px-6 rounded-lg transition-colors"
              >
                Monitor
              </button>
            </form>
          </div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-500/50 text-text-rose p-4 rounded-lg mb-8 flex items-center gap-3">
            <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </div>
        )}

        {loading && !sessions.length && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="bg-bg-glass rounded-xl border border-border-subtle overflow-hidden flex flex-col h-[280px] animate-pulse">
                <div className="bg-bg-glass p-4 flex justify-between items-start border-b border-border-subtle">
                  <div>
                    <div className="h-5 w-24 bg-white/[0.06] rounded-md mb-2"></div>
                    <div className="h-3 w-16 bg-white/[0.06] rounded-md"></div>
                  </div>
                  <div className="h-6 w-16 bg-white/[0.06] rounded-full"></div>
                </div>
                <div className="p-4 flex-1 flex flex-col gap-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="h-3 w-16 bg-white/[0.06] rounded-md mb-1"></div>
                      <div className="h-5 w-12 bg-white/[0.06] rounded-md"></div>
                    </div>
                    <div>
                      <div className="h-3 w-16 bg-white/[0.06] rounded-md mb-1"></div>
                      <div className="h-5 w-12 bg-white/[0.06] rounded-md"></div>
                    </div>
                  </div>
                  <div className="h-3 w-3/4 bg-white/[0.06] rounded-md mt-auto"></div>
                </div>
              </div>
            ))}
          </div>
        )}

        {(() => {
          const filteredSessions = mode === 'global' && selectedClassroom !== 'All' 
            ? sessions.filter(s => s.classroom_name === selectedClassroom)
            : sessions;
          
          return (
            <>
              {(mode === 'global' || (mode === 'task' && activeTaskId)) && !loading && filteredSessions.length === 0 && !error && (
                <div className="flex flex-col items-center justify-center py-20 px-6 text-center rounded-xl border border-border-subtle/50 bg-bg-glass/30">
                  <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-slate-500/10 text-text-muted ring-4 ring-slate-500/5">
                    <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                    </svg>
                  </div>
                  <h3 className="mb-2 text-lg font-semibold text-text-main">No Active Sessions</h3>
                  <p className="text-sm text-text-muted max-w-sm">
                    {mode === 'global' 
                      ? (selectedClassroom === 'All' ? "No students are currently active in any of your classrooms." : `No students are currently active in ${selectedClassroom}.`)
                      : `No students are currently active in Task ${activeTaskId}.`}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredSessions.map((session) => {
            const hasWarning = session.tab_switches > 3;
            
            return (
              <div 
                key={session.id || session.student_id || Math.random()} 
                className={`bg-bg-glass p-5 rounded-xl border transition-all duration-300 flex flex-col relative overflow-hidden ${
                  hasWarning 
                    ? 'border-amber-500/50 bg-amber-900/10 shadow-[0_0_15px_rgba(245,158,11,0.1)]' 
                    : 'border-border-subtle hover:border-border-subtle'
                }`}
              >
                {hasWarning && (
                  <div className="absolute top-0 left-0 w-full h-1 bg-amber-500/70"></div>
                )}
                
                <div className="flex justify-between items-start mb-5">
                  <div className="flex-1 pr-3">
                    <h3 className="text-lg font-semibold text-text-main truncate">
                      {session.student_name || 'Unknown Student'}
                    </h3>
                    {mode === 'global' && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {session.classroom_name && (
                          <span className="inline-flex items-center rounded-md bg-blue-500/10 px-2 py-1 text-xs font-medium text-text-blue ring-1 ring-inset ring-blue-500/20">
                            {session.classroom_name}
                          </span>
                        )}
                        {session.task_title && (
                          <span className="inline-flex items-center rounded-md bg-purple-500/10 px-2 py-1 text-xs font-medium text-text-violet ring-1 ring-inset ring-purple-500/20">
                            {session.task_title}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 mt-1 bg-bg-base px-2 py-1 rounded-xl border border-border-subtle">
                    <span className="text-[10px] font-medium text-text-muted uppercase tracking-wider">
                      {session.is_active ? 'Active' : 'Idle'}
                    </span>
                    <div className={`w-2 h-2 rounded-full ${session.is_active ? 'bg-green-500 shadow-[0_0_5px_rgba(34,197,94,0.5)]' : 'bg-slate-600'}`}></div>
                  </div>
                </div>

                <div className="space-y-4 flex-1">
                  <div className="flex justify-between items-center group">
                    <span className="text-sm text-text-muted flex items-center gap-2 group-hover:text-text-muted transition-colors">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path>
                      </svg>
                      Tab Switches
                    </span>
                    <span className={`font-mono text-lg font-bold ${hasWarning ? 'text-text-amber' : 'text-text-main'}`}>
                      {session.tab_switches || 0}
                    </span>
                  </div>

                  <div className="flex justify-between items-center group">
                    <span className="text-sm text-text-muted flex items-center gap-2 group-hover:text-text-muted transition-colors">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"></path>
                      </svg>
                      Paste Count
                    </span>
                    <span className="font-mono text-lg font-semibold text-text-main">
                      {session.paste_count || 0}
                    </span>
                  </div>
                </div>

                <div className="mt-5 pt-4 border-t border-border-subtle/80">
                  <div className="flex justify-between items-center text-xs text-text-muted">
                    <span className="flex items-center gap-1.5">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Last Heartbeat
                    </span>
                    <span className="font-medium text-text-muted">
                      {session.last_heartbeat 
                        ? new Date(session.last_heartbeat).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) 
                        : 'Never'}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        </>
        );
      })()}
      </div>
                </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default LiveMonitoring;
