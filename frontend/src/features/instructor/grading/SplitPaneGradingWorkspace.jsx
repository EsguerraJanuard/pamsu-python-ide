/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../../services/api';
import InstructorSidebar from '../../../components/layout/InstructorSidebar';
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
      try {
        setLoading(true);
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
      }
    }
  };

  const handleSubmitGrade = async (e) => {
    e.preventDefault();
    if (!selectedStudent) return;
    const sub = submissions[selectedStudent.id];
    if (!sub || !sub.sub_id) return;

    try {
      setSavingGrade(true);
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
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/reports/classrooms/${classId}/tasks/${taskId}/excel`, {
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
              Back to Class
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
          Back to Class
        </button>
        <header className="mb-4">
          <h1 className="text-3xl font-bold text-text-main mb-2">Activity Grading Workspace</h1>
          <p className="text-text-muted">Class {classId} • Task {taskId}</p>
        </header>
      </div>
      <div className="mt-10">
        <button 
          onClick={handleExport}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-lg transition-all hover:bg-emerald-500 hover:shadow-emerald-500/20 active:scale-95 flex items-center gap-2"
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
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">{students.length}</span>
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
              <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-lg uppercase shadow-sm">
                {(selectedStudent.name || selectedStudent.email || '?').charAt(0)}
              </div>
              <div>
                <h2 className="text-2xl font-bold text-text-main">
                  {selectedStudent.name || selectedStudent.email || `Student ${selectedStudent.id}`}
                </h2>
                <p className="text-sm text-text-muted mt-0.5">Student ID: {selectedStudent.student_id || selectedStudent.id}</p>
              </div>
            </div>

            {selectedSub ? (
              <>
                <div className="bg-bg-glass border border-border-subtle rounded-lg p-4">
                  <h3 className="text-lg font-medium text-text-main mb-2">Submitted Code</h3>
                  <pre className="bg-bg-panel p-4 rounded text-sm text-emerald-400 overflow-x-auto border border-border-subtle">
                    {detailedSub?.raw_code || detailedSub?.code || '# Loading code... or No code provided'}
                  </pre>
                </div>

                <div className="bg-bg-glass border border-border-subtle rounded-lg p-4">
                  <h3 className="text-lg font-medium text-text-main mb-2">Execution Feedback / Logs</h3>
                  <pre className="bg-bg-panel p-4 rounded text-sm text-text-muted overflow-x-auto border border-border-subtle whitespace-pre-wrap">
                    {detailedSub?.execution_log || detailedSub?.feedback_text || detailedSub?.ast_feedback?.join('\n') || 'Loading execution logs or not available.'}
                  </pre>
                </div>

                <form onSubmit={handleSubmitGrade} className="bg-bg-glass border border-border-subtle rounded-lg p-4 flex flex-col gap-4">
                  <h3 className="text-lg font-medium text-text-main">Manual Grading</h3>
                  
                  <div>
                    <label className="block text-sm font-medium text-text-muted mb-1">Score</label>
                    <input
                      type="number"
                      step="0.01"
                      value={gradeScore}
                      onChange={(e) => setGradeScore(e.target.value)}
                      className="w-[150px] bg-bg-panel border border-border-subtle rounded p-2 text-text-main focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                      placeholder="e.g. 95"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-text-muted mb-1">Feedback</label>
                    <textarea
                      value={feedbackText}
                      onChange={(e) => setFeedbackText(e.target.value)}
                      className="w-full bg-bg-panel border border-border-subtle rounded p-2 text-text-main h-32 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                      placeholder="Enter feedback for the student..."
                    />
                  </div>

                  <div>
                    <button 
                      type="submit" 
                      disabled={savingGrade}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded transition-colors disabled:opacity-50"
                    >
                      {savingGrade ? 'Saving...' : 'Save Grade'}
                    </button>
                  </div>
                </form>
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
              <svg className="w-8 h-8 text-emerald-500/50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>
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

