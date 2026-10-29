import { useEffect, useRef, useState } from "react";

import { describeApiError } from "../../services/api";

/*
 * Shared loading / empty / error presentation.
 *
 * Pages must keep these states distinct: an EmptyState means the request
 * succeeded and returned no records; an ErrorState means it did not succeed.
 */

const ICON_PATHS = {
  inbox: "M22 12h-6l-2 3h-4l-2-3H2M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z",
  offline: "M12 20h.01M8.5 16.43a5 5 0 0 1 7 0M2 8.82a15 15 0 0 1 4.17-2.65M10.66 5c4.01-.36 8.14.9 11.34 3.76M16.85 11.25a10 10 0 0 1 2.22 1.68M5 13a10 10 0 0 1 5.24-2.76M2 2l20 20",
  lock: "M7 11V7a5 5 0 0 1 10 0v4M5 11h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2z",
  search: "M21 21l-4.35-4.35M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16z",
  alert: "M12 9v4m0 4h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z",
  clock: "M12 6v6l4 2M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z",
};

const KIND_ICON = {
  unavailable: "offline",
  timeout: "clock",
  unauthorized: "lock",
  forbidden: "lock",
  not_found: "search",
};

export function StateIcon({ name = "inbox", className = "h-6 w-6" }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d={ICON_PATHS[name] || ICON_PATHS.inbox} />
    </svg>
  );
}

export function Spinner({ className = "h-5 w-5", label }) {
  return (
    <span className="inline-flex items-center gap-2" role={label ? "status" : undefined}>
      <span
        className={`${className} inline-block animate-spin rounded-full border-2 border-psu-maroon/20 border-t-psu-maroon`}
        aria-hidden="true"
      />
      {label && <span className="text-sm text-text-muted">{label}</span>}
    </span>
  );
}

/** Centered spinner with a label, used for full-panel loading. */
export function LoadingState({ label = "Loading…", className = "" }) {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 py-16 text-center ${className}`}
      role="status"
      aria-live="polite"
    >
      <span className="h-8 w-8 animate-spin rounded-full border-[3px] border-psu-maroon/15 border-t-psu-maroon" aria-hidden="true" />
      <p className="text-sm font-medium text-text-muted">{label}</p>
    </div>
  );
}

/** Stable-height skeleton rows; keeps layout from jumping while data loads. */
export function SkeletonList({ rows = 3, className = "h-20" }) {
  return (
    <div className="space-y-3" role="status" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className={`${className} animate-pulse rounded-xl border border-border-subtle bg-bg-panel`}
        >
          <div className="flex h-full flex-col justify-center gap-2 px-5">
            <div className="h-3.5 w-1/3 rounded bg-border-subtle" />
            <div className="h-3 w-1/2 rounded bg-border-subtle" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function EmptyState({ icon = "inbox", title, message, action, className = "" }) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-xl border border-dashed border-border-strong bg-bg-panel px-6 py-14 text-center ${className}`}
    >
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-psu-maroon/[0.07] text-text-brand">
        <StateIcon name={icon} />
      </div>
      <h3 className="text-base font-semibold text-text-main">{title}</h3>
      {message && <p className="mt-1 max-w-md text-sm text-text-muted">{message}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

/**
 * Error panel for a failed request. Pass the thrown error; the copy is derived
 * from its status so "server down", "forbidden" and "not found" read differently.
 */
export function ErrorState({ error, resource, onRetry, title, message, action, className = "" }) {
  const info = describeApiError(error, { resource });
  const canRetry = onRetry && !["forbidden", "not_found", "unauthorized"].includes(info.kind);

  return (
    <div
      role="alert"
      className={`flex flex-col items-center justify-center rounded-xl border border-psu-red/20 bg-psu-red/[0.04] px-6 py-12 text-center ${className}`}
    >
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-psu-red/10 text-text-rose">
        <StateIcon name={KIND_ICON[info.kind] || "alert"} />
      </div>
      <h3 className="text-base font-semibold text-text-main">{title || info.title}</h3>
      <p className="mt-1 max-w-md text-sm text-text-muted">{message || info.message}</p>
      {(canRetry || action) && (
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          {canRetry && (
            <button type="button" onClick={onRetry} className="btn-secondary">
              Try again
            </button>
          )}
          {action}
        </div>
      )}
    </div>
  );
}

const ALERT_TONES = {
  error: "border-psu-red/25 bg-psu-red/[0.06] text-text-rose",
  success: "border-emerald-600/25 bg-emerald-600/[0.07] text-text-emerald",
  info: "border-psu-gold/40 bg-selected text-text-main",
  warning: "border-psu-gold/60 bg-psu-gold/[0.14] text-text-amber",
};

/**
 * Calls `onDone` once `ms` have passed, not counting time spent paused, so a
 * message being read (pointer over it) or copied (focus inside it) stays put.
 */
function useDismissTimer(ms, paused, onDone) {
  const remaining = useRef(ms);
  const onDoneRef = useRef(onDone);
  useEffect(() => {
    onDoneRef.current = onDone;
  });
  useEffect(() => {
    if (!ms || paused) return undefined;
    const startedAt = Date.now();
    const timer = window.setTimeout(() => onDoneRef.current?.(), remaining.current);
    return () => {
      window.clearTimeout(timer);
      remaining.current = Math.max(0, remaining.current - (Date.now() - startedAt));
    };
  }, [ms, paused]);
}

/**
 * Non-blocking inline message (form result, page notice).
 * With `autoDismissMs` (and `onDismiss`) it closes itself after that long,
 * pausing while hovered or focused. Give each new message its own `key` so it
 * starts with a full timer.
 */
export function InlineAlert({ tone = "info", children, onDismiss, autoDismissMs = 0, className = "" }) {
  const [isHovered, setIsHovered] = useState(false);
  const [hasFocus, setHasFocus] = useState(false);
  const timed = Boolean(onDismiss && autoDismissMs > 0);
  useDismissTimer(timed ? autoDismissMs : 0, isHovered || hasFocus, onDismiss);
  const pauseHandlers = timed
    ? {
        onMouseEnter: () => setIsHovered(true),
        onMouseLeave: () => setIsHovered(false),
        onFocus: () => setHasFocus(true),
        onBlur: (event) => {
          if (!event.currentTarget.contains(event.relatedTarget)) setHasFocus(false);
        },
      }
    : {};

  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      aria-live="polite"
      className={`flex items-start justify-between gap-3 rounded-lg border px-4 py-3 text-sm ${ALERT_TONES[tone] || ALERT_TONES.info} ${className}`}
      {...pauseHandlers}
    >
      <div className="min-w-0 flex-1">{children}</div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 rounded p-0.5 opacity-70 transition hover:opacity-100 focus-visible:outline-2 focus-visible:outline-offset-2"
          aria-label="Dismiss message"
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
        </button>
      )}
    </div>
  );
}

/** Small field-level validation message, associated via aria-describedby. */
export function FieldError({ id, children }) {
  if (!children) return null;
  return (
    <p id={id} className="mt-1.5 text-xs font-medium text-text-rose">
      {children}
    </p>
  );
}

/** Consistent page title block used across student / instructor pages. */
export function PageHeader({ eyebrow, title, description, icon, actions }) {
  return (
    <header className="mb-6 flex flex-col gap-4 border-b border-border-subtle pb-5 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        {eyebrow && (
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-widest text-text-brand">{eyebrow}</p>
        )}
        <h1 className="flex items-center gap-2.5 text-2xl font-bold tracking-tight text-text-main">
          {icon}
          <span className="min-w-0 break-words">{title}</span>
        </h1>
        {description && <p className="mt-1 text-sm text-text-muted">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}
