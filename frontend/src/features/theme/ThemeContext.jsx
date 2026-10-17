import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useMemo, useState, useSyncExternalStore } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import {
  applyThemeToDocument,
  normalizePreference,
  readPreference,
  resolveTheme,
  storageKeyFor,
  writePreference,
} from "./themeStorage";

const ThemeContext = createContext(undefined);

const DARK_QUERY = "(prefers-color-scheme: dark)";

function subscribeToSystemTheme(onChange) {
  const query = window.matchMedia(DARK_QUERY);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}
const getSystemPrefersDark = () => window.matchMedia(DARK_QUERY).matches;
const getServerSnapshot = () => false;

const isStudentPath = (pathname) => pathname === "/student" || pathname.startsWith("/student/");

/**
 * Single source of truth for the student theme.
 *
 * Dark mode is active only while an authenticated student is on a /student
 * route. Everywhere else (login, forgot password, instructor, admin,
 * unauthorized, 404, logged-out) the document is forced back to light, even if
 * a dark preference exists in storage. The preference itself is stored per
 * account (see themeStorage.js); `system` follows prefers-color-scheme live.
 */
export function StudentThemeProvider({ children }) {
  const { isAuthenticated, role, user } = useAuth();
  const { pathname } = useLocation();

  const userId = user?.user_id ?? null;
  const enabled = isAuthenticated && role === "student" && userId != null && isStudentPath(pathname);

  // Preference is tied to the account it was loaded for; switching accounts
  // re-reads storage instead of carrying the previous student's choice over.
  const [stored, setStored] = useState(() => ({ userId, preference: readPreference(userId) }));
  if (stored.userId !== userId) {
    setStored({ userId, preference: readPreference(userId) });
  }
  const preference = stored.userId === userId ? stored.preference : readPreference(userId);

  const systemPrefersDark = useSyncExternalStore(subscribeToSystemTheme, getSystemPrefersDark, getServerSnapshot);

  const effectiveTheme = enabled ? resolveTheme(preference, systemPrefersDark) : "light";

  useLayoutEffect(() => {
    applyThemeToDocument(effectiveTheme);
  }, [effectiveTheme]);

  // Keep other tabs of the same account in step with this one.
  useEffect(() => {
    if (userId == null) return undefined;
    const key = storageKeyFor(userId);
    const handleStorage = (event) => {
      if (event.key === key || event.key === null) {
        setStored({ userId, preference: readPreference(userId) });
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [userId]);

  const setPreference = useCallback(
    (next) => {
      const normalized = normalizePreference(next);
      writePreference(userId, normalized);
      setStored({ userId, preference: normalized });
    },
    [userId],
  );

  const value = useMemo(
    () => ({
      enabled,
      preference,
      setPreference,
      effectiveTheme,
      // Aliases kept for the original context shape.
      theme: preference,
      setTheme: setPreference,
      resolvedTheme: effectiveTheme,
    }),
    [enabled, preference, setPreference, effectiveTheme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a StudentThemeProvider");
  }
  return context;
}
