import { useState, useEffect } from "react";
import Pagination from "../../components/ui/Pagination";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../services/api";

import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";


const STATUS_CONFIG = {
  awaiting_review: {
    label: "Awaiting review",
    badgeClass:
      "border-psu-maroon/30 bg-psu-maroon/10 text-text-brand",
    accentClass: "border-l-psu-maroon dark:border-l-psu-gold",
  },
  graded: {
    label: "Graded",
    badgeClass:
      "border-violet-500/30 bg-violet-500/10 text-violet-400",
    accentClass: "border-l-violet-500",
  },
};

const FILTERS = [
  { label: "All", value: "all" },
  { label: "Awaiting review", value: "awaiting_review" },
  { label: "Graded", value: "graded" },
];

function getPercentage(value, maximum) {
  if (!maximum) {
    return 0;
  }

  return Math.round((value / maximum) * 100);
}

function SubmissionList({ submissions, onOpen, isLoading }) {
  const currentPage = 1;
  const itemsPerPage = 50;

  if (isLoading) {
    return (
      <section className="space-y-4">
        {[1, 2, 3].map((i) => (
          <article key={i} className="cursor-pointer overflow-hidden rounded-xl border border-border-subtle bg-bg-glass p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-border-subtle hover:bg-bg-glass-hover hover:shadow-lg animate-pulse">
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
      {submissions.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage).map((submission, index) => {
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
                className="shrink-0 rounded-lg border border-psu-maroon/40 px-3 py-1.5 text-xs font-semibold text-text-brand transition duration-150 hover:-translate-y-px hover:bg-psu-maroon/10 active:translate-y-0 active:scale-[0.98]"
              >
                View details
              </button>
            </div>

            <div className="mb-4 flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-psu-maroon/20 bg-psu-maroon/10 px-2.5 py-1 text-[10px] font-medium text-text-brand">
                Attempt {submission.latestAttempt}
              </span>

              {submission.isOfficial && (
                <span className="rounded-full border border-psu-maroon/20 bg-psu-maroon/[0.06] px-2.5 py-1 text-[10px] text-text-brand">
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
                    <p className="text-sm font-semibold text-text-brand">
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
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-psu-maroon/10 text-text-brand ring-4 ring-psu-maroon/5">
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
        className="text-xs text-text-brand transition-colors hover:text-text-brand"
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
                  <span className="w-fit rounded-full border border-psu-maroon/20 bg-psu-maroon/10 px-2.5 py-1 text-[10px] font-medium text-text-brand">
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
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSubmissions = async () => {
      try {
        const [subRes, actRes, classRes] = await Promise.all([
          api.get("/submissions/"),
          api.get("/activities/"),
          api.get("/classrooms/mine"),
        ]);
        
        let allGrades = [];
        let currentPage = 1;
        let totalPages = 1;

        while (currentPage <= totalPages) {
          try {
            const gradesPage = await api.get(`/activities/released-grades?page=${currentPage}&page_size=100`);
            if (gradesPage && gradesPage.items) {
              allGrades = [...allGrades, ...gradesPage.items];
              totalPages = gradesPage.total_pages || gradesPage.pages || 1;
            } else {
              break;
            }
          } catch (e) {
            setError("Failed to fetch grades page.");
            break;
          }
          currentPage++;
        }
        const gradesRes = { items: allGrades };

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


        const gradeMap = {};
        if (gradesRes && gradesRes.items) {
          gradesRes.items.forEach(g => {
            gradeMap[g.sub_id] = { score: g.score, maximum: g.max_score, feedback: g.feedback };
          });
        }

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
            instructorGrade: gradeMap[sub.sub_id] ? { score: gradeMap[sub.sub_id].score, maximum: gradeMap[sub.sub_id].maximum } : null,
            instructorFeedback: gradeMap[sub.sub_id]?.feedback || "Awaiting instructor review.",
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
        setError("Failed to load submissions. Please try again later.");
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

  const filteredSubmissions = submissions.filter((sub) => {
    if (filter === "all") return true;
    if (filter === "awaiting_review") return sub.status === "submitted" || sub.status === "awaiting_review";
    if (filter === "graded") return sub.status === "graded";
    return true;
  });

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main">
      <Sidebar />

      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <main className="submissions-page min-w-0 flex-1 overflow-y-auto px-6 py-6 sm:px-8">
        <div className="max-w-6xl mx-auto w-full">
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
                    <p className="mb-1 font-mono text-xs text-text-brand">PROGRESS</p>
                    <h1 className="text-2xl font-bold flex items-center gap-3">
                      <ArchiveIcon className="h-6 w-6 text-text-brand" />
                      Submissions
                    </h1>
                    <p className="mt-1 text-sm text-text-muted">
                      {filteredSubmissions.length} submitted{" "}
                      {filteredSubmissions.length === 1
                        ? "activity"
                        : "activities"}
                    </p>
                  </div>
                  
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                    <div className="flex items-center gap-2 rounded-lg border border-border-subtle bg-bg-glass p-1">
                      {FILTERS.map((f) => (
                        <button
                          key={f.value}
                          onClick={() => setFilter(f.value)}
                          className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
                            filter === f.value
                              ? "bg-psu-maroon text-white shadow-sm"
                              : "text-text-muted hover:bg-bg-glass hover:text-text-main"
                          }`}
                        >
                          {f.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </header>

                <SubmissionList
                  submissions={filteredSubmissions}
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
                  className="mt-5 rounded-lg bg-psu-maroon px-4 py-2 text-sm font-semibold transition-colors hover:bg-psu-maroon"
                >
                  Return to submissions
                </button>
              </section>
            )}
          </div>
        </div>
      </main>

        <Statusbar />
      </div>
    </div>
  );
}
