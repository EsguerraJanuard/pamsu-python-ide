import api from "../../services/api";
import { classLabel, formatDateTime } from "../../utils/format";

export { classLabel, formatDate, formatDateTime } from "../../utils/format";

/**
 * Student activity data shared by the dashboard, assignments and class pages.
 * Every derived field here comes from the API; nothing is estimated.
 */

export const ACTIVITY_STATUS = {
  open: { label: "Open", badge: "badge-brand" },
  due_soon: { label: "Due soon", badge: "badge-gold" },
  past_due: { label: "Past due", badge: "badge-danger" },
  submitted: { label: "Submitted", badge: "badge-neutral" },
  awaiting_review: { label: "Awaiting review", badge: "badge-neutral" },
  graded: { label: "Graded", badge: "badge-success" },
  rejected: { label: "Returned", badge: "badge-danger" },
};

const DAY_MS = 24 * 60 * 60 * 1000;

/** Picks the attempt that represents the activity: the official one, else the newest. */
function representativeSubmission(attempts) {
  if (!attempts || attempts.length === 0) return null;
  const official = attempts.find((s) => s.is_official);
  if (official) return official;
  return [...attempts].sort((a, b) => new Date(b.submitted_at) - new Date(a.submitted_at))[0];
}

export function mapActivity(task, classMap, attemptsByTask, now = Date.now()) {
  const attempts = attemptsByTask[task.task_id] || [];
  const submission = representativeSubmission(attempts);
  const due = task.due_at ? new Date(task.due_at) : null;

  let status = "open";
  if (submission) {
    status = submission.status;
  } else if (due && due.getTime() < now) {
    status = "past_due";
  } else if (due && due.getTime() - now < DAY_MS) {
    status = "due_soon";
  }

  let dueLabel = "No due date";
  if (due) dueLabel = `Due ${formatDateTime(due)}`;

  return {
    id: task.task_id,
    title: task.title,
    classId: task.class_id,
    classLabel: classLabel(classMap[task.class_id]),
    activityType: task.activity_type === "homework" ? "Homework" : "Laboratory",
    dueAt: due,
    dueLabel,
    status,
    isSubmitted: Boolean(submission),
    submissionId: submission?.sub_id ?? null,
    attemptCount: attempts.length,
  };
}

/** Loads enrolled classes, visible activities and own submissions in parallel. */
export async function loadStudentActivities() {
  const [classrooms, tasks, submissions] = await Promise.all([
    api.get("/classrooms/mine"),
    api.get("/activities/"),
    api.get("/submissions/"),
  ]);

  const classMap = {};
  (classrooms || []).forEach((enrollment) => {
    if (enrollment?.classroom) classMap[enrollment.classroom.class_id] = enrollment.classroom;
  });

  const attemptsByTask = {};
  (submissions || []).forEach((sub) => {
    (attemptsByTask[sub.task_id] ||= []).push(sub);
  });

  const now = Date.now();
  const activities = (tasks || [])
    .map((task) => mapActivity(task, classMap, attemptsByTask, now))
    .sort((a, b) => {
      // Unsubmitted first, then by nearest due date, then newest id.
      if (a.isSubmitted !== b.isSubmitted) return a.isSubmitted ? 1 : -1;
      if (a.dueAt && b.dueAt) return a.dueAt - b.dueAt;
      if (a.dueAt) return -1;
      if (b.dueAt) return 1;
      return b.id - a.id;
    });

  return { classrooms: classrooms || [], classMap, activities, submissions: submissions || [] };
}

/** Where an activity card should lead: the submission record or the workspace. */
export function activityDestination(activity) {
  if (activity.isSubmitted && activity.submissionId) {
    return `/student/submissions/${activity.submissionId}`;
  }
  return `/student/workspace?activity=${activity.id}`;
}

export function isActiveActivity(activity) {
  return !activity.isSubmitted && activity.status !== "past_due";
}
