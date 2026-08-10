import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import InstructorSidebar from '../../components/layout/InstructorSidebar';
import ConfirmationModal from '../../components/modals/ConfirmationModal';
import api from '../../services/api';

export default function ClassManagement() {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  
  // Confirmation Modal State
  const [confirmModal, setConfirmModal] = useState({ isOpen: false, classToToggle: null });
  
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: '',
    subject_code: '',
    section: ''
  });

  const fetchClasses = async () => {
    try {
      setLoading(true);
      const data = await api.get('/classrooms/');
      setClasses(Array.isArray(data) ? data : []);
      setError('');
    } catch (err) {
      console.error('Failed to fetch classrooms:', err);
      setError('Failed to load classrooms.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClasses();
  }, []);

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await api.post('/classrooms/', formData);
      setIsModalOpen(false);
      setFormData({ name: '', subject_code: '', section: '' });
      await fetchClasses();
    } catch (err) {
      console.error('Failed to create classroom:', err);
      alert(typeof err === 'string' ? err : err.message || 'Failed to create classroom');
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleClassActiveStatus = (cls, e) => {
    e.stopPropagation(); // prevent card click
    setConfirmModal({ isOpen: true, classToToggle: cls });
  };

  const handleConfirmToggle = async () => {
    const cls = confirmModal.classToToggle;
    if (!cls) return;
    
    try {
      await api.patch(`/classrooms/${cls.class_id}`, { is_active: !cls.is_active });
      // Update local state to reflect change quickly
      setClasses(prev => prev.map(c => 
        c.class_id === cls.class_id ? { ...c, is_active: !c.is_active } : c
      ));
      setConfirmModal({ isOpen: false, classToToggle: null });
    } catch (err) {
      console.error('Failed to update classroom status:', err);
      alert('Failed to update classroom status.');
    }
  };

  const copyToClipboard = (e, text, id) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
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
                  <p className="mb-1 font-mono text-xs text-emerald-400">MANAGEMENT</p>
                  <h1 className="text-2xl font-bold">My Classrooms</h1>
                  <p className="mt-1 text-sm text-white/40">
                    Create and manage your classes, generate enrollment codes, and monitor students.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <button 
                    onClick={() => setIsModalOpen(true)}
                    className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-emerald-500"
                  >
                    + Create New Class
                  </button>
                </div>
              </header>

              {error && (
                <div className="mb-6 rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
                  {error}
                </div>
              )}

              {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="dashboard-card rounded-xl border border-white/[0.06] bg-[#1a1d27] p-5 flex flex-col animate-pulse">
                      <div className="mb-2 h-6 w-3/4 rounded-md bg-white/[0.06]"></div>
                      <div className="mb-4 h-4 w-1/2 rounded-md bg-white/[0.06]"></div>
                      <div className="mb-6 h-10 w-full rounded-md bg-white/[0.06]"></div>
                      <div className="mt-auto flex justify-between">
                        <div className="h-4 w-1/3 rounded-md bg-white/[0.06]"></div>
                        <div className="h-4 w-1/4 rounded-md bg-white/[0.06]"></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : classes.length === 0 ? (
                <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/[0.08] bg-white/[0.01] py-16 px-6 text-center transition-all hover:bg-white/[0.02]">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10 mb-3 ring-4 ring-emerald-500/5 text-emerald-400">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-white/90 mb-1">No Classrooms Yet</h3>
                  <p className="text-sm text-white/50 mb-6 max-w-md">
                    You haven't created any classes. Create your first class to generate an enrollment code for your students.
                  </p>
                  <button 
                    onClick={() => setIsModalOpen(true)}
                    className="rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-500 active:scale-95 shadow-lg shadow-emerald-500/20"
                  >
                    + Create New Class
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {classes.map((cls, idx) => (
                    <div 
                      key={cls.class_id} 
                      onClick={() => navigate(`/instructor/classes/${cls.class_id}`)}
                      className="dashboard-card rounded-xl border border-white/[0.06] bg-[#1a1d27] p-5 flex flex-col transition hover:border-emerald-500/30 cursor-pointer relative group"
                      style={{ animation: `dashboardFadeUp 400ms ease ${idx * 70}ms both` }}
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <span className="inline-block px-2 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-md text-[10px] font-mono mb-2">
                            {cls.subject_code} - {cls.section}
                          </span>
                          <h3 className={`font-semibold text-lg leading-tight group-hover:text-emerald-400 transition-colors ${!cls.is_active ? 'text-white/50' : ''}`}>
                            {cls.name}
                          </h3>
                        </div>
                        <div title={cls.is_active ? 'Active' : 'Inactive'} className={`w-2 h-2 rounded-full ${cls.is_active ? 'bg-emerald-400 animate-pulse' : 'bg-red-400/50'} mt-1 flex-shrink-0`}></div>
                      </div>
                      
                      <div className="flex items-center justify-between mt-auto pt-4 border-t border-white/[0.06]">
                        <div>
                          <p className="text-[10px] text-white/40 mb-0.5">Enrollment Code</p>
                          <div className="flex items-center gap-2 group/copy">
                            <p className="font-mono text-sm text-white/90">{cls.class_code}</p>
                            <button
                              onClick={(e) => copyToClipboard(e, cls.class_code, cls.class_id)}
                              className="text-white/40 hover:text-emerald-400 transition-colors"
                              title="Copy to clipboard"
                            >
                              {copiedId === cls.class_id ? (
                                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" className="text-emerald-400">
                                  <path d="M3 8l3 3 7-7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                              ) : (
                                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                                  <path d="M5.5 3.5h7v7M3.5 5.5v7h7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                              )}
                            </button>
                          </div>
                        </div>
                        <div className="text-right flex items-center justify-end">
                          <button
                            onClick={(e) => toggleClassActiveStatus(cls, e)}
                            className={`px-3 py-1.5 text-xs rounded transition-colors ${
                              cls.is_active 
                                ? 'bg-white/5 text-white/60 hover:bg-red-500/10 hover:text-red-400' 
                                : 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'
                            }`}
                          >
                            {cls.is_active ? 'Archive' : 'Activate'}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
                  <div className="w-full max-w-md bg-[#1a1d27] rounded-xl border border-white/[0.1] shadow-2xl p-6 relative" style={{ animation: 'dashboardFadeUp 300ms ease both' }}>
                    <button 
                      onClick={() => setIsModalOpen(false)}
                      className="absolute top-4 right-4 text-white/40 hover:text-white"
                      disabled={isSubmitting}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 256 256"><path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"></path></svg>
                    </button>
                    
                    <h2 className="text-lg font-bold mb-6">Create New Class</h2>
                    
                    <form onSubmit={handleCreateSubmit} className="space-y-4">
                      <div>
                        <label className="block text-xs font-medium text-white/70 mb-1">Subject Code</label>
                        <input 
                          type="text" 
                          required
                          value={formData.subject_code}
                          onChange={(e) => setFormData({...formData, subject_code: e.target.value})}
                          placeholder="e.g. CS301" 
                          className="w-full rounded-lg border border-white/[0.08] bg-[#0f1117] px-3 py-2.5 text-sm text-white focus:border-emerald-500 focus:outline-none transition" 
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-white/70 mb-1">Section</label>
                        <input 
                          type="text" 
                          required
                          value={formData.section}
                          onChange={(e) => setFormData({...formData, section: e.target.value})}
                          placeholder="e.g. BSIT 3A" 
                          className="w-full rounded-lg border border-white/[0.08] bg-[#0f1117] px-3 py-2.5 text-sm text-white focus:border-emerald-500 focus:outline-none transition" 
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-white/70 mb-1">Classroom Name</label>
                        <input 
                          type="text" 
                          required
                          value={formData.name}
                          onChange={(e) => setFormData({...formData, name: e.target.value})}
                          placeholder="e.g. Operating Systems" 
                          className="w-full rounded-lg border border-white/[0.08] bg-[#0f1117] px-3 py-2.5 text-sm text-white focus:border-emerald-500 focus:outline-none transition" 
                        />
                      </div>
                      <div className="pt-2">
                        <button 
                          type="submit" 
                          disabled={isSubmitting}
                          className="w-full rounded-lg bg-emerald-600 py-2.5 text-sm font-semibold text-white hover:bg-emerald-500 transition shadow-[0_0_15px_rgba(16,185,129,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isSubmitting ? 'Creating...' : 'Generate Class & Code'}
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              )}

              {/* Confirmation Modal */}
              <ConfirmationModal
                isOpen={confirmModal.isOpen}
                title={confirmModal.classToToggle?.is_active ? "Archive Classroom" : "Restore Classroom"}
                message={confirmModal.classToToggle?.is_active 
                  ? `Are you sure you want to archive "${confirmModal.classToToggle?.name}"? Students will no longer be able to submit tasks.`
                  : `Are you sure you want to restore "${confirmModal.classToToggle?.name}"? Students will be able to submit tasks again.`
                }
                confirmText={confirmModal.classToToggle?.is_active ? "Archive" : "Restore"}
                isDanger={confirmModal.classToToggle?.is_active}
                onConfirm={handleConfirmToggle}
                onCancel={() => setConfirmModal({ isOpen: false, classToToggle: null })}
              />

            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
