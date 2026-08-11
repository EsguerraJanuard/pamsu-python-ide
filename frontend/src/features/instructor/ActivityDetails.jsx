import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import InstructorSidebar from "../../components/layout/InstructorSidebar";
import ConfirmationModal from '../../components/modals/ConfirmationModal';

const ActivityDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activity, setActivity] = useState(null);
  const [testCases, setTestCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [newTestCase, setNewTestCase] = useState({
    input_data: '',
    expected_output: '',
    is_hidden: false
  });

  const [confirmModal, setConfirmModal] = useState({ isOpen: false, testCaseId: null });

  useEffect(() => {
    fetchActivityDetails();
    fetchTestCases();
  }, [id]);

  const fetchActivityDetails = async () => {
    try {
      const response = await api.get(`/instructors/tasks/${id}`);
      setActivity(response);
    } catch (err) {
      setError('Failed to fetch activity details.');
      console.error(err);
    }
  };

  const fetchTestCases = async () => {
    try {
      const response = await api.get(`/instructors/tasks/${id}/test-cases`);
      setTestCases(response);
    } catch (err) {
      console.error('Failed to fetch test cases', err);
    } finally {
      setLoading(false);
    }
  };

  const togglePublication = async () => {
    try {
      const newStatus = !activity.is_published;
      await api.patch(`/instructors/tasks/${id}/publication`, { is_published: newStatus });
      setActivity(prev => ({ ...prev, is_published: newStatus }));
    } catch (err) {
      console.error('Failed to toggle publication status', err);
    }
  };

  const toggleAllowPaste = async () => {
    try {
      const newStatus = !activity.allow_paste;
      await api.patch(`/instructors/tasks/${id}`, { allow_paste: newStatus });
      setActivity(prev => ({ ...prev, allow_paste: newStatus }));
    } catch (err) {
      console.error('Failed to toggle allow paste', err);
    }
  };

  const handleAddTestCase = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/instructors/tasks/${id}/test-cases`, newTestCase);
      setNewTestCase({ input_data: '', expected_output: '', is_hidden: false });
      fetchTestCases();
    } catch (err) {
      console.error('Failed to add test case', err);
    }
  };

  const promptDeleteTestCase = (testCaseId) => {
    setConfirmModal({ isOpen: true, testCaseId });
  };

  const handleConfirmDelete = async () => {
    const testCaseId = confirmModal.testCaseId;
    if (!testCaseId) return;

    try {
      await api.delete(`/test-cases/${testCaseId}`);
      fetchTestCases();
      setConfirmModal({ isOpen: false, testCaseId: null });
    } catch (err) {
      console.error('Failed to delete test case', err);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
        <InstructorSidebar />
        <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
          <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
            <div className="mx-auto max-w-6xl animate-pulse">
              <div className="mb-4 h-6 w-24 rounded-md bg-white/[0.06]"></div>
              <div className="mb-8 h-8 w-64 rounded-md bg-white/[0.06]"></div>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                  <div className="h-40 rounded-xl bg-white/[0.06]"></div>
                  <div className="h-64 rounded-xl bg-white/[0.06]"></div>
                </div>
                <div className="h-80 rounded-xl bg-white/[0.06]"></div>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  if (error || !activity) {
    return <div className="text-text-rose p-6">{error || 'Activity not found'}</div>;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
      <InstructorSidebar />
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
                        
            <div className="mx-auto max-w-6xl ">

      <div className="w-full space-y-8">
        
        {/* Header section */}
        <div className="bg-bg-glass p-6 rounded-xl border border-border-subtle">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold mb-2">{activity.title}</h1>
              <p className="text-text-muted">{activity.description}</p>
            </div>
            <button onClick={() => navigate(-1)} className="text-text-emerald hover:text-text-emerald">
              Back
            </button>
          </div>
          <div className="mt-6 flex items-center space-x-8">
            <label className="relative inline-flex items-center gap-3 cursor-pointer group">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={!!activity.is_published}
                  onChange={togglePublication}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-white/10 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500 group-hover:bg-white/20 peer-checked:group-hover:bg-emerald-400"></div>
              </div>
              <span className="text-sm font-semibold text-text-main select-none group-hover:text-text-main transition-colors">
                {activity.is_published ? "Published" : "Draft"}
              </span>
            </label>

            <label className={`relative inline-flex items-center gap-3 group ${activity.is_published ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}>
              <div className="relative">
                <input
                  type="checkbox"
                  checked={!!activity.allow_paste}
                  onChange={toggleAllowPaste}
                  disabled={activity.is_published}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-white/10 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500 group-hover:bg-white/20 peer-checked:group-hover:bg-emerald-400 peer-disabled:group-hover:bg-white/10 peer-checked:peer-disabled:group-hover:bg-emerald-500"></div>
              </div>
              <span className="text-sm font-semibold text-text-main select-none group-hover:text-text-main transition-colors">Allow Paste</span>
            </label>
          </div>
        </div>

        {/* Content Details */}
        <div className="bg-bg-glass p-6 rounded-xl border border-border-subtle space-y-4">
          <h2 className="text-xl font-semibold text-text-main border-b border-border-subtle pb-2">Details</h2>
          
          <div>
            <h3 className="text-sm font-medium text-text-emerald">Instructions</h3>
            <div className="mt-1 bg-bg-glass/50 p-3 rounded border border-border-subtle whitespace-pre-wrap">
              {activity.instructions || 'No instructions provided.'}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-text-emerald">Requirements</h3>
            <div className="mt-1 bg-bg-glass/50 p-3 rounded border border-border-subtle whitespace-pre-wrap">
              {activity.requirements || 'No requirements provided.'}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-text-emerald">Expected Output (Global)</h3>
            <div className="mt-1 bg-bg-glass/50 p-3 rounded border border-border-subtle whitespace-pre-wrap">
              {activity.expected_output || 'No expected output provided.'}
            </div>
          </div>
        </div>

        {/* Test Cases Section */}
        <div className="bg-bg-glass p-6 rounded-xl border border-border-subtle space-y-6">
          <h2 className="text-xl font-semibold text-text-main border-b border-border-subtle pb-2">Test Cases</h2>
          
          <div className="space-y-4">
            {testCases.length === 0 ? (
              <p className="text-text-muted">No test cases found.</p>
            ) : (
              testCases.map((tc, idx) => (
                <div key={tc.id || idx} className="bg-bg-glass p-4 rounded border border-border-subtle flex flex-col md:flex-row gap-4 justify-between items-start">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-text-main">Test Case #{idx + 1}</span>
                      {tc.is_hidden && <span className="bg-slate-800 text-xs px-2 py-1 rounded text-text-muted">Hidden</span>}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <div className="text-xs text-text-muted mb-1">Input Data</div>
                        <pre className="text-sm bg-bg-base p-2 rounded border border-border-subtle overflow-x-auto">{tc.input_data || '-'}</pre>
                      </div>
                      <div>
                        <div className="text-xs text-text-muted mb-1">Expected Output</div>
                        <pre className="text-sm bg-bg-base p-2 rounded border border-border-subtle overflow-x-auto">{tc.expected_output || '-'}</pre>
                      </div>
                    </div>
                  </div>
                    {!activity.is_published && (
                      <button 
                        onClick={() => promptDeleteTestCase(tc.id)}
                        className="text-text-rose hover:text-text-rose px-3 py-1 bg-red-400/10 rounded border border-red-400/20"
                      >
                        Delete
                      </button>
                    )}
                </div>
              ))
            )}
          </div>

          {/* Add Test Case Form */}
          {!activity.is_published ? (
            <form onSubmit={handleAddTestCase} className="mt-8 border-t border-border-subtle pt-6 space-y-4">
              <h3 className="text-lg font-medium text-text-main">Add New Test Case</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Input Data</label>
                <textarea 
                  value={newTestCase.input_data}
                  onChange={e => setNewTestCase({...newTestCase, input_data: e.target.value})}
                  className="w-full bg-bg-glass border border-border-subtle rounded p-2 text-text-main focus:border-emerald-500 focus:outline-none h-24"
                  placeholder="Enter input data..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Expected Output</label>
                <textarea 
                  value={newTestCase.expected_output}
                  onChange={e => setNewTestCase({...newTestCase, expected_output: e.target.value})}
                  className="w-full bg-bg-glass border border-border-subtle rounded p-2 text-text-main focus:border-emerald-500 focus:outline-none h-24"
                  required
                  placeholder="Enter expected output..."
                />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <label className="relative inline-flex items-center gap-3 cursor-pointer group">
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={newTestCase.is_hidden}
                    onChange={e => setNewTestCase({...newTestCase, is_hidden: e.target.checked})}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-white/10 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500 group-hover:bg-white/20 peer-checked:group-hover:bg-emerald-400"></div>
                </div>
                <span className="text-sm font-semibold text-text-main select-none group-hover:text-text-main transition-colors">Hidden Test Case</span>
              </label>
              <button 
                type="submit"
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-text-main rounded transition-colors"
              >
                Add Test Case
                </button>
              </div>
            </form>
          ) : (
            <div className="mt-8 border-t border-border-subtle pt-6">
              <p className="text-sm text-text-amber/80 bg-amber-500/10 border border-amber-500/20 rounded p-4">
                This activity is currently published. You must unpublish it before you can add or delete test cases.
              </p>
            </div>
          )}
        </div>

      </div>
                </div>
          </main>
        </div>
      </div>
      <ConfirmationModal
        isOpen={confirmModal.isOpen}
        title="Delete Test Case"
        message="Are you sure you want to delete this test case? This action cannot be undone."
        confirmText="Delete"
        isDanger={true}
        onConfirm={handleConfirmDelete}
        onCancel={() => setConfirmModal({ isOpen: false, testCaseId: null })}
      />
    </div>
  );
};

export default ActivityDetails;