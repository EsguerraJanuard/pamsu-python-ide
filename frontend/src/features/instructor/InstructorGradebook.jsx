import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import InstructorSidebar from '../../components/layout/InstructorSidebar';
import CustomSelect from '../../components/ui/CustomSelect';
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
      const data = response?.items || response || [];
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
        <span className="inline-flex items-center rounded-md bg-slate-400/10 px-2 py-1 text-[10px] font-medium text-text-muted ring-1 ring-inset ring-slate-400/20">
          Pending Grade
        </span>
      );
    }
    if (grade.grade_is_released) {
      return (
        <span className="inline-flex items-center rounded-md bg-emerald-500/10 px-2 py-1 text-[10px] font-medium text-text-emerald ring-1 ring-inset ring-emerald-500/20">
          Released
        </span>
      );
    }
    return (
      <span className="inline-flex items-center rounded-md bg-amber-400/10 px-2 py-1 text-[10px] font-medium text-text-amber ring-1 ring-inset ring-amber-400/20">
        Unreleased
      </span>
    );
  };

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
      <InstructorSidebar />
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
            
            
            <div className="mx-auto max-w-6xl ">
              <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="mb-1 font-mono text-xs text-text-emerald">MONITORING & GRADING</p>
                  <h1 className="text-2xl font-bold">Gradebook</h1>
                  <p className="mt-1 text-sm text-text-muted">
                    Overview of student grades across all your classes and activities.
                  </p>
                </div>
                <div className="flex flex-col sm:flex-row gap-3">
                  <CustomSelect
                    value={selectedClassId}
                    onChange={setSelectedClassId}
                    className="w-full sm:w-48 px-3 py-2 text-sm"
                    options={[
                      { value: "", label: "All Classrooms" },
                      ...classrooms.map(c => ({ value: c.id, label: `${c.subject_code} - ${c.section}` }))
                    ]}
                  />
                  <CustomSelect
                    value={selectedTaskId}
                    onChange={setSelectedTaskId}
                    className="w-full sm:w-48 px-3 py-2 text-sm"
                    options={[
                      { value: "", label: "All Activities" },
                      ...tasks.map(t => ({ value: t.id, label: t.title }))
                    ]}
                  />
                </div>
              </header>

              <div className="rounded-xl border border-border-subtle bg-bg-glass overflow-hidden shadow-lg">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm text-text-main">
                    <thead className="bg-bg-base/50 text-xs uppercase text-text-muted border-b border-border-subtle">
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
                        [1, 2, 3, 4, 5].map(i => (
                          <tr key={i} className="animate-pulse">
                            <td className="px-6 py-4"><div className="h-4 w-32 bg-white/[0.06] rounded-md"></div></td>
                            <td className="px-6 py-4"><div className="h-4 w-24 bg-white/[0.06] rounded-md"></div></td>
                            <td className="px-6 py-4"><div className="h-4 w-40 bg-white/[0.06] rounded-md"></div></td>
                            <td className="px-6 py-4 text-center"><div className="h-4 w-8 mx-auto bg-white/[0.06] rounded-md"></div></td>
                            <td className="px-6 py-4 text-center"><div className="h-6 w-20 mx-auto bg-white/[0.06] rounded-full"></div></td>
                            <td className="px-6 py-4 text-right"><div className="h-8 w-16 ml-auto bg-white/[0.06] rounded-md"></div></td>
                          </tr>
                        ))
                      ) : error ? (
                        <tr>
                          <td colSpan="6" className="px-6 py-12 text-center text-text-rose bg-red-500/5">
                            {error}
                          </td>
                        </tr>
                      ) : grades.length === 0 ? (
                        <tr>
                          <td colSpan="6" className="px-6 py-20 text-center">
                            <div className="flex flex-col items-center justify-center">
                              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10 text-text-emerald ring-4 ring-emerald-500/5">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                                </svg>
                              </div>
                              <h3 className="mb-1 text-base font-semibold text-text-main">No Grades Found</h3>
                              <p className="text-sm text-text-muted">
                                There are no graded submissions matching your current filters.
                              </p>
                            </div>
                          </td>
                        </tr>
                      ) : (
                        grades.map((grade, idx) => (
                          <tr 
                            key={grade.sub_id} 
                            className="transition-colors hover:bg-bg-glass"
                            style={{ animation: `dashboardFadeUp 400ms ease ${idx * 40}ms both` }}
                          >
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="font-semibold text-text-main">{grade.student?.name || 'Unknown'}</div>
                              <div className="font-mono text-[10px] text-text-muted">{grade.student?.school_id || 'N/A'}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-text-main">{grade.activity?.subject_code || 'Unknown'}</div>
                              <div className="text-xs text-text-muted">{grade.activity?.section || 'N/A'}</div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="text-text-main truncate max-w-[200px]">{grade.activity?.title || 'Unknown Task'}</div>
                              <div className="text-[10px] text-text-muted uppercase tracking-wider">{grade.activity?.activity_type}</div>
                            </td>
                            <td className="px-6 py-4 text-center whitespace-nowrap">
                              {grade.has_manual_grade ? (
                                <div>
                                  <span className="font-semibold text-text-main">{grade.score}</span>
                                  <span className="text-text-muted mx-1">/</span>
                                  <span className="text-text-muted">{grade.max_score}</span>
                                  <div className="text-[10px] text-text-emerald mt-1 font-mono">
                                    {grade.percentage?.toFixed(1)}%
                                  </div>
                                </div>
                              ) : (
                                <span className="text-text-muted">—</span>
                              )}
                            </td>
                            <td className="px-6 py-4 text-center whitespace-nowrap">
                              {getStatusBadge(grade)}
                            </td>
                            <td className="px-6 py-4 text-right whitespace-nowrap">
                              <button
                                onClick={() => navigate(`/instructor/submissions/${grade.sub_id}`)}
                                className="inline-flex items-center justify-center rounded bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-text-emerald transition hover:bg-emerald-500 hover:text-text-main"
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
