import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../services/api";

import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";


const STATUS_CONFIG = {
  awaiting_review: {
    label: "Awaiting review",
    badgeClass:
      "border-blue-500/30 bg-blue-500/10 text-blue-400",
    accentClass: "border-l-blue-500",
  },
  graded: {
    label: "Graded",
    badgeClass:
      "border-violet-500/30 bg-violet-500/10 text-violet-400",
    accentClass: "border-l-violet-500",
  },
};

function getPercentage(value, maximum) {
  if (!maximum) {
    return 0;
  }

  return Math.round((value / maximum) * 100);
}

function SubmissionList({ submissions, onOpen, isLoading }) {
  if (isLoading) {
    return (
      <section className="space-y-4">
        {[1, 2, 3].map((i) => (
          <article key={i} className="cursor-pointer overflow-hidden rounded-xl border border-white/[0.04] bg-bg-glass p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-border-subtle hover:bg-bg-glass-hover hover:shadow-lg animate-pulse">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="flex-1">
                <div className="mb-2 h-6 w-3/4 rounded-md bg-white/[0.05]"></div>
                <div className="mb-4 h-4 w-1/2 rounded-md bg-white/[0.05]"></div>
                <div className="flex items-center gap-2">
                  <div className="h-5 w-16 rounded-full bg-white/[0.05]"></div>
                  <div className="h-5 w-24 rounded-full bg-white/[0.05]"></div>
                </div>
              </div>
              <div className="h-10 w-24 rounded-lg bg-white/[0.05]"></div>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-4 rounded-lg border border-border-subtle bg-bg-glass p-4 sm:grid-cols-4">
              <div className="h-12 w-full rounded-md bg-white/[0.05]"></div>
              <div className="h-12 w-full rounded-md bg-white/[0.05]"></div>
            </div>
          </article>
        ))}
      </section>
    );
  }

  return (
    <section
      className="space-y-4"
      aria-label="Submitted activities"
    >
      {submissions.map((submission, index) => {
        const status =
          STATUS_CONFIG[submission.status] ??
          STATUS_CONFIG.awaiting_review;


        return (
          <article
            key={submission.id}
            className={`submission-card rounded-xl border border-l-[3px] border-border-subtle bg-bg-glass p-5 ${status.accentClass}`}
            style={{
              animation: `submissionsFadeUp 400ms ease ${
                index * 70
              }ms both`,
            }}
          >
            <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <h2 className="text-sm font-semibold">
                    {submission.activityTitle}
                  </h2>

                  <span
                    className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${status.badgeClass}`}
                  >
                    {status.label}
                  </span>
                </div>

                <p className="text-[11px] text-text-muted">
                  {submission.courseCode} ·{" "}
                  {submission.activityType}
                </p>

                <p className="mt-1 text-[11px] text-text-muted">
                  Submitted {submission.submittedLabel}
                </p>
              </div>

              <button
                type="button"
                onClick={() => onOpen(submission.id)}
                className="shrink-0 rounded-lg border border-blue-500/40 px-3 py-1.5 text-xs font-semibold text-text-blue transition duration-150 hover:-translate-y-px hover:bg-blue-500/10 active:translate-y-0 active:scale-[0.98]"
              >
                View details
              </button>
            </div>

            <div className="mb-4 flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-green-500/20 bg-green-500/10 px-2.5 py-1 text-[10px] font-medium text-green-400">
                Attempt {submission.latestAttempt}
              </span>

              {submission.isOfficial && (
                <span className="rounded-full border border-green-500/20 bg-green-500/[0.06] px-2.5 py-1 text-[10px] text-green-300">
                  Latest official submission
                </span>
              )}

              <span className="text-[10px] text-text-muted">
                {submission.totalAttempts}{" "}
                {submission.totalAttempts === 1
                  ? "attempt"
                  : "attempts"}{" "}
                recorded
              </span>
            </div>



            <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-1">
              <div className="rounded-lg border border-border-subtle bg-bg-glass p-3">
                {submission.instructorGrade ? (
                  <>
                    <p className="text-lg font-bold text-text-violet">
                      {submission.instructorGrade.score} /{" "}
                      {submission.instructorGrade.maximum}
                    </p>

                    <p className="mt-0.5 text-[10px] text-text-muted">
                      Instructor grade
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-sm font-semibold text-text-blue">
                      Pending
                    </p>

                    <p className="mt-1 text-[10px] text-text-muted">
                      Instructor grade
                    </p>
                  </>
                )}
              </div>
            </div>

            <div className="rounded-lg border-l-2 border-border-subtle bg-bg-glass px-3 py-2 font-mono text-[11px] text-text-muted">
              <span className="text-text-muted">
                Instructor feedback:{" "}
              </span>

              {submission.instructorFeedback}
            </div>
          </article>
        );
      })}

      {submissions.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border-subtle py-20 px-6 text-center transition-all hover:bg-bg-glass">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-500/10 text-text-blue ring-4 ring-blue-500/5">
            <ArchiveIcon className="h-8 w-8" />
          </div>
          <h3 className="mb-2 text-xl font-semibold text-text-main">No Submissions Yet</h3>
          <p className="max-w-md text-sm text-text-muted">
            You haven't submitted any activities. Your completed laboratory and homework modules will appear here for review.
          </p>
        </div>
      )}
    </section>
  );
}

function SubmissionDetails({ submission, onBack }) {
  const status =
    STATUS_CONFIG[submission.status] ??
    STATUS_CONFIG.awaiting_review;



  return (
    <div className="space-y-5">
      <button
        type="button"
        onClick={onBack}
        className="text-xs text-text-blue transition-colors hover:text-text-blue"
      >
        ← Back to submissions
      </button>

      <section
        className={`rounded-xl border border-l-[3px] border-border-subtle bg-bg-glass p-5 ${status.accentClass}`}
      >
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="mb-1 flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-bold">
                {submission.activityTitle}
              </h1>

              <span
                className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${status.badgeClass}`}
              >
                {status.label}
              </span>
            </div>

            <p className="text-xs text-text-muted">
              {submission.courseCode} ·{" "}
              {submission.activityType}
            </p>

            <p className="mt-1 text-[11px] text-text-muted">
              Latest submission: {submission.submittedLabel}
            </p>
          </div>

          {submission.instructorGrade && (
            <div className="rounded-lg border border-violet-500/20 bg-violet-500/10 px-4 py-3 text-center">
              <p className="text-2xl font-bold text-text-violet">
                {submission.instructorGrade.score} /{" "}
                {submission.instructorGrade.maximum}
              </p>

              <p className="text-[10px] text-text-violet">
                Instructor grade
              </p>
            </div>
          )}
        </div>

        <section className="mb-5">
          <h2 className="mb-3 text-xs font-semibold text-text-muted">
            Submission attempts
          </h2>

          <div className="space-y-2">
            {submission.attempts.map((attempt) => (
              <div
                key={attempt.attemptNumber}
                className="flex flex-col gap-2 rounded-lg border border-border-subtle bg-bg-glass px-3 py-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="text-xs font-medium text-text-muted">
                    Attempt {attempt.attemptNumber}
                  </p>

                  <p className="mt-0.5 text-[10px] text-text-muted">
                    Submitted {attempt.submittedLabel}
                  </p>
                </div>

                {attempt.isOfficial ? (
                  <span className="w-fit rounded-full border border-green-500/20 bg-green-500/10 px-2.5 py-1 text-[10px] font-medium text-green-400">
                    Latest official submission
                  </span>
                ) : (
                  <span className="w-fit rounded-full border border-border-subtle bg-bg-glass px-2.5 py-1 text-[10px] text-text-muted">
                    Previous attempt
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>



        <section className="rounded-lg border-l-2 border-violet-500/30 bg-violet-500/[0.05] px-4 py-3">
          <h2 className="mb-1 text-xs font-semibold text-text-violet">
            Instructor feedback
          </h2>

          <p className="text-[11px] leading-relaxed text-text-muted">
            {submission.instructorFeedback}
          </p>
        </section>
      </section>
    </div>
  );
}

function isSubmittedActivity(activity) {
  return (
    activity.status === "submitted" ||
    activity.status === "graded"
  );
}

function ArchiveIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><rect width="20" height="5" x="2" y="3" rx="1"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><path d="M10 12h4"/></svg>
  );
}

export default function Submissions() {
  const navigate = useNavigate();
  const { id } = useParams();

  const [submissions, setSubmissions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchSubmissions = async () => {
      try {
        const [subRes, actRes, classRes] = await Promise.all([
          api.get("/submissions/"),
          api.get("/activities/"),
          api.get("/classrooms/mine"),
        ]);

        const classMap = {};
        classRes.forEach(c => {
          classMap[c.classroom.class_id] = c.classroom.subject_code;
        });

        const actMap = {};
        actRes.forEach(a => {
          actMap[a.task_id] = {
            title: a.title,
            type: a.activity_type === "laboratory" ? "Laboratory" : "Homework",
            course: classMap[a.class_id] || "Unknown",
          };
        });

        const mappedSubs = subRes.map((sub) => {
          const act = actMap[sub.task_id] || { title: "Unknown", type: "Unknown", course: "Unknown" };
          return {
            id: sub.sub_id,
            activityTitle: act.title,
            activityType: act.type,
            courseCode: act.course,
            status: sub.status,
            latestAttempt: sub.attempt_number,
            totalAttempts: sub.attempt_number,
            submittedLabel: new Date(sub.submitted_at).toLocaleString(),
            isOfficial: sub.is_official,
            instructorGrade: null,
            instructorFeedback: "Awaiting instructor review.",
            attempts: [
              {
                attemptNumber: sub.attempt_number,
                submittedLabel: new Date(sub.submitted_at).toLocaleString(),
                isOfficial: sub.is_official,
              }
            ],
            rawCode: sub.raw_code
          };
        });

        setSubmissions(mappedSubs);
      } catch (err) {
        console.error("Failed to load submissions", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSubmissions();
  }, []);

  const selectedSubmission = id
    ? submissions.find(
        (submission) => submission.id === Number(id),
      )
    : null;

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main">
      <Sidebar />

      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <main className="submissions-page flex-1 overflow-y-auto px-6 py-6 sm:px-8">
          <style>
            {`
              @keyframes submissionsFadeUp {
                from {
                  opacity: 0;
                  transform: translateY(10px);
                }

                to {
                  opacity: 1;
                  transform: translateY(0);
                }
              }

              .submissions-page {
                animation:
                  submissionsFadeUp 450ms
                  cubic-bezier(0.25, 0.46, 0.45, 0.94)
                  both;
              }

              @media (prefers-reduced-motion: reduce) {
                .submissions-page,
                .submission-card {
                  animation: none !important;
                }
              }
            `}
          </style>

          <div className="w-full">
            {!id && (
              <>
                <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-border-subtle pb-6">
                  <div>
                    <h1 className="text-2xl font-bold flex items-center gap-3">
                      <ArchiveIcon className="h-6 w-6 text-green-500" />
                      Submissions
                    </h1>
                    <p className="mt-1 text-sm text-text-muted">
                      {submissions.length} submitted{" "}
                      {submissions.length === 1
                        ? "activity"
                        : "activities"}
                    </p>
                  </div>
                </header>



                <SubmissionList
                  submissions={submissions}
                  isLoading={isLoading}
                  onOpen={(submissionId) =>
                    navigate(`/student/submissions/${submissionId}`)
                  }
                />
              </>
            )}

            {id && selectedSubmission && (
              <SubmissionDetails
                submission={selectedSubmission}
                onBack={() => navigate("/student/submissions")}
              />
            )}

            {id && !selectedSubmission && (
              <section className="rounded-xl border border-dashed border-border-subtle px-5 py-16 text-center">
                <h1 className="text-lg font-semibold">
                  Submission not found
                </h1>

                <p className="mt-2 text-sm text-text-muted">
                  The requested submission does not exist or is not
                  available to this account.
                </p>

                <button
                  type="button"
                  onClick={() => navigate("/student/submissions")}
                  className="mt-5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold transition-colors hover:bg-blue-500"
                >
                  Return to submissions
                </button>
              </section>
            )}
          </div>
        </main>

        <Statusbar />
      </div>
    </div>
  );
}
