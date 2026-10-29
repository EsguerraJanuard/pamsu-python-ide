import { useCallback, useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";

import SignOutModal from "../../components/layout/SignOutModal";
import ConfirmationModal from "../../components/modals/ConfirmationModal";
import Modal from "../../components/ui/Modal";
import { EmptyState, ErrorState, FieldError, InlineAlert, LoadingState, PageHeader, useDismissTimer } from "../../components/ui/StateViews";
import api, { ApiError, getErrorMessage, TIMEOUT_ERROR_STATUS } from "../../services/api";
import { formatDate, formatDateTime, humanize } from "../../utils/format";
import { useAuth } from "../auth/AuthContext";
import { isGuestUser } from "../auth/guest";
import { ChangePasswordSection } from "../settings/AccountSections";
import StrictnessPicker from "../settings/StrictnessPicker";
import useUrlFilters from "../../hooks/useUrlFilters";

const PAGE_SIZE = 50;
// Brevo's free plan: ~300 emails a day; leave room for password-reset codes.
const BREVO_SAFE_DAILY_EMAILS = 250;
const RECENT_ACTIVITY_COUNT = 6;
// The backend's hosting stops it when idle and takes about a minute to start
// again. A settings page left open that long would otherwise fail its save
// after the 15 s default (QA ADM-27).
const SETTINGS_SAVE_TIMEOUT_MS = 90000;
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
  copy: "M11 9h9a2 2 0 012 2v9a2 2 0 01-2 2h-9a2 2 0 01-2-2v-9a2 2 0 012-2zM5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1",
  tick: "M20 6L9 17l-5-5",
  // Three dots; draw with a heavy stroke so the round caps read as dots.
  dotsVertical: "M12 5h.01M12 12h.01M12 19h.01",
};

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "faculty", label: "Faculty" },
  { id: "students", label: "Students" },
  { id: "audit", label: "Audit trail" },
  { id: "settings", label: "Settings" },
];

// Account action results (a reset password, a suspension) close after this long.
const NOTICE_DISMISS_MS = 60_000;

const QUICK_ACTIONS = [
  { id: "add-faculty", icon: "userPlus", title: "Add a faculty account", text: "Invite an instructor; they set their own password.", tab: "faculty", focus: "provision-instructor-email" },
  { id: "add-student", icon: "userPlus", title: "Add a student account", text: "Register one student; they set their own password.", tab: "students", focus: "provision-student-email" },
  { id: "masterlist", icon: "upload", title: "Import a masterlist", text: "Create many student accounts from a CSV or .xlsx file.", tab: "students", focus: "admin-bulk-file" },
  { id: "audit", icon: "shield", title: "Review the audit trail", text: "Check sign-ins and account changes.", tab: "audit" },
  { id: "settings", icon: "settings", title: "System settings", text: "Maintenance mode and the default AST strictness.", tab: "settings" },
];

const OUTCOME_TONE = { succeeded: "success", failed: "danger", denied: "warning" };

const AUDIT_PAGE_SIZES = [25, 50, 100];
const EMPTY_AUDIT_FILTERS = { q: "", action_type: "", outcome: "", actor_role: "", from: "", to: "" };
// Audit filters live in the URL (?audit_event=login_failed&audit_from=…), so
// a reload or a shared link reopens the same search.
const AUDIT_URL_KEYS = {
  q: "audit_q",
  action_type: "audit_event",
  outcome: "audit_outcome",
  actor_role: "audit_role",
  from: "audit_from",
  to: "audit_to",
};
const AUDIT_URL_DEFAULTS = Object.fromEntries(Object.values(AUDIT_URL_KEYS).map((key) => [key, ""]));

// ?tab=students&q=dela%20cruz&guests=1 — the open tab and the directory
// searches, kept in the URL for reloads and shared links.
const PAGE_URL_DEFAULTS = { tab: "overview", q: "", fq: "", guests: "" };
const PAGE_URL_ALLOWED = { tab: TABS.map((tab) => tab.id), guests: ["1"] };
const AUDIT_OUTCOMES = ["succeeded", "failed", "denied"];
const AUDIT_ROLES = ["admin", "instructor", "student", "system"];

// A status change names the state the account was put in; the new state is in
// the record's details. Records without it keep the generic label.
function auditEventLabel(log) {
  if (log.action_type === "user_status_changed" && typeof log.details?.is_active === "boolean") {
    return log.details.is_active ? "User activated" : "User deactivated";
  }
  return humanize(log.action_type);
}

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

/**
 * Put text on the clipboard. Without the Clipboard API (a page served over
 * plain http) or when the browser refuses it, the text in `element` is
 * selected so Ctrl+C copies it, and the older copy command is tried.
 * Resolves to "copied", "selected" (copy it by hand) or "failed".
 */
async function copyText(text, element) {
  try {
    await navigator.clipboard.writeText(text);
    return "copied";
  } catch {
    // No Clipboard API here, or the browser refused it.
  }
  const selection = window.getSelection();
  selection?.removeAllRanges();
  if (element) {
    const range = document.createRange();
    range.selectNodeContents(element);
    selection?.addRange(range);
  }
  const putText = (event) => {
    if (!event.clipboardData) return;
    event.clipboardData.setData("text/plain", text);
    event.preventDefault();
  };
  document.addEventListener("copy", putText);
  let copied;
  try {
    copied = document.execCommand("copy");
  } catch {
    copied = false;
  } finally {
    document.removeEventListener("copy", putText);
  }
  if (copied) return "copied";
  return element ? "selected" : "failed";
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

/** "class" → "classes", "match" → "matches", "account" → "accounts". */
function pluralWord(word) {
  return /(s|x|ch|sh)$/.test(word) ? `${word}es` : `${word}s`;
}

function plural(count, word) {
  return `${count} ${count === 1 ? word : pluralWord(word)}`;
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

function CountBadge({ count, word, hasMore }) {
  return (
    <span className="badge badge-neutral tabular-nums" aria-live="polite">
      {hasMore ? `${count}+ ${pluralWord(word)}` : plural(count, word)}
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

/** `value`, updated only after it has stopped changing for `delayMs`. */
function useDebouncedValue(value, delayMs = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(timer);
  }, [value, delayMs]);
  return debounced;
}

/**
 * The account directory of one tab. Role, search and order are sent to the
 * server, so a search covers every account, not just the pages loaded so far.
 */
function directoryEndpoint(role, search, includeGuests) {
  const params = new URLSearchParams({ role, order: "newest" });
  if (includeGuests) params.set("include_guests", "true");
  if (search) params.set("q", search);
  return `/admin/users?${params}`;
}

/** Accounts of `role` matching `query`. The server already filters; this only matters on a server without search. */
function directoryRows(items, role, query) {
  return items.filter((u) => u.role === role && (!query || matchesAccount(u, query)));
}

function useAdminList(endpoint) {
  const [items, setItems] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState(null);
  // A newer load (another search) makes older answers obsolete; they may
  // arrive later than the newer one and must not replace it.
  const requestId = useRef(0);

  const page = useCallback(
    (skip) => `${endpoint}${endpoint.includes("?") ? "&" : "?"}skip=${skip}&limit=${PAGE_SIZE}`,
    [endpoint],
  );

  const load = useCallback(async () => {
    const id = ++requestId.current;
    setIsLoading(true);
    setIsLoadingMore(false);
    setError(null);
    try {
      const data = await api.get(page(0));
      if (id !== requestId.current) return;
      const list = Array.isArray(data) ? data : [];
      setItems(list);
      setHasMore(list.length === PAGE_SIZE);
    } catch (err) {
      if (id === requestId.current) setError(err);
    } finally {
      if (id === requestId.current) setIsLoading(false);
    }
  }, [page]);

  const loadMore = async () => {
    const id = requestId.current;
    setIsLoadingMore(true);
    try {
      const data = await api.get(page(items.length));
      if (id !== requestId.current) return;
      const list = Array.isArray(data) ? data : [];
      setItems((prev) => [...prev, ...list]);
      setHasMore(list.length === PAGE_SIZE);
    } catch (err) {
      if (id === requestId.current) setError(err);
    } finally {
      if (id === requestId.current) setIsLoadingMore(false);
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
 * Accounts are created without a password: the person sets one from the
 * welcome email ("Forgot password?"). A server from before 2026-10-22 still
 * requires one; then a random temporary password is sent instead (that
 * server emails it), and the caller shows it to MIS.
 */
async function createAccount(endpoint, payload) {
  try {
    return { created: await api.post(endpoint, payload) };
  } catch (err) {
    if (!isPasswordRequired(err)) throw err;
    const fallbackPassword = generateTempPassword();
    return { created: await api.post(endpoint, { ...payload, password: fallbackPassword }), fallbackPassword };
  }
}

function NoPasswordNote({ who }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-border-subtle bg-bg-alt/50 px-4 py-3">
      <Icon name="key" className="mt-0.5 h-4 w-4 shrink-0 text-text-brand" />
      <p className="text-sm text-text-muted">
        <span className="font-semibold text-text-main">No password to share.</span> The welcome email links to &ldquo;Forgot password?&rdquo;, where
        the {who} gets a one-time code and chooses their own password.
      </p>
    </div>
  );
}

const COPY_NAMES = { email: "Email", password: "Temporary password" };

function copyFeedback({ target, result }) {
  if (result === "copied") return target === "both" ? "Email and password copied, one per line." : `${COPY_NAMES[target]} copied.`;
  if (result === "selected") return `The browser blocked copying, so the ${target === "email" ? "email" : "password"} is selected: press Ctrl+C (⌘C on a Mac) to copy it.`;
  return "The browser blocked copying. Copy the email and the password one at a time.";
}

/**
 * A generated temporary password with the email it signs in with, each in its
 * own box with a Copy button. It closes after NOTICE_DISMISS_MS (the clock
 * pauses while the pointer is over it or a control inside it has focus), when
 * the admin dismisses it, or when they leave the section. The password lives
 * only in the caller's state, never in storage, the URL or logs.
 */
function TemporaryPassword({ title, description, email, password, onDismiss }) {
  const headingId = `${useId()}-title`;
  const panelRef = useRef(null);
  const valueRefs = { email: useRef(null), password: useRef(null) };
  const [feedback, setFeedback] = useState(null);
  const resetTimer = useRef(null);
  const [isHovered, setIsHovered] = useState(false);
  const [isInUse, setIsInUse] = useState(false);
  useDismissTimer(NOTICE_DISMISS_MS, isHovered || isInUse, onDismiss);

  // Arrives after a dialog closes, possibly far from where the admin is
  // looking: bring it into view and move focus to it.
  useEffect(() => {
    const panel = panelRef.current;
    panel?.scrollIntoView({ block: "nearest", behavior: "smooth" });
    panel?.focus({ preventScroll: true });
    return () => window.clearTimeout(resetTimer.current);
  }, []);

  const copy = async (target) => {
    const text = target === "both" ? `${email}\n${password}` : target === "email" ? email : password;
    const result = await copyText(text, valueRefs[target]?.current);
    window.clearTimeout(resetTimer.current);
    setFeedback({ target, result });
    // Only the "Copied" label goes back; the block itself stays.
    if (result === "copied") resetTimer.current = window.setTimeout(() => setFeedback(null), 2500);
  };

  const copyButton = (target, label, srLabel) => {
    const done = feedback?.target === target && feedback.result === "copied";
    return (
      <button type="button" onClick={() => copy(target)} className="btn-secondary btn-sm min-w-[5.5rem] shrink-0">
        <Icon name={done ? "tick" : "copy"} className="h-3.5 w-3.5" />
        {done ? "Copied" : label}
        <span className="sr-only"> {srLabel}</span>
      </button>
    );
  };

  const field = (target, label) => (
    <div>
      <dt className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">{label}</dt>
      <dd className="mt-1 flex items-center gap-2">
        {/* select-all: one click selects the whole value, dash and "!" included. */}
        <code
          ref={valueRefs[target]}
          className="min-w-0 flex-1 select-all break-all rounded-lg border border-border-strong bg-bg-panel px-3 py-2 font-mono text-sm text-text-main"
        >
          {target === "email" ? email : password}
        </code>
        {copyButton(target, "Copy", label.toLowerCase())}
      </dd>
    </div>
  );

  return (
    <section
      ref={panelRef}
      tabIndex={-1}
      aria-labelledby={headingId}
      className="scroll-mt-24 rounded-lg border border-emerald-600/25 bg-emerald-600/[0.07] px-4 py-4 focus:outline-none sm:px-5"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      // The panel itself is focused when it appears; only focus on a control
      // inside it (a Copy button, a selected value) means it is being used.
      onFocus={(event) => setIsInUse(event.target !== event.currentTarget)}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setIsInUse(false);
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-2.5">
          <Icon name="check" className="mt-0.5 h-4 w-4 shrink-0 text-text-emerald" />
          <div className="min-w-0">
            <h2 id={headingId} className="break-words text-sm font-semibold text-text-emerald">
              {title}
            </h2>
            {description && <p className="mt-0.5 text-sm text-text-main">{description}</p>}
          </div>
        </div>
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 rounded p-0.5 text-text-emerald opacity-70 transition hover:opacity-100 focus-visible:outline-2 focus-visible:outline-offset-2"
          aria-label="Dismiss the temporary password"
        >
          <Icon name="x" className="h-3.5 w-3.5" strokeWidth={2} />
        </button>
      </div>

      <dl className="mt-4 max-w-xl space-y-3">
        {field("email", "Email")}
        {field("password", "Temporary password")}
      </dl>

      <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-2">
        {copyButton("both", "Copy both", "email and password")}
        <p role="status" aria-live="polite" className="min-w-0 flex-1 text-xs font-medium text-text-main">
          {feedback ? copyFeedback(feedback) : ""}
        </p>
      </div>

      <p className="mt-3 flex items-start gap-2 border-t border-emerald-600/20 pt-3 text-xs text-text-muted">
        <Icon name="key" className="mt-px h-3.5 w-3.5 shrink-0 text-text-brand" />
        <span>
          <span className="font-semibold text-text-main">Share it securely.</span> It is shown only here and closes after a minute (or when you
          leave this section); it can&rsquo;t be shown again. Pointing at it or copying pauses the timer.
        </span>
      </p>
    </section>
  );
}

function ProvisionForm({ role, onCreated, onTemporaryPassword }) {
  const isStudent = role === "student";
  const who = isStudent ? "student" : "instructor";
  const empty = { email: "", first_name: "", middle_name: "", last_name: "", school_id: "" };
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
        ...(isStudent ? { school_id: form.school_id.trim() } : {}),
      };
      const { created, fallbackPassword } = await createAccount(isStudent ? "/admin/students" : "/admin/instructors", payload);
      const pending = created?.pending_enrollments;
      const joined = pending?.enrolled_class_ids?.length ?? 0;
      const waiting = pending?.skipped?.length ?? 0;
      const enrollmentNote = [
        joined > 0 && `Added to ${joined} class${joined === 1 ? "" : "es"} that had queued this email.`,
        waiting > 0 && `${waiting} queued class${waiting === 1 ? " is" : "es are"} inactive or could not be joined and stay${waiting === 1 ? "s" : ""} pending.`,
      ].filter(Boolean).join(" ");
      const signIn = fallbackPassword
        ? // A server from before 2026-10-22 still requires a password and emails it.
          "This server still emails a temporary password; if the email doesn't arrive, share the one shown at the top of the page."
        : `The ${who} is emailed a link to set their own password. If the email doesn't arrive, they can use "Forgot password?" on the sign-in page with this address.`;
      if (fallbackPassword) {
        onTemporaryPassword?.({
          title: `Temporary password for ${fullName}`,
          description: "This server also emails it. Share it only if the email doesn't arrive.",
          email: payload.email,
          password: fallbackPassword,
        });
      }
      setResult({
        tone: waiting > 0 ? "warning" : "success",
        text: `Account created for ${payload.email}. ${signIn}${enrollmentNote ? ` ${enrollmentNote}` : ""}`,
      });
      setForm(empty);
      onCreated?.();
    } catch (err) {
      setResult({ tone: "error", text: getErrorMessage(err, "The account could not be created.") });
    } finally {
      setIsSaving(false);
    }
  };

  const prefix = `provision-${role}`;
  return (
    <Panel
      as="form"
      onSubmit={handleSubmit}
      noValidate
      title={isStudent ? "Create student account" : "Create faculty account"}
      description={isStudent ? "For one student. They are emailed a link to set their own password." : "The instructor is emailed a link to set their own password."}
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
            <NoPasswordNote who={who} />
          )}
        </div>
        <div className="grid grid-cols-1 gap-5 rounded-lg border border-border-subtle bg-bg-alt/40 p-4 @xl:grid-cols-3">
          <TextField id={`${prefix}-first`} label="First name" value={form.first_name} onChange={set("first_name")} error={errors.first_name} disabled={isSaving} maxLength={70} />
          <TextField id={`${prefix}-middle`} label="Middle name (optional)" value={form.middle_name} onChange={set("middle_name")} error={errors.middle_name} disabled={isSaving} maxLength={70} />
          <TextField id={`${prefix}-last`} label="Last name" value={form.last_name} onChange={set("last_name")} error={errors.last_name} disabled={isSaving} maxLength={70} />
        </div>
        {isStudent && <NoPasswordNote who={who} />}
      </div>
    </Panel>
  );
}

/** Self-service guest ("Continue as Guest Student"). Older servers don't send is_guest. */
const isGuestAccount = isGuestUser;

const ROW_ACTION =
  "inline-flex items-center gap-1.5 whitespace-nowrap rounded-md border border-border-subtle bg-bg-panel px-2.5 py-1.5 text-xs font-semibold text-text-main transition-colors disabled:cursor-not-allowed disabled:opacity-60";

const MENU_GAP = 6;
const MENU_MARGIN = 8;
const MENU_ITEM_TONES = {
  default: "text-text-main hover:bg-bg-alt focus-visible:bg-bg-alt",
  danger: "text-text-rose hover:bg-psu-red/[0.06] focus-visible:bg-psu-red/[0.06]",
  success: "text-text-emerald hover:bg-emerald-600/[0.07] focus-visible:bg-emerald-600/[0.07]",
};

/**
 * The "⋮" button for one table row and its menu. The menu is rendered in a
 * portal with fixed positioning, so the table's scroll wrapper and the card's
 * rounded clipping never cut it off. It opens below the button (above when
 * there is no room) and closes on a choice, Escape, Tab, an outside click,
 * scrolling or resizing. Arrow keys, Home and End move between items.
 *
 * items: [{ id, label, hint?, icon, onSelect, disabled?, tone?, separatorBefore? }]
 */
function RowActionsMenu({ label, items, busy = false }) {
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState(null);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const menuId = useId();

  const close = useCallback((returnFocus) => {
    setIsOpen(false);
    setPosition(null);
    if (returnFocus) triggerRef.current?.focus();
  }, []);

  // Measure and place the menu before it is painted.
  useLayoutEffect(() => {
    if (!isOpen || !triggerRef.current || !menuRef.current) return;
    const anchor = triggerRef.current.getBoundingClientRect();
    const { offsetWidth: width, offsetHeight: height } = menuRef.current;
    const roomBelow = window.innerHeight - anchor.bottom - MENU_GAP - MENU_MARGIN;
    const above = height > roomBelow && anchor.top - MENU_GAP - MENU_MARGIN >= height;
    setPosition({
      top: above ? anchor.top - MENU_GAP - height : anchor.bottom + MENU_GAP,
      left: Math.max(MENU_MARGIN, Math.min(anchor.right - width, window.innerWidth - width - MENU_MARGIN)),
      above,
    });
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen || !position) return;
    menuRef.current?.querySelector('[role="menuitem"]:not(:disabled)')?.focus({ preventScroll: true });
  }, [isOpen, position]);

  useEffect(() => {
    if (!isOpen) return undefined;
    const onPointerDown = (event) => {
      if (menuRef.current?.contains(event.target) || triggerRef.current?.contains(event.target)) return;
      close(false);
    };
    // A fixed menu would drift away from its row, so moving the page closes it.
    const onViewportChange = () => close(false);
    document.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("resize", onViewportChange);
    window.addEventListener("scroll", onViewportChange, true);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("resize", onViewportChange);
      window.removeEventListener("scroll", onViewportChange, true);
    };
  }, [isOpen, close]);

  const onMenuKeyDown = (event) => {
    const options = [...menuRef.current.querySelectorAll('[role="menuitem"]:not(:disabled)')];
    const index = options.indexOf(document.activeElement);
    const focusAt = (i) => options[(i + options.length) % options.length]?.focus();
    if (event.key === "ArrowDown") focusAt(index + 1);
    else if (event.key === "ArrowUp") focusAt(index - 1);
    else if (event.key === "Home") focusAt(0);
    else if (event.key === "End") focusAt(options.length - 1);
    else if (event.key === "Escape" || event.key === "Tab") close(true);
    else return;
    event.preventDefault();
  };

  const choose = (item) => {
    // Focus goes back to the ⋮ button first, so a dialog the action opens
    // returns focus there when it closes.
    close(true);
    item.onSelect();
  };

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-controls={isOpen ? menuId : undefined}
        aria-busy={busy || undefined}
        title="More actions"
        onClick={() => (isOpen ? close(false) : setIsOpen(true))}
        onKeyDown={(event) => {
          if (event.key === "ArrowDown" && !isOpen) {
            event.preventDefault();
            setIsOpen(true);
          }
        }}
        className={`inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md border transition-colors ${
          isOpen
            ? "border-psu-maroon/40 bg-psu-cream text-text-brand"
            : "border-border-subtle bg-bg-panel text-text-muted hover:border-border-strong hover:bg-bg-alt hover:text-text-main"
        }`}
      >
        {busy ? <Icon name="refresh" className="h-4 w-4 animate-spin" /> : <Icon name="dotsVertical" className="h-4 w-4" strokeWidth={3} />}
      </button>
      {isOpen &&
        createPortal(
          <div
            ref={menuRef}
            id={menuId}
            role="menu"
            aria-label={label}
            onKeyDown={onMenuKeyDown}
            style={{ top: position?.top ?? 0, left: position?.left ?? 0, visibility: position ? "visible" : "hidden" }}
            className={`fixed z-50 w-64 rounded-xl border border-border-subtle bg-bg-panel p-1.5 shadow-[0_16px_40px_-12px_var(--shadow-popover)] animate-scale-in ${
              position?.above ? "origin-bottom-right" : "origin-top-right"
            }`}
          >
            {items.map((item) => (
              <div key={item.id}>
                {item.separatorBefore && <div role="separator" className="mx-1 my-1.5 h-px bg-border-subtle" />}
                <button
                  type="button"
                  role="menuitem"
                  disabled={item.disabled}
                  onClick={() => choose(item)}
                  className={`flex w-full items-start gap-2.5 rounded-lg px-2.5 py-2 text-left transition-colors disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent ${
                    MENU_ITEM_TONES[item.tone || "default"]
                  }`}
                >
                  <Icon name={item.icon} className="mt-0.5 h-4 w-4 shrink-0" />
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold">{item.label}</span>
                    {item.hint && <span className="mt-0.5 block text-xs font-normal leading-snug text-text-muted">{item.hint}</span>}
                  </span>
                </button>
              </div>
            ))}
          </div>,
          document.body,
        )}
    </>
  );
}

/** The menu items for one account row; guests expire on their own, so they can only be suspended or reactivated. */
function accountMenuItems(user, onAction, busy) {
  const guest = isGuestAccount(user);
  return [
    !guest && user.role === "student" && {
      id: "apply",
      label: busy ? "Applying…" : "Re-apply pending enrollments",
      hint: user.is_active ? "Enroll them in classes that queued their email." : "Activate the account first.",
      icon: "refresh",
      disabled: busy || !user.is_active,
      onSelect: () => onAction(user, "apply"),
    },
    !guest && {
      id: "reset",
      label: "Reset password",
      hint: "Shows you a one-time temporary password.",
      icon: "key",
      onSelect: () => onAction(user, "reset"),
    },
    {
      id: "status",
      label: user.is_active ? "Suspend account" : "Activate account",
      hint: user.is_active ? "Blocks sign-in until it is activated again." : "Lets them sign in again.",
      icon: user.is_active ? "ban" : "check",
      tone: user.is_active ? "danger" : "success",
      separatorBefore: !guest,
      onSelect: () => onAction(user, "status"),
    },
  ].filter(Boolean);
}

function UserTable({ users, caption, emptyMessage, onAction, busyUserId = null }) {
  if (users.length === 0) {
    return (
      <div className="p-5 sm:p-6">
        <EmptyState className="py-10" title="No accounts" message={emptyMessage} />
      </div>
    );
  }
  return (
    // Fixed column widths keep the table inside a desktop card; the scroll
    // wrapper is only a fallback for phones (the row menu is portaled, so it
    // is never clipped by it).
    <div className="overflow-x-auto">
      <table className="w-full min-w-[320px] table-fixed text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead className="border-b border-border-subtle bg-bg-alt/70">
          <tr>
            <th scope="col" className={TH}>Name</th>
            <th scope="col" className={`${TH} hidden w-36 md:table-cell`}>School ID</th>
            <th scope="col" className={`${TH} hidden w-32 sm:table-cell`}>Status</th>
            <th scope="col" className={`${TH} w-28 text-right sm:w-36`}>Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border-subtle">
          {users.map((user) => {
            const guest = isGuestAccount(user);
            const busy = busyUserId === user.user_id;
            const schoolId = user.school_id ? (
              <span className="rounded-md border border-border-subtle bg-bg-alt px-2 py-0.5 font-mono text-xs text-text-main">{user.school_id}</span>
            ) : (
              <span className="text-text-muted">—</span>
            );
            return (
            <tr key={user.user_id} className="transition-colors hover:bg-psu-cream/70">
              <td className="px-5 py-3.5">
                <div className="flex min-w-0 items-center gap-3">
                  <Avatar name={user.name} />
                  <div className="min-w-0">
                    <p className="flex min-w-0 items-center gap-2">
                      <span className="truncate font-semibold text-text-main" title={user.name}>{user.name}</span>
                      {guest && <Pill tone="warning">Guest</Pill>}
                    </p>
                    <p className="truncate text-xs text-text-muted" title={user.email}>{user.email}</p>
                    {/* Narrow screens hide the School ID (below md) and Status (below sm) columns; show them here instead. */}
                    <div className="mt-1 flex flex-wrap items-center gap-1.5 md:hidden">
                      {user.school_id && schoolId}
                      <span className="sm:hidden">
                        <Pill tone={user.is_active ? "success" : "neutral"}>{user.is_active ? "Active" : "Suspended"}</Pill>
                      </span>
                    </div>
                  </div>
                </div>
              </td>
              <td className="hidden px-5 py-3.5 md:table-cell">{schoolId}</td>
              <td className="hidden px-5 py-3.5 sm:table-cell">
                <Pill tone={user.is_active ? "success" : "neutral"}>{user.is_active ? "Active" : "Suspended"}</Pill>
              </td>
              <td className="px-5 py-3.5">
                <div className="flex items-center justify-end gap-2">
                  {/* Guest accounts expire on their own; they can only be suspended or reactivated. */}
                  {!guest && (
                    <button
                      type="button"
                      className={`${ROW_ACTION} hover:border-psu-maroon/40 hover:bg-psu-cream hover:text-text-brand`}
                      aria-label={`Edit ${user.name}`}
                      onClick={() => onAction(user, "edit")}
                    >
                      <Icon name="pencil" className="h-3.5 w-3.5" />
                      {/* Icon only on phones; the aria-label names it either way. */}
                      <span className="hidden sm:inline">Edit</span>
                    </button>
                  )}
                  <RowActionsMenu label={`More actions for ${user.name}`} items={accountMenuItems(user, onAction, busy)} busy={busy} />
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
              <td className="px-5 py-3.5 font-medium text-text-main">{auditEventLabel(log)}</td>
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

/**
 * Splits a stored full name for the edit form. Only the full name is stored,
 * so the split is the API's (first word, then the rest as the last name,
 * which keeps surnames like "Dela Cruz" whole). Joining the three fields
 * gives back the same name, so saving without edits changes nothing.
 */
function splitFullName(user) {
  const parts = (user?.name || "").split(/\s+/).filter(Boolean);
  return {
    first_name: user?.first_name ?? parts[0] ?? "",
    middle_name: "",
    last_name: user?.last_name ?? parts.slice(1).join(" "),
  };
}

const joinName = (...parts) => parts.join(" ").split(/\s+/).filter(Boolean).join(" ");

/**
 * Dialog for correcting an account. It has the same editable fields as the
 * create forms: university email, first, middle and last name, and (for
 * students) the school ID. Role and status are changed elsewhere.
 */
function EditAccountModal({ user, onClose, onSaved }) {
  const isStudent = user?.role === "student";
  const [nameParts, setNameParts] = useState(() => splitFullName(user));
  const [email, setEmail] = useState(user?.email ?? "");
  const [schoolId, setSchoolId] = useState(user?.school_id ?? "");
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const emailRef = useRef(null);

  const setNamePart = (field) => (e) => {
    const value = e.target.value;
    setNameParts((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: "", name: "" }));
  };

  const trimmedName = joinName(nameParts.first_name, nameParts.middle_name, nameParts.last_name);
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
    if (!nameParts.first_name.trim()) next.first_name = "First name is required.";
    if (!nameParts.last_name.trim()) next.last_name = "Last name is required.";
    if (trimmedName.length > 150) next.last_name = "The full name must be at most 150 characters.";
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
          ? "The same details as when the account was created: email, name and school ID. Role and status are changed elsewhere."
          : "The same details as when the account was created: email and name. Role and status are changed elsewhere."
      }
      size="xl"
      dismissible={!isSaving}
      initialFocusRef={emailRef}
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
          <div className={`grid grid-cols-1 gap-5 ${isStudent ? "sm:grid-cols-2" : ""}`}>
            <TextField
              ref={emailRef}
              id="admin-edit-email"
              label="University email"
              type="email"
              autoComplete="off"
              placeholder="name@pampangastateu.edu.ph"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setErrors((prev) => ({ ...prev, email: "" }));
              }}
              error={errors.email}
              disabled={isSaving}
            />
            {isStudent && (
              <TextField
                id="admin-edit-school-id"
                label="School ID"
                className="input-field py-2.5 font-mono"
                placeholder="2026000001 or 2026-00001"
                maxLength={10}
                value={schoolId}
                onChange={(e) => {
                  setSchoolId(e.target.value);
                  setErrors((prev) => ({ ...prev, school_id: "" }));
                }}
                error={errors.school_id}
                hint="The student number from the MIS masterlist. Masterlist uploads are matched on it."
                disabled={isSaving}
                autoComplete="off"
              />
            )}
          </div>
          <div className="grid grid-cols-1 gap-5 rounded-lg border border-border-subtle bg-bg-alt/40 p-4 sm:grid-cols-3">
            <TextField id="admin-edit-first" label="First name" value={nameParts.first_name} onChange={setNamePart("first_name")} error={errors.first_name} disabled={isSaving} maxLength={70} autoComplete="off" />
            <TextField id="admin-edit-middle" label="Middle name (optional)" value={nameParts.middle_name} onChange={setNamePart("middle_name")} error={errors.middle_name} disabled={isSaving} maxLength={70} autoComplete="off" />
            <TextField id="admin-edit-last" label="Last name" value={nameParts.last_name} onChange={setNamePart("last_name")} error={errors.last_name} disabled={isSaving} maxLength={70} autoComplete="off" />
          </div>
          {nameChanged && !errors.first_name && !errors.last_name && (
            <p className="-mt-2 text-xs text-text-muted">
              Will be saved as <span className="font-semibold text-text-main">{trimmedName}</span>.
            </p>
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
  const [urlFilters, setUrlFilters] = useUrlFilters(AUDIT_URL_DEFAULTS);
  const filters = useMemo(
    () => Object.fromEntries(Object.entries(AUDIT_URL_KEYS).map(([field, key]) => [field, urlFilters[key]])),
    [urlFilters],
  );
  const [search, setSearch] = useState(() => filters.q.trim());
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
    setUrlFilters({ [AUDIT_URL_KEYS[key]]: value });
    setPage(1);
  };
  const clearFilters = () => {
    setUrlFilters(Object.fromEntries(Object.entries(AUDIT_URL_KEYS).map(([field, key]) => [key, EMPTY_AUDIT_FILTERS[field]])));
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
  const [pageFilters, setPageFilters] = useUrlFilters(PAGE_URL_DEFAULTS, PAGE_URL_ALLOWED);
  const activeTab = pageFilters.tab;
  const [pendingTab, setPendingTab] = useState(null);
  const [focusTarget, setFocusTarget] = useState(null);
  const [isSignOutOpen, setIsSignOutOpen] = useState(false);

  const [stats, setStats] = useState(null);
  const [statsError, setStatsError] = useState(null);
  const showGuests = pageFilters.guests === "1";
  // Typing waits for a pause before asking the server.
  const query = useDebouncedValue(pageFilters.q.trim().toLowerCase());
  const facultyQuery = useDebouncedValue(pageFilters.fq.trim().toLowerCase());
  const facultyList = useAdminList(directoryEndpoint("instructor", facultyQuery, false));
  const studentList = useAdminList(directoryEndpoint("student", query, showGuests));
  const logs = useAdminList("/admin/audit-logs");
  // Each directory loads when its tab is first opened.
  const [visitedTabs, setVisitedTabs] = useState(() => ({ [activeTab]: true }));
  useEffect(() => {
    setVisitedTabs((visited) => (visited[activeTab] ? visited : { ...visited, [activeTab]: true }));
  }, [activeTab]);

  const [settings, setSettings] = useState(null);
  const [savedSettings, setSavedSettings] = useState(null);
  const [settingsError, setSettingsError] = useState(null);
  const [settingsMessage, setSettingsMessage] = useState(null);
  const [isSavingSettings, setIsSavingSettings] = useState(false);

  const search = pageFilters.q;
  const setSearch = (value) => setPageFilters({ q: value });
  const facultySearch = pageFilters.fq;
  const setFacultySearch = (value) => setPageFilters({ fq: value });
  const [editingUser, setEditingUser] = useState(null);
  const [exportingRole, setExportingRole] = useState(null);
  // The audit search loads only once its tab has been opened (or the page
  // was opened on it from a link).
  const [auditVisited, setAuditVisited] = useState(() => activeTab === "audit");
  const audit = useAuditSearch(auditVisited);
  const [userAction, setUserAction] = useState(null);
  const [isActing, setIsActing] = useState(false);
  const [applyingUserId, setApplyingUserId] = useState(null);
  const [pendingRefresh, setPendingRefresh] = useState(0);
  const [actionMessage, setActionMessage] = useState(null);
  const messageCount = useRef(0);
  // A result message belongs to the section where its action started (the
  // activeTab this handler saw), so a reply that lands after the admin moved
  // on never shows up in another section.
  const notify = (message) => {
    messageCount.current += 1;
    setActionMessage({ ...message, id: messageCount.current, tab: activeTab });
  };
  // A generated password shown to the admin: kept only here (never stored or
  // logged). Like a result message it belongs to the section where it was
  // made, and it closes itself after a minute (see TemporaryPassword).
  const [temporaryPassword, setTemporaryPassword] = useState(null);
  const temporaryPasswordCount = useRef(0);
  // Leaving a section by any route (tab button, Back/Forward, a link) takes
  // its result message and any temporary password with it.
  useEffect(
    () => () => {
      setActionMessage(null);
      setTemporaryPassword(null);
    },
    [activeTab],
  );
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

  const { load: loadFaculty } = facultyList;
  const { load: loadStudents } = studentList;
  const { load: loadLogs } = logs;
  useEffect(() => {
    loadStats();
    loadLogs();
    loadSettings();
  }, [loadStats, loadLogs, loadSettings]);

  // Separate, so a search or the "Show guests" switch reloads only its list.
  useEffect(() => {
    if (visitedTabs.faculty) loadFaculty();
  }, [visitedTabs.faculty, loadFaculty]);
  useEffect(() => {
    if (visitedTabs.students) loadStudents();
  }, [visitedTabs.students, loadStudents]);

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
    if (tab === "audit") setAuditVisited(true);
    setPageFilters({ tab });
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

  const filteredFaculty = directoryRows(facultyList.items, "instructor", facultyQuery);
  const filteredStudents = directoryRows(studentList.items, "student", query);
  // Status and edits change one row in place in whichever list holds it.
  const updateListedUser = (userId, update) => {
    for (const list of [facultyList, studentList]) {
      list.setItems((prev) => prev.map((u) => (u.user_id === userId ? update(u) : u)));
    }
  };

  const showTemporaryPassword = (details) => {
    temporaryPasswordCount.current += 1;
    setTemporaryPassword({ ...details, id: temporaryPasswordCount.current, tab: activeTab });
  };

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
      notify({
        tone: waiting > 0 ? "warning" : "success",
        text: parts.length ? `${user.name}: ${parts.join(", ")}.` : `${user.name} has no queued class enrollments.`,
      });
      setPendingRefresh((n) => n + 1);
    } catch (err) {
      notify({
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
    updateListedUser(result.user_id, (u) => ({ ...u, name: result.name, email: result.email, school_id: result.school_id ?? u.school_id }));
    const changed = result.changed_fields ?? [];
    const joined = result.pending_enrollments?.enrolled_class_ids?.length ?? 0;
    const parts = [
      changed.includes("name") && `the name is now ${result.name}`,
      changed.includes("email") && `they now sign in as ${result.email}`,
      changed.includes("school_id") && `the school ID is now ${result.school_id}`,
    ].filter(Boolean);
    notify({
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
        const batch = await api.get(`/admin/users?role=${role}&skip=${skip}&limit=500`);
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
      notify({ tone: "error", text: getErrorMessage(err, "The list could not be exported.") });
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
        updateListedUser(user.user_id, (u) => ({ ...u, is_active: res?.is_active ?? !u.is_active }));
        notify({ tone: "success", text: `${user.name} is now ${(res?.is_active ?? !user.is_active) ? "active" : "suspended"}.` });
      } else {
        await api.patch(`/admin/users/${user.user_id}/password`, { new_password: password });
        setActionMessage(null);
        showTemporaryPassword({
          title: `Password reset for ${user.name}`,
          description: "They sign in with this email and temporary password.",
          email: user.email,
          password,
        });
      }
    } catch (err) {
      notify({ tone: "error", text: getErrorMessage(err, "The action could not be completed.") });
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
        tone: failedRows.length > 0 || pendingLeft > 0 || created > BREVO_SAFE_DAILY_EMAILS ? "warning" : "success",
        text:
          `${created} account${created === 1 ? "" : "s"} created, ${res?.skipped ?? 0} already existed, ${failedRows.length} row${failedRows.length === 1 ? "" : "s"} failed.` +
          (created > 0 ? " Each new student is emailed their account details and a link to set their own password." : "") +
          // Brevo's free plan sends about 300 emails a day, password-reset codes included.
          (created > BREVO_SAFE_DAILY_EMAILS
            ? ` The email service sends about 300 emails a day, so some of these welcome emails may not go out today. Students who don't get one can use "Forgot password?" tomorrow; split large masterlists across days.`
            : "") +
          (fromPending > 0 ? ` ${fromPending} queued class enrollment${fromPending === 1 ? " was" : "s were"} completed.` : "") +
          (pendingLeft > 0 ? ` ${pendingLeft} stay${pendingLeft === 1 ? "s" : ""} pending because the class is inactive or could not be joined.` : ""),
        rows: failedRows,
      });
      studentList.load();
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
      }, {}, SETTINGS_SAVE_TIMEOUT_MS);
      setSavedSettings(settings);
      setSettingsMessage({ tone: "success", text: "Settings saved." });
    } catch (err) {
      if (err?.status === TIMEOUT_ERROR_STATUS) {
        // The save may still have gone through: show what the server holds.
        try {
          const stored = await api.get("/admin/settings", {}, SETTINGS_SAVE_TIMEOUT_MS);
          setSavedSettings(stored);
          if (stored.maintenance_mode === Boolean(settings.maintenance_mode)
            && stored.default_ast_strictness === (settings.default_ast_strictness || "moderate")) {
            setSettings(stored);
            setSettingsMessage({ tone: "success", text: "Settings saved." });
            return;
          }
        } catch {
          // Fall through to the timeout message.
        }
      }
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
  const userListBody = (source, list, caption, emptyMessage) =>
    source.error ? (
      <div className="p-5 sm:p-6">
        <AdminErrorState error={source.error} resource={caption.toLowerCase()} onRetry={source.load} />
      </div>
    ) : source.isLoading ? (
      <LoadingState label="Loading accounts…" className="py-14" />
    ) : (
      <UserTable users={list} caption={caption} emptyMessage={emptyMessage} onAction={handleUserAction} busyUserId={applyingUserId} />
    );
  const exportButton = (role, enabled) => (
    <button type="button" className="btn-secondary" onClick={() => exportAccounts(role)} disabled={!enabled || exportingRole !== null}>
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
  const loadMoreButton = (source) =>
    source.hasMore && !source.error && !source.isLoading && (
      <button type="button" className="btn-secondary w-full" onClick={source.loadMore} disabled={source.isLoadingMore}>
        {source.isLoadingMore ? "Loading…" : "Load more accounts"}
      </button>
    );
  // Export takes every account of the role, whatever the search shows.
  const canExport = (source, searching) => searching || source.isLoading || source.items.length > 0;

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
          {/* Shown only in the section where the password was made; leaving it clears the password. */}
          {temporaryPassword?.tab === activeTab && (
            <div className="mx-auto mb-5 w-full max-w-6xl">
              <TemporaryPassword
                key={temporaryPassword.id}
                title={temporaryPassword.title}
                description={temporaryPassword.description}
                email={temporaryPassword.email}
                password={temporaryPassword.password}
                onDismiss={() => setTemporaryPassword(null)}
              />
            </div>
          )}
          <div key={activeTab} className="animate-page-fade mx-auto w-full max-w-6xl">
            {actionMessage?.tab === activeTab && (
              <InlineAlert
                key={actionMessage.id}
                tone={actionMessage.tone}
                onDismiss={() => setActionMessage(null)}
                // Results fade after a minute; errors stay until dismissed.
                autoDismissMs={actionMessage.tone === "error" ? 0 : NOTICE_DISMISS_MS}
                className="mb-5"
              >
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
                                {auditEventLabel(log)}
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
                  actions={exportButton("instructor", canExport(facultyList, Boolean(facultyQuery)))}
                />
                {/* Form above a full-width directory, so the table never has to
                    scroll sideways on a desktop display. */}
                <div className="grid grid-cols-1 items-start gap-6">
                  <ProvisionForm role="instructor" onCreated={() => { facultyList.load(); loadStats(); }} onTemporaryPassword={showTemporaryPassword} />
                  <div className="min-w-0 space-y-4">
                    <Panel
                      title="Faculty directory"
                      description="Instructors who can sign in to the IDE."
                      icon="faculty"
                      flush
                      actions={
                        <>
                          {!facultyList.isLoading && !facultyList.error && (
                            <CountBadge count={filteredFaculty.length} word={facultyQuery ? "match" : "account"} hasMore={facultyList.hasMore} />
                          )}
                          {searchBox("admin-faculty-search", "Search faculty", facultySearch, setFacultySearch)}
                        </>
                      }
                    >
                      {userListBody(facultyList, filteredFaculty, "Faculty accounts", facultyQuery ? "No faculty match your search." : "No faculty accounts have been created yet.")}
                    </Panel>
                    {loadMoreButton(facultyList)}
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
                  actions={exportButton("student", canExport(studentList, Boolean(query)))}
                />
                {/* Form and masterlist side by side, full-width directory below. */}
                <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
                  <div>
                    <ProvisionForm role="student" onCreated={() => { studentList.load(); loadStats(); }} onTemporaryPassword={showTemporaryPassword} />
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
                          {!studentList.isLoading && !studentList.error && (
                            <CountBadge count={filteredStudents.length} word={query ? "match" : "account"} hasMore={studentList.hasMore} />
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
                              onClick={() => setPageFilters({ guests: showGuests ? "" : "1" })}
                              className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${showGuests ? "bg-psu-maroon" : "bg-border-strong"}`}
                            >
                              <span className={`inline-block h-5 w-5 rounded-full bg-white shadow transition-transform ${showGuests ? "translate-x-[22px]" : "translate-x-0.5"}`} aria-hidden="true" />
                            </button>
                          </div>
                          {searchBox("admin-student-search", "Search students", search, setSearch)}
                        </>
                      }
                    >
                      {userListBody(studentList, filteredStudents, "Student accounts", query ? "No students match your search." : "No student accounts yet.")}
                    </Panel>
                    {loadMoreButton(studentList)}
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
                        <div className="px-5 py-5 sm:px-6">
                          <StrictnessPicker
                            name="default-strictness"
                            legend="Default AST strictness"
                            description="Starting level for new instructor accounts and the level used for practice modules. Instructors can change their own level in Settings."
                            value={settings.default_ast_strictness}
                            onChange={(value) => setSettings((prev) => ({ ...prev, default_ast_strictness: value }))}
                          />
                        </div>
                      </div>
                    </Panel>
                  )}
                  {/* Outside the settings form so it stays available when the
                      system settings fail to load. */}
                  <ChangePasswordSection />
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
