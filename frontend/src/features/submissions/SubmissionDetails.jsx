import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";

import PageShell from "../../components/layout/PageShell";
import { ErrorState, InlineAlert, PageHeader, SkeletonList } from "../../components/ui/StateViews";
import api from "../../services/api";
import { formatDateTime } from "../student/studentData";
import { SUBMISSION_STATUS, formatScore, loadReleasedGrades } from "./submissionData";

export default function SubmissionDetails() {
  const { id } = useParams();
  const location = useLocation();
  const [showSubmitted, setShowSubmitted] = useState(Boolean(location.state?.justSubmitted));
  const [submission, setSubmission] = useState(null);
  const [activity, setActivity] = useState(null);
  const [attempts, setAttempts] = useState([]);
  const [grade, setGrade] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDetails = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const sub = await api.get(`/submissions/${id}`);
      setSubmission(sub);

      // Supporting data is optional: the submission itself is the record of truth.
      const [activityRes, attemptsRes, gradesRes] = await Promise.allSettled([
        api.get(`/activities/${sub.task_id}`),
        api.get(`/submissions/?task_id=${sub.task_id}`),
        loadReleasedGrades(`&task_id=${sub.task_id}`),
      ]);
      setActivity(activityRes.status === "fulfilled" ? activityRes.value : null);
      setAttempts(
        attemptsRes.status === "fulfilled"
          ? [...attemptsRes.value].sort((a, b) => b.attempt_number - a.attempt_number)
          : [],
      );
      setGrade(gradesRes.status === "fulfilled" ? gradesRes.value.find((g) => g.sub_id === sub.sub_id) || null : null);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDetails();
  }, [fetchDetails]);

  const status = submission ? SUBMISSION_STATUS[submission.status] || SUBMISSION_STATUS.submitted : null;

  return (
    <PageShell>
      <Link
        to="/student/submissions"
        className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-text-muted transition-colors hover:text-text-main"
      >
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Back to submissions
      </Link>

      {error ? (
        <ErrorState
          error={error}
          resource="this submission"
          onRetry={fetchDetails}
          action={
            <Link to="/student/submissions" className="btn-secondary">
              All submissions
            </Link>
          }
        />
      ) : isLoading ? (
        <SkeletonList rows={3} className="h-28" />
      ) : (
        <>
          <PageHeader
            eyebrow="Submission"
            title={activity?.title || grade?.activity?.title || `Activity #${submission.task_id}`}
            description={`Attempt ${submission.attempt_number} · Submitted ${formatDateTime(submission.submitted_at)}`}
            actions={
              activity && submission.status !== "graded" ? (
                <Link to={`/student/workspace?activity=${submission.task_id}`} className="btn-secondary">
                  Open workspace
                </Link>
              ) : null
            }
          />

          {showSubmitted && (
            <InlineAlert tone="success" onDismiss={() => setShowSubmitted(false)} className="mb-5">
              Your solution was submitted and recorded as attempt {submission.attempt_number}.
            </InlineAlert>
          )}

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_300px]">
            <div className="min-w-0 space-y-5">
              <section className="card p-5" aria-labelledby="grade-heading">
                <h2 id="grade-heading" className="mb-3 text-sm font-semibold">
                  Instructor grade &amp; feedback
                </h2>
                {grade ? (
                  <>
                    <p className="text-3xl font-bold tracking-tight text-text-main">{formatScore(grade)}</p>
                    <p className="text-xs text-text-muted">
                      {Math.round(grade.percentage)}% · Released {formatDateTime(grade.released_at)}
                    </p>
                    <div className="mt-4 rounded-lg border-l-[3px] border-psu-gold bg-bg-alt px-4 py-3">
                      <p className="text-xs font-semibold text-text-muted">Feedback</p>
                      <p className="mt-1 whitespace-pre-wrap text-sm text-text-main">
                        {grade.feedback || "Your instructor did not leave written feedback."}
                      </p>
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-text-muted">
                    {submission.is_official
                      ? "Your instructor has not released a grade for this attempt yet."
                      : "Only the official attempt is graded. This earlier attempt is kept for your records."}
                  </p>
                )}
              </section>

              <section className="card overflow-hidden" aria-labelledby="code-heading">
                <div className="flex items-center justify-between border-b border-border-subtle px-5 py-3">
                  <h2 id="code-heading" className="text-sm font-semibold">
                    Submitted code
                  </h2>
                  <span className="font-mono text-xs text-text-muted">main.py</span>
                </div>
                {submission.raw_code ? (
                  <pre className="max-h-[480px] overflow-auto bg-bg-alt p-4 font-mono text-xs leading-5 text-text-main">
                    {submission.raw_code}
                  </pre>
                ) : (
                  <p className="p-5 text-sm text-text-muted">The code for this attempt isn&apos;t available.</p>
                )}
              </section>
            </div>

            <aside className="space-y-5">
              <section className="card p-5" aria-label="Submission record">
                <h2 className="mb-3 text-sm font-semibold">Record</h2>
                <dl className="space-y-2.5 text-sm">
                  <div className="flex justify-between gap-3">
                    <dt className="text-text-muted">Status</dt>
                    <dd>
                      <span className={`badge ${status.badge}`}>{status.label}</span>
                    </dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="text-text-muted">Official attempt</dt>
                    <dd className="font-medium">{submission.is_official ? "Yes" : "No"}</dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="text-text-muted">Submitted</dt>
                    <dd className="text-right font-medium">{formatDateTime(submission.submitted_at)}</dd>
                  </div>
                  {submission.accepted_at && (
                    <div className="flex justify-between gap-3">
                      <dt className="text-text-muted">Accepted</dt>
                      <dd className="text-right font-medium">{formatDateTime(submission.accepted_at)}</dd>
                    </div>
                  )}
                </dl>
              </section>

              {attempts.length > 1 && (
                <section className="card p-5" aria-label="All attempts">
                  <h2 className="mb-3 text-sm font-semibold">All attempts</h2>
                  <ul className="space-y-1">
                    {attempts.map((attempt) => (
                      <li key={attempt.sub_id}>
                        <Link
                          to={`/student/submissions/${attempt.sub_id}`}
                          aria-current={attempt.sub_id === submission.sub_id ? "page" : undefined}
                          className={`flex items-center justify-between rounded-lg px-2.5 py-2 text-sm transition-colors ${
                            attempt.sub_id === submission.sub_id ? "bg-psu-cream font-semibold text-psu-maroon" : "hover:bg-bg-alt"
                          }`}
                        >
                          <span>Attempt {attempt.attempt_number}</span>
                          {attempt.is_official && <span className="badge badge-brand">Official</span>}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </aside>
          </div>
        </>
      )}
    </PageShell>
  );
}
