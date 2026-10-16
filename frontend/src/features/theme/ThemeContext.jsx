import { createContext, useContext, useEffect } from "react";

const ThemeContext = createContext(undefined);

/**
 * The application chrome ships a single light PSU theme. The previous
 * light/dark switch only re-skinned part of the UI, so it was retired.
 * The code editor keeps its own theme preference (see Workspace).
 */
const THEME_VALUE = Object.freeze({ theme: "light", resolvedTheme: "light", setTheme: () => {} });

export function ThemeProvider({ children }) {
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove("dark");
    root.classList.add("light");
    try {
      localStorage.removeItem("pamsu_theme");
    } catch {
      // Storage may be unavailable; nothing to clean up.
    }
  }, []);

  return <ThemeContext.Provider value={THEME_VALUE}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
