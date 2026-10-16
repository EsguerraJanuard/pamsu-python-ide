import api from "../../services/api";

export const SUBMISSION_STATUS = {
  submitted: { label: "Submitted", badge: "badge-neutral" },
  awaiting_review: { label: "Awaiting review", badge: "badge-neutral" },
  graded: { label: "Graded", badge: "badge-success" },
  rejected: { label: "Returned", badge: "badge-danger" },
};

/** Loads every page of the student's released grades (page_size max is 100). */
export async function loadReleasedGrades(params = "") {
  const items = [];
  let page = 1;
  let totalPages;
  do {
    const response = await api.get(`/activities/released-grades?page=${page}&page_size=100${params}`);
    items.push(...(response?.items || []));
    totalPages = response?.total_pages || 1;
    page += 1;
  } while (page <= totalPages && page <= 20);
  return items;
}

export function formatScore(grade) {
  if (!grade) return "";
  const score = Number.isInteger(grade.score) ? grade.score : grade.score.toFixed(2);
  const max = Number.isInteger(grade.max_score) ? grade.max_score : grade.max_score.toFixed(2);
  return `${score} / ${max}`;
}
