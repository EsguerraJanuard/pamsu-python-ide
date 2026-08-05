import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../../services/api";

export default function ClassRosterView() {
  const { id: classId } = useParams();
  const navigate = useNavigate();
  const [students, setStudents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [studentToRemove, setStudentToRemove] = useState(null);
  const [isRemoving, setIsRemoving] = useState(false);

  const [classroom, setClassroom] = useState(null);

  useEffect(() => {
    fetchRoster();
  }, [classId]);

  const fetchRoster = async () => {
    setIsLoading(true);
    try {
      const [classData, membersData] = await Promise.all([
        api.get(`/classrooms/${classId}`),
        api.get(`/classrooms/${classId}/members`),
      ]);
      setClassroom(classData);
      setStudents(membersData.filter(m => m.status !== "removed") || []);
    } catch (err) {
      setError(err.message || "Failed to load roster data.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveConfirm = async () => {
    if (!studentToRemove) return;
    setIsRemoving(true);
    try {
      await api.patch(`/classrooms/enrollments/${studentToRemove.enrollment_id}/status`, {
        status: "removed",
      });
      
      setStudents((prev) => prev.filter((s) => s.enrollment_id !== studentToRemove.enrollment_id));
      setStudentToRemove(null);
    } catch (err) {
      alert(err.message || "Failed to remove student.");
    } finally {
      setIsRemoving(false);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-[#0f1117] select-none">
      <div className="flex-1 overflow-y-auto p-6 sm:p-8">
        <div className="mx-auto max-w-6xl">
          <header className="mb-6 flex items-center justify-between">
            <div>
              <button 
                onClick={() => navigate('/instructor/dashboard')}
                className="mb-4 flex items-center gap-2 text-xs font-semibold text-emerald-400 transition-colors hover:text-emerald-300"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-2xl font-bold text-white">
                {classroom ? `${classroom.subject_code} - ${classroom.section}` : "Class Roster"}
              </h1>
              <p className="mt-1 text-sm text-white/40">
                {classroom ? classroom.name : "Manage enrolled students."}
              </p>
            </div>
            <div className="text-sm font-semibold text-emerald-400">
              Total Students: {students.length}
            </div>
          </header>

          {isLoading ? (
            <div className="flex h-40 items-center justify-center text-sm text-white/40">Loading roster...</div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-white/[0.06] bg-[#1a1d27]">
              <table className="w-full text-left text-sm text-white/70">
                <thead className="border-b border-white/[0.06] bg-white/[0.02] text-xs font-semibold uppercase tracking-wider text-white/50">
                  <tr>
                    <th className="px-6 py-4">Student</th>
                    <th className="px-6 py-4">ID / Email</th>
                    <th className="px-6 py-4">Enrolled</th>
                    <th className="px-6 py-4 text-center">Submissions</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.06]">
                  {students.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="px-6 py-8 text-center text-white/40">No students enrolled yet.</td>
                    </tr>
                  ) : (
                    students.map((student) => (
                      <tr key={student.enrollment_id} className="transition-colors hover:bg-white/[0.02]">
                        <td className="px-6 py-4 font-medium text-white">{student.name}</td>
                        <td className="px-6 py-4">
                          <div className="text-white/80">{student.school_id}</div>
                          <div className="text-xs text-white/40">{student.email}</div>
                        </td>
                        <td className="px-6 py-4 text-white/60">
                          {student.status === "active" ? (
                             <span className="text-emerald-400">Active</span>
                          ) : (
                             <span className="text-amber-400">Disabled</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-center font-mono text-white/30">0</td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => setStudentToRemove(student)}
                            className="rounded p-1.5 text-white/30 transition hover:bg-red-500/10 hover:text-red-400"
                            title="Remove Student"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {studentToRemove && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl border border-white/[0.08] bg-[#1a1d27] p-6 shadow-2xl">
            <h3 className="mb-2 text-lg font-bold text-white">Remove Student?</h3>
            <p className="mb-6 text-sm text-white/60">
              Are you sure you want to remove <span className="font-semibold text-white">{studentToRemove.name}</span> from this class? Their submission records will be archived.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setStudentToRemove(null)}
                disabled={isRemoving}
                className="rounded-lg px-4 py-2 text-xs font-semibold text-white/60 transition hover:bg-white/[0.04]"
              >
                Cancel
              </button>
              <button
                onClick={handleRemoveConfirm}
                disabled={isRemoving}
                className="rounded-lg bg-red-500/20 px-4 py-2 text-xs font-semibold text-red-400 transition disabled:opacity-50 hover:bg-red-500/30"
              >
                {isRemoving ? "Removing..." : "Yes, Remove"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}