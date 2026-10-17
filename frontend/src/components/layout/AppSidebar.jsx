import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthContext";
import SignOutModal from "./SignOutModal";

const ICONS = {
  grid: <><rect x="1" y="1" width="6" height="6" rx="1" /><rect x="9" y="1" width="6" height="6" rx="1" /><rect x="1" y="9" width="6" height="6" rx="1" /><rect x="9" y="9" width="6" height="6" rx="1" /></>,
  list: <path d="M3 4h10M3 8h10M3 12h10" />,
  code: <path d="M5 5L2 8l3 3M11 5l3 3-3 3M9 3l-2 10" />,
  book: <path d="M2 3h4a2 2 0 012 2v9a2 2 0 00-2-2H2V3zM14 3h-4a2 2 0 00-2 2v9a2 2 0 012-2h4V3z" />,
  terminal: <path d="M2 3l5 5-5 5M9 13h5" />,
  chart: <path d="M2 12l4-4 3 3 5-6" />,
  file: <><rect x="3" y="1" width="10" height="14" rx="1.5" /><path d="M6 5h4M6 8h4M6 11h2" /></>,
  bell: <path d="M8 1.5a3.5 3.5 0 00-3.5 3.5v2.793l-.707.707A1 1 0 003.5 10h9a1 1 0 00.707-1.707l-.707-.707V5A3.5 3.5 0 008 1.5zM6.5 12a1.5 1.5 0 003 0" />,
  shield: <path d="M8 1.5L2.5 4v4.5c0 3.5 2.5 6 5.5 6.5 3-.5 5.5-3 5.5-6.5V4L8 1.5z" />,
  settings: <><circle cx="8" cy="8" r="2.5" /><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M3.05 12.95l1.41-1.41M11.54 4.46l1.41-1.41" /></>,
  logout: <path d="M6 2H3a1 1 0 00-1 1v10a1 1 0 001 1h3M10 11l3-3-3-3M13 8H6" />,
  check: <><rect x="2" y="2" width="12" height="12" rx="2" /><path d="M5 8l2 2 4-4" /></>,
  monitor: <><rect x="1.5" y="2.5" width="13" height="9" rx="1.5" /><path d="M5.5 14.5h5M8 11.5v3" /></>,
  plus: <path d="M8 3v10M3 8h10" />,
};

function NavIcon({ name, size = 16 }) {
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
      {ICONS[name] ?? null}
    </svg>
  );
}

const COLLAPSE_KEY = "pamsu_sidebar_collapsed";
const NARROW_QUERY = "(max-width: 1023px)";

function readStoredCollapse() {
  try {
    if (window.matchMedia(NARROW_QUERY).matches) return true;
    return localStorage.getItem(COLLAPSE_KEY) === "true";
  } catch {
    return false;
  }
}

/**
 * Shared navigation rail for student and instructor areas.
 * `sections`: [{ label, links: [{ icon, label, path, end }] }]
 * `badges`:   { [path]: number } — small counters next to a link
 * `renderThemeControl`: optional (collapsed) => node shown in the profile area
 *             (student and instructor sidebars; the admin area stays light-only).
 */
export default function AppSidebar({ sections, ariaLabel, roleLabel, badges = {}, renderThemeControl }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [isSignOutOpen, setIsSignOutOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(readStoredCollapse);

  // Narrow screens always start collapsed so content keeps usable width.
  useEffect(() => {
    const query = window.matchMedia(NARROW_QUERY);
    const handleChange = (event) => {
      if (event.matches) setIsCollapsed(true);
    };
    query.addEventListener("change", handleChange);
    return () => query.removeEventListener("change", handleChange);
  }, []);

  const toggleCollapse = () => {
    setIsCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(COLLAPSE_KEY, String(next));
      } catch {
        // Preference persistence is optional.
      }
      return next;
    });
  };

  const name = user?.name || "Account";
  const initials =
    name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("") || "?";

  const handleConfirmSignOut = () => {
    setIsSignOutOpen(false);
    logout();
    navigate("/login", { replace: true });
  };

  const itemBase = `flex w-full items-center gap-2.5 rounded-lg text-[13px] transition-colors duration-150 ${
    isCollapsed ? "justify-center px-0 py-2.5" : "px-2.5 py-2"
  }`;

  return (
    <>
      <aside
        className={`flex h-full shrink-0 flex-col overflow-hidden border-r border-border-subtle bg-bg-panel pb-3 pt-3.5 transition-[width] duration-200 ${
          isCollapsed ? "w-[60px] px-2" : "w-[232px] px-3"
        }`}
      >
        <div className="mb-3 shrink-0 border-b border-border-subtle pb-3">
          <div className={`flex items-center ${isCollapsed ? "flex-col gap-2" : "justify-between gap-2 px-0.5"}`}>
            <div className="flex min-w-0 items-center gap-2.5">
              <img
                src="/school_logo.png"
                alt="Pampanga State University logo"
                className="h-8 w-8 shrink-0 object-contain"
              />
              {!isCollapsed && (
                <div className="min-w-0 leading-tight">
                  <p className="truncate text-sm font-bold tracking-tight text-text-main">PAMSU IDE</p>
                  <p className="truncate text-[10px] font-semibold uppercase tracking-wider text-text-brand">{roleLabel}</p>
                </div>
              )}
            </div>
            <button
              type="button"
              onClick={toggleCollapse}
              aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              aria-expanded={!isCollapsed}
              title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-border-subtle text-text-muted transition-colors hover:bg-bg-alt hover:text-text-main"
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true" className={isCollapsed ? "rotate-180" : ""}>
                <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        </div>

        <nav
          aria-label={ariaLabel}
          className="min-h-0 flex-1 space-y-4 overflow-y-auto [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        >
          {sections.map((section) => (
            <section key={section.label}>
              {isCollapsed ? (
                <div className="mx-2 my-2 h-px bg-border-subtle" />
              ) : (
                <h2 className="mb-1 px-2.5 text-[10px] font-semibold uppercase tracking-widest text-text-muted">
                  {section.label}
                </h2>
              )}
              <ul className="space-y-0.5">
                {section.links.map((link) => {
                  const badge = badges[link.path] || 0;
                  return (
                    <li key={link.path}>
                      <NavLink
                        to={link.path}
                        end={link.end}
                        title={isCollapsed ? link.label : undefined}
                        aria-label={isCollapsed ? link.label : undefined}
                        className={({ isActive }) =>
                          `${itemBase} ${
                            isActive
                              ? "bg-selected font-semibold text-text-brand shadow-[inset_3px_0_0_var(--color-psu-gold)]"
                              : "font-medium text-text-muted hover:bg-bg-alt hover:text-text-main"
                          }`
                        }
                      >
                        <span className="relative">
                          <NavIcon name={link.icon} />
                          {isCollapsed && badge > 0 && (
                            <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-psu-maroon" aria-hidden="true" />
                          )}
                        </span>
                        {!isCollapsed && <span className="min-w-0 flex-1 truncate">{link.label}</span>}
                        {!isCollapsed && badge > 0 && (
                          <span className="rounded-full bg-psu-maroon px-1.5 py-0.5 text-[10px] font-semibold text-white">
                            {badge}
                            <span className="sr-only"> pending</span>
                          </span>
                        )}
                      </NavLink>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </nav>

        <div className="mt-auto shrink-0 space-y-1 border-t border-border-subtle pt-3">
          <div
            className={`flex items-center gap-2.5 ${isCollapsed ? "justify-center" : "px-1.5"}`}
            title={isCollapsed ? name : undefined}
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-psu-maroon text-xs font-bold text-white">
              {initials}
            </div>
            {!isCollapsed && (
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-semibold text-text-main">{name}</p>
                <p className="truncate text-[11px] text-text-muted">{user?.email || roleLabel}</p>
              </div>
            )}
          </div>
          {renderThemeControl?.(isCollapsed)}
          <button
            type="button"
            onClick={() => setIsSignOutOpen(true)}
            title={isCollapsed ? "Sign out" : undefined}
            aria-label={isCollapsed ? "Sign out" : undefined}
            className={`${itemBase} font-medium text-text-muted hover:bg-psu-red/[0.06] hover:text-text-rose`}
          >
            <NavIcon name="logout" />
            {!isCollapsed && <span>Sign out</span>}
          </button>
        </div>
      </aside>

      <SignOutModal
        isOpen={isSignOutOpen}
        onClose={() => setIsSignOutOpen(false)}
        onConfirm={handleConfirmSignOut}
      />
    </>
  );
}
