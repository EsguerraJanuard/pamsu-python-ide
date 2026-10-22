import { useCallback, useEffect, useId, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import SignOutModal from "../../components/layout/SignOutModal";
import ConfirmationModal from "../../components/modals/ConfirmationModal";
import Modal from "../../components/ui/Modal";
import { EmptyState, ErrorState, FieldError, InlineAlert, LoadingState, PageHeader } from "../../components/ui/StateViews";
import api, { ApiError, getErrorMessage } from "../../services/api";
import { formatDate, formatDateTime, humanize } from "../../utils/format";
import { useAuth } from "../auth/AuthContext";
import { ChangePasswordSection } from "../settings/AccountSections";

const PAGE_SIZE = 50;
const RECENT_ACTIVITY_COUNT = 6;
const SCHOOL_EMAIL = /^[^\s@]+@pampangastateu\.edu\.ph$/i;
const SCHOOL_ID = /^(\d{10}|\d{4}-\d{5})$/;

/* Stroke icons (24×24, drawn with currentColor). */
const ICONS = {
  overview: "M3 12l2-2 7-7 7 7 2 2M5 10v10h4v-6h6v6h4V10",
  faculty: "M12 14l9-5-9-5-9 5 9 5zm0 0v6m-6-9.5v5.5l6 3 6-3v-5.5",
  students: "M17 20h5v-2a3 3 0 00-5.36-1.86M9 20H4v-2a4 4 0 017-2.65M15 7a3 3 0 11-6 0 3 3 0 016 0z",
  audit: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4",
  settings: "M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-2.82 1.17V21a2 2 0 11-4 0v-.09A1.65 1.65 0 008.6 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06A1.65 1.65 0 003 15.08V15a2 2 0 110-4h.09A1.65 1.65 0 004.6 8.6a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06A1.65 1.65 0 009 4.6V4a2 2 0 114 0v.09a1.65 1.65 0 001.03 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06A1.65 1.65 0 0019.4 9c.4.16.84.24 1.28.24H21a2 2 0 110 4h-.09c-.44 0-.88.08-1.28.24z",
  classroom: "M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6",
  shield: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10zM9 12l2 2 4-4",
  wrench: "M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z",
  activity: "M22 12h-4l-3 9L9 3l-3 9H2",
  userPlus: "M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M9 3a4 4 0 100 8 4 4 0 000-8zM19 8v6M22 11h-6",
  upload: "M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12",
  download: "M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3",
  chevronRight: "M9 18l6-6-6-6",
  arrowRight: "M5 12h14M13 6l6 6-6 6",
  key: "M21 2l-2 2m-7.61 7.61a5.5 5.5 0 11-7.78 7.78 5.5 5.5 0 017.78-7.78zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4",
  ban: "M12 22a10 10 0 100-20 10 10 0 000 20zM4.93 4.93l14.14 14.14",
  check: "M22 11.08V12a10 10 0 11-5.93-9.14M22 4L12 14.01l-3-3",
  search: "M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z",
  signOut: "M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9",
  calendar: "M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2z",
  bolt: "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
  pencil: "M12 20h9M16.5 3.5a2.12 2.12 0 013 3L7 19l-4 1 1-4 12.5-12.5z",
  refresh: "M21 12a9 9 0 11-2.64-6.36L21 8M21 3v5h-5",
  x: "M18 6L6 18M6 6l12 12",
  chevronLeft: "M15 18l-6-6 6-6",
};

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "faculty", label: "Faculty" },
  { id: "students", label: "Students" },
  { id: "audit", label: "Audit trail" },
  { id: "settings", label: "Settings" },
];

const STRICTNESS = [
  ["lax", "Lenient", "Focus on execution output; structural checks are relaxed."],
  ["moderate", "Moderate", "Balanced structural checks (recommended)."],
  ["strict", "Strict", "Required structures are enforced rigidly."],
];

const QUICK_ACTIONS = [
  { id: "add-faculty", icon: "userPlus", title: "Add a faculty account", text: "Invite an instructor; they set their own password.", tab: "faculty", focus: "provision-instructor-email" },
  { id: "add-student", icon: "userPlus", title: "Add a student account", text: "Register one student by university email and school ID.", tab: "students", focus: "provision-student-email" },
  { id: "masterlist", icon: "upload", title: "Import a masterlist", text: "Create many student accounts from a CSV or .xlsx file.", tab: "students", focus: "admin-bulk-file" },
  { id: "audit", icon: "shield", title: "Review the audit trail", text: "Check sign-ins and account changes.", tab: "audit" },
  { id: "settings", icon: "settings", title: "System settings", text: "Maintenance mode and the default AST strictness.", tab: "settings" },
];

const OUTCOME_TONE = { succeeded: "success", failed: "danger", denied: "warning" };

const AUDIT_PAGE_SIZES = [25, 50, 100];
const EMPTY_AUDIT_FILTERS = { q: "", action_type: "", outcome: "", actor_role: "", from: "", to: "" };
const AUDIT_OUTCOMES = ["succeeded", "failed", "denied"];
const AUDIT_ROLES = ["admin", "instructor", "student", "system"];

/**
 * True when the server doesn't have the endpoint yet (the backend is deployed
 * separately from this page): 405 on a path that exists with other methods,
 * or FastAPI's bare 404 for an unknown path.
 */
function isMissingRoute(error) {
  return error instanceof ApiError && (error.status === 405 || (error.status === 404 && error.data?.detail === "Not Found"));
}

/** Download rows as CSV. Cells that a spreadsheet would run as a formula are prefixed with '. */
function downloadCsv(filename, rows) {
  const cell = (value) => {
    let text = String(value ?? "");
    if (/^[=+\-@\t\r]/.test(text)) text = `'${text}`;
    return `"${text.replace(/"/g, '""')}"`;
  };
  const blob = new Blob([rows.map((row) => row.map(cell).join(",")).join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

/** ISO instant for local midnight of a yyyy-mm-dd date, optionally days later. */
function localDayStart(dateString, addDays = 0) {
  const [year, month, day] = dateString.split("-").map(Number);
  return new Date(year, month - 1, day + addDays).toISOString();
}

function matchesAccount(user, query) {
  return [user.name, user.email, user.school_id].some((value) => value && value.toLowerCase().includes(query));
}

const TH = "px-5 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-text-muted";
const ELEVATED = "shadow-[0_1px_2px_rgba(28,25,23,0.04),0_12px_32px_-20px_rgba(119,37,11,0.45)]";

/** Random temporary password (letters, digits, symbol) shown once to the admin. */
function generateTempPassword() {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789";
  const bytes = new Uint32Array(10);
  crypto.getRandomValues(bytes);
  const core = Array.from(bytes, (b) => alphabet[b % alphabet.length]).join("");
  return `${core.slice(0, 5)}-${core.slice(5)}!`;
}

function formatTime(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

/** "Just now", "12 min ago", "3 h ago", then the full date. */
function timeAgo(value, now = Date.now()) {
  const time = new Date(value).getTime();
  if (Number.isNaN(time)) return "";
  const minutes = Math.floor((now - time) / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return formatDateTime(value);
}

function greeting(now = new Date()) {
  const hour = now.getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function initials(name) {
  const parts = String(name || "").trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return `${parts[0][0]}${last}`.toUpperCase();
}

function plural(count, word) {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}

function Icon({ name, className = "h-4 w-4", strokeWidth = 1.8 }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <path d={ICONS[name]} />
    </svg>
  );
}

function Avatar({ name, size = "md" }) {
  const sizes = { sm: "h-8 w-8 text-[11px]", md: "h-9 w-9 text-xs" };
  return (
    <span
      aria-hidden="true"
      className={`inline-flex shrink-0 items-center justify-center rounded-full bg-psu-maroon/[0.08] font-semibold text-text-brand ring-1 ring-psu-maroon/15 ${sizes[size]}`}
    >
      {initials(name)}
    </span>
  );
}

const PILL_TONES = {
  success: "border-emerald-600/25 bg-emerald-600/[0.08] text-text-emerald",
  danger: "border-psu-red/25 bg-psu-red/[0.07] text-text-rose",
  warning: "border-psu-gold/60 bg-psu-gold/15 text-text-amber",
  neutral: "border-border-strong bg-bg-alt text-text-muted",
};
const DOT_TONES = { success: "bg-emerald-600", danger: "bg-psu-red", warning: "bg-psu-gold-dark", neutral: "bg-text-muted" };

/** Status pill: a coloured dot plus text, so the state never depends on colour alone. */
function Pill({ tone = "neutral", children }) {
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-semibold ${PILL_TONES[tone]}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${DOT_TONES[tone]}`} aria-hidden="true" />
      {children}
    </span>
  );
}

function OutcomePill({ status }) {
  return <Pill tone={OUTCOME_TONE[status] || "neutral"}>{humanize(status)}</Pill>;
}

/**
 * Card with a header row (title, description, actions) separated from its
 * body, and an optional footer. Pass as="form" to make the whole card a form.
 */
function Panel({ as: Tag = "section", title, description, icon, actions, footer, flush = false, className = "", children, ...rest }) {
  const headingId = `${useId()}-title`;
  return (
    <Tag aria-labelledby={title ? headingId : undefined} className={`card overflow-hidden ${className}`} {...rest}>
      {title && (
        <div className="flex flex-col gap-3 border-b border-border-subtle px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="flex min-w-0 items-start gap-3">
            {icon && (
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-psu-maroon/[0.07] text-text-brand">
                <Icon name={icon} className="h-[18px] w-[18px]" />
              </span>
            )}
            <div className="min-w-0">
              <h2 id={headingId} className="text-base font-semibold text-text-main">
                {title}
              </h2>
              {description && <p className="mt-0.5 text-sm text-text-muted">{description}</p>}
            </div>
          </div>
          {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className={flush ? "" : "p-5 sm:p-6"}>{children}</div>
      {footer && <div className="border-t border-border-subtle bg-bg-alt/60 px-5 py-3.5 sm:px-6">{footer}</div>}
    </Tag>
  );
}

function StatCard({ icon, label, value, hint, tone = "brand" }) {
  return (
    <div className={`card relative overflow-hidden p-5 ${ELEVATED}`}>
      <span className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-psu-maroon via-psu-maroon to-psu-gold" aria-hidden="true" />
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-text-muted">{label}</p>
          <p className={`mt-2 text-3xl font-bold tracking-tight tabular-nums ${tone === "warning" ? "text-text-amber" : "text-text-main"}`}>{value}</p>
        </div>
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-psu-maroon to-psu-maroon-dark text-white shadow-sm ring-2 ring-psu-gold/30">
          <Icon name={icon} className="h-5 w-5" />
        </span>
      </div>
      {hint && <p className="mt-3 border-t border-border-subtle pt-3 text-xs text-text-muted">{hint}</p>}
    </div>
  );
}

function CountBadge({ count, word, hasMore, shown }) {
  const total = hasMore ? `${count}+ ${word}s` : plural(count, word);
  return (
    <span className="badge badge-neutral tabular-nums" aria-live="polite">
      {shown === undefined ? total : `${shown} of ${total}`}
    </span>
  );
}

function ListSkeleton({ rows = 4 }) {
  return (
    <ul className="divide-y divide-border-subtle" role="status" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <li key={i} className="flex animate-pulse items-center gap-3 px-5 py-3.5 sm:px-6">
          <span className="h-8 w-8 rounded-full bg-border-subtle" />
          <span className="flex-1 space-y-2">
            <span className="block h-3 w-2/5 rounded bg-border-subtle" />
            <span className="block h-2.5 w-3/5 rounded bg-border-subtle" />
          </span>
        </li>
      ))}
    </ul>
  );
}

/** Admin endpoints may be missing on a server; explain that plainly. */
function AdminErrorState({ error, resource, onRetry }) {
  if (error?.status === 404) {
    return (
      <ErrorState
        error={error}
        title="Administration service unavailable"
        message="This server does not expose the administration API, so this information can't be loaded. Contact the system maintainer."
      />
    );
  }
  return <ErrorState error={error} resource={resource} onRetry={onRetry} />;
}

function useAdminList(endpoint) {
  const [items, setItems] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState(null);

  const page = (skip) => `${endpoint}${endpoint.includes("?") ? "&" : "?"}skip=${skip}&limit=${PAGE_SIZE}`;

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get(`${endpoint}${endpoint.includes("?") ? "&" : "?"}skip=0&limit=${PAGE_SIZE}`);
      const list = Array.isArray(data) ? data : [];
      setItems(list);
      setHasMore(list.length === PAGE_SIZE);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [endpoint]);

  const loadMore = async () => {
    setIsLoadingMore(true);
    try {
      const data = await api.get(page(items.length));
      const list = Array.isArray(data) ? data : [];
      setItems((prev) => [...prev, ...list]);
      setHasMore(list.length === PAGE_SIZE);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoadingMore(false);
    }
  };

  return { items, setItems, hasMore, isLoading, isLoadingMore, error, load, loadMore };
}

function TextField({ id, label, hint, error, ...props }) {
  return (
    <div>
      <label htmlFor={id} className="field-label">
        {label}
      </label>
      <input
        id={id}
        className="input-field py-2.5"
        aria-invalid={Boolean(error)}
        aria-describedby={[hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(" ") || undefined}
        {...props}
      />
      {hint && !error && (
        <p id={`${id}-hint`} className="mt-1.5 text-xs text-text-muted">
          {hint}
        </p>
      )}
      <FieldError id={`${id}-error`}>{error}</FieldError>
    </div>
  );
}

/** True for a 422 that only says the (older) server requires a password. */
function isPasswordRequired(error) {
  const detail = error instanceof ApiError && error.status === 422 ? error.data?.detail : null;
  return Array.isArray(detail) && detail.length > 0 && detail.every((item) => item?.type === "missing" && item?.loc?.at(-1) === "password");
}

/**
 * Faculty accounts are created without a password: the instructor sets one
 * from the welcome email. A server from before 2026-10-22 still requires one;
 * then a random temporary password is sent instead (that server emails it).
 */
async function createFaculty(payload) {
  try {
    return { created: await api.post("/admin/instructors", payload) };
  } catch (err) {
    if (!isPasswordRequired(err)) throw err;
    const fallbackPassword = generateTempPassword();
    return { created: await api.post("/admin/instructors", { ...payload, password: fallbackPassword }), fallbackPassword };
  }
}

function ProvisionForm({ role, onCreated }) {
  const isStudent = role === "student";
  const empty = { email: "", first_name: "", middle_name: "", last_name: "", school_id: "", password: generateTempPassword() };
  const [form, setForm] = useState(empty);
  const [errors, setErrors] = useState({});
  const [result, setResult] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const set = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    setErrors((prev) => ({ ...prev, [field]: "" }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const next = {};
    if (!SCHOOL_EMAIL.test(form.email.trim())) next.email = "Use an @pampangastateu.edu.ph email address.";
    if (!form.first_name.trim()) next.first_name = "First name is required.";
    if (!form.last_name.trim()) next.last_name = "Last name is required.";
    const fullName = [form.first_name, form.middle_name, form.last_name].map((part) => part.trim()).filter(Boolean).join(" ");
    if (fullName.length > 150) next.last_name = "The full name must be at most 150 characters.";
    if (isStudent && !SCHOOL_ID.test(form.school_id.trim())) next.school_id = "Use a 10-digit ID or the format 2026-00001.";
    if (isStudent && form.password.length < 8) next.password = "Use at least 8 characters.";
    setErrors(next);
    if (Object.keys(next).length) return;

    setIsSaving(true);
    setResult(null);
    try {
      const payload = {
        email: form.email.trim().toLowerCase(),
        first_name: form.first_name.trim(),
        middle_name: form.middle_name.trim() || null,
        last_name: form.last_name.trim(),
        ...(isStudent ? { school_id: form.school_id.trim(), password: form.password } : {}),
      };
      if (!isStudent) {
        const { fallbackPassword } = await createFaculty(payload);
        setResult({
          tone: "success",
          text: fallbackPassword
            ? // A server from before 2026-10-22 still requires a password and emails it.
              `Account created for ${payload.email}. This server still emails a temporary password; if the email doesn't arrive, it is ${fallbackPassword}.`
            : `Account created for ${payload.email}. The instructor is emailed a link to set their own password. If the email doesn't arrive, they can use "Forgot password?" on the sign-in page with this address.`,
        });
        setForm({ ...empty, password: generateTempPassword() });
        onCreated?.();
        return;
      }
      const created = await api.post("/admin/students", payload);
      const pending = created?.pending_enrollments;
      const joined = pending?.enrolled_class_ids?.length ?? 0;
      const waiting = pending?.skipped?.length ?? 0;
      const enrollmentNote = [
        joined > 0 && `Added to ${joined} class${joined === 1 ? "" : "es"} that had queued this email.`,
        waiting > 0 && `${waiting} queued class${waiting === 1 ? " is" : "es are"} inactive or could not be joined and stay${waiting === 1 ? "s" : ""} pending.`,
      ].filter(Boolean).join(" ");
      setResult({
        tone: waiting > 0 ? "warning" : "success",
        // Delivery happens after the response and isn't confirmed, so the
        // password stays visible here in case the email doesn't arrive.
        text: `Account created for ${payload.email}. Their sign-in details, including the temporary password, are being emailed to them. If the email doesn't arrive, the temporary password is ${payload.password}.${enrollmentNote ? ` ${enrollmentNote}` : ""}`,
      });
      setForm({ ...empty, password: generateTempPassword() });
      onCreated?.();
    } catch (err) {
      setResult({ tone: "error", text: getErrorMessage(err, "The account could not be created.") });
    } finally {
      setIsSaving(false);
    }
  };

  const prefix = `provision-${role}`;
  const passwordField = (
    <TemporaryPasswordField
      prefix={prefix}
      value={form.password}
      error={errors.password}
      disabled={isSaving}
      onChange={set("password")}
      onGenerate={() => setForm((p) => ({ ...p, password: generateTempPassword() }))}
    />
  );
  return (
    <Panel
      as="form"
      onSubmit={handleSubmit}
      noValidate
      title={isStudent ? "Create student account" : "Create faculty account"}
      description={isStudent ? "For one student. The sign-in details are emailed automatically." : "The instructor is emailed a link to set their own password."}
      icon="userPlus"
      footer={
        <div className="@container">
          <div className="flex justify-end">
            <button type="submit" disabled={isSaving} className="btn-primary w-full py-2.5 text-[15px] @md:w-auto @md:min-w-52">
              <Icon name="userPlus" className="h-[18px] w-[18px]" />
              {isSaving ? "Creating account…" : "Create account"}
            </button>
          </div>
        </div>
      }
    >
      {/* Laid out by the card's own width: one column in a narrow side
          column, a field grid when the card spans the page. */}
      <div className="@container space-y-5">
        {result && (
          <InlineAlert tone={result.tone} onDismiss={() => setResult(null)}>
            {result.text}
          </InlineAlert>
        )}
        <div className="grid grid-cols-1 gap-5 @xl:grid-cols-2">
          <TextField id={`${prefix}-email`} label="University email" type="email" autoComplete="off" placeholder="name@pampangastateu.edu.ph" value={form.email} onChange={set("email")} error={errors.email} disabled={isSaving} />
          {isStudent ? (
            <TextField id={`${prefix}-school-id`} label="School ID" placeholder="2026000001 or 2026-00001" value={form.school_id} onChange={set("school_id")} error={errors.school_id} disabled={isSaving} />
          ) : (
            <div className="flex items-start gap-3 rounded-lg border border-border-subtle bg-bg-alt/50 px-4 py-3">
              <Icon name="key" className="mt-0.5 h-4 w-4 shrink-0 text-text-brand" />
              <p className="text-sm text-text-muted">
                <span className="font-semibold text-text-main">No password to share.</span> The welcome email links to "Forgot password?", where the
                instructor gets a one-time code and chooses their own password.
              </p>
            </div>
          )}
        </div>
        <div className="grid grid-cols-1 gap-5 rounded-lg border border-border-subtle bg-bg-alt/40 p-4 @xl:grid-cols-3">
          <TextField id={`${prefix}-first`} label="First name" value={form.first_name} onChange={set("first_name")} error={errors.first_name} disabled={isSaving} maxLength={70} />
          <TextField id={`${prefix}-middle`} label="Middle name (optional)" value={form.middle_name} onChange={set("middle_name")} error={errors.middle_name} disabled={isSaving} maxLength={70} />
          <TextField id={`${prefix}-last`} label="Last name" value={form.last_name} onChange={set("last_name")} error={errors.last_name} disabled={isSaving} maxLength={70} />
        </div>
        {isStudent && <div className="@xl:max-w-[calc(50%-0.625rem)]">{passwordField}</div>}
      </div>
    </Panel>
  );
}

function TemporaryPasswordField({ prefix, value, error, disabled, onChange, onGenerate }) {
  return (
    <div>
      <label htmlFor={`${prefix}-password`} className="field-label">
        Temporary password
      </label>
      <div className="flex gap-2">
        <input
          id={`${prefix}-password`}
          type="text"
          value={value}
          onChange={onChange}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${prefix}-password-error` : `${prefix}-password-hint`}
          className="input-field py-2.5 font-mono"
          disabled={disabled}
          autoComplete="off"
        />
        <button type="button" className="btn-secondary shrink-0" onClick={onGenerate} disabled={disabled}>
          Generate
        </button>
      </div>
      {error ? (
        <FieldError id={`${prefix}-password-error`}>{error}</FieldError>
      ) : (
        <p id={`${prefix}-password-hint`} className="mt-1.5 text-xs text-text-muted">
          Account credentials will be automatically emailed to the user.
        </p>
      )}
    </div>
  );
}

/** Self-service guest ("Continue as Guest Student"). Older servers don't send is_guest. */
function isGuestAccount(user) {
  if (typeof user.is_guest === "boolean") return user.is_guest;
  return user.role === "student" && /^guest_/i.test(user.email || "") && /^GST/.test(user.school_id || "");
}

const ROW_ACTION =
  "inline-flex items-center gap-1.5 whitespace-nowrap rounded-md border border-border-subtle bg-bg-panel px-2.5 py-1.5 text-xs font-semibold text-text-main transition-colors disabled:cursor-not-allowed disabled:opacity-60";

function UserTable({ users, caption, emptyMessage, onAction, busyUserId = null }) {
  if (users.length === 0) {
    return (
      <div className="p-5 sm:p-6">
        <EmptyState className="py-10" title="No accounts" message={emptyMessage} />
      </div>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[820px] text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead className="border-b border-border-subtle bg-bg-alt/70">
          <tr>
            <th scope="col" className={TH}>Name</th>
            <th scope="col" className={TH}>School ID</th>
            <th scope="col" className={TH}>Status</th>
            <th scope="col" className={`${TH} text-right`}>Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border-subtle">
          {users.map((user) => {
            const guest = isGuestAccount(user);
            const busy = busyUserId === user.user_id;
            return (
            <tr key={user.user_id} className="transition-colors hover:bg-psu-cream/70">
              <td className="px-5 py-3.5">
                <div className="flex items-center gap-3">
                  <Avatar name={user.name} />
                  <div className="min-w-0">
                    <p className="flex min-w-0 items-center gap-2">
                      <span className="truncate font-semibold text-text-main">{user.name}</span>
                      {guest && <Pill tone="warning">Guest</Pill>}
                    </p>
                    <p className="truncate text-xs text-text-muted">{user.email}</p>
                  </div>
                </div>
              </td>
              <td className="px-5 py-3.5">
                {user.school_id ? (
                  <span className="rounded-md border border-border-subtle bg-bg-alt px-2 py-0.5 font-mono text-xs text-text-main">{user.school_id}</span>
                ) : (
                  <span className="text-text-muted">—</span>
                )}
              </td>
              <td className="px-5 py-3.5">
                <Pill tone={user.is_active ? "success" : "neutral"}>{user.is_active ? "Active" : "Suspended"}</Pill>
              </td>
              <td className="px-5 py-3.5">
                <div className="flex justify-end gap-2">
                  {/* Guest accounts expire on their own; they can only be suspended or reactivated. */}
                  {!guest && (
                    <button
                      type="button"
                      className={`${ROW_ACTION} hover:border-psu-maroon/40 hover:bg-psu-cream hover:text-text-brand`}
                      aria-label={`Edit ${user.name}`}
                      onClick={() => onAction(user, "edit")}
                    >
                      <Icon name="pencil" className="h-3.5 w-3.5" />
                      Edit
                    </button>
                  )}
                  {!guest && user.role === "student" && (
                    <button
                      type="button"
                      className={`${ROW_ACTION} hover:border-psu-maroon/40 hover:bg-psu-cream hover:text-text-brand`}
                      aria-label={`Re-apply pending class enrollments for ${user.name}`}
                      title="Enroll this student in classes that queued their email"
                      onClick={() => onAction(user, "apply")}
                      disabled={busy || !user.is_active}
                    >
                      <Icon name="refresh" className={`h-3.5 w-3.5 ${busy ? "animate-spin" : ""}`} />
                      {busy ? "Applying…" : "Re-apply pending"}
                    </button>
                  )}
                  {!guest && (
                    <button
                      type="button"
                      className={`${ROW_ACTION} hover:border-border-strong hover:bg-bg-alt`}
                      aria-label={`Reset password for ${user.name}`}
                      onClick={() => onAction(user, "reset")}
                    >
                      <Icon name="key" className="h-3.5 w-3.5" />
                      Reset password
                    </button>
                  )}
                  <button
                    type="button"
                    className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-md border border-border-subtle bg-bg-panel px-2.5 py-1.5 text-xs font-semibold transition-colors ${
                      user.is_active
                        ? "text-text-main hover:border-psu-red/40 hover:bg-psu-red/[0.05] hover:text-text-rose"
                        : "text-text-main hover:border-emerald-600/40 hover:bg-emerald-600/[0.06] hover:text-text-emerald"
                    }`}
                    aria-label={`${user.is_active ? "Suspend" : "Activate"} ${user.name}`}
                    onClick={() => onAction(user, "status")}
                  >
                    <Icon name={user.is_active ? "ban" : "check"} className="h-3.5 w-3.5" />
                    {user.is_active ? "Suspend" : "Activate"}
                  </button>
                </div>
              </td>
            </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function AuditTable({ logs }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] text-sm">
        <caption className="sr-only">Audit events, newest first</caption>
        <thead className="border-b border-border-subtle bg-bg-alt/70">
          <tr>
            <th scope="col" className={TH}>When</th>
            <th scope="col" className={TH}>Actor</th>
            <th scope="col" className={TH}>Event</th>
            <th scope="col" className={TH}>Resource</th>
            <th scope="col" className={`${TH} text-right`}>Outcome</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border-subtle">
          {logs.map((log) => (
            <tr key={log.log_id} className="transition-colors hover:bg-psu-cream/70">
              <td className="whitespace-nowrap px-5 py-3.5">
                <time dateTime={log.occurred_at} className="block">
                  <span className="block text-sm text-text-main">{formatDate(log.occurred_at)}</span>
                  <span className="block text-xs text-text-muted">{formatTime(log.occurred_at)}</span>
                </time>
              </td>
              <td className="px-5 py-3.5">
                <div className="flex items-center gap-3">
                  <Avatar name={log.actor_name} size="sm" />
                  <div className="min-w-0">
                    <p className="truncate font-semibold text-text-main">{log.actor_name}</p>
                    <p className="truncate text-xs text-text-muted">
                      {log.actor_role ? humanize(log.actor_role) : "Automated"}
                      {log.actor_email ? ` · ${log.actor_email}` : ""}
                    </p>
                  </div>
                </div>
              </td>
              <td className="px-5 py-3.5 font-medium text-text-main">{humanize(log.action_type)}</td>
              <td className="px-5 py-3.5">
                <span className="rounded-md border border-border-subtle bg-bg-alt px-2 py-0.5 text-xs font-medium text-text-muted">{humanize(log.resource_type)}</span>
                {/* The affected account; older backends don't send target fields. */}
                {log.target_name ? (
                  <p className="mt-1 truncate text-xs text-text-main">
                    {log.target_name}
                    {log.target_role ? <span className="text-text-muted"> · {humanize(log.target_role)}</span> : null}
                  </p>
                ) : log.target_exists === false ? (
                  <p className="mt-1 text-xs text-text-muted">Deleted account #{log.target_user_id}</p>
                ) : null}
              </td>
              <td className="px-5 py-3.5 text-right">
                <OutcomePill status={log.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** True for the 422 an older server gives for a field it doesn't accept yet. */
function isUnsupportedField(error, field) {
  const detail = error instanceof ApiError && error.status === 422 ? error.data?.detail : null;
  return Array.isArray(detail) && detail.some((item) => item?.type === "extra_forbidden" && item?.loc?.at(-1) === field);
}

/** Dialog for correcting an account's name or university email, or a student's school ID. */
function EditAccountModal({ user, onClose, onSaved }) {
  const isStudent = user?.role === "student";
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [schoolId, setSchoolId] = useState(user?.school_id ?? "");
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const nameRef = useRef(null);

  const trimmedName = name.split(/\s+/).filter(Boolean).join(" ");
  const trimmedEmail = email.trim().toLowerCase();
  const trimmedSchoolId = schoolId.trim();
  const nameChanged = Boolean(user) && trimmedName !== user.name;
  const emailChanged = Boolean(user) && trimmedEmail !== (user.email || "").toLowerCase();
  const schoolIdChanged = isStudent && trimmedSchoolId !== (user.school_id || "");
  const anyChange = nameChanged || emailChanged || schoolIdChanged;
  const formId = "admin-edit-account-form";

  const submit = async (event) => {
    event.preventDefault();
    const next = {};
    if (!trimmedName) next.name = "Enter the full name.";
    else if (trimmedName.length > 150) next.name = "The full name must be at most 150 characters.";
    if (!SCHOOL_EMAIL.test(trimmedEmail)) next.email = "Use an @pampangastateu.edu.ph email address.";
    else if (trimmedEmail.startsWith("guest_")) next.email = "Addresses starting with guest_ are reserved for guest accounts.";
    if (schoolIdChanged && !SCHOOL_ID.test(trimmedSchoolId)) next.school_id = "Use a 10-digit ID or the format 2026-00001.";
    setErrors(next);
    if (Object.keys(next).length || !anyChange) return;

    setIsSaving(true);
    setFormError(null);
    try {
      const result = await api.patch(`/admin/users/${user.user_id}`, {
        ...(nameChanged ? { name: trimmedName } : {}),
        ...(emailChanged ? { email: trimmedEmail } : {}),
        ...(schoolIdChanged ? { school_id: trimmedSchoolId } : {}),
      });
      onSaved(result);
    } catch (err) {
      if (isMissingRoute(err)) {
        setFormError("Editing accounts needs the latest server update. Ask the system maintainer to deploy the backend, then try again.");
      } else if (isUnsupportedField(err, "school_id")) {
        setErrors({ school_id: "Changing school IDs needs the latest server update. Save the other changes without it, or ask the system maintainer to deploy the backend." });
      } else if (err instanceof ApiError && err.status === 409) {
        const message = getErrorMessage(err, "Another account already uses this email.");
        setErrors(/school ID/i.test(message) ? { school_id: message } : { email: message });
      } else {
        setFormError(getErrorMessage(err, "The changes could not be saved."));
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      isOpen={Boolean(user)}
      onClose={onClose}
      title={user ? `Edit ${user.role === "instructor" ? "faculty" : "student"} account` : "Edit account"}
      description={
        isStudent
          ? "Correct a misspelled name, email or school ID. Role and status are changed elsewhere."
          : "Correct a misspelled name or email. Role and status are changed elsewhere."
      }
      size="lg"
      dismissible={!isSaving}
      initialFocusRef={nameRef}
      footer={
        <div className="flex justify-end gap-2">
          <button type="button" className="btn-secondary" onClick={onClose} disabled={isSaving}>
            Cancel
          </button>
          <button type="submit" form={formId} className="btn-primary" disabled={isSaving || !anyChange}>
            {isSaving ? "Saving…" : "Save changes"}
          </button>
        </div>
      }
    >
      {user && (
        <form id={formId} onSubmit={submit} noValidate className="space-y-5">
          {formError && (
            <InlineAlert tone="error" onDismiss={() => setFormError(null)}>
              {formError}
            </InlineAlert>
          )}
          <div className="flex items-center gap-3 rounded-lg border border-border-subtle bg-bg-alt/50 px-4 py-3">
            <Avatar name={user.name} />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-text-main">{user.name}</p>
              <p className="truncate text-xs text-text-muted">{user.email}</p>
            </div>
            {user.school_id && (
              <span className="rounded-md border border-border-subtle bg-bg-panel px-2 py-0.5 font-mono text-xs text-text-main">{user.school_id}</span>
            )}
          </div>
          <div>
            <label htmlFor="admin-edit-name" className="field-label">
              Full name
            </label>
            <input
              ref={nameRef}
              id="admin-edit-name"
              className="input-field py-2.5"
              value={name}
              maxLength={150}
              onChange={(e) => {
                setName(e.target.value);
                setErrors((prev) => ({ ...prev, name: "" }));
              }}
              aria-invalid={Boolean(errors.name)}
              aria-describedby={errors.name ? "admin-edit-name-error" : "admin-edit-name-hint"}
              disabled={isSaving}
              autoComplete="off"
            />
            {errors.name ? (
              <FieldError id="admin-edit-name-error">{errors.name}</FieldError>
            ) : (
              <p id="admin-edit-name-hint" className="mt-1.5 text-xs text-text-muted">
                First, middle and last name, as they should appear on records.
              </p>
            )}
          </div>
          <div>
            <label htmlFor="admin-edit-email" className="field-label">
              University email
            </label>
            <input
              id="admin-edit-email"
              type="email"
              className="input-field py-2.5"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setErrors((prev) => ({ ...prev, email: "" }));
              }}
              aria-invalid={Boolean(errors.email)}
              aria-describedby={errors.email ? "admin-edit-email-error" : undefined}
              disabled={isSaving}
              autoComplete="off"
            />
            <FieldError id="admin-edit-email-error">{errors.email}</FieldError>
          </div>
          {isStudent && (
            <div>
              <label htmlFor="admin-edit-school-id" className="field-label">
                School ID
              </label>
              <input
                id="admin-edit-school-id"
                className="input-field py-2.5 font-mono"
                value={schoolId}
                placeholder="2026000001 or 2026-00001"
                maxLength={10}
                onChange={(e) => {
                  setSchoolId(e.target.value);
                  setErrors((prev) => ({ ...prev, school_id: "" }));
                }}
                aria-invalid={Boolean(errors.school_id)}
                aria-describedby={errors.school_id ? "admin-edit-school-id-error" : "admin-edit-school-id-hint"}
                disabled={isSaving}
                autoComplete="off"
              />
              {errors.school_id ? (
                <FieldError id="admin-edit-school-id-error">{errors.school_id}</FieldError>
              ) : (
                <p id="admin-edit-school-id-hint" className="mt-1.5 text-xs text-text-muted">
                  The student number from the MIS masterlist. Masterlist uploads are matched on it.
                </p>
              )}
            </div>
          )}
          {emailChanged && !errors.email && (
            <InlineAlert tone="warning">
              The account will sign in with the new address, and any password-reset code sent to the old address stops working.
              {user.role === "student" && " Classes that queued the new address are joined automatically."}
            </InlineAlert>
          )}
        </form>
      )}
    </Modal>
  );
}

const PENDING_VIEWS = [
  ["ready", "Ready to apply"],
  ["waiting", "Waiting"],
];

/** Why a queued enrollment can't be applied yet. */
function pendingStatus(item) {
  if (item.ready) return { tone: "success", text: "Ready" };
  if (!item.class_active) return { tone: "neutral", text: "Class archived" };
  if (item.user_id == null) return { tone: "warning", text: "No account yet" };
  if (item.student_active === false) return { tone: "neutral", text: "Account suspended" };
  return { tone: "neutral", text: "Not a student account" };
}

/**
 * Class enrollments that instructors queued for university emails (GET
 * /admin/pending-enrollments). "Ready" rows have an active student account
 * and an active class, so applying enrolls them now. Until the server has the
 * endpoint, the panel says so and the directory's row action still works.
 */
function PendingEnrollmentsPanel({ onApply, busyUserId, refreshKey }) {
  const [view, setView] = useState("ready");
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [unsupported, setUnsupported] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setData(await api.get(`/admin/pending-enrollments?state=${view}&limit=50`));
    } catch (err) {
      if (isMissingRoute(err)) setUnsupported(true);
      else setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [view]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  return (
    <Panel
      title="Queued class enrollments"
      description="Addresses instructors added to a class before the student had an account. Only MIS sees them."
      icon="classroom"
      flush
      actions={
        !unsupported && (
          <>
            {data && !error && (
              <span className="badge badge-neutral tabular-nums" aria-live="polite">
                {plural(data.ready ?? 0, "ready enrollment")}
              </span>
            )}
            <div className="flex gap-1 rounded-lg border border-border-subtle bg-bg-panel p-1" role="group" aria-label="Show queued enrollments">
              {PENDING_VIEWS.map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  aria-pressed={view === value}
                  onClick={() => setView(value)}
                  className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
                    view === value ? "bg-psu-maroon text-white" : "text-text-muted hover:bg-bg-alt hover:text-text-main"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </>
        )
      }
    >
      {unsupported ? (
        <div className="p-5 sm:p-6">
          <InlineAlert tone="info">
            This list appears after the next server update. Until then, use &ldquo;Re-apply pending&rdquo; on a student&apos;s row in the directory.
          </InlineAlert>
        </div>
      ) : error ? (
        <div className="p-5 sm:p-6">
          <AdminErrorState error={error} resource="queued enrollments" onRetry={load} />
        </div>
      ) : !data ? (
        <ListSkeleton rows={3} />
      ) : data.items.length === 0 ? (
        <div className="p-5 sm:p-6">
          <EmptyState
            className="py-8"
            title={view === "ready" ? "Nothing to apply" : "Nothing waiting"}
            message={
              view === "ready"
                ? "Every queued address with an active student account has been enrolled."
                : "No queued address is waiting for an account or a reactivated class."
            }
          />
        </div>
      ) : (
        <div aria-busy={isLoading} className={`transition-opacity ${isLoading ? "opacity-60" : ""}`}>
          <ul className="divide-y divide-border-subtle">
            {data.items.map((item) => {
              const status = pendingStatus(item);
              const busy = busyUserId === item.user_id;
              return (
                <li key={item.pending_id} className="flex flex-col gap-3 px-5 py-3.5 sm:flex-row sm:items-center sm:px-6">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-text-main">{item.student_name || item.email}</p>
                    <p className="truncate text-xs text-text-muted">
                      {item.student_name ? `${item.email} · ` : ""}
                      {[item.class_name, item.subject_code, item.section].filter(Boolean).join(" · ")}
                      {" · queued "}
                      {formatDate(item.queued_at)}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Pill tone={status.tone}>{status.text}</Pill>
                    {item.ready && (
                      <button
                        type="button"
                        className="btn-secondary btn-sm"
                        disabled={busyUserId !== null}
                        onClick={() => onApply({ user_id: item.user_id, name: item.student_name || item.email, is_active: true })}
                        aria-label={`Apply queued enrollments for ${item.student_name || item.email}`}
                      >
                        <Icon name="refresh" className={`h-3.5 w-3.5 ${busy ? "animate-spin" : ""}`} />
                        {busy ? "Applying…" : "Apply"}
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
          {data.total > data.items.length && (
            <p className="border-t border-border-subtle px-5 py-3 text-xs text-text-muted sm:px-6">
              Showing the newest {data.items.length} of {data.total}.
            </p>
          )}
        </div>
      )}
    </Panel>
  );
}

/**
 * Filtered, paged audit records from GET /admin/audit-logs/search. Until the
 * server has that endpoint, `unsupported` is true and the page falls back to
 * the plain newest-first list.
 */
function useAuditSearch(enabled) {
  const [filters, setFilters] = useState(EMPTY_AUDIT_FILTERS);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(AUDIT_PAGE_SIZES[0]);
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [unsupported, setUnsupported] = useState(false);
  const requestId = useRef(0);

  // Typing in the search box waits for a pause before asking the server.
  useEffect(() => {
    const timer = window.setTimeout(() => setSearch(filters.q.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [filters.q]);

  const dateError = filters.from && filters.to && filters.from > filters.to ? "The start date must be on or before the end date." : "";
  const { action_type: actionType, outcome, actor_role: actorRole, from, to } = filters;

  const load = useCallback(async () => {
    if (!enabled || unsupported || dateError) return;
    const id = ++requestId.current;
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (search) params.set("q", search);
    if (actionType) params.set("action_type", actionType);
    if (outcome) params.set("outcome", outcome);
    if (actorRole) params.set("actor_role", actorRole);
    if (from) params.set("occurred_from", localDayStart(from));
    if (to) params.set("occurred_to", localDayStart(to, 1));
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.get(`/admin/audit-logs/search?${params}`);
      if (id === requestId.current) setData(result);
    } catch (err) {
      if (id !== requestId.current) return;
      if (isMissingRoute(err)) setUnsupported(true);
      else setError(err);
    } finally {
      if (id === requestId.current) setIsLoading(false);
    }
  }, [enabled, unsupported, dateError, page, pageSize, search, actionType, outcome, actorRole, from, to]);

  useEffect(() => {
    load();
  }, [load]);

  const setFilter = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1);
  };
  const clearFilters = () => {
    setFilters(EMPTY_AUDIT_FILTERS);
    setSearch("");
    setPage(1);
  };
  const changePageSize = (size) => {
    setPageSize(size);
    setPage(1);
  };
  const hasFilters = Object.values(filters).some(Boolean);

  return { filters, setFilter, clearFilters, hasFilters, dateError, page, setPage, pageSize, changePageSize, data, isLoading, error, unsupported, reload: load };
}

function FilterField({ id, label, className = "", children }) {
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1 block text-xs font-semibold text-text-muted">
        {label}
      </label>
      {children}
    </div>
  );
}

function AuditFilters({ audit, actionTypes }) {
  const { filters, setFilter, clearFilters, hasFilters, dateError } = audit;
  return (
    <div className="border-b border-border-subtle bg-bg-alt/40 px-5 py-4 sm:px-6">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-12">
        <FilterField id="audit-filter-q" label="Actor" className="sm:col-span-2 lg:col-span-4">
          <div className="relative">
            <Icon name="search" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
            <input
              id="audit-filter-q"
              type="search"
              value={filters.q}
              onChange={(e) => setFilter("q", e.target.value)}
              placeholder="Name or email…"
              maxLength={100}
              className="input-field pl-9"
            />
          </div>
        </FilterField>
        <FilterField id="audit-filter-event" label="Event" className="lg:col-span-3">
          <select id="audit-filter-event" value={filters.action_type} onChange={(e) => setFilter("action_type", e.target.value)} className="input-field">
            <option value="">All events</option>
            {actionTypes.map((type) => (
              <option key={type} value={type}>
                {humanize(type)}
              </option>
            ))}
          </select>
        </FilterField>
        <FilterField id="audit-filter-outcome" label="Outcome" className="lg:col-span-2">
          <select id="audit-filter-outcome" value={filters.outcome} onChange={(e) => setFilter("outcome", e.target.value)} className="input-field">
            <option value="">All outcomes</option>
            {AUDIT_OUTCOMES.map((value) => (
              <option key={value} value={value}>
                {humanize(value)}
              </option>
            ))}
          </select>
        </FilterField>
        <FilterField id="audit-filter-role" label="Role" className="lg:col-span-3">
          <select id="audit-filter-role" value={filters.actor_role} onChange={(e) => setFilter("actor_role", e.target.value)} className="input-field">
            <option value="">All roles</option>
            {AUDIT_ROLES.map((value) => (
              <option key={value} value={value}>
                {humanize(value)}
              </option>
            ))}
          </select>
        </FilterField>
        <FilterField id="audit-filter-from" label="From" className="lg:col-span-3">
          <input
            id="audit-filter-from"
            type="date"
            value={filters.from}
            onChange={(e) => setFilter("from", e.target.value)}
            aria-invalid={Boolean(dateError)}
            aria-describedby={dateError ? "audit-filter-date-error" : undefined}
            className="input-field"
          />
        </FilterField>
        <FilterField id="audit-filter-to" label="To" className="lg:col-span-3">
          <input
            id="audit-filter-to"
            type="date"
            value={filters.to}
            onChange={(e) => setFilter("to", e.target.value)}
            aria-invalid={Boolean(dateError)}
            aria-describedby={dateError ? "audit-filter-date-error" : undefined}
            className="input-field"
          />
        </FilterField>
        <div className="flex items-end sm:col-span-2 lg:col-span-6 lg:justify-end">
          <button type="button" className="btn-ghost" onClick={clearFilters} disabled={!hasFilters}>
            <Icon name="x" className="h-4 w-4" />
            Clear filters
          </button>
        </div>
      </div>
      <FieldError id="audit-filter-date-error">{dateError}</FieldError>
    </div>
  );
}

function Pagination({ page, pageSize, total, onPage, onPageSize, isLoading }) {
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const first = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const last = Math.min(page * pageSize, total);
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm text-text-muted" aria-live="polite">
        Showing <span className="font-semibold text-text-main tabular-nums">{first}–{last}</span> of{" "}
        <span className="font-semibold text-text-main tabular-nums">{total}</span> event{total === 1 ? "" : "s"}
      </p>
      <div className="flex flex-wrap items-center gap-3">
        <label htmlFor="audit-page-size" className="text-sm text-text-muted">
          Rows per page
        </label>
        <select id="audit-page-size" value={pageSize} onChange={(e) => onPageSize(Number(e.target.value))} className="input-field w-auto py-1.5">
          {AUDIT_PAGE_SIZES.map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </select>
        <div className="flex items-center gap-1">
          <button type="button" className="btn-secondary btn-sm" onClick={() => onPage(page - 1)} disabled={isLoading || page <= 1} aria-label="Previous page">
            <Icon name="chevronLeft" className="h-4 w-4" />
          </button>
          <span className="px-2 text-sm text-text-main tabular-nums">
            Page {Math.min(page, pageCount)} of {pageCount}
          </span>
          <button type="button" className="btn-secondary btn-sm" onClick={() => onPage(page + 1)} disabled={isLoading || page >= pageCount} aria-label="Next page">
            <Icon name="chevronRight" className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function SettingRow({ labelId, title, description, children }) {
  return (
    <div className="flex flex-col gap-3 px-5 py-5 sm:flex-row sm:items-center sm:justify-between sm:gap-8 sm:px-6">
      <div className="min-w-0">
        <p id={labelId} className="text-sm font-semibold text-text-main">
          {title}
        </p>
        <p className="mt-0.5 text-sm text-text-muted">{description}</p>
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

export default function AdminDashboard() {
  const navigate = useNavigate();
  const { logout, user: currentUser } = useAuth();
  const [activeTab, setActiveTab] = useState("overview");
  const [pendingTab, setPendingTab] = useState(null);
  const [focusTarget, setFocusTarget] = useState(null);
  const [isSignOutOpen, setIsSignOutOpen] = useState(false);

  const [stats, setStats] = useState(null);
  const [statsError, setStatsError] = useState(null);
  const [showGuests, setShowGuests] = useState(false);
  const users = useAdminList(showGuests ? "/admin/users?include_guests=true" : "/admin/users");
  const logs = useAdminList("/admin/audit-logs");

  const [settings, setSettings] = useState(null);
  const [savedSettings, setSavedSettings] = useState(null);
  const [settingsError, setSettingsError] = useState(null);
  const [settingsMessage, setSettingsMessage] = useState(null);
  const [isSavingSettings, setIsSavingSettings] = useState(false);

  const [search, setSearch] = useState("");
  const [facultySearch, setFacultySearch] = useState("");
  const [editingUser, setEditingUser] = useState(null);
  const [exportingRole, setExportingRole] = useState(null);
  const [auditVisited, setAuditVisited] = useState(false);
  const audit = useAuditSearch(auditVisited);
  const [userAction, setUserAction] = useState(null);
  const [isActing, setIsActing] = useState(false);
  const [applyingUserId, setApplyingUserId] = useState(null);
  const [pendingRefresh, setPendingRefresh] = useState(0);
  const [actionMessage, setActionMessage] = useState(null);
  const [bulkMessage, setBulkMessage] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileRef = useRef(null);

  const loadStats = useCallback(async () => {
    setStatsError(null);
    try {
      setStats(await api.get("/admin/stats"));
    } catch (err) {
      setStatsError(err);
    }
  }, []);

  const loadSettings = useCallback(async () => {
    setSettingsError(null);
    try {
      const data = await api.get("/admin/settings");
      setSettings(data);
      setSavedSettings(data);
    } catch (err) {
      setSettingsError(err);
    }
  }, []);

  const { load: loadUsers } = users;
  const { load: loadLogs } = logs;
  useEffect(() => {
    loadStats();
    loadLogs();
    loadSettings();
  }, [loadStats, loadLogs, loadSettings]);

  // Separate, so the "Show guests" switch reloads only the account list.
  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // Without the search endpoint the audit tab shows the plain list; fetch it
  // fresh at that moment rather than showing what was loaded at sign-in.
  const auditUnsupported = audit.unsupported;
  useEffect(() => {
    if (auditUnsupported) loadLogs();
  }, [auditUnsupported, loadLogs]);

  // Quick actions open a tab and then move focus to the field they name.
  useEffect(() => {
    if (!focusTarget) return undefined;
    const frame = window.requestAnimationFrame(() => {
      const element = document.getElementById(focusTarget);
      if (element) {
        element.scrollIntoView({ block: "center", behavior: "smooth" });
        element.focus({ preventScroll: true });
        setFocusTarget(null);
      }
    });
    return () => window.cancelAnimationFrame(frame);
  }, [focusTarget, activeTab]);

  const settingsDirty =
    settings && savedSettings && ["maintenance_mode", "default_ast_strictness"].some((k) => settings[k] !== savedSettings[k]);

  const showTab = (tab) => {
    // A result message belongs to the section where the action happened.
    if (tab !== activeTab) setActionMessage(null);
    if (tab === "audit") setAuditVisited(true);
    setActiveTab(tab);
  };

  const changeTab = (tab) => {
    if (activeTab === "settings" && settingsDirty && tab !== "settings") {
      setPendingTab(tab);
      return;
    }
    showTab(tab);
  };

  const openQuickAction = (action) => {
    setFocusTarget(action.focus || null);
    changeTab(action.tab);
  };

  const faculty = users.items.filter((u) => u.role === "instructor");
  const students = users.items.filter((u) => u.role === "student");
  const query = search.trim().toLowerCase();
  const filteredStudents = query ? students.filter((s) => matchesAccount(s, query)) : students;
  const facultyQuery = facultySearch.trim().toLowerCase();
  const filteredFaculty = facultyQuery ? faculty.filter((f) => matchesAccount(f, facultyQuery)) : faculty;

  const handleUserAction = (user, type) => {
    if (type === "edit") setEditingUser(user);
    else if (type === "apply") applyPendingEnrollments(user);
    else setUserAction({ user, type, password: generateTempPassword() });
  };

  /** Enroll a student in the classes that queued their email (safe to repeat). */
  const applyPendingEnrollments = async (user) => {
    if (applyingUserId !== null) return;
    setApplyingUserId(user.user_id);
    try {
      const result = await api.post(`/admin/students/${user.user_id}/pending-enrollments/apply`);
      const joined = result?.enrolled_class_ids?.length ?? 0;
      const already = result?.already_enrolled_class_ids?.length ?? 0;
      const waiting = result?.skipped?.length ?? 0;
      const parts = [
        joined > 0 && `added to ${plural(joined, "class")}`,
        already > 0 && `${plural(already, "queued class")} already had them`,
        waiting > 0 && `${plural(waiting, "class")} still waiting (archived or busy; try again later)`,
      ].filter(Boolean);
      setActionMessage({
        tone: waiting > 0 ? "warning" : "success",
        text: parts.length ? `${user.name}: ${parts.join(", ")}.` : `${user.name} has no queued class enrollments.`,
      });
      setPendingRefresh((n) => n + 1);
    } catch (err) {
      setActionMessage({
        tone: "error",
        text:
          err instanceof ApiError && err.status === 409
            ? `${user.name} can't be enrolled: ${getErrorMessage(err, "only active student accounts can join classes.")}`
            : getErrorMessage(err, "The queued enrollments could not be applied."),
      });
    } finally {
      setApplyingUserId(null);
    }
  };

  const handleAccountSaved = (result) => {
    const previous = editingUser;
    users.setItems((prev) =>
      prev.map((u) => (u.user_id === result.user_id ? { ...u, name: result.name, email: result.email, school_id: result.school_id ?? u.school_id } : u)),
    );
    const changed = result.changed_fields ?? [];
    const joined = result.pending_enrollments?.enrolled_class_ids?.length ?? 0;
    const parts = [
      changed.includes("name") && `the name is now ${result.name}`,
      changed.includes("email") && `they now sign in as ${result.email}`,
      changed.includes("school_id") && `the school ID is now ${result.school_id}`,
    ].filter(Boolean);
    setActionMessage({
      tone: "success",
      text:
        (parts.length ? `Saved ${previous?.name ?? "the account"}: ${parts.join(", and ")}.` : "No changes were needed.") +
        (joined > 0 ? ` Added to ${joined} class${joined === 1 ? "" : "es"} that had queued the new address.` : ""),
    });
    setEditingUser(null);
  };

  /** Every account of a role, not just the pages loaded on screen. */
  const exportAccounts = async (role) => {
    setExportingRole(role);
    try {
      const all = [];
      for (let skip = 0; ; skip += 500) {
        const batch = await api.get(`/admin/users?skip=${skip}&limit=500`);
        const list = Array.isArray(batch) ? batch : [];
        all.push(...list);
        if (list.length < 500) break;
      }
      const accounts = all.filter((u) => u.role === role);
      downloadCsv(role === "instructor" ? "psu_faculty.csv" : "psu_students.csv", [
        ["User ID", "Name", "Email", "School ID", "Active"],
        ...accounts.map((u) => [u.user_id, u.name, u.email, u.school_id, u.is_active ? "Yes" : "No"]),
      ]);
    } catch (err) {
      setActionMessage({ tone: "error", text: getErrorMessage(err, "The list could not be exported.") });
    } finally {
      setExportingRole(null);
    }
  };

  const runUserAction = async () => {
    if (!userAction || isActing) return;
    const { user, type, password } = userAction;
    setIsActing(true);
    try {
      if (type === "status") {
        const res = await api.patch(`/admin/users/${user.user_id}/status`);
        users.setItems((prev) => prev.map((u) => (u.user_id === user.user_id ? { ...u, is_active: res?.is_active ?? !u.is_active } : u)));
        setActionMessage({ tone: "success", text: `${user.name} is now ${(res?.is_active ?? !user.is_active) ? "active" : "suspended"}.` });
      } else {
        await api.patch(`/admin/users/${user.user_id}/password`, { new_password: password });
        setActionMessage({ tone: "success", text: `Password for ${user.email} was reset to ${password} — share it securely.` });
      }
    } catch (err) {
      setActionMessage({ tone: "error", text: getErrorMessage(err, "The action could not be completed.") });
    } finally {
      setIsActing(false);
      setUserAction(null);
    }
  };

  const handleBulkUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setIsUploading(true);
    setBulkMessage(null);
    try {
      const res = await api.post("/admin/students/bulk-register/file", formData);
      const fromPending = res?.enrolled_from_pending ?? 0;
      const pendingLeft = res?.pending_left ?? 0;
      const created = res?.created ?? 0;
      const failedRows = (res?.rows ?? []).filter((row) => row.status === "failed");
      setBulkMessage({
        tone: failedRows.length > 0 || pendingLeft > 0 ? "warning" : "success",
        text:
          `${created} account${created === 1 ? "" : "s"} created, ${res?.skipped ?? 0} already existed, ${failedRows.length} row${failedRows.length === 1 ? "" : "s"} failed.` +
          (created > 0 ? " Each new student is emailed their account details and a link to set their own password." : "") +
          (fromPending > 0 ? ` ${fromPending} queued class enrollment${fromPending === 1 ? " was" : "s were"} completed.` : "") +
          (pendingLeft > 0 ? ` ${pendingLeft} stay${pendingLeft === 1 ? "s" : ""} pending because the class is inactive or could not be joined.` : ""),
        rows: failedRows,
      });
      users.load();
      loadStats();
    } catch (err) {
      setBulkMessage({ tone: "error", text: getErrorMessage(err, "The file could not be processed.") });
    } finally {
      setIsUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const saveSettings = async (event) => {
    event.preventDefault();
    setIsSavingSettings(true);
    setSettingsMessage(null);
    try {
      await api.patch("/admin/settings", {
        maintenance_mode: Boolean(settings.maintenance_mode),
        // Accounts are provisioned by MIS only (panel requirement), so the
        // retired public self-registration stays off. The API still requires
        // the field.
        registration_enabled: false,
        default_ast_strictness: settings.default_ast_strictness || "moderate",
      });
      setSavedSettings(settings);
      setSettingsMessage({ tone: "success", text: "Settings saved." });
    } catch (err) {
      setSettingsMessage({ tone: "error", text: getErrorMessage(err, "Settings could not be saved.") });
    } finally {
      setIsSavingSettings(false);
    }
  };

  const tabButton = (tab, compact = false) => (
    <button
      key={tab.id}
      type="button"
      onClick={() => changeTab(tab.id)}
      aria-current={activeTab === tab.id ? "page" : undefined}
      className={`flex items-center gap-3 rounded-lg text-sm transition-colors ${compact ? "shrink-0 px-3 py-2" : "w-full px-3 py-2.5"} ${
        activeTab === tab.id
          ? "bg-psu-cream font-semibold text-psu-maroon shadow-[inset_3px_0_0_var(--color-psu-gold)]"
          : "font-medium text-text-muted hover:bg-bg-alt hover:text-text-main"
      }`}
    >
      <Icon name={tab.id} className="h-[18px] w-[18px]" />
      {tab.label}
    </button>
  );

  const maintenanceOn = Boolean(savedSettings?.maintenance_mode);
  const recentLogs = logs.items.slice(0, RECENT_ACTIVITY_COUNT);
  const userListBody = (list, caption, emptyMessage) =>
    users.error ? (
      <div className="p-5 sm:p-6">
        <AdminErrorState error={users.error} resource={caption.toLowerCase()} onRetry={users.load} />
      </div>
    ) : users.isLoading ? (
      <LoadingState label="Loading accounts…" className="py-14" />
    ) : (
      <UserTable users={list} caption={caption} emptyMessage={emptyMessage} onAction={handleUserAction} busyUserId={applyingUserId} />
    );
  const exportButton = (role, count) => (
    <button type="button" className="btn-secondary" onClick={() => exportAccounts(role)} disabled={count === 0 || exportingRole !== null}>
      <Icon name="download" className="h-4 w-4" />
      {exportingRole === role ? "Exporting…" : "Export CSV"}
    </button>
  );
  const searchBox = (id, label, value, onChange) => (
    <div className="relative w-full sm:w-64">
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <Icon name="search" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
      <input id={id} type="search" value={value} onChange={(e) => onChange(e.target.value)} placeholder="Search name, email or ID…" className="input-field pl-9" />
    </div>
  );
  const loadMoreUsers = users.hasMore && !users.error && (
    <button type="button" className="btn-secondary w-full" onClick={users.loadMore} disabled={users.isLoadingMore}>
      {users.isLoadingMore ? "Loading…" : "Load more accounts"}
    </button>
  );

  return (
    <div className="flex min-h-screen flex-col bg-bg-base text-text-main">
      <header className="sticky top-0 z-40 flex h-16 shrink-0 items-center justify-between bg-bg-panel px-4 shadow-[0_1px_0_var(--border-subtle)] sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <img src="/school_logo.png" alt="Pampanga State University logo" className="h-10 w-10 object-contain" />
          <div className="min-w-0 leading-tight">
            <p className="truncate text-sm font-bold tracking-tight sm:text-base">Pampanga State University</p>
            <p className="text-[11px] font-semibold uppercase tracking-widest text-text-brand">MIS Administration</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {currentUser?.name && (
            <div className="hidden items-center gap-3 border-r border-border-subtle pr-4 md:flex">
              <div className="text-right leading-tight">
                <p className="text-sm font-semibold text-text-main">{currentUser.name}</p>
                <p className="text-xs text-text-muted">{currentUser.email}</p>
              </div>
              <Avatar name={currentUser.name} />
            </div>
          )}
          <button type="button" onClick={() => setIsSignOutOpen(true)} className="btn-secondary btn-sm">
            <Icon name="signOut" className="h-3.5 w-3.5" />
            Sign out
          </button>
        </div>
        <span className="pointer-events-none absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-psu-maroon via-psu-gold to-psu-maroon" aria-hidden="true" />
      </header>

      <nav aria-label="Administration sections" className="flex gap-1 overflow-x-auto border-b border-border-subtle bg-bg-panel px-3 py-2 lg:hidden">
        {TABS.map((tab) => tabButton(tab, true))}
      </nav>

      <div className="flex min-h-0 flex-1">
        <aside className="sticky top-16 hidden h-[calc(100vh-4rem)] w-64 shrink-0 flex-col border-r border-border-subtle bg-bg-panel lg:flex">
          <p className="px-7 pb-2 pt-6 text-[11px] font-semibold uppercase tracking-widest text-text-muted">Administration</p>
          <nav aria-label="Administration sections" className="space-y-1 px-4">
            {TABS.map((tab) => tabButton(tab))}
          </nav>
          <div className="mt-auto border-t border-border-subtle px-7 py-4">
            <p className="text-xs font-semibold text-text-main">PSU Python IDE</p>
            <p className="text-xs text-text-muted">MIS console</p>
          </div>
        </aside>

        <main className="min-w-0 flex-1 px-4 py-6 sm:px-8 lg:py-8">
          <div key={activeTab} className="animate-page-fade mx-auto w-full max-w-6xl">
            {actionMessage && (
              <InlineAlert tone={actionMessage.tone} onDismiss={() => setActionMessage(null)} className="mb-5">
                {actionMessage.text}
              </InlineAlert>
            )}

            {activeTab === "overview" && (
              <div className="space-y-6">
                <section aria-labelledby="admin-welcome-title" className={`relative overflow-hidden rounded-2xl bg-gradient-to-br from-psu-maroon via-psu-maroon to-psu-maroon-dark px-6 py-7 text-white sm:px-8 ${ELEVATED}`}>
                  <span className="pointer-events-none absolute -right-20 -top-24 h-64 w-64 rounded-full bg-psu-gold/20 blur-3xl" aria-hidden="true" />
                  <span className="pointer-events-none absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-psu-gold via-psu-gold/70 to-transparent" aria-hidden="true" />
                  <div className="relative flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-widest text-psu-gold">System overview</p>
                      <h1 id="admin-welcome-title" className="mt-1.5 text-2xl font-bold tracking-tight sm:text-[26px]">
                        {greeting()}, {currentUser?.name || "Administrator"}
                      </h1>
                      <p className="mt-1.5 max-w-xl text-sm text-white/80">
                        Manage faculty and student accounts, review recorded activity and set platform-wide policies for the PSU Python IDE.
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2 text-xs font-semibold">
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1.5 ring-1 ring-white/20">
                        <Icon name="calendar" className="h-3.5 w-3.5" />
                        {formatDate(new Date(), { weekday: "long", month: "long", day: "numeric", year: "numeric" })}
                      </span>
                      {savedSettings && (
                        <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 ring-1 ${maintenanceOn ? "bg-psu-gold text-psu-maroon-dark ring-psu-gold" : "bg-white/10 ring-white/20"}`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${maintenanceOn ? "bg-psu-maroon-dark" : "bg-emerald-300"}`} aria-hidden="true" />
                          {maintenanceOn ? "Maintenance mode on" : "All services open"}
                        </span>
                      )}
                    </div>
                  </div>
                </section>

                {statsError ? (
                  <AdminErrorState error={statsError} resource="platform statistics" onRetry={loadStats} />
                ) : !stats ? (
                  <LoadingState label="Loading statistics…" className="py-10" />
                ) : (
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                    <StatCard icon="faculty" label="Instructors" value={stats.total_instructors ?? 0} hint="Faculty accounts, active and suspended." />
                    <StatCard icon="students" label="Students" value={stats.total_students ?? 0} hint="All student accounts, including guests." />
                    <StatCard icon="classroom" label="Classrooms" value={stats.total_classrooms ?? 0} hint="Every class, including archived ones." />
                    <StatCard
                      icon={maintenanceOn ? "wrench" : "shield"}
                      label="Student access"
                      value={savedSettings ? (maintenanceOn ? "Paused" : "Open") : "—"}
                      tone={maintenanceOn ? "warning" : "brand"}
                      hint={savedSettings ? (maintenanceOn ? "Maintenance mode blocks student sign-in." : "Students can sign in normally.") : "Settings unavailable."}
                    />
                  </div>
                )}

                <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
                  <Panel
                    title="Recent activity"
                    description="The latest recorded events across the platform."
                    icon="activity"
                    flush
                    footer={
                      <button type="button" onClick={() => changeTab("audit")} className="inline-flex items-center gap-1.5 text-sm font-semibold text-text-brand hover:underline">
                        View the full audit trail
                        <Icon name="arrowRight" className="h-4 w-4" />
                      </button>
                    }
                  >
                    {logs.error ? (
                      <div className="p-5 sm:p-6">
                        <AdminErrorState error={logs.error} resource="recent activity" onRetry={logs.load} />
                      </div>
                    ) : logs.isLoading ? (
                      <ListSkeleton />
                    ) : recentLogs.length === 0 ? (
                      <div className="p-5 sm:p-6">
                        <EmptyState className="py-10" title="No activity yet" message="Sign-ins and account changes will appear here." />
                      </div>
                    ) : (
                      <ul className="divide-y divide-border-subtle">
                        {recentLogs.map((log) => (
                          <li key={log.log_id} className="flex items-center gap-3 px-5 py-3.5 transition-colors hover:bg-psu-cream/60 sm:px-6">
                            <Avatar name={log.actor_name} size="sm" />
                            <div className="min-w-0 flex-1">
                              <p className="truncate text-sm text-text-main">
                                <span className="font-semibold">{log.actor_name}</span>
                                <span className="text-text-muted"> · </span>
                                {humanize(log.action_type)}
                              </p>
                              <p className="truncate text-xs text-text-muted">
                                {log.actor_role ? humanize(log.actor_role) : "Automated"} · {humanize(log.resource_type)} ·{" "}
                                <time dateTime={log.occurred_at} title={formatDateTime(log.occurred_at)}>
                                  {timeAgo(log.occurred_at)}
                                </time>
                              </p>
                            </div>
                            <OutcomePill status={log.status} />
                          </li>
                        ))}
                      </ul>
                    )}
                  </Panel>

                  <Panel title="Quick actions" description="Common MIS tasks." icon="bolt" flush>
                    <ul className="divide-y divide-border-subtle">
                      {QUICK_ACTIONS.map((action) => (
                        <li key={action.id}>
                          <button
                            type="button"
                            onClick={() => openQuickAction(action)}
                            className="group flex w-full items-center gap-3 px-5 py-3.5 text-left transition-colors hover:bg-psu-cream/70 sm:px-6"
                          >
                            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-psu-gold/40 bg-psu-gold/10 text-text-amber transition-colors group-hover:border-psu-maroon/30 group-hover:bg-psu-maroon group-hover:text-white">
                              <Icon name={action.icon} className="h-[18px] w-[18px]" />
                            </span>
                            <span className="min-w-0 flex-1">
                              <span className="block text-sm font-semibold text-text-main">{action.title}</span>
                              <span className="block text-xs text-text-muted">{action.text}</span>
                            </span>
                            <Icon name="chevronRight" className="h-4 w-4 shrink-0 text-text-muted transition-transform group-hover:translate-x-0.5 group-hover:text-text-brand" />
                          </button>
                        </li>
                      ))}
                    </ul>
                  </Panel>
                </div>
              </div>
            )}

            {activeTab === "faculty" && (
              <>
                <PageHeader
                  eyebrow="Accounts"
                  title="Faculty"
                  description="Create instructor accounts and manage their access."
                  actions={exportButton("instructor", faculty.length)}
                />
                {/* Form above a full-width directory, so the table never has to
                    scroll sideways on a desktop display. */}
                <div className="grid grid-cols-1 items-start gap-6">
                  <ProvisionForm role="instructor" onCreated={() => { users.load(); loadStats(); }} />
                  <div className="min-w-0 space-y-4">
                    <Panel
                      title="Faculty directory"
                      description="Instructors who can sign in to the IDE."
                      icon="faculty"
                      flush
                      actions={
                        <>
                          {!users.isLoading && !users.error && (
                            <CountBadge count={faculty.length} word="account" hasMore={users.hasMore} shown={facultyQuery ? filteredFaculty.length : undefined} />
                          )}
                          {searchBox("admin-faculty-search", "Search faculty", facultySearch, setFacultySearch)}
                        </>
                      }
                    >
                      {userListBody(filteredFaculty, "Faculty accounts", facultyQuery ? "No faculty match your search." : "No faculty accounts have been created yet.")}
                    </Panel>
                    {loadMoreUsers}
                  </div>
                </div>
              </>
            )}

            {activeTab === "students" && (
              <>
                <PageHeader
                  eyebrow="Accounts"
                  title="Students"
                  description="Create student accounts individually or from a masterlist file."
                  actions={exportButton("student", students.length)}
                />
                {/* Form and masterlist side by side, full-width directory below. */}
                <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
                  <div>
                    <ProvisionForm role="student" onCreated={() => { users.load(); loadStats(); }} />
                  </div>
                  <div>
                    <Panel title="Bulk register from masterlist" description="New students are emailed their account details automatically." icon="upload">
                      <div className="space-y-4">
                        <p className="text-sm text-text-muted">
                          Columns: <code className="rounded bg-bg-alt px-1 py-0.5 text-xs">email</code>, <code className="rounded bg-bg-alt px-1 py-0.5 text-xs">school_id</code> and{" "}
                          <code className="rounded bg-bg-alt px-1 py-0.5 text-xs">name</code> (or <code className="rounded bg-bg-alt px-1 py-0.5 text-xs">first_name</code> and{" "}
                          <code className="rounded bg-bg-alt px-1 py-0.5 text-xs">last_name</code>).
                        </p>
                        {bulkMessage && (
                          <InlineAlert tone={bulkMessage.tone} onDismiss={() => setBulkMessage(null)}>
                            {bulkMessage.text}
                            {bulkMessage.rows?.length > 0 && (
                              <ul className="mt-2 max-h-40 list-disc space-y-1 overflow-y-auto pl-4 text-xs">
                                {bulkMessage.rows.map((row) => (
                                  <li key={row.row}>
                                    Row {row.row}
                                    {row.email ? ` (${row.email})` : ""}: {row.reason}
                                  </li>
                                ))}
                              </ul>
                            )}
                          </InlineAlert>
                        )}
                        <label
                          htmlFor="admin-bulk-file"
                          className={`relative flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border-strong bg-bg-alt/40 px-4 py-6 text-center transition-colors hover:border-psu-maroon/40 hover:bg-psu-cream/60 focus-within:border-psu-maroon focus-within:ring-2 focus-within:ring-border-focus/20 ${isUploading ? "pointer-events-none opacity-70" : ""}`}
                        >
                          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-psu-maroon/[0.08] text-text-brand">
                            <Icon name="upload" className="h-5 w-5" />
                          </span>
                          <span className="text-sm font-semibold text-text-main">{isUploading ? "Uploading…" : "Choose a masterlist file"}</span>
                          <span className="text-xs text-text-muted">CSV or .xlsx</span>
                          <input ref={fileRef} id="admin-bulk-file" type="file" accept=".csv,.xlsx" className="sr-only" onChange={handleBulkUpload} disabled={isUploading} />
                        </label>
                      </div>
                    </Panel>
                  </div>
                  <div className="min-w-0 space-y-4 lg:col-span-2">
                    <Panel
                      title="Student directory"
                      description={showGuests ? "Including self-service guest accounts." : "Self-service guest accounts are hidden."}
                      icon="students"
                      flush
                      actions={
                        <>
                          {!users.isLoading && !users.error && (
                            <CountBadge count={students.length} word="account" hasMore={users.hasMore} shown={query ? filteredStudents.length : undefined} />
                          )}
                          <div className="flex items-center gap-2">
                            <span id="admin-show-guests-label" className="text-xs font-semibold text-text-muted">
                              Show guests
                            </span>
                            <button
                              type="button"
                              role="switch"
                              aria-checked={showGuests}
                              aria-labelledby="admin-show-guests-label"
                              onClick={() => setShowGuests((on) => !on)}
                              className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${showGuests ? "bg-psu-maroon" : "bg-border-strong"}`}
                            >
                              <span className={`inline-block h-5 w-5 rounded-full bg-white shadow transition-transform ${showGuests ? "translate-x-[22px]" : "translate-x-0.5"}`} aria-hidden="true" />
                            </button>
                          </div>
                          {searchBox("admin-student-search", "Search students", search, setSearch)}
                        </>
                      }
                    >
                      {userListBody(filteredStudents, "Student accounts", query ? "No students match your search." : "No student accounts yet.")}
                    </Panel>
                    {loadMoreUsers}
                    <PendingEnrollmentsPanel onApply={applyPendingEnrollments} busyUserId={applyingUserId} refreshKey={pendingRefresh} />
                  </div>
                </div>
              </>
            )}

            {activeTab === "audit" && (
              <>
                <PageHeader
                  eyebrow="Security"
                  title="Global audit trail"
                  description="Recorded account, classroom and academic events."
                  actions={
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => (audit.unsupported ? logs.load() : audit.reload())}
                      disabled={audit.unsupported ? logs.isLoading : audit.isLoading}
                    >
                      <Icon name="refresh" className="h-4 w-4" />
                      Refresh
                    </button>
                  }
                />
                {audit.unsupported ? (
                  // The server doesn't have the search endpoint yet: plain newest-first list.
                  <div className="space-y-4">
                    <InlineAlert tone="info">
                      Filters and page numbers become available after the next server update. Showing the newest events for now.
                    </InlineAlert>
                    <Panel
                      title="Event log"
                      description="Newest first."
                      icon="shield"
                      flush
                      actions={!logs.isLoading && !logs.error && logs.items.length > 0 && <CountBadge count={logs.items.length} word="event" hasMore={logs.hasMore} />}
                    >
                      {logs.error ? (
                        <div className="p-5 sm:p-6">
                          <AdminErrorState error={logs.error} resource="the audit trail" onRetry={logs.load} />
                        </div>
                      ) : logs.isLoading ? (
                        <LoadingState label="Loading audit trail…" className="py-14" />
                      ) : logs.items.length === 0 ? (
                        <div className="p-5 sm:p-6">
                          <EmptyState title="No audit events" message="Recorded actions will appear here." />
                        </div>
                      ) : (
                        <AuditTable logs={logs.items} />
                      )}
                    </Panel>
                    {logs.hasMore && !logs.error && (
                      <button type="button" className="btn-secondary w-full" onClick={logs.loadMore} disabled={logs.isLoadingMore}>
                        {logs.isLoadingMore ? "Loading…" : "Load older events"}
                      </button>
                    )}
                  </div>
                ) : (
                  <Panel
                    title="Event log"
                    description="Newest first. Filter by actor, event, outcome, role or date."
                    icon="shield"
                    flush
                    actions={audit.data && !audit.error && <CountBadge count={audit.data.total} word={audit.hasFilters ? "matching event" : "event"} />}
                    footer={
                      audit.data && !audit.error && audit.data.total > 0 && (
                        <Pagination
                          page={audit.page}
                          pageSize={audit.pageSize}
                          total={audit.data.total}
                          onPage={audit.setPage}
                          onPageSize={audit.changePageSize}
                          isLoading={audit.isLoading}
                        />
                      )
                    }
                  >
                    <AuditFilters audit={audit} actionTypes={audit.data?.action_types ?? []} />
                    {audit.error ? (
                      <div className="p-5 sm:p-6">
                        <AdminErrorState error={audit.error} resource="the audit trail" onRetry={audit.reload} />
                      </div>
                    ) : !audit.data ? (
                      <LoadingState label="Loading audit trail…" className="py-14" />
                    ) : audit.data.items.length === 0 ? (
                      <div className="p-5 sm:p-6">
                        <EmptyState
                          title={audit.hasFilters ? "No matching events" : "No audit events"}
                          message={audit.hasFilters ? "Try a wider date range or fewer filters." : "Recorded actions will appear here."}
                          action={
                            audit.hasFilters && (
                              <button type="button" className="btn-secondary" onClick={audit.clearFilters}>
                                Clear filters
                              </button>
                            )
                          }
                        />
                      </div>
                    ) : (
                      <div aria-busy={audit.isLoading} className={`transition-opacity ${audit.isLoading ? "opacity-60" : ""}`}>
                        <AuditTable logs={audit.data.items} />
                      </div>
                    )}
                  </Panel>
                )}
              </>
            )}

            {activeTab === "settings" && (
              <div className="mx-auto w-full max-w-4xl">
                <PageHeader eyebrow="Configuration" title="System settings" description="Platform-wide policies and your administrator account." />
                <div className="space-y-6">
                  {settingsError ? (
                    <AdminErrorState error={settingsError} resource="system settings" onRetry={loadSettings} />
                  ) : !settings ? (
                    <LoadingState label="Loading settings…" />
                  ) : (
                    <Panel
                      as="form"
                      onSubmit={saveSettings}
                      noValidate
                      title="Platform policies"
                      description="These apply to every account. Changes take effect when you save."
                      flush
                      footer={
                        <div className="flex items-center justify-end gap-3">
                          {settingsDirty && (
                            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-text-amber">
                              <span className="h-1.5 w-1.5 rounded-full bg-psu-gold-dark" aria-hidden="true" />
                              Unsaved changes
                            </span>
                          )}
                          <button type="submit" className="btn-primary" disabled={isSavingSettings || !settingsDirty}>
                            {isSavingSettings ? "Saving…" : "Save settings"}
                          </button>
                        </div>
                      }
                    >
                      {settingsMessage && (
                        <div className="px-5 pt-5 sm:px-6">
                          <InlineAlert tone={settingsMessage.tone} onDismiss={() => setSettingsMessage(null)}>
                            {settingsMessage.text}
                          </InlineAlert>
                        </div>
                      )}
                      <div className="divide-y divide-border-subtle">
                        <SettingRow labelId="setting-maintenance_mode-label" title="Maintenance mode" description="Blocks student sign-in. Instructors and MIS keep access.">
                          <div className="flex items-center gap-3">
                            <span className={`text-xs font-semibold ${settings.maintenance_mode ? "text-text-amber" : "text-text-muted"}`} aria-hidden="true">
                              {settings.maintenance_mode ? "On" : "Off"}
                            </span>
                            <button
                              type="button"
                              role="switch"
                              aria-checked={Boolean(settings.maintenance_mode)}
                              aria-labelledby="setting-maintenance_mode-label"
                              onClick={() => setSettings((prev) => ({ ...prev, maintenance_mode: !prev.maintenance_mode }))}
                              className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${settings.maintenance_mode ? "bg-psu-maroon" : "bg-border-strong"}`}
                            >
                              <span className={`inline-block h-5 w-5 rounded-full bg-white shadow transition-transform ${settings.maintenance_mode ? "translate-x-[22px]" : "translate-x-0.5"}`} aria-hidden="true" />
                            </button>
                          </div>
                        </SettingRow>
                        <fieldset className="px-5 py-5 sm:px-6">
                          <legend className="sr-only">Default AST strictness</legend>
                          <p className="text-sm font-semibold text-text-main" aria-hidden="true">
                            Default AST strictness
                          </p>
                          <p className="mb-4 mt-0.5 text-sm text-text-muted">
                            Starting level for new instructor accounts and the level used for practice modules. Instructors can change their own level in Settings.
                          </p>
                          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                            {STRICTNESS.map(([value, label, help]) => (
                              <label
                                key={value}
                                className="relative flex cursor-pointer flex-col rounded-xl border border-border-strong bg-bg-panel p-4 transition-colors hover:border-psu-maroon/40 has-[:checked]:border-psu-maroon has-[:checked]:bg-psu-cream has-[:checked]:ring-1 has-[:checked]:ring-psu-maroon"
                              >
                                <span className="flex items-center gap-2">
                                  <input
                                    type="radio"
                                    name="default-strictness"
                                    value={value}
                                    checked={settings.default_ast_strictness === value}
                                    onChange={() => setSettings((prev) => ({ ...prev, default_ast_strictness: value }))}
                                    className="accent-psu-maroon"
                                  />
                                  <span className="text-sm font-semibold text-text-main">{label}</span>
                                </span>
                                <span className="mt-1.5 block text-xs text-text-muted">{help}</span>
                              </label>
                            ))}
                          </div>
                        </fieldset>
                      </div>
                    </Panel>
                  )}
                  {/* Outside the settings form so it stays available when the
                      system settings fail to load. */}
                  <ChangePasswordSection divided />
                </div>
              </div>
            )}
          </div>
        </main>
      </div>

      <ConfirmationModal
        isOpen={Boolean(userAction)}
        title={
          userAction?.type === "reset"
            ? "Reset password?"
            : userAction?.user?.is_active
              ? "Suspend account?"
              : "Activate account?"
        }
        message={
          userAction?.type === "reset"
            ? `${userAction?.user?.name}'s password will be replaced with a new temporary password, which will be shown to you once.`
            : userAction?.user?.is_active
              ? `${userAction?.user?.name} will not be able to sign in until the account is activated again.`
              : `${userAction?.user?.name} will be able to sign in again.`
        }
        confirmText={userAction?.type === "reset" ? "Reset password" : userAction?.user?.is_active ? "Suspend" : "Activate"}
        isDanger={userAction?.type === "reset" || Boolean(userAction?.user?.is_active)}
        isLoading={isActing}
        onConfirm={runUserAction}
        onCancel={() => setUserAction(null)}
      />
      <ConfirmationModal
        isOpen={Boolean(pendingTab)}
        title="Discard unsaved settings?"
        message="You changed system settings without saving. Leaving this section discards those changes."
        confirmText="Discard changes"
        isDanger
        onConfirm={() => {
          setSettings(savedSettings);
          showTab(pendingTab);
          setPendingTab(null);
        }}
        onCancel={() => {
          setPendingTab(null);
          setFocusTarget(null);
        }}
      />
      {editingUser && (
        <EditAccountModal key={editingUser.user_id} user={editingUser} onClose={() => setEditingUser(null)} onSaved={handleAccountSaved} />
      )}
      <SignOutModal
        isOpen={isSignOutOpen}
        onClose={() => setIsSignOutOpen(false)}
        onConfirm={() => {
          setIsSignOutOpen(false);
          logout();
          navigate("/login", { replace: true });
        }}
      />
    </div>
  );
}
