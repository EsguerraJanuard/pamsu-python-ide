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
      <div className="flex min-w-0 flex-1 items-center justify-center min-h-screen text-text-main bg-transparent">
        <div className="animate-pulse flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p>Loading classes...</p>
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
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col overflow-y-auto">
        <main className="min-h-screen p-8 bg-transparent">
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
                className="group cursor-pointer bg-bg-glass hover:bg-bg-glass-hover transition-all duration-200 rounded-xl border border-border-subtle hover:border-emerald-500/50 overflow-hidden flex flex-col h-48"
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
  );
};

export default GradingBenchRoot;

