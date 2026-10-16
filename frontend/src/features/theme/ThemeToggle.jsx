/**
 * Light / dark switch for the code editor surface only.
 * Values are Monaco theme names ("light" | "vs-dark").
 */
export function ThemeToggle({ className = "", value, onChange }) {
  const isDark = value === "vs-dark";

  const options = [
    { id: "light", label: "Light editor theme", icon: "sun" },
    { id: "vs-dark", label: "Dark editor theme", icon: "moon" },
  ];

  return (
    <div
      role="radiogroup"
      aria-label="Editor theme"
      className={`flex items-center rounded-full border border-border-subtle bg-bg-alt p-0.5 ${className}`}
    >
      {options.map((option) => {
        const selected = option.id === "vs-dark" ? isDark : !isDark;
        return (
          <button
            key={option.id}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange?.(option.id)}
            title={option.label}
            aria-label={option.label}
            className={`flex items-center justify-center rounded-full p-1.5 transition-colors ${
              selected ? "bg-bg-panel text-psu-maroon shadow-sm" : "text-text-muted hover:text-text-main"
            }`}
          >
            {option.icon === "sun" ? (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="5" />
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
              </svg>
            ) : (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>
        );
      })}
    </div>
  );
}
