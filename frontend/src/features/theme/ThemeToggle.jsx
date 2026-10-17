import { useTheme } from "./ThemeContext";

const OPTIONS = [
  { id: "light", label: "Light" },
  { id: "dark", label: "Dark" },
  { id: "system", label: "System" },
];

const NEXT = { system: "light", light: "dark", dark: "system" };

function ThemeIcon({ name, size = 14 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.4"
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
 * Student theme control for the sidebar profile area.
 * Expanded: a 3-way radio group (Light / Dark / System) with a status line.
 * Collapsed: one button that cycles System → Light → Dark. Both have a fixed
 * height so changing the selection never shifts the layout.
 */
export default function ThemeToggle({ collapsed = false }) {
  const { preference, effectiveTheme, setPreference } = useTheme();
  const summary = describe(preference, effectiveTheme);

  if (collapsed) {
    const next = NEXT[preference];
    const nextLabel = OPTIONS.find((option) => option.id === next).label;
    return (
      <button
        type="button"
        onClick={() => setPreference(next)}
        title={`Theme: ${summary}. Switch to ${nextLabel}.`}
        aria-label={`Theme: ${summary}. Switch to ${nextLabel}.`}
        className="flex h-9 w-full items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-bg-alt hover:text-text-main"
      >
        <ThemeIcon name={preference === "system" ? "system" : preference} size={16} />
      </button>
    );
  }

  return (
    <div className="px-1.5">
      <div
        role="radiogroup"
        aria-label="Color theme"
        className="grid h-8 grid-cols-3 gap-0.5 rounded-lg border border-border-subtle bg-bg-alt p-0.5"
      >
        {OPTIONS.map((option) => {
          const selected = preference === option.id;
          return (
            <button
              key={option.id}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => setPreference(option.id)}
              className={`flex items-center justify-center gap-1 rounded-md text-[11px] font-semibold transition-colors ${
                selected
                  ? "bg-bg-panel text-text-brand shadow-sm"
                  : "text-text-muted hover:text-text-main"
              }`}
            >
              <ThemeIcon name={option.id} size={12} />
              {option.label}
            </button>
          );
        })}
      </div>
      <p className="mt-1 h-4 truncate text-[10px] text-text-muted" role="status" aria-live="polite">
        {preference === "system" ? `Following device · ${effectiveTheme}` : `${summary} · set manually`}
      </p>
    </div>
  );
}
