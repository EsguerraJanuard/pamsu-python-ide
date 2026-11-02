import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import PageShell from "../../components/layout/PageShell";
import BulkEnrollModal from "../../components/modals/BulkEnrollModal";
import ConfirmationModal from "../../components/modals/ConfirmationModal";
import EditClassModal from "../../components/modals/EditClassModal";
import StudentGradebookModal from "../../components/modals/StudentGradebookModal";
import Avatar from "../../components/ui/Avatar";
import Icon from "../../components/ui/Icon";
import RowActionsMenu from "../../components/ui/RowActionsMenu";
import { EmptyState, ErrorState, InlineAlert, PageHeader, SkeletonList } from "../../components/ui/StateViews";
import useUrlFilters from "../../hooks/useUrlFilters";
import api, { getErrorMessage } from "../../services/api";
import { copyText } from "../../utils/clipboard";
import { formatDateTime } from "../../utils/format";

const MEMBER_STATUS = {
  active: { label: "Active", badge: "badge-success" },
  disabled: { label: "Paused", badge: "badge-gold" },
};

// ?tab=activities or ?q=dela — the open tab and the roster search, kept in
// the URL for reloads and shared links.
const URL_DEFAULTS = { tab: "roster", q: "" };
const URL_ALLOWED = { tab: ["roster", "activities"] };

export default function ClassRosterView() {
  const { id: classId } = useParams();
  const [classroom, setClassroom] = useState(null);
  const [students, setStudents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);
  const [urlFilters, setUrlFilters] = useUrlFilters(URL_DEFAULTS, URL_ALLOWED);
  const activeTab = urlFilters.tab;
  const setActiveTab = (tab) => setUrlFilters({ tab });
  const searchQuery = urlFilters.q;
  const setSearchQuery = (value) => setUrlFilters({ q: value });
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

  const onlineCount = useMemo(() => students.filter((s) => s.is_online).length, [students]);

  const handleCopyEmail = async (student) => {
    const copied = await copyText(student.email);
    setActionMessage(
      copied
        ? { tone: "success", text: `Copied ${student.email}.` }
        : { tone: "error", text: `The email could not be copied. It is ${student.email}.` },
    );
  };

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
      activeTab === tab ? "border-psu-maroon text-text-brand" : "border-transparent text-text-muted hover:text-text-main"
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
                <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="relative w-full sm:w-80">
                    <label htmlFor="roster-search" className="sr-only">
                      Search students
                    </label>
                    <Icon name="search" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                    <input
                      id="roster-search"
                      type="search"
                      placeholder="Search by name, ID or email…"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="input-field pl-9"
                    />
                  </div>
                  <p className="text-xs text-text-muted" aria-live="polite">
                    {searchQuery.trim()
                      ? `${filteredStudents.length} of ${students.length} students`
                      : `${students.length} ${students.length === 1 ? "student" : "students"}`}
                    {onlineCount > 0 && ` · ${onlineCount} online now`}
                  </p>
                </div>
                <div className="card overflow-clip">
                  <table className="data-table table-fixed">
                    <caption className="sr-only">Students enrolled in {classroom.name}</caption>
                    <thead>
                      <tr>
                        <th scope="col">Student</th>
                        <th scope="col" className="hidden w-36 md:table-cell">School ID</th>
                        <th scope="col" className="hidden w-28 sm:table-cell">Enrollment</th>
                        <th scope="col" className="hidden w-28 sm:table-cell">Session</th>
                        <th scope="col" className="w-28 text-right sm:w-40">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredStudents.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="py-10 text-center text-sm text-text-muted">
                            No students match your search.
                          </td>
                        </tr>
                      ) : (
                        filteredStudents.map((student) => {
                          const status = MEMBER_STATUS[student.status] || MEMBER_STATUS.active;
                          const statusBadge = <span className={`badge ${status.badge}`}>{status.label}</span>;
                          const session = student.is_online ? (
                            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-text-emerald">
                              <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" aria-hidden="true" />
                              Online
                            </span>
                          ) : (
                            <span className="text-xs text-text-muted">Offline</span>
                          );
                          return (
                            <tr key={student.enrollment_id}>
                              <td>
                                <div className="flex min-w-0 items-center gap-3">
                                  <Avatar name={student.name} />
                                  <div className="min-w-0">
                                    <p className="truncate font-semibold text-text-main" title={student.name}>
                                      {student.name}
                                    </p>
                                    <p className="truncate text-xs text-text-muted" title={student.email}>
                                      {student.email}
                                    </p>
                                    {/* Narrow screens hide School ID (below md), Enrollment and Session (below sm); show them here instead. */}
                                    <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 md:hidden">
                                      {student.school_id && <span className="font-mono text-xs text-text-muted">{student.school_id}</span>}
                                      <span className="flex items-center gap-2 sm:hidden">
                                        {statusBadge}
                                        {session}
                                      </span>
                                    </div>
                                  </div>
                                </div>
                              </td>
                              <td className="hidden md:table-cell">
                                {student.school_id ? (
                                  <span className="rounded-md border border-border-subtle bg-bg-alt px-2 py-0.5 font-mono text-xs text-text-main">
                                    {student.school_id}
                                  </span>
                                ) : (
                                  <span className="text-text-muted">—</span>
                                )}
                              </td>
                              <td className="hidden sm:table-cell">{statusBadge}</td>
                              <td className="hidden sm:table-cell">{session}</td>
                              <td>
                                <div className="flex items-center justify-end gap-2">
                                  <button
                                    type="button"
                                    onClick={() => setStudentToInspect(student)}
                                    className="btn-row"
                                    aria-label={`Grades for ${student.name}`}
                                  >
                                    <Icon name="chart" className="h-3.5 w-3.5" />
                                    {/* Icon only on phones; the aria-label names it either way. */}
                                    <span className="hidden sm:inline">Grades</span>
                                  </button>
                                  <RowActionsMenu
                                    label={`More actions for ${student.name}`}
                                    items={[
                                      {
                                        id: "copy-email",
                                        label: "Copy email address",
                                        hint: student.email,
                                        icon: "copy",
                                        disabled: !student.email,
                                        onSelect: () => handleCopyEmail(student),
                                      },
                                      {
                                        id: "remove",
                                        label: "Remove from class",
                                        hint: "Their submissions stay on record.",
                                        icon: "trash",
                                        tone: "danger",
                                        separatorBefore: true,
                                        onSelect: () => setStudentToRemove(student),
                                      },
                                    ]}
                                  />
                                </div>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
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
