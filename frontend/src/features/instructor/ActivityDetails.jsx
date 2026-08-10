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
      setActivity(response.data);
    } catch (err) {
      setError('Failed to fetch activity details.');
      console.error(err);
    }
  };

  const fetchTestCases = async () => {
    try {
      const response = await api.get(`/instructors/tasks/${id}/test-cases`);
      setTestCases(response.data);
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
      <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white select-none">
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
    return <div className="text-red-400 p-6">{error || 'Activity not found'}</div>;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white select-none">
      <InstructorSidebar />
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
                        
            <div className="mx-auto max-w-6xl ">

      <div className="w-full space-y-8">
        
        {/* Header section */}
        <div className="bg-[#1a1d27] p-6 rounded-xl border border-white/[0.06]">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold mb-2">{activity.title}</h1>
              <p className="text-white/70">{activity.description}</p>
            </div>
            <button onClick={() => navigate(-1)} className="text-emerald-400 hover:text-emerald-300">
              Back
            </button>
          </div>

          <div className="mt-6 flex items-center space-x-6">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input 
                type="checkbox" 
                checked={!!activity.is_published}
                onChange={togglePublication}
                className="rounded border-white/[0.06] bg-slate-800 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-slate-900"
              />
              <span>Published</span>
            </label>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input 
                type="checkbox" 
                checked={!!activity.allow_paste}
                onChange={toggleAllowPaste}
                className="rounded border-white/[0.06] bg-slate-800 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-slate-900"
              />
              <span>Allow Paste</span>
            </label>
          </div>
        </div>

        {/* Content Details */}
        <div className="bg-[#1a1d27] p-6 rounded-xl border border-white/[0.06] space-y-4">
          <h2 className="text-xl font-semibold text-white border-b border-white/[0.06] pb-2">Details</h2>
          
          <div>
            <h3 className="text-sm font-medium text-emerald-400">Instructions</h3>
            <div className="mt-1 bg-slate-950/50 p-3 rounded border border-white/[0.06] whitespace-pre-wrap">
              {activity.instructions || 'No instructions provided.'}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-emerald-400">Requirements</h3>
            <div className="mt-1 bg-slate-950/50 p-3 rounded border border-white/[0.06] whitespace-pre-wrap">
              {activity.requirements || 'No requirements provided.'}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-emerald-400">Expected Output (Global)</h3>
            <div className="mt-1 bg-slate-950/50 p-3 rounded border border-white/[0.06] whitespace-pre-wrap">
              {activity.expected_output || 'No expected output provided.'}
            </div>
          </div>
        </div>

        {/* Test Cases Section */}
        <div className="bg-[#1a1d27] p-6 rounded-xl border border-white/[0.06] space-y-6">
          <h2 className="text-xl font-semibold text-white border-b border-white/[0.06] pb-2">Test Cases</h2>
          
          <div className="space-y-4">
            {testCases.length === 0 ? (
              <p className="text-white/70">No test cases found.</p>
            ) : (
              testCases.map((tc, idx) => (
                <div key={tc.id || idx} className="bg-slate-950 p-4 rounded border border-white/[0.06] flex flex-col md:flex-row gap-4 justify-between items-start">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-white">Test Case #{idx + 1}</span>
                      {tc.is_hidden && <span className="bg-slate-800 text-xs px-2 py-1 rounded text-white/70">Hidden</span>}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <div className="text-xs text-white/40 mb-1">Input Data</div>
                        <pre className="text-sm bg-[#0f1117] p-2 rounded border border-white/[0.06] overflow-x-auto">{tc.input_data || '-'}</pre>
                      </div>
                      <div>
                        <div className="text-xs text-white/40 mb-1">Expected Output</div>
                        <pre className="text-sm bg-[#0f1117] p-2 rounded border border-white/[0.06] overflow-x-auto">{tc.expected_output || '-'}</pre>
                      </div>
                    </div>
                  </div>
                    <button 
                      onClick={() => promptDeleteTestCase(tc.id)}
                      className="text-red-400 hover:text-red-300 px-3 py-1 bg-red-400/10 rounded border border-red-400/20"
                    >
                    Delete
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Add Test Case Form */}
          <form onSubmit={handleAddTestCase} className="mt-8 border-t border-white/[0.06] pt-6 space-y-4">
            <h3 className="text-lg font-medium text-white">Add New Test Case</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Input Data</label>
                <textarea 
                  value={newTestCase.input_data}
                  onChange={e => setNewTestCase({...newTestCase, input_data: e.target.value})}
                  className="w-full bg-slate-950 border border-white/[0.06] rounded p-2 text-white/90 focus:border-emerald-500 focus:outline-none h-24"
                  placeholder="Enter input data..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Expected Output</label>
                <textarea 
                  value={newTestCase.expected_output}
                  onChange={e => setNewTestCase({...newTestCase, expected_output: e.target.value})}
                  className="w-full bg-slate-950 border border-white/[0.06] rounded p-2 text-white/90 focus:border-emerald-500 focus:outline-none h-24"
                  required
                  placeholder="Enter expected output..."
                />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={newTestCase.is_hidden}
                  onChange={e => setNewTestCase({...newTestCase, is_hidden: e.target.checked})}
                  className="rounded border-white/[0.06] bg-slate-800 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-slate-900"
                />
                <span>Hidden Test Case</span>
              </label>
              <button 
                type="submit"
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded transition-colors"
              >
                Add Test Case
              </button>
            </div>
          </form>
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