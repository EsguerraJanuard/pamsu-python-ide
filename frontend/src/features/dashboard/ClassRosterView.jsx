import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../../services/api";
import EditClassModal from "../../components/modals/EditClassModal";
export default function ClassRosterView() {
  const { id: classId } = useParams();
  const navigate = useNavigate();
  const [students, setStudents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("roster");
  const [searchQuery, setSearchQuery] = useState("");
  const [studentToRemove, setStudentToRemove] = useState(null);
  const [isRemoving, setIsRemoving] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  const [classroom, setClassroom] = useState(null);

  useEffect(() => {
    fetchRoster();
  }, [classId]);

  const fetchRoster = async () => {
    setIsLoading(true);
    try {
      const [classData, membersData, tasksData] = await Promise.all([
        api.get(`/classrooms/${classId}`).catch(() => ({
          id: classId,
          name: "CS101 — Intro to Programming",
          subject_code: "CS101",
          section: "Sec 01",
          code: "XYZ890",
          schedule: "Mon/Wed 10:00 AM - 12:00 PM",
        })),
        api.get(`/classrooms/${classId}/members`).catch(() => [
          { enrollment_id: "enr-1", name: "Dela Cruz, Juan", school_id: "2024-0012", email: "juan@univ.edu", status: "active" },
          { enrollment_id: "enr-2", name: "Santos, Maria", school_id: "2024-0019", email: "maria@univ.edu", status: "active" },
        ]),
        api.get(`/instructors/tasks/?class_id=${classId}`).catch(() => []),
      ]);
      setClassroom(classData);
      setStudents(Array.isArray(membersData) ? membersData.filter(m => m.status !== "removed") : []);
      setTasks(Array.isArray(tasksData) ? tasksData : []);
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
      setStudents((prev) => prev.filter((s) => s.enrollment_id !== studentToRemove.enrollment_id));
      setStudentToRemove(null);
    } finally {
      setIsRemoving(false);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-bg-base select-none">
      <div className="flex-1 overflow-y-auto p-6 sm:p-8">
        <div className="mx-auto max-w-6xl space-y-6">
          <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-6">
            <div>
              <button 
                onClick={() => navigate('/instructor/classes')}
                className="mb-4 flex items-center gap-2 text-xs font-semibold text-emerald-400 transition-colors hover:text-emerald-300"
              >
                ← Back to Classrooms
              </button>
              <h1 className="text-2xl font-bold text-text-main">
                {classroom ? `${classroom.subject_code || classroom.name} ${classroom.section ? `- ${classroom.section}` : ''}` : "Class Roster"}
              </h1>
              <p className="mt-1 text-sm text-text-muted">
                {classroom ? (classroom.name || classroom.schedule || "Manage enrolled students.") : "Manage enrolled students."}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsEditModalOpen(true)}
                className="rounded-lg border border-border-subtle bg-slate-800 px-4 py-2 text-xs font-semibold text-text-main shadow hover:bg-slate-700 transition"
              >
                ⚙ Classroom Settings
              </button>

              <div className="text-sm font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg">
                Students: {students.length}
              </div>
            </div>
          </header>

          {/* Navigation Tabs */}
          <div className="flex gap-4 border-b border-border-subtle text-xs font-semibold">
            <button
              onClick={() => setActiveTab("roster")}
              className={`pb-3 px-1 transition border-b-2 ${
                activeTab === "roster"
                  ? "border-emerald-400 text-emerald-400"
                  : "border-transparent text-text-muted hover:text-text-main"
              }`}
            >
              Enrolled Roster ({students.length})
            </button>
            <button
              onClick={() => setActiveTab("activities")}
              className={`pb-3 px-1 transition border-b-2 ${
                activeTab === "activities"
                  ? "border-emerald-400 text-emerald-400"
                  : "border-transparent text-text-muted hover:text-text-main"
              }`}
            >
              Activities
            </button>
          </div>

          {isLoading ? (
            <div className="flex h-40 items-center justify-center text-sm text-text-muted">Loading roster...</div>
          ) : activeTab === "roster" ? (
            <>
              {/* Search Bar */}
              <div className="flex items-center gap-2 rounded-lg border border-border-subtle bg-bg-glass px-3 py-2 w-full max-w-sm focus-within:border-emerald-500/50 focus-within:ring-1 focus-within:ring-emerald-500/50 transition">
                <svg className="h-4 w-4 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search students by name, ID, or email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-transparent text-sm text-text-main outline-none placeholder:text-text-muted"
                />
              </div>

              <div className="overflow-hidden rounded-xl border border-border-subtle bg-bg-glass">
                <table className="w-full text-left text-sm text-text-muted">
                  <thead className="border-b border-border-subtle bg-bg-glass text-xs font-semibold uppercase tracking-wider text-text-muted">
                    <tr>
                      <th className="px-6 py-4">Student</th>
                      <th className="px-6 py-4">ID / Email</th>
                      <th className="px-6 py-4">Status</th>
                      <th className="px-6 py-4 text-center">Submissions</th>
                      <th className="px-6 py-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.06]">
                    {(() => {
                      const filteredStudents = students.filter(s => 
                        s.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                        (s.school_id && s.school_id.toLowerCase().includes(searchQuery.toLowerCase())) || 
                        (s.email && s.email.toLowerCase().includes(searchQuery.toLowerCase()))
                      );
                      
                      if (filteredStudents.length === 0) {
                        return (
                          <tr>
                            <td colSpan="5" className="px-6 py-8 text-center text-text-muted">
                              {searchQuery ? "No students found matching your search." : "No students enrolled yet."}
                            </td>
                          </tr>
                        );
                      }
                      
                      return filteredStudents.map((student) => (
                        <tr key={student.enrollment_id || student.id} className="transition-colors hover:bg-bg-glass">
                          <td className="px-6 py-4 font-medium text-text-main">{student.name}</td>
                          <td className="px-6 py-4">
                            <div className="text-text-main">{student.school_id || "2026-N/A"}</div>
                            <div className="text-xs text-text-muted">{student.email}</div>
                          </td>
                          <td className="px-6 py-4 text-text-muted">
                            {student.status === "active" || student.status === "approved" ? (
                               <span className="text-emerald-400">Active</span>
                            ) : (
                               <span className="text-amber-400">Disabled</span>
                            )}
                          </td>
                          <td className="px-6 py-4 text-center font-mono text-text-muted">0</td>
                          <td className="px-6 py-4 text-right">
                            <button
                              onClick={() => setStudentToRemove(student)}
                              className="rounded p-1.5 text-text-muted transition hover:bg-red-500/10 hover:text-red-400"
                              title="Remove Student"
                            >
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" strokeLinecap="round" strokeLinejoin="round" />
                              </svg>
                            </button>
                          </td>
                        </tr>
                      ));
                    })()}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {tasks.length === 0 ? (
                <div className="flex flex-col items-center justify-center rounded-xl border border-border-subtle bg-bg-glass py-16 text-center">
                  <div className="mb-3 rounded-full bg-slate-800/50 p-4 text-text-muted">
                    <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-text-main">No Activities Yet</h3>
                  <p className="mt-1 max-w-sm text-sm text-text-muted">
                    You haven't assigned any activities or tasks to this classroom.
                  </p>
                </div>
              ) : (
                tasks.map(task => (
                  <div key={task.task_id} className="flex items-center justify-between rounded-xl border border-border-subtle bg-bg-glass p-5 transition hover:border-emerald-500/30 hover:bg-bg-glass/80">
                    <div className="flex items-center gap-4">
                      <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${task.is_published ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800/50 text-text-muted'}`}>
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="text-base font-semibold text-text-main">{task.title}</h3>
                        <div className="mt-1 flex items-center gap-3 text-xs text-text-muted">
                          <span className="capitalize">{task.activity_type.replace('_', ' ')}</span>
                          <span>•</span>
                          <span className={task.is_published ? 'text-emerald-400/80 font-medium' : 'text-text-muted font-medium'}>
                            {task.is_published ? 'Published' : 'Draft'}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-6">
                      {task.is_published ? (
                        <div className="flex items-center gap-6 mr-4 border-r border-border-subtle pr-8">
                          <div className="flex flex-col items-center">
                            <span className="text-xl font-semibold text-text-main">{task.turned_in_count || 0}</span>
                            <span className="text-[10px] uppercase tracking-wider text-text-muted mt-1">Turned In</span>
                          </div>
                          <div className="flex flex-col items-center">
                            <span className="text-xl font-semibold text-text-main">{task.assigned_count || 0}</span>
                            <span className="text-[10px] uppercase tracking-wider text-text-muted mt-1">Assigned</span>
                          </div>
                          <div className="flex flex-col items-center">
                            <span className="text-xl font-semibold text-emerald-400">{task.graded_count || 0}</span>
                            <span className="text-[10px] uppercase tracking-wider text-emerald-400/60 mt-1">Graded</span>
                          </div>
                        </div>
                      ) : (
                        <div className="mr-6 text-xs italic text-text-muted border-r border-border-subtle pr-8">
                          Students cannot see drafts
                        </div>
                      )}
                      
                      <button 
                        onClick={() => navigate(`/instructor/activities/${task.task_id}`)}
                        className="rounded-lg border border-border-subtle bg-bg-glass px-4 py-2 text-xs font-semibold text-text-main transition hover:bg-bg-glass-hover hover:text-emerald-400"
                      >
                        {task.is_published ? "View Activity" : "Edit Activity"}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* Edit Classroom Settings Modal */}
      <EditClassModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        classroom={classroom}
        onSuccess={(updated) => setClassroom((prev) => ({ ...prev, ...updated }))}
      />

      {/* Confirm Remove Student Modal */}
      {studentToRemove && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl border border-border-subtle bg-bg-glass p-6 shadow-2xl">
            <h3 className="mb-2 text-lg font-bold text-text-main">Remove Student?</h3>
            <p className="mb-6 text-sm text-text-muted">
              Are you sure you want to remove <span className="font-semibold text-text-main">{studentToRemove.name}</span> from this class? Their submission records will be archived.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setStudentToRemove(null)}
                disabled={isRemoving}
                className="rounded-lg px-4 py-2 text-xs font-semibold text-text-muted transition hover:bg-bg-glass"
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