import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../../services/api';
import InstructorSidebar from '../../../components/layout/InstructorSidebar';
import { DiffEditor } from '@monaco-editor/react';
import AlertModal from '../../../components/modals/AlertModal';

const SplitPaneGradingWorkspace = () => {
  const { classId, taskId } = useParams();
  const navigate = useNavigate();
  const [students, setStudents] = useState([]);
  const [submissions, setSubmissions] = useState({});
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [detailedSub, setDetailedSub] = useState(null);
  const [loading, setLoading] = useState(true);

  // Grade form state
  const [gradeScore, setGradeScore] = useState('');
  const [feedbackText, setFeedbackText] = useState('');
  const [savingGrade, setSavingGrade] = useState(false);
  const [alertConfig, setAlertConfig] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch roster
        const rosterRes = await api.get(`/classrooms/${classId}/members`);
        const roster = Array.isArray(rosterRes) ? rosterRes : (rosterRes?.data || []);
        setStudents(roster);

        // Fetch submissions for this task
        // We append task_id to URL directly since custom fetch api wrapper ignores params object
        const subsRes = await api.get(`/instructors/review-queue?task_id=${taskId}`);
        // Map submissions by student_id
        const subsMap = {};
        if (subsRes && Array.isArray(subsRes.items)) {
          subsRes.items.forEach(sub => {
              if (sub.activity?.task_id === parseInt(taskId)) {
                 subsMap[sub.student.student_id] = sub;
              }
          });
        }
        setSubmissions(subsMap);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };
    if (classId && taskId) {
      fetchData();
    }
  }, [classId, taskId]);

  const handleSelectStudent = async (student) => {
    setSelectedStudent(student);
    setDetailedSub(null); // Clear previous
    setGradeScore('');
    setFeedbackText('');

    const sub = submissions[student.student_id];
    if (sub && sub.sub_id) {
      try {
        // 1. Fetch the raw code from the instructor submissions endpoint
        const codeRes = await api.get(`/instructors/submissions/${sub.sub_id}`);
        
        // 2. Fetch the evaluation details (which contains the AST analyses and the instructor grade)
        const evalRes = await api.get(`/evaluation/submissions/${sub.sub_id}`);
        
        setDetailedSub(codeRes);
        
        // Pre-fill grade if it exists
        const manualGrade = evalRes.instructor_grade;
        if (manualGrade) {
          setGradeScore(manualGrade.score);
          setFeedbackText(manualGrade.feedback || '');
        }
      } catch (err) {
        console.error("Failed to fetch submission details", err);
        setAlertConfig({ title: "Error", message: "Failed to fetch submission details.", isError: true });
      }
    }
  };

  const handleSubmitGrade = async (e) => {
    e.preventDefault();
    if (!selectedStudent) return;
    const sub = submissions[selectedStudent.id];
    if (!sub || !sub.sub_id) return;

    setSavingGrade(true);
      try {
      // MUST send 'score' and 'feedback' to match InstructorGradeUpdate Pydantic schema
      const res = await api.patch(`/evaluation/submissions/${sub.sub_id}/grade`, {
        score: parseFloat(gradeScore),
        feedback: feedbackText
      });
      
      // Update local state so the badge updates immediately
      setSubmissions(prev => ({
        ...prev,
        [selectedStudent.id]: {
          ...prev[selectedStudent.id],
          has_manual_grade: true,
          status: 'graded'
        }
      }));
      setAlertConfig({ title: 'Success', message: 'Grade saved successfully', isError: false });
    } catch (error) {
      console.error('Error saving grade:', error);
      setAlertConfig({ title: 'Error', message: 'Failed to save grade', isError: true });
    } finally {
      setSavingGrade(false);
    }
  };

  const handleExport = async () => {
    try {
      const token = localStorage.getItem('pamsu_access_token');
      const baseUrl = import.meta.env.VITE_API_BASE_URL ;
      const response = await fetch(`${baseUrl}/reports/classrooms/${classId}/gradebook.csv?task_id=${taskId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error("Failed to export grades from server");
      }
      
      // Get filename from Content-Disposition header if possible
      let filename = `class_${classId}_task_${taskId}_grades.xlsx`;
      const disposition = response.headers.get('Content-Disposition');
      if (disposition && disposition.includes('filename="')) {
        filename = disposition.split('filename="')[1].split('"')[0];
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error("Export Error:", err);
      setAlertConfig({ title: 'Export Failed', message: 'Failed to export Excel gradebook. Please try again.', isError: true });
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
        <InstructorSidebar />
        <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
          <div className="flex min-h-0 flex-1">
            <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8 flex flex-col">
              <div className="max-w-6xl mx-auto w-full flex-1 flex flex-col">
                <div className="mb-6">
            <button onClick={() => navigate(-1)} className="text-sm text-text-muted hover:text-text-main flex items-center gap-2 transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
              Back to Activities
            </button>
          </div>
          <header className="mb-8">
            <h1 className="text-3xl font-bold text-text-main mb-2">Activity Grading Workspace</h1>
            <p className="text-text-muted">Task ID: {taskId} • Loading data...</p>
          </header>
          <div className="flex min-h-0 flex-1 flex-row border border-border-subtle rounded-xl overflow-hidden shadow-sm">
            {/* Left Panel Skeleton */}
            <div className="w-1/3 border-r border-border-subtle flex flex-col bg-bg-panel/30">
              <div className="p-4 border-b border-border-subtle flex justify-between items-center bg-bg-glass animate-pulse">
                <div className="h-6 bg-border-subtle rounded w-24"></div>
                <div className="h-8 bg-border-subtle rounded w-32"></div>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-4 animate-pulse">
                {[1, 2, 3, 4, 5].map(i => (
                  <div key={i} className="p-4 border border-border-subtle rounded-lg flex justify-between items-center">
                    <div>
                      <div className="h-5 bg-border-subtle rounded w-32 mb-2"></div>
                      <div className="h-4 bg-border-subtle rounded w-40"></div>
                    </div>
                    <div className="h-6 w-16 bg-border-subtle rounded-full"></div>
                  </div>
                ))}
              </div>
            </div>
            {/* Right Panel Skeleton */}
            <div className="w-2/3 p-6 flex flex-col gap-6 bg-bg-base animate-pulse">
              <div className="h-8 bg-border-subtle rounded w-64 mb-4"></div>
              <div className="bg-bg-glass border border-border-subtle rounded-lg p-4 h-64">
                <div className="h-6 bg-border-subtle rounded w-40 mb-4"></div>
                <div className="h-4 bg-border-subtle rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-border-subtle rounded w-1/2"></div>
              </div>
              <div className="bg-bg-glass border border-border-subtle rounded-lg p-4 h-48">
                <div className="h-6 bg-border-subtle rounded w-48 mb-4"></div>
                <div className="h-4 bg-border-subtle rounded w-full"></div>
              </div>
            </div>
          </div>
              </div>
            </main>
          </div>
        </div>
      </div>
    );
  }

  const selectedSub = selectedStudent ? submissions[selectedStudent.id] : null;

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
  <InstructorSidebar />
  <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
    <div className="flex min-h-0 flex-1">
      <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8 flex flex-col">
        <div className="max-w-6xl mx-auto w-full flex-1 flex flex-col">
          <div className="mb-6 flex justify-between items-start shrink-0">
      <div>
        <button onClick={() => navigate(-1)} className="text-sm text-text-muted hover:text-text-main flex items-center gap-2 transition-colors mb-6">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
          Back to Activities
        </button>
        <header className="mb-4">
          <h1 className="text-3xl font-bold text-text-main mb-2">Activity Grading Workspace</h1>
          <p className="text-text-muted">Class {classId} • Task {taskId}</p>
        </header>
      </div>
      <div className="mt-10">
        <button 
          onClick={handleExport}
          className="rounded-lg bg-psu-maroon px-4 py-2 text-sm font-semibold text-white shadow-lg transition-all hover:bg-psu-maroon hover:shadow-psu-maroon/20 active:scale-95 flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
          Export Grades
        </button>
      </div>
    </div>
    <div className="flex min-h-0 flex-1 flex-row border border-border-subtle rounded-xl overflow-hidden shadow-sm bg-bg-base">
      {/* Left Panel: Master List */}
      <div className="w-1/3 border-r border-border-subtle flex flex-col bg-bg-panel/30">
        <div className="px-5 py-4 border-b border-border-subtle flex justify-between items-center bg-bg-glass shadow-sm z-0">
          <h2 className="text-sm font-bold tracking-wider text-text-muted uppercase">Student Submissions</h2>
          <span className="text-xs font-mono text-emerald-400 bg-psu-maroon/10 px-2 py-0.5 rounded-full border border-psu-maroon/20">{students.length}</span>
        </div>
        <div className="flex-1 overflow-y-auto">
          {students.map(student => {
            const sub = submissions[student.student_id];
            let badgeText = 'Missing';
            let badgeColor = 'bg-red-900/50 text-red-400 border border-red-800';
            
            if (sub) {
              if (sub.has_manual_grade || sub.status === 'graded') {
                badgeText = 'Graded';
                badgeColor = 'bg-green-900/50 text-green-400 border border-green-800';
              } else if (sub.status === 'late') {
                badgeText = 'Late';
                badgeColor = 'bg-yellow-900/50 text-yellow-400 border border-yellow-800';
              } else {
                badgeText = 'Submitted';
                badgeColor = 'bg-blue-900/50 text-blue-400 border border-blue-800';
              }
            }

            return (
              <div 
                key={student.student_id}
                onClick={() => handleSelectStudent(student)}
                className={`p-4 border-b border-border-subtle cursor-pointer hover:bg-bg-glass transition-colors flex justify-between items-center ${selectedStudent?.student_id === student.student_id ? 'bg-bg-glass-hover' : ''}`}
              >
                <div>
                  <p className="font-medium text-text-main">{student.name || student.email || `Student ${student.student_id}`}</p>
                  <p className="text-sm text-text-muted">{student.email}</p>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${badgeColor}`}>
                  {badgeText}
                </span>
              </div>
            );
          })}
          {students.length === 0 && (
            <div className="p-4 text-text-muted text-center">No students found.</div>
          )}
        </div>
      </div>

      {/* Right Panel: Detail View */}
      <div className="w-2/3 flex flex-col bg-bg-base overflow-y-auto">
        {selectedStudent ? (
          <div className="flex-1 p-8 flex flex-col gap-8 max-w-5xl mx-auto w-full">
            <div className="flex items-center gap-4 pb-4 border-b border-border-subtle">
              <div className="w-12 h-12 rounded-full bg-psu-maroon/10 border border-psu-maroon/20 flex items-center justify-center text-emerald-400 font-bold text-lg uppercase shadow-sm">
                {(selectedStudent.name || selectedStudent.email || '?').charAt(0)}
              </div>
              <div>
                <h2 className="text-2xl font-bold text-text-main">
                  {selectedStudent.name || selectedStudent.email || `Student ${selectedStudent.id}`}
                </h2>
                                  <p className="text-sm text-text-muted mt-0.5">Student ID: {selectedStudent.student_id || selectedStudent.id}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Academic Integrity:</span>
                    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-bold ring-1 ring-inset ${
                      (selectedStudent.academic_integrity_score ?? 100) >= 90 ? "bg-psu-maroon/10 text-emerald-400 ring-psu-maroon/20" : 
                      (selectedStudent.academic_integrity_score ?? 100) >= 70 ? "bg-amber-500/10 text-amber-400 ring-amber-500/20" : 
                      "bg-rose-500/10 text-rose-400 ring-rose-500/20"
                    }`}>
                      {Math.round(selectedStudent.academic_integrity_score ?? 100)}%
                    </span>
                  </div>
              </div>
            </div>

            {/* NEW LAYOUT: Violations -> Grading -> Code */}
              {selectedSub ? (
                <>
                  {/* TOP SECTION: Student Violations & Activity Analysis */}
                  <div className="bg-bg-glass border border-border-subtle rounded-xl p-6 shadow-sm mb-6">
                     <h3 className="text-lg font-bold text-psu-red dark:text-psu-gold mb-4 flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                        Student Violations & Analysis
                     </h3>
                     
                     <div className="space-y-6">
                        {/* Telemetry Indicators */}
                                                  <div className="grid grid-cols-2 gap-4 border-b border-border-subtle pb-6">
                            {(detailedSub?.jaccard_score !== undefined && detailedSub?.jaccard_score !== null) && (
                              <div className={`flex flex-col items-center justify-center p-4 rounded-xl border ${(detailedSub?.jaccard_score >= 70) ? 'bg-psu-maroon/10 border-psu-maroon/30 text-psu-red' : 'bg-bg-panel border-border-strong text-text-main'}`}>
                                <span className="text-[10px] font-bold uppercase tracking-wider opacity-60 mb-1">Similarity</span>
                                <span className="text-2xl font-black">{detailedSub?.jaccard_score.toFixed(1)}%</span>
                              </div>
                            )}
                            {detailedSub?.coding_session && (
                              <>
                                <div className={`flex flex-col items-center justify-center p-4 rounded-xl border ${(detailedSub?.coding_session.tab_switch_count > 3) ? 'bg-amber-500/10 border-amber-500/30 text-amber-500' : 'bg-bg-panel border-border-strong text-text-main'}`}>
                                  <span className="text-[10px] font-bold uppercase tracking-wider opacity-60 mb-1">Tab Switches</span>
                                  <span className="text-2xl font-black">{detailedSub?.coding_session.tab_switch_count}</span>
                                </div>
                                <div className={`flex flex-col items-center justify-center p-4 rounded-xl border ${(detailedSub?.coding_session.blocked_paste_count > 0) ? 'bg-psu-maroon/10 border-psu-maroon/30 text-psu-red' : 'bg-bg-panel border-border-strong text-text-main'}`}>
                                  <span className="text-[10px] font-bold uppercase tracking-wider opacity-60 mb-1">Blocked Pastes</span>
                                  <span className="text-2xl font-black">{detailedSub?.coding_session.blocked_paste_count}</span>
                                </div>
                                <div className={`flex flex-col items-center justify-center p-4 rounded-xl border ${(detailedSub?.coding_session.mouseleave_count > 5) ? 'bg-amber-500/10 border-amber-500/30 text-amber-500' : 'bg-bg-panel border-border-strong text-text-main'}`}>
                                  <span className="text-[10px] font-bold uppercase tracking-wider opacity-60 mb-1">Mouse Leaves</span>
                                  <span className="text-2xl font-black">{detailedSub?.coding_session.mouseleave_count}</span>
                                </div>
                              </>
                            )}
                          </div>
                          {/* AST Analysis & Execution Logs */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                             <div className="flex flex-col h-full">
                                 <h4 className="text-xs font-bold text-text-muted mb-2 uppercase tracking-wider">AST Analysis</h4>
                               <div className="flex-1 bg-bg-panel p-4 rounded-lg border border-border-strong min-h-[120px] max-h-[250px] overflow-y-auto shadow-inner">
                                 {detailedSub?.ast_feedback && detailedSub.ast_feedback.length > 0 ? (
                                   <ul className="space-y-3">
                                     {detailedSub.ast_feedback.map((fb, idx) => {
                                        const isPass = fb.includes("PASSED");
                                        const cleanText = fb.replace(/\[.*?\]\s*PASSED\s*-\s*/, '').replace(/\[.*?\]\s*FAILED\s*-\s*/, '').replace(/\[.*?\]\s*/, '');
                                        return (
                                          <li key={idx} className={`flex items-start gap-2 text-sm ${isPass ? 'text-text-main opacity-80' : 'text-psu-red font-semibold'}`}>
                                            <svg className={`w-4 h-4 mt-0.5 shrink-0 ${isPass ? 'text-text-brand' : 'text-psu-red'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                              {isPass ? (
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                              ) : (
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                              )}
                                            </svg>
                                            <span className="leading-snug font-mono text-[11px]">{cleanText}</span>
                                          </li>
                                        );
                                     })}
                                   </ul>
                                 ) : (
                                   <div className="flex flex-col items-center gap-2 text-text-brand h-full justify-center opacity-80 py-6">
                                      <svg className="w-8 h-8 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                      </svg>
                                      <span className="text-xs font-semibold uppercase tracking-widest text-text-main mt-1">Perfect Structure</span>
                                      <span className="text-[10px] text-text-muted">Passed all AST requirements.</span>
                                   </div>
                                 )}
                               </div>
                             </div>
                             <div className="flex flex-col h-full">
                                 <h4 className="text-xs font-bold text-text-muted mb-2 uppercase tracking-wider">Execution Logs</h4>
                               <div className="flex-1 bg-[#0a0a0f] p-4 rounded-lg border border-border-strong min-h-[120px] max-h-[250px] overflow-y-auto font-mono text-[11px] leading-relaxed shadow-inner">
                                 {detailedSub?.execution_log ? (
                                   <span className="text-slate-300 whitespace-pre-wrap">{detailedSub.execution_log}</span>
                                 ) : (
                                   <div className="flex items-center justify-center h-full text-slate-500 italic py-6">
                                     ~ Execution logs empty or unavailable ~
                                   </div>
                                 )}
                               </div>
                             </div>
                          </div>
                       </div>
                    </div>
  
                    {/* MIDDLE SECTION: Grading Form */}
                  <form onSubmit={handleSubmitGrade} className="bg-bg-glass border border-border-subtle rounded-xl p-6 shadow-sm flex flex-col gap-6 mb-6">
                    <h3 className="text-lg font-bold text-text-main border-b border-border-subtle pb-4">Activity Grading Assessment</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                       {/* Suggested Grade */}
                       <div className="bg-psu-maroon/5 border border-psu-maroon/20 dark:bg-psu-gold/5 dark:border-psu-gold/20 rounded-lg p-5 flex flex-col justify-center">
                          <label className="block text-xs font-bold text-text-brand mb-2 uppercase tracking-wider">Suggested Grade</label>
                          <div className="text-5xl font-black text-text-main tracking-tight">
                            {(() => {
                                if (!detailedSub) return '0';
                                if (detailedSub.jaccard_score >= 70) return '0';
                                
                                let score = 100;
                                if (detailedSub.ast_feedback && detailedSub.ast_feedback.length > 0) {
                                    const fails = detailedSub.ast_feedback.filter(f => f.includes('missing') || f.includes('failed') || f.includes('Missing'));
                                    score -= (fails.length * 20);
                                }
                                if (detailedSub.execution_log && detailedSub.execution_log.toLowerCase().includes('error')) {
                                    score -= 30; 
                                }
                                if (score < 0) score = 0;
                                return score;
                            })()}
                          </div>
                          <p className="text-xs text-text-muted mt-3">Calculated from AST rule satisfaction and syntax validation.</p>
                       </div>

                       {/* Manual Grade */}
                       <div className="flex flex-col justify-center">
                          <label className="block text-xs font-bold text-text-muted mb-2 uppercase tracking-wider">Manual Score</label>
                                                      <input
                              type="number"
                              min="0"
                              max="100"
                              step="0.01"
                              value={gradeScore}
                              onChange={(e) => {
                                let val = e.target.value;
                                if (val === '') {
                                  setGradeScore('');
                                  return;
                                }
                                let num = parseFloat(val);
                                if (num < 0) val = '0';
                                if (num > 100) val = '100';
                                setGradeScore(val);
                              }}
                              onKeyDown={(e) => {
                                if (e.key === '-' || e.key === 'e' || e.key === 'E' || e.key === '+') {
                                  e.preventDefault();
                                }
                              }}
                              className="w-full bg-bg-panel border border-border-strong rounded-lg px-4 py-3 text-2xl font-bold text-text-main focus:outline-none focus:border-psu-maroon focus:ring-2 focus:ring-psu-maroon/30 transition-all shadow-sm [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none m-0"
                              placeholder="e.g. 95"
                            />
                          <p className="text-xs text-text-muted mt-3">Override the suggested grade manually here.</p>
                       </div>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-text-muted mb-2 uppercase tracking-wider">Instructor Feedback</label>
                      <textarea
                        value={feedbackText}
                        onChange={(e) => setFeedbackText(e.target.value)}
                        className="w-full bg-bg-panel border border-border-strong rounded-lg p-4 text-text-main h-32 focus:outline-none focus:border-psu-maroon focus:ring-2 focus:ring-psu-maroon/30 transition-all shadow-sm"
                        placeholder="Provide constructive feedback for the student..."
                      />
                    </div>

                    <div className="flex gap-4 pt-4 border-t border-border-subtle mt-2">
                      <button 
                        type="submit" 
                        disabled={savingGrade}
                        className="px-6 py-3 bg-psu-maroon hover:bg-psu-red text-white font-bold rounded-lg shadow-sm transition-all disabled:opacity-50 flex-1 flex items-center justify-center gap-2"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                        {savingGrade ? 'Saving Grade...' : 'Save Final Grade'}
                      </button>
                      
                      {detailedSub?.retake_requested && (
                        <button
                          type="button"
                          onClick={async () => {
                            if (!window.confirm("Are you sure you want to allow a retake? The student workspace will be unlocked.")) return;
                            try {
                              await api.patch(`/submissions/${detailedSub.sub_id || detailedSub.id}/allow-retake`);
                              alert("Retake approved! Student can now resubmit.");
                              setDetailedSub({...detailedSub, retake_allowed: true, retake_requested: false});
                              window.location.reload();
                            } catch (err) {
                              alert("Failed to approve retake.");
                            }
                          }}
                          className="px-6 py-3 bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 font-bold rounded-lg transition-all hover:bg-amber-500/20"
                        >
                          Approve Retake
                        </button>
                      )}
                      
                      {!detailedSub?.retake_requested && !detailedSub?.retake_allowed && (
                        <button
                          type="button"
                          onClick={async () => {
                            if (!window.confirm("Are you sure you want to allow a retake? The student workspace will be unlocked.")) return;
                            try {
                              await api.patch(`/submissions/${detailedSub.sub_id || detailedSub.id}/allow-retake`);
                              alert("Retake allowed! Student can now resubmit.");
                              setDetailedSub({...detailedSub, retake_allowed: true});
                              window.location.reload();
                            } catch (err) {
                              alert("Failed to allow retake.");
                            }
                          }}
                          className="px-4 py-3 bg-bg-base border border-border-strong text-text-muted text-sm font-bold rounded-lg transition-all hover:bg-bg-glass-hover hover:text-text-main"
                        >
                          Allow Retake
                        </button>
                      )}
                    </div>
                  </form>

                  {/* BOTTOM SECTION: Submitted Code */}
                  <div className="bg-bg-glass border border-border-subtle rounded-xl p-6 shadow-sm flex flex-col">
                    <h3 className="text-lg font-bold text-text-main mb-4 border-b border-border-subtle pb-4">Submitted Code vs Starter Code</h3>
                    <div className="h-[500px] border border-border-strong rounded-lg overflow-hidden shadow-sm">
                      {!detailedSub ? (
                         <div className="flex items-center justify-center h-full text-sm text-text-muted animate-pulse">Loading submission code...</div>
                      ) : (
                        <DiffEditor
                          height="100%"
                          language="python"
                          theme={'vs-dark'}
                          original={detailedSub?.activity?.starter_code || detailedSub?.coding_session?.initial_code || '# No starter code available'}
                          modified={detailedSub?.raw_code || detailedSub?.code || '# No code provided'}
                          options={{
                            readOnly: true,
                            minimap: { enabled: false },
                            scrollBeyondLastLine: false,
                            renderSideBySide: true,
                            wordWrap: "on"
                          }}
                        />
                      )}
                    </div>
                  </div>
                </>
              ) : (
              <div className="text-text-muted italic bg-bg-panel p-6 rounded border border-border-subtle text-center">
                No submission found for this student.
              </div>
            )}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-text-muted bg-bg-base bg-blend-overlay">
            <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mb-4 border border-border-subtle shadow-lg">
              <svg className="w-8 h-8 text-psu-maroon/50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>
            </div>
            <h3 className="text-lg font-medium text-text-main mb-1">No Submission Selected</h3>
            <p className="text-sm max-w-sm text-center">Select a student from the left panel to review their code and provide a grade.</p>
          </div>
        )}
      </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  <AlertModal 
        isOpen={!!alertConfig} 
        title={alertConfig?.title} 
        message={alertConfig?.message} 
        isError={alertConfig?.isError} 
        onClose={() => setAlertConfig(null)} 
      />
</div>
  );
};

export default SplitPaneGradingWorkspace;
