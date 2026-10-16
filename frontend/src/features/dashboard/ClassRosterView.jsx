import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import PageShell from "../../components/layout/PageShell";
import BulkEnrollModal from "../../components/modals/BulkEnrollModal";
import ConfirmationModal from "../../components/modals/ConfirmationModal";
import EditClassModal from "../../components/modals/EditClassModal";
import StudentGradebookModal from "../../components/modals/StudentGradebookModal";
import { EmptyState, ErrorState, InlineAlert, PageHeader, SkeletonList } from "../../components/ui/StateViews";
import api, { getErrorMessage } from "../../services/api";
import { formatDateTime } from "../../utils/format";

const MEMBER_STATUS = {
  active: { label: "Active", badge: "badge-success" },
  disabled: { label: "Paused", badge: "badge-gold" },
};

export default function ClassRosterView() {
  const { id: classId } = useParams();
  const [classroom, setClassroom] = useState(null);
  const [students, setStudents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);
  const [activeTab, setActiveTab] = useState("roster");
  const [searchQuery, setSearchQuery] = useState("");
  const [studentToRemove, setStudentToRemove] = useState(null);
  const [isRemoving, setIsRemoving] = useState(false);
  const [studentToInspect, setStudentToInspect] = useState(null);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isBulkOpen, setIsBulkOpen] = useState(false);

  const fetchRoster = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [classData, members, classTasks] = await Promise.all([
        api.get(`/classrooms/${classId}`),
        api.get(`/classrooms/${classId}/members`),
        api.get(`/instructors/tasks/?class_id=${classId}`),
      ]);
      setClassroom(classData);
      setStudents((Array.isArray(members) ? members : []).filter((m) => m.status !== "removed"));
      setTasks(Array.isArray(classTasks) ? classTasks.filter((t) => String(t.class_id) === String(classId)) : []);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [classId]);

  useEffect(() => {
    fetchRoster();
  }, [fetchRoster]);

  const filteredStudents = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return students;
    return students.filter((s) =>
      [s.name, s.school_id, s.email].some((value) => value && value.toLowerCase().includes(query)),
    );
  }, [students, searchQuery]);

  const handleRemoveConfirm = async () => {
    if (!studentToRemove || isRemoving) return;
    setIsRemoving(true);
    try {
      await api.patch(`/classrooms/enrollments/${studentToRemove.enrollment_id}/status`, { status: "removed" });
      setStudents((prev) => prev.filter((s) => s.enrollment_id !== studentToRemove.enrollment_id));
      setActionMessage({ tone: "success", text: `${studentToRemove.name} was removed from the class.` });
    } catch (err) {
      setActionMessage({ tone: "error", text: getErrorMessage(err, `${studentToRemove.name} could not be removed.`) });
    } finally {
      setIsRemoving(false);
      setStudentToRemove(null);
    }
  };

  const tabClass = (tab) =>
    `-mb-px border-b-2 px-1 pb-3 text-sm font-semibold transition-colors ${
      activeTab === tab ? "border-psu-maroon text-psu-maroon" : "border-transparent text-text-muted hover:text-text-main"
    }`;

  return (
    <PageShell role="instructor" statusContext={classroom?.name}>
      <Link
        to="/instructor/classes"
        className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-text-muted transition-colors hover:text-text-main"
      >
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Back to classes
      </Link>

      {error ? (
        <ErrorState error={error} resource="this class" onRetry={fetchRoster} />
      ) : isLoading ? (
        <>
          <div className="card mb-6 h-24 animate-pulse" />
          <SkeletonList rows={4} className="h-14" />
        </>
      ) : (
        <>
          <PageHeader
            eyebrow={[classroom.subject_code, classroom.section && `Section ${classroom.section}`].filter(Boolean).join(" · ") || "Class"}
            title={classroom.name}
            description={`Enrollment code ${classroom.class_code}${classroom.is_active ? "" : " · Archived"}`}
            actions={
              <>
                <button type="button" onClick={() => setIsBulkOpen(true)} className="btn-secondary">
                  Bulk enroll
                </button>
                <button type="button" onClick={() => setIsEditOpen(true)} className="btn-secondary">
                  Class settings
                </button>
              </>
            }
          />

          {actionMessage && (
            <InlineAlert tone={actionMessage.tone} onDismiss={() => setActionMessage(null)} className="mb-5">
              {actionMessage.text}
            </InlineAlert>
          )}

          <div className="mb-5 flex gap-6 border-b border-border-subtle" role="tablist" aria-label="Class sections">
            <button type="button" role="tab" aria-selected={activeTab === "roster"} onClick={() => setActiveTab("roster")} className={tabClass("roster")}>
              Students ({students.length})
            </button>
            <button type="button" role="tab" aria-selected={activeTab === "activities"} onClick={() => setActiveTab("activities")} className={tabClass("activities")}>
              Activities ({tasks.length})
            </button>
          </div>

          {activeTab === "roster" ? (
            students.length === 0 ? (
              <EmptyState
                title="No students enrolled"
                message={`Share the enrollment code ${classroom.class_code} with your students, or enroll them in bulk.`}
                action={
                  <button type="button" className="btn-primary" onClick={() => setIsBulkOpen(true)}>
                    Bulk enroll
                  </button>
                }
              />
            ) : (
              <>
                <div className="mb-4 w-full sm:w-80">
                  <label htmlFor="roster-search" className="sr-only">
                    Search students
                  </label>
                  <input
                    id="roster-search"
                    type="search"
                    placeholder="Search by name, ID or email…"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="input-field"
                  />
                </div>
                <div className="card overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[640px] text-left text-sm">
                      <thead className="border-b border-border-subtle bg-bg-alt text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                        <tr>
                          <th scope="col" className="px-4 py-3">Student</th>
                          <th scope="col" className="px-4 py-3">School ID</th>
                          <th scope="col" className="px-4 py-3">Enrollment</th>
                          <th scope="col" className="px-4 py-3">Session</th>
                          <th scope="col" className="px-4 py-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border-subtle">
                        {filteredStudents.length === 0 ? (
                          <tr>
                            <td colSpan={5} className="px-4 py-10 text-center text-sm text-text-muted">
                              No students match your search.
                            </td>
                          </tr>
                        ) : (
                          filteredStudents.map((student) => {
                            const status = MEMBER_STATUS[student.status] || MEMBER_STATUS.active;
                            return (
                              <tr key={student.enrollment_id} className="hover:bg-bg-alt/60">
                                <td className="px-4 py-3">
                                  <p className="font-medium text-text-main">{student.name}</p>
                                  <p className="text-xs text-text-muted">{student.email}</p>
                                </td>
                                <td className="px-4 py-3 font-mono text-xs text-text-muted">{student.school_id || "—"}</td>
                                <td className="px-4 py-3">
                                  <span className={`badge ${status.badge}`}>{status.label}</span>
                                </td>
                                <td className="px-4 py-3 text-xs">
                                  {student.is_online ? (
                                    <span className="inline-flex items-center gap-1.5 font-medium text-text-emerald">
                                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" aria-hidden="true" />
                                      Online
                                    </span>
                                  ) : (
                                    <span className="text-text-muted">Offline</span>
                                  )}
                                </td>
                                <td className="px-4 py-3">
                                  <div className="flex justify-end gap-1">
                                    <button type="button" onClick={() => setStudentToInspect(student)} className="btn-ghost btn-sm">
                                      Grades
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => setStudentToRemove(student)}
                                      className="btn-ghost btn-sm hover:text-psu-red"
                                      aria-label={`Remove ${student.name} from class`}
                                    >
                                      Remove
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )
          ) : (
            <>
              <div className="mb-4 flex justify-end">
                <Link to={`/instructor/activities/create?class=${classId}`} className="btn-primary">
                  New activity for this class
                </Link>
              </div>
              {tasks.length === 0 ? (
                <EmptyState title="No activities yet" message="Activities you assign to this class will appear here." />
              ) : (
                <ul className="space-y-3">
                  {tasks.map((task) => (
                    <li key={task.task_id} className="card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                      <div className="min-w-0">
                        <div className="mb-1 flex flex-wrap items-center gap-2">
                          <h3 className="text-sm font-semibold text-text-main">{task.title}</h3>
                          <span className={`badge ${task.is_published ? "badge-success" : "badge-neutral"}`}>
                            {task.is_published ? "Published" : "Draft"}
                          </span>
                          <span className="badge badge-neutral">{task.activity_type === "homework" ? "Homework" : "Laboratory"}</span>
                        </div>
                        <p className="text-xs text-text-muted">{task.due_at ? `Due ${formatDateTime(task.due_at)}` : "No due date"}</p>
                      </div>
                      <div className="flex shrink-0 gap-2">
                        <Link to={`/instructor/activities/${task.task_id}`} className="btn-secondary btn-sm">
                          Manage
                        </Link>
                        {task.is_published && (
                          <Link to={`/instructor/bench/${classId}/${task.task_id}`} className="btn-ghost btn-sm">
                            Grade
                          </Link>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </>
      )}

      <BulkEnrollModal isOpen={isBulkOpen} onClose={() => setIsBulkOpen(false)} classId={classId} onSuccess={fetchRoster} />
      <EditClassModal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        classroom={classroom}
        onSuccess={(updated) => setClassroom((prev) => ({ ...prev, ...updated }))}
      />
      <StudentGradebookModal
        isOpen={Boolean(studentToInspect)}
        onClose={() => setStudentToInspect(null)}
        student={studentToInspect}
        classId={classId}
      />
      <ConfirmationModal
        isOpen={Boolean(studentToRemove)}
        title="Remove student?"
        message={`${studentToRemove?.name} will lose access to this class. Their existing submissions stay on record.`}
        confirmText="Remove student"
        loadingText="Removing…"
        isDanger
        isLoading={isRemoving}
        onConfirm={handleRemoveConfirm}
        onCancel={() => setStudentToRemove(null)}
      />
    </PageShell>
  );
}
