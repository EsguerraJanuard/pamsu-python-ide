import { NavLink, useNavigate } from "react-router-dom";

const DEFAULT_USER = {
  name: "Student Account",
  initials: "SA",
  role: "Student",
  course: "No active class",
};

const NAV_SECTIONS = [
  {
    label: "MAIN",
    links: [
      {
        icon: "grid",
        label: "Dashboard",
        path: "/dashboard/student",
        end: true,
      },
      {
        icon: "list",
        label: "Assignments",
        path: "/assignments",
      },
      {
        icon: "code",
        label: "Workspace",
        path: "/workspace",
      },
    ],
  },
  {
    label: "PROGRESS",
    links: [
      {
        icon: "chart",
        label: "My Analytics",
        path: "/analytics",
      },
      {
        icon: "file",
        label: "Submissions",
        path: "/submissions",
      },
    ],
  },
  {
    label: "ACCOUNT",
    links: [
      {
        icon: "settings",
        label: "Settings",
        path: "/settings",
      },
    ],
  },
];

function Icon({ name, size = 15 }) {
  const icons = {
    grid: (
      <svg
        width={size}
        height={size}
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <rect
          x="1"
          y="1"
          width="6"
          height="6"
          rx="1"
          stroke="currentColor"
          strokeWidth="1.3"
        />
        <rect
          x="9"
          y="1"
          width="6"
          height="6"
          rx="1"
          stroke="currentColor"
          strokeWidth="1.3"
        />
        <rect
          x="1"
          y="9"
          width="6"
          height="6"
          rx="1"
          stroke="currentColor"
          strokeWidth="1.3"
        />
        <rect
          x="9"
          y="9"
          width="6"
          height="6"
          rx="1"
          stroke="currentColor"
          strokeWidth="1.3"
        />
      </svg>
    ),
    list: (
      <svg
        width={size}
        height={size}
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M3 4h10M3 8h10M3 12h10"
          stroke="currentColor"
          strokeWidth="1.3"
          strokeLinecap="round"
        />
      </svg>
    ),
    code: (
      <svg
        width={size}
        height={size}
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M5 5L2 8l3 3M11 5l3 3-3 3M9 3l-2 10"
          stroke="currentColor"
          strokeWidth="1.3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
    chart: (
      <svg
        width={size}
        height={size}
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M2 12l4-4 3 3 5-6"
          stroke="currentColor"
          strokeWidth="1.3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
    file: (
      <svg
        width={size}
        height={size}
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <rect
          x="3"
          y="1"
          width="10"
          height="14"
          rx="1.5"
          stroke="currentColor"
          strokeWidth="1.3"
        />
        <path
          d="M6 5h4M6 8h4M6 11h2"
          stroke="currentColor"
          strokeWidth="1.3"
          strokeLinecap="round"
        />
      </svg>
    ),
    settings: (
      <svg
        width={size}
        height={size}
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <circle
          cx="8"
          cy="8"
          r="2.5"
          stroke="currentColor"
          strokeWidth="1.3"
        />
        <path
          d="M8 1v2M8 13v2M1 8h2M13 8h2M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M3.05 12.95l1.41-1.41M11.54 4.46l1.41-1.41"
          stroke="currentColor"
          strokeWidth="1.3"
          strokeLinecap="round"
        />
      </svg>
    ),
    logout: (
      <svg
        width={size}
        height={size}
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M6 2H3a1 1 0 00-1 1v10a1 1 0 001 1h3M10 11l3-3-3-3M13 8H6"
          stroke="currentColor"
          strokeWidth="1.3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  };

  return icons[name] ?? null;
}

function getStoredUser() {
  try {
    const storedUser = sessionStorage.getItem("user");

    if (!storedUser) {
      return DEFAULT_USER;
    }

    const parsedUser = JSON.parse(storedUser);

    return {
      name: parsedUser.name || DEFAULT_USER.name,
      initials: parsedUser.initials || DEFAULT_USER.initials,
      role: parsedUser.role || DEFAULT_USER.role,
      course: parsedUser.course || DEFAULT_USER.course,
    };
  } catch {
    return DEFAULT_USER;
  }
}

export default function Sidebar({
  user = getStoredUser(),
  assignmentCount = 0,
}) {
  const navigate = useNavigate();

  const handleSignOut = () => {
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("user");
    sessionStorage.removeItem("refreshToken");

    navigate("/login", {
      replace: true,
    });
  };

  return (
    <aside className="flex w-[220px] shrink-0 flex-col justify-between overflow-y-auto border-r border-white/[0.06] bg-[#0f1117] px-3 py-4">
      <div>
        <div className="mb-6 flex items-center gap-2 px-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[#3b82f6] font-mono text-xs font-bold text-white">
            &gt;_
          </div>

          <span className="text-sm font-semibold tracking-wide text-white">
            PAMSU IDE
          </span>
        </div>

        <div className="mb-6 flex items-center gap-2.5 border-b border-white/[0.06] px-2 pb-4">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#3b82f6] text-xs font-bold text-white">
            {user.initials}
          </div>

          <div className="min-w-0">
            <p className="truncate text-xs font-semibold text-white">
              {user.name}
            </p>

            <p className="truncate text-[10px] text-white/40">
              {user.role} · {user.course}
            </p>
          </div>
        </div>

        <nav aria-label="Student navigation">
          {NAV_SECTIONS.map((section) => (
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
                          ? "bg-[#3b82f6]/[0.12] text-[#3b82f6]"
                          : "text-white/45 hover:bg-white/[0.04] hover:text-white/80",
                      ].join(" ")
                    }
                  >
                    <span className="flex items-center gap-2.5">
                      <Icon name={link.icon} />
                      <span>{link.label}</span>
                    </span>

                    {link.path === "/assignments" &&
                      assignmentCount > 0 && (
                        <span className="rounded-full bg-[#3b82f6] px-1.5 py-0.5 text-[10px] font-semibold text-white">
                          {assignmentCount}
                        </span>
                      )}
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
        className="flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-sm text-white/30 transition-colors duration-200 hover:bg-red-500/[0.08] hover:text-red-400"
      >
        <Icon name="logout" />
        <span>Sign out</span>
      </button>
    </aside>
  );
}
