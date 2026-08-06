import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import InstructorSidebar from '../../components/layout/InstructorSidebar';
import api from '../../services/api';

export default function InstructorGradebook() {
  const navigate = useNavigate();
  const [grades, setGrades] = useState([]);
  const [classrooms, setClassrooms] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedTaskId, setSelectedTaskId] = useState('');

  useEffect(() => {
    fetchFilters();
  }, []);

  useEffect(() => {
    fetchGradebook();
  }, [selectedClassId, selectedTaskId]);

  const fetchFilters = async () => {
    try {
      const [classRes, taskRes] = await Promise.all([
        api.get('/classrooms/'),
        api.get('/instructors/tasks/')
      ]);
      setClassrooms(classRes.data?.items || classRes.data || []);
      setTasks(taskRes.data?.items || taskRes.data || []);
    } catch (err) {
      console.error('Error fetching filters:', err);
    }
  };

  const fetchGradebook = async () => {
    try {
      setLoading(true);
      let url = '/instructors/gradebook';
      const params = new URLSearchParams();
      if (selectedClassId) params.append('class_id', selectedClassId);
      if (selectedTaskId) params.append('task_id', selectedTaskId);
      
      const queryStr = params.toString();
      if (queryStr) url += `?${queryStr}`;

      const response = await api.get(url);
      const data = response.data?.items || response.items || response.data || [];
      setGrades(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      console.error('Error fetching gradebook:', err);
      setError('Failed to load gradebook.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (grade) => {
    if (!grade.has_manual_grade) {
      return (
        <span className="inline-flex items-center rounded-md bg-slate-400/10 px-2 py-1 text-[10px] font-medium text-slate-400 ring-1 ring-inset ring-slate-400/20">
          Pending Grade
        </span>
      );
    }
    if (grade.grade_is_released) {
      return (
        <span className="inline-flex items-center rounded-md bg-emerald-500/10 px-2 py-1 text-[10px] font-medium text-emerald-400 ring-1 ring-inset ring-emerald-500/20">
          Released
        </span>
      );
    }
    return (
      <span className="inline-flex items-center rounded-md bg-amber-400/10 px-2 py-1 text-[10px] font-medium text-amber-400 ring-1 ring-inset ring-amber-400/20">
        Unreleased
      </span>
    );
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white select-none">
      <InstructorSidebar />
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
            
            
            <div className="mx-auto max-w-6xl ">
              <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="mb-1 font-mono text-xs text-emerald-400">MONITORING & GRADING</p>
                  <h1 className="text-2xl font-bold">Gradebook</h1>
                  <p className="mt-1 text-sm text-white/40">
                    Overview of student grades across all your classes and activities.
                  </p>
                </div>
                <div className="flex flex-col sm:flex-row gap-3">
                  <select
                    value={selectedClassId}
                    onChange={(e) => setSelectedClassId(e.target.value)}
                    className="w-full sm:w-48 rounded-lg border border-white/10 bg-[#1a1d27] px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="">All Classrooms</option>
                    {classrooms.map(c => (
                      <option key={c.id} value={c.id}>{c.subject_code} - {c.section}</option>
                    ))}
                  </select>
                  <select
                    value={selectedTaskId}
                    onChange={(e) => setSelectedTaskId(e.target.value)}
                    className="w-full sm:w-48 rounded-lg border border-white/10 bg-[#1a1d27] px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="">All Activities</option>
                    {tasks.map(t => (
                      <option key={t.id} value={t.id}>{t.title}</option>
                    ))}
                  </select>
                </div>
              </header>

              <div className="rounded-xl border border-white/[0.06] bg-[#1a1d27] overflow-hidden shadow-lg">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm text-white/80">
                    <thead className="bg-[#0f1117]/50 text-xs uppercase text-white/40 border-b border-white/[0.06]">
                      <tr>
                        <th className="px-6 py-4 font-semibold">Student</th>
                        <th className="px-6 py-4 font-semibold">Class / Section</th>
                        <th className="px-6 py-4 font-semibold">Activity</th>
                        <th className="px-6 py-4 font-semibold text-center">Score</th>
                        <th className="px-6 py-4 font-semibold text-center">Status</th>
                        <th className="px-6 py-4 font-semibold text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.06]">
                      {loading ? (
                        <tr>
                          <td colSpan="6" className="px-6 py-12 text-center text-white/40">
                            <div className="flex justify-center mb-2">
                              <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
                            </div>
                            Loading gradebook...
                          </td>
                        </tr>
                      ) : error ? (
                        <tr>
                          <td colSpan="6" className="px-6 py-12 text-center text-red-400 bg-red-500/5">
                            {error}
                          </td>
                        </tr>
                      ) : grades.length === 0 ? (
                        <tr>
                          <td colSpan="6" className="px-6 py-12 text-center text-white/40">
                            No grades found for the selected filters.
                          </td>
                        </tr>
                      ) : (
                        grades.map((grade, idx) => (
                          <tr 
                            key={grade.sub_id} 
                            className="transition-colors hover:bg-white/[0.02]"
                            style={{ animation: `dashboardFadeUp 400ms ease ${idx * 40}ms both` }}
                          >
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="font-semibold text-white">{grade.student?.name || 'Unknown'}</div>
                              <div className="font-mono text-[10px] text-white/40">{grade.student?.school_id || 'N/A'}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-white/80">{grade.activity?.subject_code || 'Unknown'}</div>
                              <div className="text-xs text-white/40">{grade.activity?.section || 'N/A'}</div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="text-white/90 truncate max-w-[200px]">{grade.activity?.title || 'Unknown Task'}</div>
                              <div className="text-[10px] text-white/40 uppercase tracking-wider">{grade.activity?.activity_type}</div>
                            </td>
                            <td className="px-6 py-4 text-center whitespace-nowrap">
                              {grade.has_manual_grade ? (
                                <div>
                                  <span className="font-semibold text-white">{grade.score}</span>
                                  <span className="text-white/40 mx-1">/</span>
                                  <span className="text-white/60">{grade.max_score}</span>
                                  <div className="text-[10px] text-emerald-400 mt-1 font-mono">
                                    {grade.percentage?.toFixed(1)}%
                                  </div>
                                </div>
                              ) : (
                                <span className="text-white/20">—</span>
                              )}
                            </td>
                            <td className="px-6 py-4 text-center whitespace-nowrap">
                              {getStatusBadge(grade)}
                            </td>
                            <td className="px-6 py-4 text-right whitespace-nowrap">
                              <button
                                onClick={() => navigate(`/instructor/submissions/${grade.sub_id}`)}
                                className="inline-flex items-center justify-center rounded bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-400 transition hover:bg-emerald-500 hover:text-white"
                              >
                                View
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
