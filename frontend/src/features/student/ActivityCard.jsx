import { Link } from "react-router-dom";
import { ACTIVITY_STATUS } from "./studentData";

function ClockIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M8 5v3.5l2 1.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** One activity row used on the dashboard, assignments and class pages. */
export default function ActivityCard({ activity, showClass = true }) {
  const status = ACTIVITY_STATUS[activity.status] || ACTIVITY_STATUS.open;
  const workspacePath = `/student/workspace?activity=${activity.id}`;
  const accent =
    activity.status === "past_due" || activity.status === "rejected"
      ? "border-l-psu-red"
      : activity.isSubmitted
        ? "border-l-border-strong"
        : activity.status === "due_soon"
          ? "border-l-psu-gold"
          : "border-l-psu-maroon";

  return (
    <article className={`card border-l-[3px] ${accent} p-4 sm:p-5`}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <h3 className="min-w-0 break-words text-sm font-semibold text-text-main">{activity.title}</h3>
            <span className={`badge ${status.badge}`}>{status.label}</span>
            <span className="badge badge-neutral">{activity.activityType}</span>
          </div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-text-muted">
            {showClass && <span className="font-medium">{activity.classLabel}</span>}
            <span className="inline-flex items-center gap-1.5">
              <ClockIcon />
              {activity.dueLabel}
            </span>
            {activity.attemptCount > 0 && (
              <span>
                {activity.attemptCount} {activity.attemptCount === 1 ? "attempt" : "attempts"} submitted
              </span>
            )}
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          {activity.isSubmitted && activity.submissionId ? (
            <>
              <Link to={`/student/submissions/${activity.submissionId}`} className="btn-secondary btn-sm">
                View submission
              </Link>
              {activity.status !== "graded" && (
                <Link to={workspacePath} className="btn-ghost btn-sm">
                  Open workspace
                </Link>
              )}
            </>
          ) : (
            <Link
              to={workspacePath}
              className={activity.status === "past_due" ? "btn-secondary btn-sm" : "btn-primary btn-sm"}
            >
              {activity.status === "past_due" ? "View activity" : "Open workspace"}
            </Link>
          )}
        </div>
      </div>
    </article>
  );
}
