import { useId } from "react";

import { AST_STRICTNESS_LEVELS } from "../../utils/astRules";

/** Three rising bars; `rank` of them are filled. */
function LevelBars({ rank, active }) {
  return (
    <span
      className={`flex h-9 w-9 items-end justify-center gap-[3px] rounded-lg pb-2.5 transition-colors ${
        active ? "bg-psu-maroon/[0.1]" : "bg-bg-alt"
      }`}
      aria-hidden="true"
    >
      {["h-2", "h-3", "h-4"].map((height, index) => (
        <span
          key={height}
          className={`w-1.5 rounded-full transition-colors ${height} ${
            index < rank ? (active ? "bg-psu-maroon" : "bg-text-muted") : "bg-border-strong"
          }`}
        />
      ))}
    </span>
  );
}

function SelectedMark({ checked }) {
  return (
    <span
      className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
        checked ? "border-psu-maroon bg-psu-maroon text-white" : "border-border-strong bg-bg-panel"
      }`}
      aria-hidden="true"
    >
      {checked && (
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
          <path d="M2.5 6.2 5 8.5l4.5-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
    </span>
  );
}

/**
 * AST strictness as selectable cards (a radio group: arrow keys move between
 * levels). Used by the MIS default and each instructor's own preference.
 */
export default function StrictnessPicker({ name, value, onChange, legend, description, disabled = false }) {
  const baseId = useId();
  const descriptionId = `${baseId}-description`;

  return (
    <fieldset disabled={disabled} aria-describedby={description ? descriptionId : undefined}>
      <legend className="text-sm font-semibold text-text-main">{legend}</legend>
      {description && (
        <p id={descriptionId} className="mt-0.5 text-sm text-text-muted">
          {description}
        </p>
      )}
      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        {AST_STRICTNESS_LEVELS.map((level) => {
          const checked = value === level.value;
          return (
            <label
              key={level.value}
              className={`relative flex cursor-pointer flex-col rounded-xl border p-4 transition-[border-color,background-color,box-shadow] has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-border-focus has-[:focus-visible]:ring-offset-2 has-[:disabled]:cursor-not-allowed has-[:disabled]:opacity-60 ${
                checked
                  ? "border-psu-maroon bg-selected shadow-sm ring-1 ring-psu-maroon"
                  : "border-border-strong bg-bg-panel hover:border-psu-maroon/40 hover:bg-bg-alt/40"
              }`}
            >
              <input
                type="radio"
                name={name}
                value={level.value}
                checked={checked}
                onChange={() => onChange(level.value)}
                aria-labelledby={`${baseId}-${level.value}-label`}
                aria-describedby={`${baseId}-${level.value}-help`}
                className="sr-only"
              />
              <span className="flex items-start justify-between gap-3">
                <LevelBars rank={level.rank} active={checked} />
                <SelectedMark checked={checked} />
              </span>
              <span className="mt-3 flex flex-wrap items-center gap-2">
                <span id={`${baseId}-${level.value}-label`} className="text-sm font-semibold text-text-main">
                  {level.label}
                </span>
                {level.badge && <span className="badge badge-gold">{level.badge}</span>}
              </span>
              <span id={`${baseId}-${level.value}-help`} className="mt-1 text-xs leading-relaxed text-text-muted">
                {level.badge && <span className="sr-only">{level.badge}. </span>}
                {level.description}
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
