import { Link } from "react-router-dom";

import Icon from "./Icon";

const TONES = {
  neutral: { tile: "border-border-subtle bg-bg-alt/60", chip: "bg-bg-panel text-text-muted ring-1 ring-inset ring-border-subtle", status: "text-text-muted", dot: "bg-text-muted" },
  attention: { tile: "border-psu-gold/40 bg-psu-gold/[0.07]", chip: "bg-psu-gold/20 text-text-amber", status: "text-text-amber", dot: "bg-psu-gold" },
  success: { tile: "border-emerald-600/25 bg-emerald-600/[0.06]", chip: "bg-emerald-600/15 text-text-emerald", status: "text-text-emerald", dot: "bg-emerald-600" },
  danger: { tile: "border-psu-red/30 bg-psu-red/[0.06]", chip: "bg-psu-red/15 text-text-rose", status: "text-text-rose", dot: "bg-psu-red" },
};

const SIZES = {
  md: { tile: "p-4", value: "mt-3 text-3xl", unit: "text-base" },
  sm: { tile: "p-3", value: "mt-2 text-xl", unit: "text-sm" },
};

/**
 * Dashboard stat tile: muted uppercase label, large number, optional icon,
 * meter and caption. It renders <dt>/<dd>, so place it inside a <dl>.
 *
 * - tone: neutral | attention (gold) | success | danger. A soft tint only; the
 *   number and label always carry the meaning.
 * - status: short words for the tone ("Above typical"), shown under the number
 *   with a dot in the tone's color, so the state never depends on color alone.
 * - meter: 0–100, draws a thin bar under the number.
 * - to: makes the whole tile a link (the label is the link text).
 * - value null/undefined shows "—".
 *
 * Narrow tiles (phones, packed grids) let the label wrap to two lines and hide
 * the icon; from 8.25rem of content the label fits on one line beside it.
 */
export default function StatTile({ label, icon, value, unit, caption, status, meter, tone = "neutral", size = "md", to, className = "" }) {
  const isEmpty = value === null || value === undefined;
  const palette = TONES[tone] || TONES.neutral;
  const scale = SIZES[size] || SIZES.md;
  const linkClass = to
    ? "relative transition-[border-color,box-shadow] hover:border-psu-maroon/30 hover:shadow-md has-[a:focus-visible]:ring-2 has-[a:focus-visible]:ring-border-focus"
    : "";

  return (
    <div className={`@container flex flex-col rounded-xl border transition-colors ${palette.tile} ${scale.tile} ${linkClass} ${className}`}>
      <dt className="flex min-h-[2.75em] items-start justify-between gap-2 text-[11px] font-semibold uppercase leading-snug tracking-wider text-text-muted @min-[8.25rem]:min-h-7 @min-[8.25rem]:items-center">
        <span className="min-w-0 @min-[8.25rem]:truncate">
          {to ? (
            // The link's ::after covers the tile, so the whole tile is clickable.
            <Link to={to} className="after:absolute after:inset-0 after:rounded-xl focus-visible:outline-none">
              {label}
            </Link>
          ) : (
            label
          )}
        </span>
        {icon && (
          <span className={`hidden h-7 w-7 shrink-0 place-items-center rounded-lg @min-[8.25rem]:grid ${palette.chip}`}>
            <Icon name={icon} className="h-4 w-4" />
          </span>
        )}
      </dt>
      <dd className={`${scale.value} font-semibold leading-none tracking-tight tabular-nums ${isEmpty ? "text-text-muted" : "text-text-main"}`}>
        {isEmpty ? "—" : value}
        {!isEmpty && unit && <span className={`ml-0.5 font-medium text-text-muted ${scale.unit}`}>{unit}</span>}
      </dd>
      {status && (
        <dd className={`mt-2 flex items-center gap-1.5 text-[11px] font-semibold leading-snug ${palette.status}`}>
          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${palette.dot}`} aria-hidden="true" />
          {status}
        </dd>
      )}
      {typeof meter === "number" && (
        <dd className="mt-3 h-1.5 overflow-hidden rounded-full bg-border-subtle" aria-hidden="true">
          <span className="block h-full rounded-full bg-psu-maroon" style={{ width: `${Math.min(100, Math.max(0, meter))}%` }} />
        </dd>
      )}
      {caption && <dd className="mt-2 text-xs leading-snug text-text-muted">{caption}</dd>}
    </div>
  );
}
