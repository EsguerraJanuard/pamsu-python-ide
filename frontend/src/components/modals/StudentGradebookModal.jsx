import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../services/api";
import { formatDateTime, humanize } from "../../utils/format";
import Icon from "../ui/Icon";
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
        <div className="overflow-clip rounded-xl border border-border-subtle">
          <table className="data-table table-fixed">
            <caption className="sr-only">Official submissions and grades for {student?.name || "this student"}</caption>
            <thead>
              <tr>
                <th scope="col">Activity</th>
                <th scope="col" className="hidden w-36 sm:table-cell">Status</th>
                <th scope="col" className="w-32 sm:w-36">Grade</th>
                <th scope="col" className="w-14 text-right sm:w-36">
                  <span className="sr-only sm:not-sr-only">Review</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const statusBadge = (
                  <span className={`badge ${STATUS_BADGE[row.submission_status] || "badge-neutral"}`}>{humanize(row.submission_status)}</span>
                );
                const graded = row.has_manual_grade && row.score !== null && row.score !== undefined;
                return (
                  <tr key={row.sub_id}>
                    <td>
                      <p className="truncate font-medium text-text-main" title={row.activity?.title}>
                        {row.activity?.title}
                      </p>
                      <p className="text-xs text-text-muted">
                        Attempt {row.attempt_number} · {formatDateTime(row.submitted_at)}
                      </p>
                      {/* The Status column is hidden below sm; show it here instead. */}
                      <div className="mt-1 sm:hidden">{statusBadge}</div>
                    </td>
                    <td className="hidden sm:table-cell">{statusBadge}</td>
                    <td>
                      {graded ? (
                        <>
                          <p className="text-base font-semibold tabular-nums text-text-main">
                            {row.score}
                            <span className="text-xs font-medium text-text-muted"> / {row.max_score}</span>
                          </p>
                          <p className={`text-xs ${row.grade_is_released ? "text-text-emerald" : "text-text-muted"}`}>
                            {row.grade_is_released ? "Released" : "Not released"}
                          </p>
                        </>
                      ) : (
                        <span className="text-xs text-text-muted">Not graded</span>
                      )}
                    </td>
                    <td className="text-right">
                      <Link
                        to={`/instructor/bench/${classId}/${row.activity?.task_id}`}
                        className="btn-row"
                        onClick={onClose}
                        aria-label={`Open ${row.activity?.title || "this activity"} in the Grading Bench`}
                      >
                        <Icon name="arrowRight" className="h-3.5 w-3.5" />
                        <span className="hidden sm:inline">Open bench</span>
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Modal>
  );
}
