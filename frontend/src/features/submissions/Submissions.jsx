import { useNavigate, useParams } from "react-router-dom";

import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";

const PREVIEW_SUBMISSIONS = [
  {
    id: 3,
    activityTitle: "Lab Activity 2 — Control Flow and Functions",
    activityType: "Laboratory",
    courseCode: "CCS101",
    status: "awaiting_review",
    latestAttempt: 2,
    totalAttempts: 2,
    submittedLabel: "January 10, 2026 at 10:42 PM",
    isOfficial: true,
    astIndicators: {
      met: 5,
      total: 6,
    },
    testCases: {
      passed: 8,
      total: 10,
    },
    similarityIndicator: {
      percentage: 12,
      label: "Low structural overlap",
    },
    instructorGrade: null,
    instructorFeedback:
      "This submission is still awaiting instructor review.",
    attempts: [
      {
        attemptNumber: 1,
        submittedLabel: "January 10, 2026 at 8:15 PM",
        isOfficial: false,
      },
      {
        attemptNumber: 2,
        submittedLabel: "January 10, 2026 at 10:42 PM",
        isOfficial: true,
      },
    ],
  },
  {
    id: 4,
    activityTitle: "Lab Activity 1 — Variables and Data Types",
    activityType: "Laboratory",
    courseCode: "CCS101",
    status: "graded",
    latestAttempt: 1,
    totalAttempts: 1,
    submittedLabel: "January 5, 2026 at 9:28 PM",
    isOfficial: true,
    astIndicators: {
      met: 6,
      total: 6,
    },
    testCases: {
      passed: 10,
      total: 10,
    },
    similarityIndicator: {
      percentage: 8,
      label: "Low structural overlap",
    },
    instructorGrade: {
      score: 92,
      maximum: 100,
    },
    instructorFeedback:
      "All required concepts were demonstrated. Good use of type conversion and clear variable naming.",
    attempts: [
      {
        attemptNumber: 1,
        submittedLabel: "January 5, 2026 at 9:28 PM",
        isOfficial: true,
      },
    ],
  },
];

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

function SubmissionList({ submissions, onOpen }) {
  return (
    <section
      className="space-y-4"
      aria-label="Submitted activities"
    >
      {submissions.map((submission, index) => {
        const status =
          STATUS_CONFIG[submission.status] ??
          STATUS_CONFIG.awaiting_review;

        const astPercentage = getPercentage(
          submission.astIndicators.met,
          submission.astIndicators.total,
        );

        const testPercentage = getPercentage(
          submission.testCases.passed,
          submission.testCases.total,
        );

        return (
          <article
            key={submission.id}
            className={`submission-card rounded-xl border border-l-[3px] border-white/[0.06] bg-[#1a1d27] p-5 ${status.accentClass}`}
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

                <p className="text-[11px] text-white/35">
                  {submission.courseCode} ·{" "}
                  {submission.activityType}
                </p>

                <p className="mt-1 text-[11px] text-white/30">
                  Submitted {submission.submittedLabel}
                </p>
              </div>

              <button
                type="button"
                onClick={() => onOpen(submission.id)}
                className="shrink-0 rounded-lg border border-blue-500/40 px-3 py-1.5 text-xs font-semibold text-blue-400 transition duration-150 hover:-translate-y-px hover:bg-blue-500/10 active:translate-y-0 active:scale-[0.98]"
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

              <span className="text-[10px] text-white/30">
                {submission.totalAttempts}{" "}
                {submission.totalAttempts === 1
                  ? "attempt"
                  : "attempts"}{" "}
                recorded
              </span>
            </div>

            <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-white/[0.06] bg-white/[0.03] p-3">
                <p className="text-lg font-bold text-amber-400">
                  {submission.astIndicators.met} /{" "}
                  {submission.astIndicators.total}
                </p>

                <p className="mt-0.5 text-[10px] text-white/40">
                  AST indicators met
                </p>

                <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/[0.06]">
                  <div
                    className="h-full rounded-full bg-amber-500"
                    style={{ width: `${astPercentage}%` }}
                  />
                </div>
              </div>

              <div className="rounded-lg border border-white/[0.06] bg-white/[0.03] p-3">
                <p className="text-lg font-bold text-green-400">
                  {submission.testCases.passed} /{" "}
                  {submission.testCases.total}
                </p>

                <p className="mt-0.5 text-[10px] text-white/40">
                  Test cases passed
                </p>

                <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/[0.06]">
                  <div
                    className="h-full rounded-full bg-green-500"
                    style={{ width: `${testPercentage}%` }}
                  />
                </div>
              </div>

              <div className="rounded-lg border border-white/[0.06] bg-white/[0.03] p-3">
                {submission.instructorGrade ? (
                  <>
                    <p className="text-lg font-bold text-violet-400">
                      {submission.instructorGrade.score} /{" "}
                      {submission.instructorGrade.maximum}
                    </p>

                    <p className="mt-0.5 text-[10px] text-white/40">
                      Instructor grade
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-sm font-semibold text-blue-400">
                      Pending
                    </p>

                    <p className="mt-1 text-[10px] text-white/40">
                      Instructor grade
                    </p>
                  </>
                )}
              </div>
            </div>

            <div className="rounded-lg border-l-2 border-white/[0.08] bg-white/[0.03] px-3 py-2 font-mono text-[11px] text-white/45">
              <span className="text-white/25">
                Instructor feedback:{" "}
              </span>

              {submission.instructorFeedback}
            </div>
          </article>
        );
      })}

      {submissions.length === 0 && (
        <div className="rounded-xl border border-dashed border-white/[0.08] py-16 text-center">
          <p className="text-sm text-white/30">
            No submissions have been recorded yet.
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

  const astPercentage = getPercentage(
    submission.astIndicators.met,
    submission.astIndicators.total,
  );

  const testPercentage = getPercentage(
    submission.testCases.passed,
    submission.testCases.total,
  );

  return (
    <div className="space-y-5">
      <button
        type="button"
        onClick={onBack}
        className="text-xs text-blue-400 transition-colors hover:text-blue-300"
      >
        ← Back to submissions
      </button>

      <section
        className={`rounded-xl border border-l-[3px] border-white/[0.06] bg-[#1a1d27] p-5 ${status.accentClass}`}
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

            <p className="text-xs text-white/35">
              {submission.courseCode} ·{" "}
              {submission.activityType}
            </p>

            <p className="mt-1 text-[11px] text-white/30">
              Latest submission: {submission.submittedLabel}
            </p>
          </div>

          {submission.instructorGrade && (
            <div className="rounded-lg border border-violet-500/20 bg-violet-500/10 px-4 py-3 text-center">
              <p className="text-2xl font-bold text-violet-300">
                {submission.instructorGrade.score} /{" "}
                {submission.instructorGrade.maximum}
              </p>

              <p className="text-[10px] text-violet-200/60">
                Instructor grade
              </p>
            </div>
          )}
        </div>

        <section className="mb-5">
          <h2 className="mb-3 text-xs font-semibold text-white/70">
            Submission attempts
          </h2>

          <div className="space-y-2">
            {submission.attempts.map((attempt) => (
              <div
                key={attempt.attemptNumber}
                className="flex flex-col gap-2 rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="text-xs font-medium text-white/70">
                    Attempt {attempt.attemptNumber}
                  </p>

                  <p className="mt-0.5 text-[10px] text-white/30">
                    Submitted {attempt.submittedLabel}
                  </p>
                </div>

                {attempt.isOfficial ? (
                  <span className="w-fit rounded-full border border-green-500/20 bg-green-500/10 px-2.5 py-1 text-[10px] font-medium text-green-400">
                    Latest official submission
                  </span>
                ) : (
                  <span className="w-fit rounded-full border border-white/[0.08] bg-white/[0.03] px-2.5 py-1 text-[10px] text-white/30">
                    Previous attempt
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>

        <section className="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="rounded-lg border border-white/[0.06] bg-white/[0.03] p-4">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-medium text-white/60">
                AST indicators
              </h2>

              <span className="font-mono text-xs font-semibold text-amber-400">
                {submission.astIndicators.met} /{" "}
                {submission.astIndicators.total}
              </span>
            </div>

            <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
              <div
                className="h-full rounded-full bg-amber-500"
                style={{ width: `${astPercentage}%` }}
              />
            </div>
          </div>

          <div className="rounded-lg border border-white/[0.06] bg-white/[0.03] p-4">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-medium text-white/60">
                Test cases
              </h2>

              <span className="font-mono text-xs font-semibold text-green-400">
                {submission.testCases.passed} /{" "}
                {submission.testCases.total}
              </span>
            </div>

            <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
              <div
                className="h-full rounded-full bg-green-500"
                style={{ width: `${testPercentage}%` }}
              />
            </div>
          </div>
        </section>

        <section className="mb-5 rounded-lg border border-amber-500/15 bg-amber-500/[0.05] p-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-xs font-semibold text-amber-300">
                Structural similarity indicator
              </h2>

              <p className="mt-1 text-[11px] text-white/40">
                {submission.similarityIndicator.label}
              </p>
            </div>

            <span className="font-mono text-lg font-bold text-amber-400">
              {submission.similarityIndicator.percentage}%
            </span>
          </div>

          <p className="mt-3 text-[10px] leading-relaxed text-white/30">
            This automated result is only a review indicator. It does
            not independently prove copying, plagiarism, or academic
            misconduct. Final interpretation belongs to the authorized
            instructor.
          </p>
        </section>

        <section className="rounded-lg border-l-2 border-violet-500/30 bg-violet-500/[0.05] px-4 py-3">
          <h2 className="mb-1 text-xs font-semibold text-violet-300">
            Instructor feedback
          </h2>

          <p className="text-[11px] leading-relaxed text-white/50">
            {submission.instructorFeedback}
          </p>
        </section>
      </section>
    </div>
  );
}

export default function Submissions() {
  const navigate = useNavigate();
  const { id } = useParams();

  const selectedSubmission = id
    ? PREVIEW_SUBMISSIONS.find(
        (submission) => submission.id === Number(id),
      )
    : null;

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <main className="submissions-page flex-1 overflow-y-auto px-5 py-6 sm:px-8">
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

          <div className="mx-auto max-w-5xl">
            {!id && (
              <>
                <header className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h1 className="text-2xl font-bold">
                      My Submissions
                    </h1>

                    <p className="mt-1 text-sm text-white/40">
                      {PREVIEW_SUBMISSIONS.length} submitted{" "}
                      {PREVIEW_SUBMISSIONS.length === 1
                        ? "activity"
                        : "activities"}
                    </p>
                  </div>

                  <span className="w-fit rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-[11px] font-medium text-amber-300">
                    Preview data
                  </span>
                </header>

                <section className="mb-6 rounded-xl border border-blue-500/20 bg-blue-500/[0.07] px-4 py-3">
                  <p className="text-xs leading-relaxed text-blue-200/80">
                    System-generated AST, test-case, and similarity
                    results are review indicators only. Official grades
                    and academic decisions are made by your instructor.
                  </p>
                </section>

                <SubmissionList
                  submissions={PREVIEW_SUBMISSIONS}
                  onOpen={(submissionId) =>
                    navigate(`/submissions/${submissionId}`)
                  }
                />
              </>
            )}

            {id && selectedSubmission && (
              <SubmissionDetails
                submission={selectedSubmission}
                onBack={() => navigate("/submissions")}
              />
            )}

            {id && !selectedSubmission && (
              <section className="rounded-xl border border-dashed border-white/[0.08] px-5 py-16 text-center">
                <h1 className="text-lg font-semibold">
                  Submission not found
                </h1>

                <p className="mt-2 text-sm text-white/35">
                  The requested submission does not exist or is not
                  available to this account.
                </p>

                <button
                  type="button"
                  onClick={() => navigate("/submissions")}
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
