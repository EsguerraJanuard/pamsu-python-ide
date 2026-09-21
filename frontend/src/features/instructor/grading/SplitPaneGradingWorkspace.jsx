/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../../services/api';

const SplitPaneGradingWorkspace = () => {
  const { classId, taskId } = useParams();
  const [students, setStudents] = useState([]);
  const [submissions, setSubmissions] = useState({});
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [detailedSub, setDetailedSub] = useState(null);
  const [loading, setLoading] = useState(true);

  // Grade form state
  const [gradeScore, setGradeScore] = useState('');
  const [feedbackText, setFeedbackText] = useState('');
  const [savingGrade, setSavingGrade] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch roster
        const rosterRes = await api.get(`/classrooms/${classId}/members`);
        const roster = rosterRes;
        setStudents(roster);

        // Fetch submissions for this task
        // We might not have a direct endpoint, but let's assume we can fetch submissions for a task or get them from review queue
        const subsRes = await api.get(`/instructors/review-queue`, { params: { task_id: taskId } });
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

    const sub = submissions[student.id];
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
      alert('Grade saved successfully');
    } catch (error) {
      console.error('Error saving grade:', error);
      alert('Failed to save grade');
    } finally {
      setSavingGrade(false);
    }
  };

  const handleExport = () => {
    let csv = "Student Name,School ID,Status,Score,Submitted At,Feedback\n";
    students.forEach((s) => {
      const sub = submissions[s.id];
      const name = s.full_name || s.name || '';
      const sid = s.school_id || '';
      const status = sub?.status || 'Missing';
      const score = sub?.grade_score ?? '';
      const submitted = sub?.submitted_at ? new Date(sub.submitted_at).toLocaleString() : '';
      const feedback = sub?.feedback_text ? `"${sub.feedback_text.replace(/"/g, '""')}"` : '';
      csv += `"${name}","${sid}","${status}","${score}","${submitted}",${feedback}\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `class_${classId}_task_${taskId}_grades.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) {
    return <div className="p-6 text-white/80 bg-[#0f1117] h-screen">Loading workspace...</div>;
  }

  const selectedSub = selectedStudent ? submissions[selectedStudent.id] : null;

  return (
    <div className="flex flex-row h-screen bg-[#0f1117] text-white/80">
      {/* Left Panel: Master List */}
      <div className="w-1/3 border-r border-slate-800 flex flex-col bg-[#0f1117]">
        <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
          <h2 className="text-lg font-semibold text-white">Students</h2>
          <button 
            onClick={handleExport}
            className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm transition-colors"
          >
            Export Submissions
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {students.map(student => {
            const sub = submissions[student.id];
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
                key={student.id}
                onClick={() => handleSelectStudent(student)}
                className={`p-4 border-b border-slate-800 cursor-pointer hover:bg-slate-800/50 transition-colors flex justify-between items-center ${selectedStudent?.id === student.id ? 'bg-slate-800/80' : ''}`}
              >
                <div>
                  <p className="font-medium text-white">{student.name || student.email || `Student ${student.id}`}</p>
                  <p className="text-sm text-slate-400">{student.email}</p>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${badgeColor}`}>
                  {badgeText}
                </span>
              </div>
            );
          })}
          {students.length === 0 && (
            <div className="p-4 text-slate-500 text-center">No students found.</div>
          )}
        </div>
      </div>

      {/* Right Panel: Detail View */}
      <div className="w-2/3 flex flex-col bg-[#0f1117] overflow-y-auto">
        {selectedStudent ? (
          <div className="p-6 flex flex-col gap-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-white">
                Submission: {selectedStudent.name || selectedStudent.email || `Student ${selectedStudent.id}`}
              </h2>
            </div>

            {selectedSub ? (
              <>
                <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-white mb-2">Submitted Code</h3>
                  <pre className="bg-[#0b0c10] p-4 rounded text-sm text-blue-300 overflow-x-auto border border-slate-800">
                    {detailedSub?.raw_code || detailedSub?.code || '# Loading code... or No code provided'}
                  </pre>
                </div>

                <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-white mb-2">Execution Feedback / Logs</h3>
                  <pre className="bg-[#0b0c10] p-4 rounded text-sm text-gray-300 overflow-x-auto border border-slate-800 whitespace-pre-wrap">
                    {detailedSub?.execution_log || detailedSub?.feedback_text || detailedSub?.ast_feedback?.join('\n') || 'Loading execution logs or not available.'}
                  </pre>
                </div>

                <form onSubmit={handleSubmitGrade} className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 flex flex-col gap-4">
                  <h3 className="text-lg font-medium text-white">Manual Grading</h3>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-1">Score</label>
                    <input
                      type="number"
                      step="0.01"
                      value={gradeScore}
                      onChange={(e) => setGradeScore(e.target.value)}
                      className="w-[150px] bg-[#0b0c10] border border-slate-700 rounded p-2 text-white focus:outline-none focus:border-blue-500"
                      placeholder="e.g. 95"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-1">Feedback</label>
                    <textarea
                      value={feedbackText}
                      onChange={(e) => setFeedbackText(e.target.value)}
                      className="w-full bg-[#0b0c10] border border-slate-700 rounded p-2 text-white h-32 focus:outline-none focus:border-blue-500"
                      placeholder="Enter feedback for the student..."
                    />
                  </div>

                  <div>
                    <button 
                      type="submit" 
                      disabled={savingGrade}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors disabled:opacity-50"
                    >
                      {savingGrade ? 'Saving...' : 'Save Grade'}
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <div className="text-slate-400 italic bg-slate-900/30 p-6 rounded border border-slate-800 text-center">
                No submission found for this student.
              </div>
            )}
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-500">
            Select a student from the left panel to view their submission.
          </div>
        )}
      </div>
    </div>
  );
};

export default SplitPaneGradingWorkspace;

