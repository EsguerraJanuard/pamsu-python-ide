import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import InstructorSidebar from "../../components/layout/InstructorSidebar";

const ActivityEditor = () => {
  const navigate = useNavigate();
  const [classrooms, setClassrooms] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    class_id: '',
    due_at: '',
    scheduled_publish_at: '',
    description: '',
    instructions: '',
    expected_output: '',
    requirements: '',
    starter_code: '',
    activity_type: 'laboratory',
    is_published: false,
    allow_paste: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  useEffect(() => {
    const fetchClassrooms = async () => {
      try {
        const response = await api.get('/classrooms/');
        setClassrooms(response || []);
      } catch (err) {
        console.error('Failed to fetch classrooms', err);
      }
    };
    fetchClassrooms();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.class_id) {
      setError('Please select a classroom.');
      return;
    }
    setLoading(true);
    setError('');

    try {
      const payload = {
        ...formData,
        class_id: parseInt(formData.class_id, 10),
        due_at: formData.due_at ? new Date(formData.due_at).toISOString() : null,
        scheduled_publish_at: (!formData.is_published && formData.scheduled_publish_at) 
          ? new Date(formData.scheduled_publish_at).toISOString() 
          : null,
        requirements: formData.requirements
          .split(',')
          .map((req) => req.trim())
          .filter((req) => req !== ''),
      };

      const response = await api.post('/instructors/tasks/', payload);
      navigate(`/instructor/activities/${response.task_id}`);
    } catch (err) {
      console.error('Error creating activity:', err);
      setError('Failed to create activity. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white">
      <div className="hidden lg:flex h-full">
        <InstructorSidebar />
      </div>
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <main className="min-w-0 flex-1 overflow-y-auto px-6 py-6 sm:px-8">
          <div className="w-full">
            <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-white/[0.06] pb-6">
              <div>
                <p className="mb-1 font-mono text-xs font-bold uppercase tracking-widest text-emerald-400">MANAGEMENT</p>
                <h1 className="text-2xl font-bold tracking-tight text-white">Create New Activity</h1>
                <p className="mt-1 text-sm text-white/40">
                  Author new laboratory activities, code templates, and automated AST testing guidelines.
                </p>
              </div>
            </header>
            
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-4 rounded-xl mb-6 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Details & Instructions (7 cols) */}
              <div className="lg:col-span-7 space-y-5 bg-[#1a1d27] p-6 rounded-2xl border border-white/[0.06]">
                <h2 className="text-sm font-bold uppercase tracking-wider text-emerald-400 pb-2 border-b border-white/[0.06]">
                  Activity Details
                </h2>

                <div>
                  <label htmlFor="title" className="block text-xs font-semibold text-white/70 mb-1.5">
                    Activity Title <span className="text-emerald-400">*</span>
                  </label>
                  <input
                    type="text"
                    id="title"
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    required
                    placeholder="e.g. Lab Activity 3 — Fibonacci Sequence"
                    className="w-full bg-[#0f1117] border border-white/[0.08] rounded-xl p-3 text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>

                <div>
                  <label htmlFor="class_id" className="block text-xs font-semibold text-white/70 mb-1.5">
                    Target Classroom <span className="text-emerald-400">*</span>
                  </label>
                  <select
                    id="class_id"
                    name="class_id"
                    value={formData.class_id}
                    onChange={handleChange}
                    required
                    className="w-full bg-[#0f1117] border border-white/[0.08] rounded-xl p-3 text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
                  >
                    <option value="" disabled>Select a classroom</option>
                    {classrooms.map(cls => (
                      <option key={cls.class_id} value={cls.class_id}>
                        {cls.subject_code} - {cls.section}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="description" className="block text-xs font-semibold text-white/70 mb-1.5">Overview / Description</label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    rows={2}
                    placeholder="Brief overview of the activity goals..."
                    className="w-full bg-[#0f1117] border border-white/[0.08] rounded-xl p-3 text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>

                <div>
                  <label htmlFor="instructions" className="block text-xs font-semibold text-white/70 mb-1.5">Detailed Student Instructions</label>
                  <textarea
                    id="instructions"
                    name="instructions"
                    value={formData.instructions}
                    onChange={handleChange}
                    rows={4}
                    placeholder="Step-by-step instructions for completing the task..."
                    className="w-full bg-[#0f1117] border border-white/[0.08] rounded-xl p-3 text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="expected_output" className="block text-xs font-semibold text-white/70 mb-1.5">Expected Output</label>
                    <textarea
                      id="expected_output"
                      name="expected_output"
                      value={formData.expected_output}
                      onChange={handleChange}
                      rows={3}
                      placeholder="Target output string..."
                      className="w-full bg-[#0f1117] border border-white/[0.08] rounded-xl p-3 font-mono text-xs text-emerald-400 focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                  </div>

                  <div>
                    <label htmlFor="requirements" className="block text-xs font-semibold text-white/70 mb-1.5">AST Checklist Requirements</label>
                    <textarea
                      id="requirements"
                      name="requirements"
                      value={formData.requirements}
                      onChange={handleChange}
                      rows={3}
                      placeholder="Define function, Use a loop, Accept input..."
                      className="w-full bg-[#0f1117] border border-white/[0.08] rounded-xl p-3 text-xs text-white focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                  </div>
                </div>
              </div>

              {/* Right Column: Code Template & Settings (5 cols) */}
              <div className="lg:col-span-5 flex flex-col gap-5">
                <div className="flex-1 bg-[#1a1d27] p-6 rounded-2xl border border-white/[0.06] flex flex-col">
                  <h2 className="text-sm font-bold uppercase tracking-wider text-emerald-400 pb-2 border-b border-white/[0.06] mb-4">
                    Starter Code Template
                  </h2>

                  <div className="flex-1 min-h-[220px]">
                    <textarea
                      id="starter_code"
                      name="starter_code"
                      value={formData.starter_code}
                      onChange={handleChange}
                      rows={12}
                      placeholder="# Write initial starter code template for students..."
                      className="w-full h-full bg-[#0f1117] border border-white/[0.08] rounded-xl p-4 text-white font-mono text-xs focus:outline-none focus:border-emerald-500 transition-colors resize-none"
                    />
                  </div>
                </div>

                <div className="bg-[#1a1d27] p-6 rounded-2xl border border-white/[0.06] space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-white/50">Options & Controls</h3>
                  
                  <div className="flex flex-col gap-6">
                    <div className="flex items-center gap-8">
                      <label className="relative inline-flex items-center gap-3 cursor-pointer group">
                        <div className="relative">
                          <input
                            type="checkbox"
                            name="is_published"
                            checked={formData.is_published}
                            onChange={handleChange}
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-white/10 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500 group-hover:bg-white/20 peer-checked:group-hover:bg-emerald-400"></div>
                        </div>
                        <span className="text-xs font-semibold text-white/80 select-none group-hover:text-white transition-colors">Publish immediately</span>
                      </label>

                      <label className="relative inline-flex items-center gap-3 cursor-pointer group">
                        <div className="relative">
                          <input
                            type="checkbox"
                            name="allow_paste"
                            checked={formData.allow_paste}
                            onChange={handleChange}
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-white/10 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500 group-hover:bg-white/20 peer-checked:group-hover:bg-emerald-400"></div>
                        </div>
                        <span className="text-xs font-semibold text-white/80 select-none group-hover:text-white transition-colors">Allow Paste</span>
                      </label>
                    </div>

                    <div className="flex flex-col gap-4">
                      {!formData.is_published && (
                        <div className="animate-fade-in">
                          <label htmlFor="scheduled_publish_at" className="block text-xs font-semibold text-white/70 mb-1.5 flex items-center justify-between">
                            <span>Scheduled Publish Date <span className="text-white/40 font-normal ml-1">(Optional)</span></span>
                          </label>
                          <div className="relative group">
                            <input
                              type="datetime-local"
                              id="scheduled_publish_at"
                              name="scheduled_publish_at"
                              value={formData.scheduled_publish_at}
                              onChange={handleChange}
                              className="w-full bg-black/40 border border-white/[0.06] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all group-hover:border-white/[0.15] shadow-inner"
                              style={{ colorScheme: 'dark' }}
                            />
                            {/* Calendar icon overlay to make it look premium */}
                            <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none text-white/30 group-hover:text-emerald-400 transition-colors">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                            </div>
                          </div>
                          <p className="text-[10px] text-white/40 mt-1.5 ml-1">The activity will automatically publish at this time.</p>
                        </div>
                      )}

                      <div>
                        <label htmlFor="due_at" className="block text-xs font-semibold text-white/70 mb-1.5 flex items-center justify-between">
                          <span>Deadline / Due Date <span className="text-white/40 font-normal ml-1">(Optional)</span></span>
                        </label>
                        <div className="relative group">
                          <input
                            type="datetime-local"
                            id="due_at"
                            name="due_at"
                            value={formData.due_at}
                            onChange={handleChange}
                            className="w-full bg-black/40 border border-white/[0.06] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all group-hover:border-white/[0.15] shadow-inner"
                            style={{ colorScheme: 'dark' }}
                          />
                          <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none text-white/30 group-hover:text-emerald-400 transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/[0.06]">
                    <button
                      type="button"
                      onClick={() => navigate(-1)}
                      className="px-4 py-2 text-xs font-semibold text-white/60 hover:text-white transition-colors cursor-pointer"
                    >
                      Cancel
                    </button>

                    <button
                      type="submit"
                      disabled={loading}
                      className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-md shadow-emerald-600/20 transition-all cursor-pointer disabled:opacity-50"
                    >
                      {loading ? "Creating..." : "Create Activity"}
                    </button>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
};

export default ActivityEditor;
