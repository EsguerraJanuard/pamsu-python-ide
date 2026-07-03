/**
 * Sidebar.jsx
 * This is the left navigation panel shared across all student pages.
 *
 * HOW TO USE:
 * Import and place at the left of your page layout like this:
 *   <Sidebar activePage="Dashboard" />
 *
 * PROPS:
 *   activePage (string) — the name of the current page so the correct link gets highlighted
 *     Possible values: "Dashboard" | "Assignments" | "Workspace" | "My Analytics" | "Submissions" | "Settings"
 *
 * TODO (Frontend): replace MOCK_STUDENT with real user data from sessionStorage or API
 * TODO (Backend): GET /api/student/profile returns { name, initials, role, course, courseName }
 */

import { useNavigate } from "react-router-dom";

// ─── Mock student info — replace with real data when backend is ready ─────────
const MOCK_STUDENT = {
  name: "Juan, Miguel D.",
  initials: "JD",
  role: "Student",
  course: "CCS101",
};

// ─── Nav sections and links ───────────────────────────────────────────────────
const NAV_SECTIONS = [
  {
    label: "MAIN",
    links: [
      { icon: "grid",     label: "Dashboard",    path: "/dashboard/student" },
      { icon: "list",     label: "Assignments",  path: "/assignments",       badge: 3 },
      { icon: "code",     label: "Workspace",    path: "/workspace" },
    ],
  },
  {
    label: "PROGRESS",
    links: [
      { icon: "chart",  label: "My Analytics", path: "/analytics" },
      { icon: "file",   label: "Submissions",  path: "/submissions" },
    ],
  },
  {
    label: "ACCOUNT",
    links: [
      { icon: "settings", label: "Settings", path: "/settings" },
    ],
  },
];

// ─── Inline SVG icons — no icon libraries used ───────────────────────────────
function Icon({ name, size = 15 }) {
  const icons = {
    grid:     <svg width={size} height={size} viewBox="0 0 16 16" fill="none"><rect x="1" y="1" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.3"/><rect x="9" y="1" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.3"/><rect x="1" y="9" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.3"/><rect x="9" y="9" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.3"/></svg>,
    list:     <svg width={size} height={size} viewBox="0 0 16 16" fill="none"><path d="M3 4h10M3 8h10M3 12h10" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>,
    code:     <svg width={size} height={size} viewBox="0 0 16 16" fill="none"><path d="M5 5L2 8l3 3M11 5l3 3-3 3M9 3l-2 10" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>,
    chart:    <svg width={size} height={size} viewBox="0 0 16 16" fill="none"><path d="M2 12l4-4 3 3 5-6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>,
    file:     <svg width={size} height={size} viewBox="0 0 16 16" fill="none"><rect x="3" y="1" width="10" height="14" rx="1.5" stroke="currentColor" strokeWidth="1.3"/><path d="M6 5h4M6 8h4M6 11h2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>,
    settings: <svg width={size} height={size} viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="2.5" stroke="currentColor" strokeWidth="1.3"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M3.05 12.95l1.41-1.41M11.54 4.46l1.41-1.41" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>,
    logout:   <svg width={size} height={size} viewBox="0 0 16 16" fill="none"><path d="M6 2H3a1 1 0 00-1 1v10a1 1 0 001 1h3M10 11l3-3-3-3M13 8H6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>,
  };
  return icons[name] || null;
}

export default function Sidebar({ activePage = "Dashboard" }) {
  const navigate = useNavigate();

  const handleSignOut = () => {
    sessionStorage.removeItem("token");
    navigate("/login");
  };

  return (
    <aside className="w-[200px] flex-shrink-0 flex flex-col justify-between border-r border-white/[0.06] px-3 py-4 overflow-y-auto">

      <div>
        {/* Logo */}
        <div className="flex items-center gap-2 px-2 mb-6">
          <div className="flex items-center justify-center w-7 h-7 rounded-md bg-[#3b82f6] text-white text-xs font-bold font-mono">
            &gt;_
          </div>
          <span className="font-semibold text-white text-sm tracking-wide">Python</span>
        </div>

        {/* User info
            TODO (Frontend): replace MOCK_STUDENT with data from sessionStorage
            Example: const user = JSON.parse(sessionStorage.getItem("user"));
        */}
        <div className="flex items-center gap-2.5 px-2 mb-6 pb-4 border-b border-white/[0.06]">
          <div className="w-8 h-8 rounded-full bg-[#3b82f6] flex items-center justify-center text-xs font-bold flex-shrink-0">
            {MOCK_STUDENT.initials}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold text-white truncate">{MOCK_STUDENT.name}</p>
            <p className="text-[10px] text-white/40">{MOCK_STUDENT.role} · {MOCK_STUDENT.course}</p>
          </div>
        </div>

        {/* Nav links */}
        {NAV_SECTIONS.map((section) => (
          <div key={section.label} className="mb-4">
            <p className="text-[10px] font-semibold text-white/25 uppercase tracking-widest px-2 mb-1">
              {section.label}
            </p>
            {section.links.map((link) => {
              const isActive = activePage === link.label;
              return (
                <button
                  key={link.label}
                  type="button"
                  onClick={() => navigate(link.path)}
                  className="w-full flex items-center justify-between gap-2.5 px-2 py-2 rounded-lg text-sm mb-0.5"
                  style={{
                    background: isActive ? "rgba(59,130,246,0.12)" : "transparent",
                    color: isActive ? "#3b82f6" : "rgba(255,255,255,0.45)",
                    transition: "background 0.2s ease, color 0.2s ease",
                  }}
                  onMouseEnter={(e) => {
                    if (isActive) return;
                    e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                    e.currentTarget.style.color = "rgba(255,255,255,0.8)";
                  }}
                  onMouseLeave={(e) => {
                    if (isActive) return;
                    e.currentTarget.style.background = "transparent";
                    e.currentTarget.style.color = "rgba(255,255,255,0.45)";
                  }}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon name={link.icon} />
                    <span>{link.label}</span>
                  </div>
                  {/* Assignment badge — TODO (Frontend): get real count from API */}
                  {link.badge && (
                    <span className="text-[10px] font-semibold bg-[#3b82f6] text-white px-1.5 py-0.5 rounded-full">
                      {link.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Sign out */}
      <button
        type="button"
        onClick={handleSignOut}
        className="flex items-center gap-2.5 px-2 py-2 rounded-lg text-sm text-white/30 w-full"
        style={{ transition: "color 0.2s ease, background 0.2s ease" }}
        onMouseEnter={(e) => {
          e.currentTarget.style.color = "#ef4444";
          e.currentTarget.style.background = "rgba(239,68,68,0.08)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = "rgba(255,255,255,0.3)";
          e.currentTarget.style.background = "transparent";
        }}
      >
        <Icon name="logout" />
        Sign out
      </button>
    </aside>
  );
}