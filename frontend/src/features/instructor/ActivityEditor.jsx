import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import CustomSelect from '../../components/ui/CustomSelect';
import Flatpickr from 'react-flatpickr';
import 'flatpickr/dist/themes/dark.css';
import api from '../../services/api';
import InstructorSidebar from "../../components/layout/InstructorSidebar";

const ActivityEditor = () => {
  const navigate = useNavigate();
  const [classrooms, setClassrooms] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    class_ids: [],
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
    if (!formData.class_ids || formData.class_ids.length === 0) {
      setError('Please select at least one classroom.');
      return;
    }
    setLoading(true);
    setError('');

    try {
      const payload = {
        ...formData,
        class_ids: formData.class_ids.map(id => parseInt(id, 10)),
        due_at: formData.due_at ? new Date(formData.due_at).toISOString() : null,
        scheduled_publish_at: (!formData.is_published && formData.scheduled_publish_at) 
          ? new Date(formData.scheduled_publish_at).toISOString() 
          : null,
        required_ast_rules: formData.requirements
          .split(',')
          .map((req) => req.trim())
          .filter((req) => req !== '')
          .reduce((acc, req) => {
             acc[req] = { required: true, min_count: 1 };
             return acc;
          }, {}),
      };

      delete payload.requirements;

      const response = await api.post('/instructors/tasks/', payload);
      
      // If single classroom was selected, navigate directly to that activity's page
      if (response && Array.isArray(response) && response.length === 1) {
        navigate(`/instructor/activities/${response[0].task_id}`);
      } else {
        // Multiple activities were created, navigate to dashboard
        navigate('/instructor/dashboard');
      }
    } catch (err) {
      console.error('Error creating activity:', err);
      setError('Failed to create activity. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main">
      <div className="hidden lg:flex h-full">
        <InstructorSidebar />
      </div>
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <main className="min-w-0 flex-1 overflow-y-auto px-6 py-6 sm:px-8">
          <div className="w-full">
            <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-border-subtle pb-6">
              <div>
                <p className="mb-1 font-mono text-xs font-bold uppercase tracking-widest text-text-emerald">MANAGEMENT</p>
                <h1 className="text-2xl font-bold tracking-tight text-text-main">Create New Activity</h1>
                <p className="mt-1 text-sm text-text-muted">
                  Author new laboratory activities, code templates, and automated AST testing guidelines.
                </p>
              </div>
            </header>
            
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-text-rose p-4 rounded-xl mb-6 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Details & Instructions (7 cols) */}
              <div className="lg:col-span-7 space-y-5 bg-bg-glass p-6 rounded-2xl border border-border-subtle">
                <h2 className="text-sm font-bold uppercase tracking-wider text-text-emerald pb-2 border-b border-border-subtle">
                  Activity Details
                </h2>

                <div>
                  <label htmlFor="title" className="block text-xs font-semibold text-text-muted mb-1.5">
                    Activity Title <span className="text-text-emerald">*</span>
                  </label>
                  <input
                    type="text"
                    id="title"
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    required
                    placeholder="e.g. Lab Activity 3 — Fibonacci Sequence"
                    className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 text-sm text-text-main focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-text-muted mb-1.5">
                    Target Classroom(s) <span className="text-text-emerald">*</span>
                  </label>
                  <div className="bg-bg-glass border border-border-subtle rounded-xl p-3 max-h-56 overflow-y-auto custom-scrollbar flex flex-col gap-2">
                    {classrooms.length === 0 ? (
                      <div className="text-sm text-text-muted italic py-2 text-center">No classrooms available</div>
                    ) : (
                      classrooms.map(cls => {
                        const isSelected = formData.class_ids.includes(cls.class_id);
                        return (
                          <label 
                            key={cls.class_id} 
                            className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all ${
                              isSelected
                                ? 'bg-emerald-500/10 border-emerald-500/30 shadow-sm'
                                : 'bg-bg-base border-border-subtle hover:border-border-strong'
                            }`}
                          >
                            <div className="flex items-center gap-3">
                              <span className={`text-sm font-medium select-none ${isSelected ? 'text-text-emerald' : 'text-text-main'}`}>
                                {cls.subject_code} - {cls.section}
                              </span>
                            </div>
                            <div className={`w-5 h-5 rounded flex items-center justify-center transition-colors ${
                              isSelected
                                ? 'bg-emerald-500 border-emerald-500 text-bg-panel'
                                : 'border border-border-strong bg-transparent'
                            }`}>
                              {isSelected && (
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                              )}
                            </div>
                            <input 
                              type="checkbox" 
                              className="sr-only"
                              checked={isSelected}
                              onChange={(e) => {
                                const checked = e.target.checked;
                                setFormData(prev => ({
                                  ...prev,
                                  class_ids: checked 
                                    ? [...prev.class_ids, cls.class_id]
                                    : prev.class_ids.filter(id => id !== cls.class_id)
                                }));
                              }}
                            />
                          </label>
                        );
                      })
                    )}
                  </div>
                </div>

                <div>
                  <label htmlFor="description" className="block text-xs font-semibold text-text-muted mb-1.5">Overview / Description</label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    rows={4}
                    placeholder="Brief overview of the activity goals..."
                    className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 text-sm text-text-main focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>

                <div>
                  <label htmlFor="instructions" className="block text-xs font-semibold text-text-muted mb-1.5">Detailed Student Instructions</label>
                  <textarea
                    id="instructions"
                    name="instructions"
                    value={formData.instructions}
                    onChange={handleChange}
                    rows={8}
                    placeholder="Step-by-step instructions for completing the task..."
                    className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 text-sm text-text-main focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="expected_output" className="block text-xs font-semibold text-text-muted mb-1.5">Expected Output</label>
                    <textarea
                      id="expected_output"
                      name="expected_output"
                      value={formData.expected_output}
                      onChange={handleChange}
                      rows={3}
                      placeholder="Target output string..."
                      className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 font-mono text-xs text-text-emerald focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                  </div>

                  <div>
                    <label htmlFor="requirements" className="block text-xs font-semibold text-text-muted mb-1.5">AST Checklist Requirements</label>
                    <textarea
                      id="requirements"
                      name="requirements"
                      value={formData.requirements}
                      onChange={handleChange}
                      rows={3}
                      placeholder="Define function, Use a loop, Accept input..."
                      className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 text-xs text-text-main focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                  </div>
                </div>
              </div>

              {/* Right Column: Code Template & Settings (5 cols) */}
              <div className="lg:col-span-5 flex flex-col gap-5">
                <div className="flex-1 bg-bg-glass p-6 rounded-2xl border border-border-subtle flex flex-col">
                  <h2 className="text-sm font-bold uppercase tracking-wider text-text-emerald pb-2 border-b border-border-subtle mb-4">
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
                      className="w-full h-full bg-bg-base border border-border-subtle rounded-xl p-4 text-text-main font-mono text-xs focus:outline-none focus:border-emerald-500 transition-colors resize-none"
                    />
                  </div>
                </div>

                <div className="bg-bg-glass p-6 rounded-2xl border border-border-subtle space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted">Options & Controls</h3>
                  
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
                          <div className="w-9 h-5 bg-border-strong rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-panel after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500 group-hover:bg-text-muted/30 peer-checked:group-hover:bg-emerald-400"></div>
                        </div>
                        <span className="text-xs font-semibold text-text-main select-none group-hover:text-text-main transition-colors">Publish immediately</span>
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
                          <div className="w-9 h-5 bg-border-strong rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-panel after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500 group-hover:bg-text-muted/30 peer-checked:group-hover:bg-emerald-400"></div>
                        </div>
                        <span className="text-xs font-semibold text-text-main select-none group-hover:text-text-main transition-colors">Allow Paste</span>
                      </label>
                    </div>

                    <div className="flex flex-col gap-4">
                      
                        <div className={`animate-fade-in transition-opacity ${formData.is_published ? 'opacity-30 pointer-events-none' : ''} ${formData.class_ids.length > 1 ? 'opacity-50' : ''}`}>
                          <label htmlFor="scheduled_publish_at" className="block text-xs font-semibold text-text-muted mb-1.5 flex items-center justify-between">
                            <span>Scheduled Publish Date <span className="text-text-muted font-normal ml-1">(Optional)</span></span>
                          </label>
                          <div className="relative group flex">
                            <Flatpickr
                              data-enable-time
                              value={formData.scheduled_publish_at}
                              onChange={([date]) => setFormData(prev => ({ ...prev, scheduled_publish_at: date }))}
                              disabled={formData.is_published || formData.class_ids.length > 1}
                              className={`w-full bg-bg-glass border border-border-subtle rounded-xl pl-4 pr-10 py-2.5 text-sm focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all group-hover:border-border-strong shadow-inner ${formData.class_ids.length > 1 ? 'text-text-muted cursor-not-allowed' : 'text-text-main cursor-pointer'}`}
                              placeholder="Select date and time"
                              options={{
                                dateFormat: "Y-m-d H:i",
                                time_24hr: false,
                                altInput: true,
                                altFormat: "M j, Y h:i K"
                              }}
                            />
                            {/* Calendar icon */}
                            <div className="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none text-text-muted">
                              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                            </div>
                          </div>
                          {formData.class_ids.length > 1 && (
                            <p className="mt-2 text-xs text-text-amber flex items-center gap-1.5">
                              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                              Scheduling is disabled when assigning to multiple classrooms.
                            </p>
                          )}
                        </div>
                      
                      <div>
                        <label htmlFor="due_at" className="block text-xs font-semibold text-text-muted mb-1.5 flex items-center justify-between">
                          <span>Deadline / Due Date <span className="text-text-muted font-normal ml-1">(Optional)</span></span>
                        </label>
                        <div className="relative group flex">
                          <Flatpickr
                            data-enable-time
                            value={formData.due_at}
                            onChange={([date]) => setFormData(prev => ({ ...prev, due_at: date }))}
                            className="w-full bg-bg-glass border border-border-subtle rounded-xl pl-4 pr-10 py-2.5 text-sm text-text-main focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all group-hover:border-border-strong shadow-inner cursor-pointer"
                            placeholder="Select deadline"
                            options={{
                              dateFormat: "Y-m-d H:i",
                              time_24hr: false,
                              altInput: true,
                              altFormat: "M j, Y h:i K"
                            }}
                          />
                          <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none text-text-muted group-hover:text-text-emerald transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-3 border-t border-border-subtle">
                    <button
                      type="button"
                      onClick={() => navigate(-1)}
                      className="px-4 py-2 text-xs font-semibold text-text-muted hover:text-text-main transition-colors cursor-pointer"
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
