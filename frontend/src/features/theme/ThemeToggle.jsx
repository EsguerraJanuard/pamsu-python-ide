import { useId } from "react";
import Tooltip from "../../components/ui/Tooltip";
import { useTheme } from "./ThemeContext";

const OPTIONS = [
  { id: "light", label: "Light", action: "Use light theme" },
  { id: "dark", label: "Dark", action: "Use dark theme" },
  { id: "system", label: "System", action: "Use system theme" },
];

const NEXT = { system: "light", light: "dark", dark: "system" };

function ThemeIcon({ name, size = 14, strokeWidth = 1.4 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="shrink-0"
    >
      {name === "light" && (
        <>
          <circle cx="8" cy="8" r="2.75" />
          <path d="M8 1.5v1.5M8 13v1.5M1.5 8H3M13 8h1.5M3.4 3.4l1.05 1.05M11.55 11.55l1.05 1.05M3.4 12.6l1.05-1.05M11.55 4.45l1.05-1.05" />
        </>
      )}
      {name === "dark" && <path d="M13.5 9.6A5.7 5.7 0 016.4 2.5a5.7 5.7 0 107.1 7.1z" />}
      {name === "system" && (
        <>
          <rect x="1.5" y="2.5" width="13" height="9" rx="1.5" />
          <path d="M5.5 14.5h5M8 11.5v3" />
        </>
      )}
    </svg>
  );
}

const describe = (preference, effectiveTheme) =>
  preference === "system"
    ? `System (currently ${effectiveTheme})`
    : preference === "dark"
      ? "Dark"
      : "Light";

/**
 * Theme control for the sidebar profile area (student and instructor).
 * Expanded: a compact icon toolbar (Light / Dark / System toggle buttons,
 * `aria-pressed`), with tooltips and an off-screen status for assistive tech.
 * Collapsed: one icon button that cycles System → Light → Dark.
 * Both keep a fixed size so changing the selection never shifts the layout.
 */
export default function ThemeToggle({ collapsed = false, tooltipSide = "right" }) {
  const { preference, effectiveTheme, setPreference } = useTheme();
  const systemDescriptionId = useId();
  const summary = describe(preference, effectiveTheme);

  if (collapsed) {
    const nextLabel = OPTIONS.find((option) => option.id === NEXT[preference]).label;
    const label = `Theme: ${summary}. Switch to ${nextLabel}.`;
    const current = preference === "system" ? `System (${effectiveTheme})` : summary;
    return (
      <Tooltip content={`Theme: ${current} · next: ${nextLabel}`} side={tooltipSide}>
        <button
          type="button"
          onClick={() => setPreference(NEXT[preference])}
          aria-label={label}
          className="flex h-9 w-full items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-bg-alt hover:text-text-main"
        >
          <ThemeIcon name={preference} size={16} />
        </button>
      </Tooltip>
    );
  }

  const systemSelected = preference === "system";
  const systemNote = systemSelected
    ? `Follows your device setting (currently ${effectiveTheme})`
    : "Follows your device's light or dark setting";

  return (
    <div role="group" aria-label="Color theme" className="flex h-8 items-center gap-0.5 rounded-lg bg-bg-alt p-0.5">
      {OPTIONS.map((option) => {
        const selected = preference === option.id;
        const isSystem = option.id === "system";
        return (
          <Tooltip key={option.id} content={isSystem && selected ? `${option.action} (device: ${effectiveTheme})` : option.action}>
            <button
              type="button"
              aria-label={option.action}
              aria-pressed={selected}
              aria-describedby={isSystem ? systemDescriptionId : undefined}
              onClick={() => setPreference(option.id)}
              className={`flex h-7 w-8 items-center justify-center rounded-md transition-colors ${
                selected
                  ? "bg-bg-panel text-text-brand shadow-[var(--shadow-card),inset_0_-2px_0_var(--color-psu-gold)]"
                  : "text-text-muted hover:bg-bg-panel/60 hover:text-text-main"
              }`}
            >
              <ThemeIcon name={option.id} size={15} strokeWidth={selected ? 1.7 : 1.4} />
            </button>
          </Tooltip>
        );
      })}
      <span id={systemDescriptionId} className="sr-only">
        {systemNote}
      </span>
      <span className="sr-only" role="status" aria-live="polite">
        {systemSelected ? `Theme: ${summary}` : `Theme: ${summary}, set manually`}
      </span>
    </div>
  );
}
