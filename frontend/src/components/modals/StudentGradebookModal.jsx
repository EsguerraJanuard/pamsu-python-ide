import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { useNavigate } from 'react-router-dom';

const DownloadIcon = ({ className }) => <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>;
const XIcon = ({ className }) => <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>;
const UserIcon = ({ className }) => <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>;
const ActivityIcon = ({ className }) => <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>;
const CheckCircleIcon = ({ className }) => <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>;
const ClockIcon = ({ className }) => <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>;

export default function StudentGradebookModal({ isOpen, onClose, student, classId }) {
  const navigate = useNavigate();
  const [grades, setGrades] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !student || !classId) return;

    const fetchStudentGrades = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.get(`/instructors/gradebook?class_id=${classId}&student_id=${student.student_id}`);
        setGrades(response.data?.items || response.data || []);
      } catch (err) {
        console.error("Failed to fetch student grades:", err);
        setError("Failed to load student records.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchStudentGrades();
  }, [isOpen, student, classId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl border border-border-subtle bg-bg-glass shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border-subtle p-6">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/10 ring-4 ring-blue-500/5 text-text-blue">
              <UserIcon className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-text-main">{student?.name}</h2>
              <p className="text-sm text-text-muted">{student?.school_id || 'ID Unknown'} • {student?.email}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-text-muted transition hover:bg-bg-glass hover:text-text-main"
          >
            <XIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <h3 className="mb-4 text-lg font-semibold text-text-main flex items-center gap-2">
            <ActivityIcon className="h-5 w-5 text-blue-500" />
            Activity Records & Grades
          </h3>

          {isLoading ? (
            <div className="flex py-12 justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-border-subtle border-t-blue-500"></div>
            </div>
          ) : error ? (
            <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-text-rose text-center">
              {error}
            </div>
          ) : grades.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border-strong bg-bg-glass p-8 text-center">
              <p className="text-text-muted text-sm">No activity records found for this student.</p>
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-border-subtle bg-bg-glass">
              <table className="w-full text-left text-sm text-text-muted">
                <thead className="border-b border-border-subtle bg-bg-glass text-xs font-semibold uppercase tracking-wider text-text-muted">
                  <tr>
                    <th className="px-6 py-4">Activity Title</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4 text-center">Auto-Tests</th>
                    <th className="px-6 py-4 text-center">Final Score</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.06]">
                  {grades.map((grade) => (
                    <tr key={grade.submission?.sub_id || Math.random()} className="transition-colors hover:bg-bg-glass-hover">
                      <td className="px-6 py-4 font-medium text-text-main">
                        {grade.activity?.title || 'Unknown Activity'}
                      </td>
                      <td className="px-6 py-4">
                        {grade.submission?.status === 'graded' ? (
                          <span className="inline-flex items-center gap-1.5 rounded-md bg-emerald-500/10 px-2 py-1 text-xs font-medium text-emerald-400">
                            <CheckCircleIcon className="h-3.5 w-3.5" /> Graded
                          </span>
                        ) : grade.submission?.status === 'submitted' ? (
                          <span className="inline-flex items-center gap-1.5 rounded-md bg-blue-500/10 px-2 py-1 text-xs font-medium text-blue-400">
                            <ClockIcon className="h-3.5 w-3.5" /> Needs Review
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 rounded-md bg-amber-500/10 px-2 py-1 text-xs font-medium text-amber-400">
                            Working
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-center font-mono">
                        {grade.submission?.auto_score !== null && grade.submission?.auto_score !== undefined ? `${grade.submission.auto_score}%` : '-'}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <input 
                            type="number"
                            min="0"
                            max="100"
                            defaultValue={grade.manual_grade?.score_value ?? ''}
                            onBlur={async (e) => {
                              const newScore = e.target.value;
                              if (newScore && grade.submission?.sub_id && newScore !== (grade.manual_grade?.score_value ?? '').toString()) {
                                try {
                                  await api.patch(`/evaluation/submissions/${grade.submission.sub_id}/grade`, {
                                    score_value: parseInt(newScore),
                                    is_released: true
                                  });
                                } catch (err) {
                                  console.error("Failed to update score", err);
                                }
                              }
                            }}
                            className="w-16 rounded border border-border-subtle bg-bg-base px-2 py-1 text-center font-mono text-sm text-text-main focus:border-blue-500 focus:outline-none"
                            placeholder="---"
                          />
                          <span className="text-xs text-text-muted">/ 100</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        {grade.submission?.sub_id && (
                          <button
                            onClick={() => navigate(`/instructor/submissions/${grade.submission.sub_id}`)}
                            className="text-xs font-semibold text-blue-400 hover:text-blue-300 transition-colors"
                          >
                            View Work
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-border-subtle p-6 flex justify-end gap-3">
          <button
            onClick={() => {
              const csvData = [
                ["Activity", "Status", "Auto Score", "Final Score"],
                ...grades.map(g => [
                  `"${g.activity?.title || ''}"`, 
                  g.submission?.status || 'N/A', 
                  g.submission?.auto_score !== null && g.submission?.auto_score !== undefined ? `${g.submission.auto_score}%` : 'N/A', 
                  g.manual_grade?.score_value ?? 'N/A'
                ])
              ].map(e => e.join(",")).join("\n");
              const blob = new Blob([csvData], { type: 'text/csv' });
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `${student?.name || 'student'}_grades.csv`;
              a.click();
            }}
            disabled={grades.length === 0}
            className="flex items-center gap-2 rounded-lg border border-border-subtle bg-bg-glass px-4 py-2 text-sm font-semibold text-text-main transition hover:bg-bg-glass-hover disabled:opacity-50"
          >
            <DownloadIcon className="h-4 w-4" />
            Export Grades
          </button>
          <button
            onClick={onClose}
            className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-500"
          >
            Done
          </button>
        </div>

      </div>
    </div>
  );
}
