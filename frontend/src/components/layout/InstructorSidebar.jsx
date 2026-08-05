import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthContext";

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

  const name = user?.name || user?.fullName || "Instructor Account";
  const initials = user?.initials || name.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join("") || "INST";
  const role = user?.role || "Instructor";

  const handleSignOut = () => {
    if (logout) logout();
    navigate("/login", { replace: true });
  };

  return (
    <aside className="flex w-[220px] shrink-0 flex-col justify-between overflow-y-auto border-r border-white/[0.06] bg-[#0d1017] px-3 py-4 select-none">
      <div>
        <div className="mb-6 flex items-center gap-2 px-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[#10b981] font-mono text-xs font-bold text-white">
            &gt;_
          </div>
          <span className="text-sm font-semibold tracking-wide text-white">
            PAMSU IDE
          </span>
          <span className="rounded bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 text-[9px] font-mono font-bold text-emerald-400">
            PRO
          </span>
        </div>

        <div className="mb-6 flex items-center gap-2.5 border-b border-white/[0.06] px-2 pb-4">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#10b981] text-xs font-bold text-white">
            {initials}
          </div>
          <div className="min-w-0">
            <p className="truncate text-xs font-semibold text-white">
              {name}
            </p>
            <p className="truncate text-[10px] text-white/40">
              {role}
            </p>
          </div>
        </div>

        <nav aria-label="Instructor navigation">
          {INSTRUCTOR_NAV.map((section) => (
            <section key={section.label} className="mb-4">
              <h2 className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-widest text-white/25">
                {section.label}
              </h2>
              <div className="space-y-0.5">
                {section.links.map((link) => (
                  <NavLink
                    key={link.path}
                    to={link.path}
                    end={link.end}
                    className={({ isActive }) =>
                      [
                        "flex w-full items-center justify-between gap-2.5 rounded-lg px-2 py-2 text-sm transition-colors duration-200",
                        isActive
                          ? "bg-[#10b981]/[0.12] text-[#10b981]"
                          : "text-white/45 hover:bg-white/[0.04] hover:text-white/80",
                      ].join(" ")
                    }
                  >
                    <span className="flex items-center gap-2.5">
                      <Icon name={link.icon} />
                      <span>{link.label}</span>
                    </span>
                  </NavLink>
                ))}
              </div>
            </section>
          ))}
        </nav>
      </div>

      <button
        type="button"
        onClick={handleSignOut}
        className="flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-sm text-white/35 transition-colors duration-200 hover:bg-red-500/[0.08] hover:text-red-400"
      >
        <Icon name="logout" />
        <span>Sign out</span>
      </button>
    </aside>
  );
}