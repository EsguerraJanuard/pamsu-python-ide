import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../services/api";
import { formatDateTime, humanize } from "../../utils/format";
import Modal from "../ui/Modal";
import { EmptyState, ErrorState, LoadingState } from "../ui/StateViews";

const STATUS_BADGE = {
  graded: "badge-success",
  rejected: "badge-danger",
  submitted: "badge-neutral",
  awaiting_review: "badge-neutral",
};

/** Read-only view of one student's official submissions and grades in a class. */
export default function StudentGradebookModal({ isOpen, onClose, student, classId }) {
  const [rows, setRows] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchGrades = useCallback(async () => {
    if (!student || !classId) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get(
        `/instructors/gradebook?class_id=${classId}&student_id=${student.student_id}&page_size=100`,
      );
      setRows(response?.items || []);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [student, classId]);

  useEffect(() => {
    if (isOpen) fetchGrades();
  }, [isOpen, fetchGrades]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="xl"
      title={student?.name || "Student"}
      description={[student?.school_id, student?.email].filter(Boolean).join(" · ")}
    >
      <h3 className="mb-3 text-sm font-semibold text-text-main">Submissions &amp; grades in this class</h3>
      {error ? (
        <ErrorState error={error} resource="this student's records" onRetry={fetchGrades} />
      ) : isLoading ? (
        <LoadingState label="Loading records…" />
      ) : rows.length === 0 ? (
        <EmptyState className="py-10" title="No submissions yet" message="This student hasn't submitted any activity in this class." />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border-subtle">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead className="border-b border-border-subtle bg-bg-alt text-[11px] font-semibold uppercase tracking-wider text-text-muted">
              <tr>
                <th scope="col" className="px-3 py-2.5">Activity</th>
                <th scope="col" className="px-3 py-2.5">Status</th>
                <th scope="col" className="px-3 py-2.5">Grade</th>
                <th scope="col" className="px-3 py-2.5 text-right">Review</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {rows.map((row) => (
                <tr key={row.sub_id}>
                  <td className="px-3 py-2.5">
                    <p className="font-medium text-text-main">{row.activity?.title}</p>
                    <p className="text-xs text-text-muted">
                      Attempt {row.attempt_number} · {formatDateTime(row.submitted_at)}
                    </p>
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`badge ${STATUS_BADGE[row.submission_status] || "badge-neutral"}`}>
                      {humanize(row.submission_status)}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-text-main">
                    {row.has_manual_grade && row.score !== null && row.score !== undefined ? (
                      <>
                        <span className="font-semibold">
                          {row.score} / {row.max_score}
                        </span>
                        <span className="ml-2 text-xs text-text-muted">{row.grade_is_released ? "Released" : "Not released"}</span>
                      </>
                    ) : (
                      <span className="text-text-muted">Not graded</span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <Link
                      to={`/instructor/bench/${classId}/${row.activity?.task_id}`}
                      className="btn-ghost btn-sm"
                      onClick={onClose}
                    >
                      Open bench
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Modal>
  );
}
