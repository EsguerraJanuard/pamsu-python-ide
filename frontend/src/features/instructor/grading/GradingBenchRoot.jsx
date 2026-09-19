/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../../services/api';

const GradingBenchRoot = () => {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchClasses = async () => {
      try {
        const response = await api.get('/classrooms/');
        setClasses(response.data);
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
      <div className="flex items-center justify-center min-h-screen text-white/80 bg-[#0f1117]">
        <div className="animate-pulse flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p>Loading classes...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen text-red-400 bg-[#0f1117]">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8 bg-[#0f1117] text-white/80">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Grading Bench</h1>
          <p className="text-slate-400">Select a class to view and grade assignments.</p>
        </header>

        {classes.length === 0 ? (
          <div className="text-center py-12 bg-slate-900/50 rounded-xl border border-slate-800">
            <p className="text-slate-400">No classes found.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {classes.map((cls) => (
              <div
                key={cls.id}
                onClick={() => navigate(`/instructor/grading/classes/${cls.id}`)}
                className="group cursor-pointer bg-slate-900/50 hover:bg-slate-800/80 transition-all duration-200 rounded-xl border border-slate-800 hover:border-emerald-500/50 overflow-hidden flex flex-col h-48"
              >
                <div className="p-6 flex-grow">
                  <h2 className="text-xl font-semibold text-white mb-2 group-hover:text-emerald-400 transition-colors">
                    {cls.name}
                  </h2>
                  <p className="text-sm text-slate-400 line-clamp-2">
                    {cls.description || 'No description provided.'}
                  </p>
                </div>
                <div className="px-6 py-4 border-t border-slate-800/50 bg-slate-900/30 flex justify-between items-center text-sm">
                  <span className="text-emerald-400/80 font-medium group-hover:text-emerald-400 transition-colors">
                    Open Grading Bench
                  </span>
                  <svg
                    className="w-5 h-5 text-slate-500 group-hover:text-emerald-400 transition-colors transform group-hover:translate-x-1"
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
    </div>
  );
};

export default GradingBenchRoot;

