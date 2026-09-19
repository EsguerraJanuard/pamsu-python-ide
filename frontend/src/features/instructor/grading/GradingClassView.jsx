/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../../services/api';

const GradingClassView = () => {
  const { classId } = useParams();
  const navigate = useNavigate();
  const [classroom, setClassroom] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const classRes = await api.get(`/classrooms/${classId}`);
        setClassroom(classRes.data);

        // Fetch tasks
        const tasksRes = await api.get('/instructors/tasks/');
        // Filter by class_id
        const filteredTasks = tasksRes.data.filter(task => String(task.class_id) === String(classId));
        setActivities(filteredTasks);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (classId) {
      fetchData();
    }
  }, [classId]);

  if (loading) {
    return <div className="p-8 text-white/80 bg-[#0f1117] min-h-screen">Loading class details...</div>;
  }

  if (!classroom) {
    return <div className="p-8 text-white/80 bg-[#0f1117] min-h-screen">Class not found.</div>;
  }

  return (
    <div className="p-8 bg-[#0f1117] min-h-screen text-white/80">
      <div className="max-w-4xl mx-auto">
        <button 
          onClick={() => navigate('/instructor/grading')}
          className="mb-6 flex items-center text-blue-400 hover:text-blue-300 transition-colors"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Classes
        </button>

        <header className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">{classroom.name || 'Class Details'}</h1>
          <p className="text-slate-400">{classroom.description || 'View and grade activities for this class.'}</p>
        </header>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-white mb-4">Activities</h2>
          {activities.length === 0 ? (
            <div className="p-6 bg-slate-900/50 border border-slate-800 rounded-lg text-center text-slate-400">
              No activities found for this class.
            </div>
          ) : (
            activities.map(activity => (
              <div 
                key={activity.id} 
                className="p-6 bg-slate-900/50 border border-slate-800 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-700 transition-colors"
              >
                <div>
                  <h3 className="text-lg font-medium text-white">{activity.title}</h3>
                  <p className="text-sm text-slate-400 mt-1">{activity.description || 'No description provided'}</p>
                  {activity.due_date && (
                    <p className="text-xs text-slate-500 mt-2">Due: {new Date(activity.due_date).toLocaleDateString()}</p>
                  )}
                </div>
                <button
                  onClick={() => navigate(`/instructor/grading/classes/${classId}/activities/${activity.id}`)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-colors whitespace-nowrap flex items-center"
                >
                  View details
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default GradingClassView;

