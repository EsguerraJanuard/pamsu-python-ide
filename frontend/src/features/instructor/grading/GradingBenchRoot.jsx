/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../../services/api';
import InstructorSidebar from '../../../components/layout/InstructorSidebar';

const GradingBenchRoot = () => {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchClasses = async () => {
      try {
        const response = await api.get('/classrooms/');
        setClasses(Array.isArray(response) ? response : (response?.data || []));
      } catch (err) {
        setError('Failed to load classes.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchClasses();
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
        <InstructorSidebar />
        <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
          <div className="flex min-h-0 flex-1">
            <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
              <div className="max-w-6xl mx-auto w-full">
                <header className="mb-8 animate-pulse">
                  <div className="h-8 bg-border-subtle rounded w-48 mb-4"></div>
                  <div className="h-4 bg-border-subtle rounded w-72"></div>
                </header>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3, 4, 5, 6].map((i) => (
                    <div key={i} className="dashboard-card bg-bg-glass rounded-xl border border-border-subtle overflow-hidden flex flex-col h-48 animate-pulse">
                      <div className="p-6 flex-grow">
                        <div className="h-6 bg-border-subtle rounded w-3/4 mb-4"></div>
                        <div className="h-4 bg-border-subtle rounded w-full mb-2"></div>
                        <div className="h-4 bg-border-subtle rounded w-2/3"></div>
                      </div>
                      <div className="px-6 py-4 border-t border-border-subtle bg-bg-panel flex justify-between items-center">
                        <div className="h-4 bg-border-subtle rounded w-32"></div>
                        <div className="h-5 w-5 bg-border-subtle rounded-full"></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </main>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
      <InstructorSidebar />
      <div className="flex min-w-0 flex-1 items-center justify-center min-h-screen text-red-400 bg-transparent">
        <p>{error}</p>
      </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
      <InstructorSidebar />
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
        <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
      <div className="max-w-6xl mx-auto w-full">
        <header className="mb-8 border-b border-border-subtle pb-6">
          <p className="mb-1 font-mono text-xs text-text-brand">MONITORING &amp; GRADING</p>
          <h1 className="text-2xl font-bold text-text-main flex items-center gap-3">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6 text-text-brand"><path d="M21 10.5V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h12.5"/><path d="m9 11 3 3L22 4"/></svg>
            Grading Bench
          </h1>
          <p className="mt-1 text-sm text-text-muted">Select a class to view and grade assignments.</p>
        </header>

        {classes.length === 0 ? (
          <div className="text-center py-12 bg-bg-glass rounded-xl border border-border-subtle">
            <p className="text-text-muted">No classes found.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {classes.map((cls, idx) => (
                <div 
                  key={cls.class_id || idx} 
                  onClick={() => navigate(`/instructor/bench/${cls.class_id}`)}
                  className="dashboard-card rounded-xl border border-border-subtle bg-bg-glass p-5 flex flex-col transition hover:border-psu-maroon/30 cursor-pointer relative group"
                  style={{ animation: `dashboardFadeUp 400ms ease ${idx * 70}ms both` }}
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <span className="inline-block px-2 py-1 bg-psu-maroon/10 text-text-brand border border-psu-maroon/20 rounded-md text-[10px] font-mono mb-2">
                        {cls.subject_code || 'Classroom'} - {cls.section || 'Section'}
                      </span>
                      <h3 className={`font-semibold text-lg leading-tight group-hover:text-text-brand transition-colors ${cls.is_active === false ? 'text-text-muted' : ''}`}>
                        {cls.name}
                      </h3>
                    </div>
                    <div title={cls.is_active !== false ? 'Active' : 'Inactive'} className={`w-2 h-2 rounded-full ${cls.is_active !== false ? 'bg-psu-maroon animate-pulse' : 'bg-red-500/50'} mt-1 flex-shrink-0`}></div>
                  </div>
                  
                  <div className="flex items-center justify-between mt-auto pt-4 border-t border-border-subtle">
                    <div>
                      <p className="text-[10px] text-text-muted mb-0.5">Section</p>
                      <div className="flex items-center gap-2">
                        <p className="font-mono text-sm text-text-main">{cls.section || 'N/A'}</p>
                      </div>
                    </div>
                    <button className="rounded bg-bg-panel px-3 py-1.5 text-[10px] font-bold tracking-wider text-text-muted transition group-hover:bg-psu-maroon/10 group-hover:text-text-brand uppercase flex items-center gap-1">
                      Grade
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="opacity-0 -ml-2 group-hover:opacity-100 group-hover:ml-0 transition-all"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                    </button>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
        </main>
        </div>
      </div>
    </div>
  );
};

export default GradingBenchRoot;

