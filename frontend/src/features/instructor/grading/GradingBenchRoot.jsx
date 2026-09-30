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
          <p className="mb-1 font-mono text-xs text-psu-maroon dark:text-psu-gold">MONITORING &amp; GRADING</p>
          <h1 className="text-2xl font-bold text-text-main flex items-center gap-3">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6 text-psu-maroon dark:text-psu-gold"><path d="M21 10.5V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h12.5"/><path d="m9 11 3 3L22 4"/></svg>
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
                className="group relative flex flex-col rounded-xl border border-border-subtle bg-bg-glass shadow-inner hover:border-psu-maroon/30 hover:bg-bg-glass-hover hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)] hover:-translate-y-1 transition-all duration-300 overflow-hidden cursor-pointer"
                style={{ animation: `pageFadeUp 400ms ease ${idx * 70}ms both` }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-psu-maroon/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
                
                <div className="p-6 flex-1 flex flex-col relative z-10">
                  <div className="flex justify-between items-start mb-4">
                    {cls.subject_code ? (
                      <span className="inline-flex items-center rounded-full border border-psu-maroon/20 bg-psu-maroon/10 px-2.5 py-0.5 text-xs font-semibold tracking-wide text-psu-maroon dark:text-psu-gold shadow-sm">
                        {cls.subject_code}
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-full border border-border-strong bg-bg-panel px-2.5 py-0.5 text-xs font-semibold tracking-wide text-text-muted shadow-sm">
                        Classroom
                      </span>
                    )}
                    <div className="h-8 w-8 rounded-full bg-bg-panel border border-border-subtle flex items-center justify-center group-hover:bg-psu-maroon group-hover:border-psu-maroon transition-colors shadow-sm">
                      <svg
                        className="w-4 h-4 text-text-muted group-hover:text-white transition-transform transform group-hover:translate-x-0.5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                  
                  <h3 className="text-xl font-bold text-text-main mb-2 line-clamp-2 group-hover:text-text-main transition-colors">
                    {cls.name}
                  </h3>
                  
                  <div className="flex items-center gap-2 mb-6 mt-auto pt-4">
                    <span className="text-sm font-medium text-text-muted group-hover:text-text-main transition-colors">
                      Section {cls.section || 'Unknown'}
                    </span>
                  </div>
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

