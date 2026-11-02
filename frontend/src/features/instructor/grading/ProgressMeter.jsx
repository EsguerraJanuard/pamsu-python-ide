/**
 * Labelled progress bar for the Grading Bench lists ("Reviewed · 12 of 30").
 * `value` and `max` are counts; nothing is drawn while `max` is unknown.
 */
export default function ProgressMeter({ label, value, max, className = "" }) {
  if (typeof max !== "number" || typeof value !== "number") return null;
  const percent = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0;
  return (
    <div className={className}>
      <div className="mb-1.5 flex items-baseline justify-between gap-3 text-xs">
        <span className="text-text-muted">{label}</span>
        <span className="font-medium tabular-nums text-text-main">
          {value} <span className="text-text-muted">of {max}</span>
        </span>
      </div>
      <div
        className="h-1.5 overflow-hidden rounded-full bg-border-subtle"
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={value}
      >
        <div className="h-full rounded-full bg-psu-maroon transition-[width] duration-500" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
