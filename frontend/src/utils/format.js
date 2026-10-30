/** Shared display formatting. All helpers tolerate missing or invalid input. */

export function classLabel(classroom) {
  if (!classroom) return "Class";
  const base = classroom.subject_code || classroom.name || `Class ${classroom.class_id}`;
  return classroom.section ? `${base} · ${classroom.section}` : base;
}

export function formatDate(value, options = { month: "short", day: "numeric", year: "numeric" }) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleDateString(undefined, options);
}

export function formatDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? ""
    : date.toLocaleString(undefined, { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" });
}

export function humanize(value) {
  if (value === null || value === undefined || value === "") return "—";
  const text = String(value).replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}
