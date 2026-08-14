import { useTheme } from "./ThemeContext";

export function ThemeToggle({ className = "", value, onChange }) {
  const context = useTheme();
  
  const activeTheme = value !== undefined ? value : context?.theme || "dark";
  
  // Enforce 2-state binary switch (fallback system to dark or matchMedia)
  const isDark = activeTheme === "dark" || activeTheme === "vs-dark" || (activeTheme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);

  const handleSetLight = () => {
    if (onChange) onChange("light");
    else context?.setTheme("light");
  };

  const handleSetDark = () => {
    if (onChange) onChange("vs-dark");
    else context?.setTheme("dark");
  };

  return (
    <div className={`flex items-center rounded-full border border-border-subtle bg-bg-glass p-0.5 shadow-inner ${className}`}>
      <button
        type="button"
        onClick={handleSetLight}
        className={`flex items-center justify-center rounded-full p-1.5 transition-all ${
          !isDark 
            ? "bg-white text-emerald-600 shadow-sm" 
            : "text-text-muted hover:text-text-main"
        }`}
        title="Light Mode"
        aria-label="Switch to light theme"
        aria-pressed={!isDark}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="5"></circle>
          <line x1="12" y1="1" x2="12" y2="3"></line>
          <line x1="12" y1="21" x2="12" y2="23"></line>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
          <line x1="1" y1="12" x2="3" y2="12"></line>
          <line x1="21" y1="12" x2="23" y2="12"></line>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
        </svg>
      </button>
      <button
        type="button"
        onClick={handleSetDark}
        className={`flex items-center justify-center rounded-full p-1.5 transition-all ${
          isDark 
            ? "bg-slate-800 text-emerald-400 shadow-sm border border-white/10" 
            : "text-text-muted hover:text-text-main"
        }`}
        title="Dark Mode"
        aria-label="Switch to dark theme"
        aria-pressed={isDark}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
        </svg>
      </button>
    </div>
  );
}
