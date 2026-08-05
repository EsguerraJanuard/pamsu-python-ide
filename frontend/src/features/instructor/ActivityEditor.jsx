import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import InstructorSidebar from "../../components/layout/InstructorSidebar";

const ActivityEditor = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const payload = {
        ...formData,
        requirements: formData.requirements
          .split(',')
          .map((req) => req.trim())
          .filter((req) => req !== ''),
      };

      const response = await api.post('/instructors/tasks/', payload);
      navigate(`/instructor/activities/${response.data.id}`);
    } catch (err) {
      console.error('Error creating activity:', err);
      setError('Failed to create activity. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white select-none">
      <InstructorSidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="dashboard-page min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
                        <style>
              {`
                @keyframes dashboardFadeUp {
                  from { opacity: 0; transform: translateY(10px); }
                  to { opacity: 1; transform: translateY(0); }
                }
                .dashboard-page {
                  animation: dashboardFadeUp 450ms cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
                }
                @media (prefers-reduced-motion: reduce) {
                  .dashboard-page, .dashboard-card { animation: none !important; }
                }
              `}
            </style>
            <div className="mx-auto max-w-6xl dashboard-page">

      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-8">Create New Activity</h1>
        
        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-4 rounded-xl mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6 bg-[#1a1d27] p-6 rounded-xl border border-white/[0.06]">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-emerald-400 mb-1">Title</label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              required
              className="w-full bg-[#0f1117] border border-white/[0.06] rounded-xl p-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-emerald-400 mb-1">Description</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={3}
              className="w-full bg-[#0f1117] border border-white/[0.06] rounded-xl p-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label htmlFor="instructions" className="block text-sm font-medium text-emerald-400 mb-1">Instructions</label>
            <textarea
              id="instructions"
              name="instructions"
              value={formData.instructions}
              onChange={handleChange}
              rows={4}
              className="w-full bg-[#0f1117] border border-white/[0.06] rounded-xl p-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label htmlFor="expected_output" className="block text-sm font-medium text-emerald-400 mb-1">Expected Output</label>
            <textarea
              id="expected_output"
              name="expected_output"
              value={formData.expected_output}
              onChange={handleChange}
              rows={3}
              className="w-full bg-[#0f1117] border border-white/[0.06] rounded-xl p-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label htmlFor="requirements" className="block text-sm font-medium text-emerald-400 mb-1">Requirements (comma-separated)</label>
            <textarea
              id="requirements"
              name="requirements"
              value={formData.requirements}
              onChange={handleChange}
              rows={2}
              placeholder="e.g. use for loops, output formatting"
              className="w-full bg-[#0f1117] border border-white/[0.06] rounded-xl p-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label htmlFor="starter_code" className="block text-sm font-medium text-emerald-400 mb-1">Starter Code</label>
            <textarea
              id="starter_code"
              name="starter_code"
              value={formData.starter_code}
              onChange={handleChange}
              rows={8}
              className="w-full bg-[#0f1117] border border-white/[0.06] rounded-xl p-4 text-white font-mono text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="flex gap-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_published"
                name="is_published"
                checked={formData.is_published}
                onChange={handleChange}
                className="w-4 h-4 rounded bg-[#0f1117] border-white/[0.06] text-emerald-500 focus:ring-emerald-500 focus:ring-offset-slate-900"
              />
              <label htmlFor="is_published" className="ml-2 text-sm text-white/80">Publish immediately</label>
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                id="allow_paste"
                name="allow_paste"
                checked={formData.allow_paste}
                onChange={handleChange}
                className="w-4 h-4 rounded bg-[#0f1117] border-white/[0.06] text-emerald-500 focus:ring-emerald-500 focus:ring-offset-slate-900"
              />
              <label htmlFor="allow_paste" className="ml-2 text-sm text-white/80">Allow Paste</label>
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="px-4 py-2 text-white/60 hover:text-white mr-4 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium transition-colors disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Activity'}
            </button>
          </div>
        </form>
      </div>
                </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default ActivityEditor;
