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
        setClasses(response);
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
              <div className="max-w-6xl mx-auto">
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
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-text-main mb-2">Grading Bench</h1>
          <p className="text-text-muted">Select a class to view and grade assignments.</p>
        </header>

        {classes.length === 0 ? (
          <div className="text-center py-12 bg-bg-glass rounded-xl border border-border-subtle">
            <p className="text-text-muted">No classes found.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {classes.map((cls) => (
              <div
                key={cls.class_id}
                onClick={() => navigate(`/instructor/bench/${cls.class_id}`)}
                className="dashboard-card group cursor-pointer bg-bg-glass hover:bg-bg-glass-hover transition-all duration-200 rounded-xl border border-border-subtle hover:border-emerald-500/50 hover:shadow-lg hover:shadow-emerald-500/10 overflow-hidden flex flex-col h-48"
              >
                <div className="p-6 flex-grow">
                  <h2 className="text-xl font-semibold text-text-main mb-2 group-hover:text-emerald-400 transition-colors">
                    {cls.name}
                  </h2>
                  <p className="text-sm text-text-muted line-clamp-2">
                    {cls.description || 'No description provided.'}
                  </p>
                </div>
                <div className="px-6 py-4 border-t border-border-subtle bg-bg-panel flex justify-between items-center text-sm">
                  <span className="text-emerald-400/80 font-medium group-hover:text-emerald-400 transition-colors">
                    Open Grading Bench
                  </span>
                  <svg
                    className="w-5 h-5 text-text-muted group-hover:text-emerald-400 transition-colors transform group-hover:translate-x-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
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

