const STATUS_CONFIG = {
  active: {
    label: "Session active",
    dotClass: "bg-[#22c55e]",
    textClass: "text-[#22c55e]",
  },
  expired: {
    label: "Session expired",
    dotClass: "bg-[#ef4444]",
    textClass: "text-[#ef4444]",
  },
  disconnected: {
    label: "Server disconnected",
    dotClass: "bg-[#ef4444]",
    textClass: "text-[#ef4444]",
  },
  connecting: {
    label: "Connecting",
    dotClass: "bg-[#f59e0b] animate-pulse",
    textClass: "text-[#f59e0b]",
  },
  unknown: {
    label: "Session status unavailable",
    dotClass: "bg-white/30",
    textClass: "text-text-muted",
  },
};

export default function Statusbar({
  sessionStatus = "unknown",
  courseCode = "",
  courseName = "",
  studentName = "",
  pythonVersion = "Python 3",
}) {
  const status =
    STATUS_CONFIG[sessionStatus] ?? STATUS_CONFIG.unknown;

  const courseLabel = [courseCode, courseName]
    .filter(Boolean)
    .join(" — ");

  return (
    <footer
      className="flex h-9 shrink-0 items-center justify-between gap-4 border-t border-border-subtle bg-bg-base px-4"
      aria-label="Workspace status"
    >
      <div
        className="flex min-w-0 items-center gap-2"
        role="status"
        aria-live="polite"
      >
        <span
          className={`h-1.5 w-1.5 shrink-0 rounded-full ${status.dotClass}`}
          aria-hidden="true"
        />

        <span
          className={`truncate font-mono text-[10px] ${status.textClass}`}
        >
          {status.label}
          {courseLabel ? ` · ${courseLabel}` : ""}
        </span>
      </div>

      <span className="shrink-0 select-none font-mono text-[10px] text-white/25">
        {pythonVersion}
        {studentName ? ` · ${studentName}` : ""}
      </span>
    </footer>
  );
}
