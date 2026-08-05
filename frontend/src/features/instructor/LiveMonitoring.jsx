import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import InstructorSidebar from "../../components/layout/InstructorSidebar";

const LiveMonitoring = () => {
  const [taskIdInput, setTaskIdInput] = useState('');
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let intervalId;

    const fetchSessions = async () => {
      if (!activeTaskId) return;
      try {
        const response = await api.get(`/instructors/tasks/${activeTaskId}/coding-sessions`);
        // Handle both possible wrapper object or direct array
        const data = response.data?.sessions || response.data || [];
        setSessions(Array.isArray(data) ? data : []);
        setError(null);
      } catch (err) {
        console.error('Error fetching sessions:', err);
        setError('Failed to fetch coding sessions. Please check the Task ID and try again.');
      }
    };

    if (activeTaskId) {
      setLoading(true);
      fetchSessions().finally(() => setLoading(false));
      intervalId = setInterval(fetchSessions, 5000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [activeTaskId]);

  const handleMonitor = (e) => {
    e.preventDefault();
    if (taskIdInput.trim()) {
      setActiveTaskId(taskIdInput.trim());
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white select-none">
      <InstructorSidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="dashboard-page min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
                        <style>
              {`
                @keyframes dashboardFadeUp {
                  from { opacity: 0; transform: translateY(10px); }
                  to { opacity: 1; transform: translateY(0); }
                }
                .dashboard-page {
                  animation: dashboardFadeUp 450ms cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
                }
                @media (prefers-reduced-motion: reduce) {
                  .dashboard-page, .dashboard-card { animation: none !important; }
                }
              `}
            </style>
            <div className="mx-auto max-w-6xl dashboard-page">

      <div className="w-full">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold">Live Monitoring</h1>
          {activeTaskId && (
            <div className="flex items-center gap-2 text-sm text-green-400 bg-green-400/10 px-3 py-1.5 rounded-full border border-green-400/20">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              Live Updates Active
            </div>
          )}
        </div>
        
        <div className="bg-[#1a1d27] p-6 rounded-xl border border-white/[0.06] mb-8 shadow-sm">
          <form onSubmit={handleMonitor} className="flex gap-4 items-end">
            <div className="flex-1 max-w-md">
              <label htmlFor="taskId" className="block text-sm font-medium text-white/70 mb-2">
                Task ID to Monitor
              </label>
              <input
                type="text"
                id="taskId"
                value={taskIdInput}
                onChange={(e) => setTaskIdInput(e.target.value)}
                className="w-full bg-[#0f1117] border border-white/[0.06] rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                placeholder="Enter Task ID (e.g., 123)"
              />
            </div>
            <button
              type="submit"
              disabled={!taskIdInput.trim()}
              className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-800/50 disabled:text-white/50 text-white font-semibold py-2.5 px-6 rounded-lg transition-colors"
            >
              Monitor
            </button>
          </form>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-500/50 text-red-300 p-4 rounded-lg mb-8 flex items-center gap-3">
            <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </div>
        )}

        {loading && !sessions.length && (
          <div className="text-center py-16">
            <div className="animate-spin rounded-full h-10 w-10 border-2 border-b-transparent border-emerald-500 mx-auto"></div>
            <p className="mt-4 text-white/70 font-medium">Loading session data...</p>
          </div>
        )}

        {activeTaskId && !loading && sessions.length === 0 && !error && (
          <div className="text-center py-16 bg-slate-900/30 rounded-xl border border-white/[0.06]/50 border-dashed">
            <svg className="w-12 h-12 text-slate-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p className="text-white/70 font-medium">No active coding sessions found for Task {activeTaskId}.</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {sessions.map((session) => {
            const hasWarning = session.tab_switches > 3;
            
            return (
              <div 
                key={session.id || session.student_id || Math.random()} 
                className={`bg-[#1a1d27] p-5 rounded-xl border transition-all duration-300 flex flex-col relative overflow-hidden ${
                  hasWarning 
                    ? 'border-amber-500/50 bg-amber-900/10 shadow-[0_0_15px_rgba(245,158,11,0.1)]' 
                    : 'border-white/[0.06] hover:border-white/[0.06]'
                }`}
              >
                {hasWarning && (
                  <div className="absolute top-0 left-0 w-full h-1 bg-amber-500/70"></div>
                )}
                
                <div className="flex justify-between items-start mb-5">
                  <div className="flex-1 pr-3">
                    <h3 className="text-lg font-semibold text-slate-100 truncate">
                      {session.student_name || 'Unknown Student'}
                    </h3>
                  </div>
                  <div className="flex items-center gap-1.5 mt-1 bg-[#0f1117] px-2 py-1 rounded-xl border border-white/[0.06]">
                    <span className="text-[10px] font-medium text-white/70 uppercase tracking-wider">
                      {session.is_active ? 'Active' : 'Idle'}
                    </span>
                    <div className={`w-2 h-2 rounded-full ${session.is_active ? 'bg-green-500 shadow-[0_0_5px_rgba(34,197,94,0.5)]' : 'bg-slate-600'}`}></div>
                  </div>
                </div>

                <div className="space-y-4 flex-1">
                  <div className="flex justify-between items-center group">
                    <span className="text-sm text-white/70 flex items-center gap-2 group-hover:text-white/70 transition-colors">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path>
                      </svg>
                      Tab Switches
                    </span>
                    <span className={`font-mono text-lg font-bold ${hasWarning ? 'text-amber-400' : 'text-slate-200'}`}>
                      {session.tab_switches || 0}
                    </span>
                  </div>

                  <div className="flex justify-between items-center group">
                    <span className="text-sm text-white/70 flex items-center gap-2 group-hover:text-white/70 transition-colors">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"></path>
                      </svg>
                      Paste Count
                    </span>
                    <span className="font-mono text-lg font-semibold text-slate-200">
                      {session.paste_count || 0}
                    </span>
                  </div>
                </div>

                <div className="mt-5 pt-4 border-t border-white/[0.06]/80">
                  <div className="flex justify-between items-center text-xs text-white/40">
                    <span className="flex items-center gap-1.5">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Last Heartbeat
                    </span>
                    <span className="font-medium text-white/70">
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
      </div>
                </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default LiveMonitoring;
