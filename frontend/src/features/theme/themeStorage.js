/**
 * Theme preference storage for the themed areas (student and instructor).
 *
 * The preference is "system" | "light" | "dark" and is stored per account
 * (keyed by user_id) so one user's choice never applies to another account
 * (or role) that signs in on the same browser. Only the preference string is stored; no
 * tokens or account details. index.html repeats the read logic for pre-paint
 * initialisation — keep the key format in sync.
 */
export const THEME_PREFERENCES = Object.freeze(["system", "light", "dark"]);

const KEY_PREFIX = "pamsu_theme_pref_v1:";

export const storageKeyFor = (userId) => `${KEY_PREFIX}${userId}`;

export const normalizePreference = (value) =>
  value === "light" || value === "dark" ? value : "system";

export function readPreference(userId) {
  if (userId == null) return "system";
  try {
    return normalizePreference(localStorage.getItem(storageKeyFor(userId)));
  } catch {
    return "system";
  }
}

export function writePreference(userId, preference) {
  if (userId == null) return;
  try {
    if (preference === "system") {
      localStorage.removeItem(storageKeyFor(userId));
    } else {
      localStorage.setItem(storageKeyFor(userId), preference);
    }
  } catch {
    // The theme still applies for this session when storage is unavailable.
  }
}

export const resolveTheme = (preference, systemPrefersDark) => {
  if (preference === "light" || preference === "dark") return preference;
  return systemPrefersDark ? "dark" : "light";
};

/** Applies the effective theme to <html>, the one place Tailwind and the CSS tokens both read. */
export function applyThemeToDocument(theme) {
  const root = document.documentElement;
  root.classList.remove("light", "dark");
  root.classList.add(theme);
  root.setAttribute("data-theme", theme);
  root.style.colorScheme = theme;
}
