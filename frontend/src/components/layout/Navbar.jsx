import { useState, useEffect } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthContext";
import SignOutModal from "./SignOutModal";
import { ThemeToggle } from "../../features/theme/ThemeToggle";

const INSTRUCTOR_NAV = [
  {
    label: "MANAGEMENT",
    links: [
      {
        icon: "grid",
        label: "Overview",
        path: "/instructor/dashboard",
        end: true,
      },
      {
        icon: "book",
        label: "Class Management",
        path: "/instructor/classes",
      },
      {
        icon: "code",
        label: "Activity Authoring",
        path: "/instructor/activities",
      },
    ],
  },
  {
    label: "MONITORING & GRADING",
    links: [
      {
        icon: "check",
        label: "Grading Bench",
        path: "/instructor/submissions",
      },
      {
        icon: "list",
        label: "Gradebook",
        path: "/instructor/gradebook",
      },
      {
        icon: "terminal",
        label: "Live Monitoring",
        path: "/instructor/monitoring",
      },
    ],
  },
  {
    label: "ACCOUNT & SYSTEM",
    links: [
      {
        icon: "bell",
        label: "Notifications",
        path: "/instructor/notifications",
      },
      {
        icon: "shield",
        label: "Security Audit Logs",
        path: "/instructor/audit-logs",
      },
      {
        icon: "settings",
        label: "Settings",
        path: "/instructor/settings",
      },
      {
        icon: "logout",
        label: "Sign out",
        isSignOut: true,
      },
    ],
  },
];

function Icon({ name, size = 15 }) {
  const icons = {
    grid: (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <rect x="1" y="1" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.3" />
        <rect x="9" y="1" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.3" />
        <rect x="1" y="9" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.3" />
        <rect x="9" y="9" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.3" />
      </svg>
    ),
    book: (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M2 3h4a2 2 0 012 2v9a2 2 0 00-2-2H2V3zM14 3h-4a2 2 0 00-2 2v9a2 2 0 012-2h4V3z" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    code: (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M5 5L2 8l3 3M11 5l3 3-3 3M9 3l-2 10" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    check: (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M3 8l3 3 7-7" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    list: (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M5 4h8M5 8h8M5 12h8M3 4h.01M3 8h.01M3 12h.01" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    terminal: (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M2 3l5 5-5 5M9 13h5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    bell: (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M8 1.5a3.5 3.5 0 00-3.5 3.5v2.793l-.707.707A1 1 0 003.5 10h9a1 1 0 00.707-1.707l-.707-.707V5A3.5 3.5 0 008 1.5zM6.5 12a1.5 1.5 0 003 0" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    shield: (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M8 1.5L2.5 4v4.5c0 3.5 2.5 6 5.5 6.5 3-.5 5.5-3 5.5-6.5V4L8 1.5z" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    settings: (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <circle cx="8" cy="8" r="2.5" stroke="currentColor" strokeWidth="1.3" />
        <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M3.05 12.95l1.41-1.41M11.54 4.46l1.41-1.41" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      </svg>
    ),
    logout: (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M6 2H3a1 1 0 00-1 1v10a1 1 0 001 1h3M10 11l3-3-3-3M13 8H6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  };
  return icons[name] ?? null;
}

export default function InstructorSidebar() {
  const navigate = useNavigate();
  const auth = useAuth() || {};
  const { user, logout } = auth;
  const [isSignOutOpen, setIsSignOutOpen] = useState(false);

  // Read initial collapsed state from localStorage
  const [isCollapsed, setIsCollapsed] = useState(() => {
    return localStorage.getItem("pamsu_sidebar_collapsed") === "true";
  });

  const toggleCollapse = () => {
    setIsCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem("pamsu_sidebar_collapsed", String(next));
      return next;
    });
  };

  const name = user?.name || user?.fullName || "Instructor Account";
  const initials = user?.initials || name.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join("") || "INST";
  const role = user?.role || "Instructor";

  const handleConfirmSignOut = () => {
    setIsSignOutOpen(false);
    if (logout) logout();
    navigate("/login", { replace: true });
  };

  return (
    <>
      <aside
        className={`flex h-full shrink-0 flex-col overflow-hidden border-r border-border-subtle bg-bg-base pt-3.5 pb-3 select-none transition-all duration-300 ${
          isCollapsed ? "w-[64px] px-2.5" : "w-[220px] px-3.5"
        }`}
      >
        {/* Dedicated Top Header Bar Container */}
        <div className="shrink-0 mb-3 border-b border-border-subtle pb-3">
          <div className={`flex items-center ${isCollapsed ? "justify-center" : "justify-between px-0.5"}`}>
            <div className="flex items-center gap-2 min-w-0">
              <button
                type="button"
                onClick={isCollapsed ? toggleCollapse : undefined}
                title={isCollapsed ? "Expand sidebar" : undefined}
                className={`flex h-7.5 w-7.5 shrink-0 items-center justify-center rounded-lg bg-[#10b981] font-mono text-xs font-bold text-white shadow-sm shadow-emerald-500/20 transition-transform ${
                  isCollapsed ? "hover:scale-105 active:scale-95 cursor-pointer" : ""
                }`}
              >
                &gt;_
              </button>
              {!isCollapsed && (
                <span className="truncate text-sm font-bold tracking-wide text-text-main">
                  PAMSU IDE
                </span>
              )}
            </div>

            {!isCollapsed && (
              <button
                type="button"
                onClick={toggleCollapse}
                title="Collapse sidebar"
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-border-subtle bg-bg-glass text-text-muted transition-all duration-200 hover:border-border-strong hover:bg-bg-glass-hover hover:text-text-main active:scale-95 cursor-pointer shadow-sm"
              >
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                  <path d="M10 3L5 8l5 5M14 3v10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Scrollable Navigation List */}
        <nav aria-label="Instructor navigation" className="flex-1 min-h-0 overflow-y-auto space-y-3.5 pr-0.5 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
          {INSTRUCTOR_NAV.map((section) => (
            <section key={section.label}>
              {!isCollapsed ? (
                <h2 className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-widest text-text-muted">
                  {section.label}
                </h2>
              ) : (
                <div className="my-1.5 h-px bg-border-subtle" />
              )}
              <div className="space-y-0.5">
                {section.links.map((link) =>
                  link.isSignOut ? (
                    <button
                      key="sign-out-item"
                      type="button"
                      onClick={() => setIsSignOutOpen(true)}
                      title={isCollapsed ? link.label : undefined}
                      className={`flex w-full items-center gap-2.5 rounded-lg text-xs font-medium text-text-muted transition-colors duration-150 hover:bg-red-500/[0.08] hover:text-text-rose ${
                        isCollapsed ? "justify-center px-0 py-2" : "px-2.5 py-2"
                      }`}
                    >
                      <Icon name="logout" />
                      {!isCollapsed && <span>{link.label}</span>}
                    </button>
                  ) : (
                    <NavLink
                      key={link.path}
                      to={link.path}
                      end={link.end}
                      title={isCollapsed ? link.label : undefined}
                      className={({ isActive }) =>
                        [
                          "flex w-full items-center gap-2.5 rounded-lg text-xs transition-colors duration-150",
                          isCollapsed ? "justify-center px-0 py-2" : "justify-between px-2.5 py-2",
                          isActive
                            ? "bg-[#10b981]/[0.12] text-text-emerald font-semibold"
                            : "text-text-muted hover:bg-bg-glass hover:text-text-main font-medium",
                        ].join(" ")
                      }
                    >
                      <span className="flex items-center gap-2.5 min-w-0">
                        <Icon name={link.icon} />
                        {!isCollapsed && <span className="truncate">{link.label}</span>}
                      </span>
                    </NavLink>
                  )
                )}
              </div>
            </section>
          ))}
        </nav>

        {/* Pinned Bottom User Profile Card */}
        <div className="shrink-0 pt-2.5 pb-1 border-t border-border-subtle mt-auto space-y-2">
          <div
            className={`flex items-center gap-2.5 ${isCollapsed ? "justify-center" : "px-1"}`}
            title={isCollapsed ? `${name} (${role})` : undefined}
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#10b981] text-xs font-bold text-white shadow-sm ring-1 ring-white/10">
              {initials}
            </div>
            {!isCollapsed && (
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-semibold text-text-main tracking-tight">
                  {name}
                </p>
                <p className="truncate text-[10px] text-text-muted">
                  {role}
                </p>
              </div>
            )}
          </div>
          <div className={`flex ${isCollapsed ? "justify-center" : "justify-end px-1"}`}>
            <ThemeToggle />
          </div>
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