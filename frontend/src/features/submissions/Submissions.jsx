import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import PageShell from "../../components/layout/PageShell";
import { EmptyState, ErrorState, PageHeader, SkeletonList } from "../../components/ui/StateViews";
import api from "../../services/api";
import { classLabel, formatDateTime } from "../student/studentData";
import { SUBMISSION_STATUS, formatScore, loadReleasedGrades } from "./submissionData";

const FILTERS = [
  { label: "All", value: "all" },
  { label: "Awaiting review", value: "pending" },
  { label: "Graded", value: "graded" },
];

export default function Submissions() {
  const [rows, setRows] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");

  const fetchSubmissions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [submissions, activities, classrooms, grades] = await Promise.all([
        api.get("/submissions/"),
        api.get("/activities/"),
        api.get("/classrooms/mine"),
        loadReleasedGrades(),
      ]);

      const classMap = {};
      (classrooms || []).forEach((c) => {
        if (c?.classroom) classMap[c.classroom.class_id] = c.classroom;
      });
      const activityMap = {};
      (activities || []).forEach((a) => {
        activityMap[a.task_id] = a;
      });
      const gradeMap = {};
      grades.forEach((g) => {
        gradeMap[g.sub_id] = g;
      });

      const mapped = (submissions || [])
        .map((sub) => {
          const activity = activityMap[sub.task_id];
          const grade = gradeMap[sub.sub_id];
          return {
            id: sub.sub_id,
            taskId: sub.task_id,
            title: activity?.title || grade?.activity?.title || `Activity #${sub.task_id}`,
            classLabel: activity
              ? classLabel(classMap[activity.class_id])
              : grade?.activity?.class_name || "",
            status: sub.status,
            attempt: sub.attempt_number,
            isOfficial: sub.is_official,
            submittedAt: sub.submitted_at,
            grade,
          };
        })
        .sort((a, b) => new Date(b.submittedAt) - new Date(a.submittedAt));

      setRows(mapped);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSubmissions();
  }, [fetchSubmissions]);

  const visibleRows = useMemo(
    () =>
      rows.filter((row) => {
        if (filter === "graded") return row.status === "graded";
        if (filter === "pending") return row.status === "submitted" || row.status === "awaiting_review";
        return true;
      }),
    [rows, filter],
  );

  return (
    <PageShell>
      <PageHeader
        eyebrow="Progress"
        title="Submissions"
        description={
          isLoading || error ? "Every attempt you have submitted." : `${rows.length} ${rows.length === 1 ? "attempt" : "attempts"} recorded`
        }
      />

      {error ? (
        <ErrorState error={error} resource="your submissions" onRetry={fetchSubmissions} />
      ) : (
        <>
          <div
            className="mb-5 flex w-full gap-1 overflow-x-auto rounded-lg border border-border-subtle bg-bg-panel p-1 sm:w-fit"
            role="tablist"
            aria-label="Filter submissions"
          >
            {FILTERS.map((option) => {
              const selected = filter === option.value;
              return (
                <button
                  key={option.value}
                  type="button"
                  role="tab"
                  aria-selected={selected}
                  onClick={() => setFilter(option.value)}
                  className={`whitespace-nowrap rounded-md px-3.5 py-1.5 text-sm font-medium transition-colors ${
                    selected ? "bg-psu-maroon text-white shadow-sm" : "text-text-muted hover:bg-bg-alt hover:text-text-main"
                  }`}
                >
                  {option.label}
                </button>
              );
            })}
          </div>

          {isLoading ? (
            <SkeletonList rows={4} />
          ) : rows.length === 0 ? (
            <EmptyState
              title="No submissions yet"
              message="When you submit an activity from the workspace, each attempt is recorded here."
              action={
                <Link to="/student/assignments" className="btn-secondary">
                  View assignments
                </Link>
              }
            />
          ) : visibleRows.length === 0 ? (
            <EmptyState icon="search" title="Nothing in this view" message="No submissions match the selected filter." />
          ) : (
            <ul className="space-y-3">
              {visibleRows.map((row) => {
                const status = SUBMISSION_STATUS[row.status] || SUBMISSION_STATUS.submitted;
                return (
                  <li key={row.id} className="card p-4 sm:p-5">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                      <div className="min-w-0">
                        <div className="mb-1.5 flex flex-wrap items-center gap-2">
                          <h2 className="text-sm font-semibold text-text-main">{row.title}</h2>
                          <span className={`badge ${status.badge}`}>{status.label}</span>
                          {row.isOfficial && <span className="badge badge-brand">Official attempt</span>}
                        </div>
                        <p className="text-xs text-text-muted">
                          {[row.classLabel, `Attempt ${row.attempt}`, `Submitted ${formatDateTime(row.submittedAt)}`]
                            .filter(Boolean)
                            .join(" · ")}
                        </p>
                      </div>
                      <div className="flex shrink-0 items-center gap-4">
                        <div className="text-right">
                          <p className={`text-sm font-semibold ${row.grade ? "text-text-main" : "text-text-muted"}`}>
                            {row.grade ? formatScore(row.grade) : "Not released"}
                          </p>
                          <p className="text-[11px] text-text-muted">Instructor grade</p>
                        </div>
                        <Link to={`/student/submissions/${row.id}`} className="btn-secondary btn-sm">
                          Details
                        </Link>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </>
      )}
    </PageShell>
  );
}
