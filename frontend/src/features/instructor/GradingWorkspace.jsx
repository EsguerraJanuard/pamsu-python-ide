import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import InstructorSidebar from "../../components/layout/InstructorSidebar";

const GradingWorkspace = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [submissionData, setSubmissionData] = useState(null);
    const [gradeScore, setGradeScore] = useState('');
    const [feedbackText, setFeedbackText] = useState('');
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [telemetry, setTelemetry] = useState(null);

    useEffect(() => {
        const fetchSubmission = async () => {
            try {
                const response = await api.get(`/evaluation/submissions/${id}`);
                try {
                    const telRes = await api.get(`/logs/behavioral/submission/${id}`);
                    setTelemetry(telRes);
                } catch(e) {
                    console.error('Failed to fetch telemetry', e);
                }
                setSubmissionData(response);
                // Pre-fill if already graded
                if (response.submission?.grade_score !== null && response.submission?.grade_score !== undefined) {
                    setGradeScore(response.submission.grade_score);
                }
                if (response.submission?.feedback_text) {
                    setFeedbackText(response.submission.feedback_text);
                }
            } catch (err) {
                console.error(err);
                setError('Failed to load submission data.');
            } finally {
                setLoading(false);
            }
        };
        fetchSubmission();
    }, [id]);

    const handleGradeSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            await api.patch(`/evaluation/submissions/${id}/grade`, {
                grade_score: Number(gradeScore),
                feedback_text: feedbackText
            });
            navigate('/instructor/submissions');
        } catch (err) {
            console.error(err);
            alert('Failed to submit grade');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="flex h-screen overflow-hidden bg-bg-base">
                <div className="flex w-full flex-col lg:flex-row animate-pulse">
                    <div className="flex flex-1 flex-col border-b border-border-subtle lg:border-b-0 lg:border-r">
                        <div className="flex h-12 items-center border-b border-border-subtle bg-bg-glass px-4">
                            <div className="h-4 w-32 rounded bg-white/[0.06]"></div>
                        </div>
                        <div className="flex-1 bg-bg-base p-4">
                            <div className="h-full w-full rounded bg-white/[0.06]"></div>
                        </div>
                    </div>
                    <div className="flex w-full flex-col bg-bg-glass lg:w-[400px]">
                        <div className="flex h-12 items-center border-b border-border-subtle px-6">
                            <div className="h-4 w-24 rounded bg-white/[0.06]"></div>
                        </div>
                        <div className="flex-1 p-6 space-y-6">
                            <div className="h-24 w-full rounded bg-white/[0.06]"></div>
                            <div className="h-40 w-full rounded bg-white/[0.06]"></div>
                            <div className="h-10 w-full rounded bg-white/[0.06]"></div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-screen bg-bg-base text-text-rose">
                {error}
            </div>
        );
    }

    if (!submissionData) return null;

    const { submission, evaluation_result, ast_feedback } = submissionData;

    return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
      <InstructorSidebar />
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
                        
            <div className="mx-auto max-w-6xl ">
            <div className="flex h-screen bg-bg-base text-text-main font-sans">
            {/* Left Side: Details & Grading Form */}
            <div className="w-1/2 p-6 overflow-y-auto border-r border-border-subtle flex flex-col gap-6">
                <div className="mb-2 -mt-2">
                    <button
                        onClick={() => navigate(-1)}
                        className="flex items-center gap-1.5 rounded-lg border border-border-subtle bg-bg-glass/80 px-3 py-1.5 text-xs font-medium text-text-muted hover:border-border-subtle hover:bg-bg-glass-hover hover:text-text-main transition inline-flex w-fit"
                    >
                        <span>←</span> Back
                    </button>
                </div>
                <div>
                    <h2 className="text-2xl font-bold text-text-main mb-2">Grading Workspace</h2>
                    <p className="text-sm text-text-muted">
                        Student: <span className="text-text-emerald">{submission?.student?.name || submission?.student_id || 'Unknown'}</span>
                    </p>
                    <p className="text-sm text-text-muted">
                        Task: <span className="text-text-main">{submission?.task?.title || submission?.task_id || 'Unknown'}</span>
                    </p>
                </div>

                {/* Telemetry and Similarity Section */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="bg-bg-glass p-4 rounded-xl border border-border-subtle">
                        <h3 className="text-sm font-semibold text-text-main mb-2">Telemetry</h3>
                        <div className="space-y-1 text-sm">
                            <p className="flex justify-between">
                                <span className="text-text-muted">Tab Switches:</span>
                                <span className={telemetry?.tab_switches_count > 3 ? 'text-text-rose font-bold' : 'text-text-main'}>
                                    {telemetry?.tab_switches_count || 0}
                                </span>
                            </p>
                            <p className="flex justify-between">
                                <span className="text-text-muted">Blocked Pastes:</span>
                                <span className={telemetry?.blocked_paste_count > 0 ? 'text-text-amber font-bold' : 'text-text-main'}>
                                    {telemetry?.blocked_paste_count || 0}
                                </span>
                            </p>
                            <p className="flex justify-between">
                                <span className="text-text-muted">Mouse Exits:</span>
                                <span className={telemetry?.mouseleave_count > 5 ? 'text-text-amber font-bold' : 'text-text-main'}>
                                    {telemetry?.mouseleave_count || 0}
                                </span>
                            </p>
                        </div>
                    </div>
                    <div className="bg-bg-glass p-4 rounded-xl border border-border-subtle">
                        <h3 className="text-sm font-semibold text-text-main mb-2">Similarity (Jaccard)</h3>
                        <div className="flex items-center justify-center h-full pb-6 text-2xl font-bold">
                            {submission?.jaccard_score !== null && submission?.jaccard_score !== undefined ? (
                                <span className={(submission.jaccard_score * 100) > 70 ? 'text-text-rose' : 'text-text-emerald'}>
                                    {(submission.jaccard_score <= 1 ? submission.jaccard_score * 100 : submission.jaccard_score).toFixed(1)}%
                                </span>
                            ) : (
                                <span className="text-text-muted text-base">N/A</span>
                            )}
                        </div>
                    </div>
                </div>

                {ast_feedback && ast_feedback.length > 0 && (
                    <div className="bg-bg-glass p-4 rounded-xl border border-border-subtle">
                        <h3 className="text-lg font-semibold text-text-main mb-3 flex items-center gap-2">
                            <svg className="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            AST Feedback
                        </h3>
                        <ul className="list-disc list-inside space-y-1 text-sm text-text-muted">
                            {ast_feedback.map((fb, idx) => (
                                <li key={idx}>{fb}</li>
                            ))}
                        </ul>
                    </div>
                )}

                <div className="bg-bg-glass p-4 rounded-xl border border-border-subtle flex-1 flex flex-col">
                    <h3 className="text-lg font-semibold text-text-main mb-3 flex items-center gap-2">
                        <svg className="w-5 h-5 text-text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                        </svg>
                        Execution Output
                    </h3>
                    <div className="bg-black text-text-emerald font-mono text-sm p-4 rounded overflow-auto flex-1 min-h-[12rem] border border-border-subtle">
                        {evaluation_result?.stdout && (
                            <div className="mb-4">
                                <div className="text-text-muted mb-1 select-none"># stdout</div>
                                <pre className="whitespace-pre-wrap">{evaluation_result.stdout}</pre>
                            </div>
                        )}
                        {evaluation_result?.stderr && (
                            <div>
                                <div className="text-text-muted mb-1 select-none"># stderr</div>
                                <pre className="whitespace-pre-wrap text-text-rose">{evaluation_result.stderr}</pre>
                            </div>
                        )}
                        {!evaluation_result?.stdout && !evaluation_result?.stderr && (
                            <span className="text-text-muted italic">No execution output available.</span>
                        )}
                    </div>
                </div>

                <form onSubmit={handleGradeSubmit} className="bg-bg-glass p-4 rounded-xl border border-border-subtle flex flex-col gap-4">
                    <h3 className="text-lg font-semibold text-text-main">Manual Grading</h3>
                    <div>
                        <label className="block text-sm font-medium mb-1 text-text-muted">Score (0-100)</label>
                        <input 
                            type="number" 
                            className="w-full bg-bg-base border border-border-subtle rounded p-2 text-text-main focus:outline-none focus:border-emerald-500 transition-colors" 
                            value={gradeScore} 
                            onChange={(e) => setGradeScore(e.target.value)}
                            required
                            min="0"
                            max="100"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1 text-text-muted">Feedback</label>
                        <textarea 
                            className="w-full bg-bg-base border border-border-subtle rounded p-2 text-text-main h-24 focus:outline-none focus:border-emerald-500 transition-colors resize-y" 
                            value={feedbackText} 
                            onChange={(e) => setFeedbackText(e.target.value)}
                            placeholder="Provide feedback to the student..."
                        />
                    </div>
                    <button 
                        type="submit" 
                        disabled={submitting}
                        className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white py-2 px-4 rounded font-medium transition-colors mt-2"
                    >
                        {submitting ? 'Submitting...' : 'Submit Grade'}
                    </button>
                </form>
            </div>

            {/* Right Side: Code Editor */}
            <div className="w-1/2 flex flex-col border-l border-border-subtle bg-bg-base">
                <div className="p-4 border-b border-border-subtle bg-bg-glass flex items-center gap-2">
                    <svg className="w-5 h-5 text-text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path>
                    </svg>
                    <h3 className="text-text-main font-medium">Submitted Code</h3>
                </div>
                <textarea 
                    className="flex-1 w-full p-6 bg-bg-base text-text-emerald font-mono text-sm resize-none focus:outline-none"
                    readOnly
                    value={submission?.raw_code || ''}
                    spellCheck="false"
                />
            </div>
            </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default GradingWorkspace;
