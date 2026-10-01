/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../../services/api';
import InstructorSidebar from '../../../components/layout/InstructorSidebar';

const GradingClassView = () => {
  const { classId } = useParams();
  const navigate = useNavigate();
  const [classroom, setClassroom] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const classRes = await api.get(`/classrooms/${classId}`);
        setClassroom(classRes);

        // Fetch tasks
        const tasksRes = await api.get('/instructors/tasks/');
        // Filter by class_id
        const safeTasks = Array.isArray(tasksRes) ? tasksRes : (tasksRes?.data || []);
        const filteredTasks = safeTasks.filter(task => String(task.class_id) === String(classId));
        setActivities(filteredTasks);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError(error?.message || 'Failed to load class data from server.');
      } finally {
        setLoading(false);
      }
    };

    if (classId) {
      fetchData();
    }
  }, [classId]);

  if (loading) {
    return (
      <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
        <InstructorSidebar />
        <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
          <div className="flex min-h-0 flex-1">
            <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
              <div className="max-w-6xl mx-auto w-full animate-pulse">
                <div className="w-24 h-4 bg-border-subtle rounded mb-6"></div>
                <div className="dashboard-card p-8 border border-border-subtle bg-bg-glass mb-8 rounded-xl shadow-sm">
                  <div className="h-8 bg-border-subtle rounded w-64 mb-4"></div>
                  <div className="h-4 bg-border-subtle rounded w-48"></div>
                </div>
                <div className="h-6 bg-border-subtle rounded w-32 mb-6"></div>
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="dashboard-card p-6 border border-border-subtle rounded-xl bg-bg-glass flex justify-between items-center">
                      <div className="flex-1">
                        <div className="h-6 bg-border-subtle rounded w-48 mb-2"></div>
                        <div className="h-4 bg-border-subtle rounded w-1/3"></div>
                      </div>
                      <div className="w-28 h-10 bg-border-subtle rounded-lg"></div>
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

  if (error || !classroom) {
    return (
      <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
        <InstructorSidebar />
        <div className="flex min-w-0 flex-1 flex-col items-center justify-center text-center p-8">
          <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center mb-4 border border-red-500/20">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
          </div>
          <h2 className="text-xl font-bold text-red-400 mb-2">Failed to load class</h2>
          <p className="text-text-muted max-w-md">{error || "The class could not be found or you don't have access to it."}</p>
          <button onClick={() => navigate('/instructor/bench')} className="mt-6 px-4 py-2 bg-bg-panel hover:bg-bg-glass border border-border-subtle rounded-lg text-text-main transition-colors">
            Back to Grading Bench
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
      <InstructorSidebar />
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
        <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8 text-text-main">
      <div className="max-w-6xl mx-auto w-full">
        <button 
          onClick={() => navigate('/instructor/bench')}
          className="mb-6 flex items-center text-text-muted hover:text-emerald-500 transition-colors"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Classes
        </button>

        <header className="mb-8">
          <h1 className="text-3xl font-bold text-text-main mb-2">{classroom.name || 'Class Details'}</h1>
          <p className="text-text-muted">{classroom.description || 'View and grade activities for this class.'}</p>
        </header>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-text-main mb-4">Activities</h2>
          {activities.length === 0 ? (
            <div className="p-6 bg-bg-glass border border-border-subtle rounded-lg text-center text-text-muted">
              No activities found for this class.
            </div>
          ) : (
            activities.map(activity => (
              <div 
                key={activity.task_id} 
                onClick={() => navigate(`/instructor/bench/${classId}/${activity.task_id}`)}
                className="p-6 bg-bg-glass border border-border-subtle rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-emerald-500/50 hover:shadow-lg cursor-pointer transition-all group relative overflow-hidden"
              >
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-transparent group-hover:bg-emerald-500 transition-colors"></div>
                <div>
                  <h3 className="text-lg font-bold text-text-main group-hover:text-emerald-400 transition-colors">{activity.title}</h3>
                  <p className="text-sm text-text-muted mt-1">{activity.description || 'No description provided'}</p>
                  {activity.due_date && (
                    <p className="text-xs text-text-muted mt-2 font-mono">
                      Due: {new Date(activity.due_date).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <div className="w-full sm:w-auto z-10">
                  <button 
                    className="w-full sm:w-auto rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-4 py-2 text-sm font-semibold transition group-hover:bg-emerald-600 group-hover:text-white group-hover:border-transparent group-hover:shadow-lg group-hover:shadow-emerald-500/20 flex items-center"
                  >
                    View details
                    <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
        </main>
        </div>
      </div>
    </div>
  );
};

export default GradingClassView;

