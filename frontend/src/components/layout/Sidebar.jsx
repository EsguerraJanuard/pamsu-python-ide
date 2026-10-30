import AppSidebar from "./AppSidebar";
import ThemeToggle from "../../features/theme/ThemeToggle";

const STUDENT_NAV = [
  {
    label: "Main",
    links: [
      { icon: "grid", label: "Dashboard", path: "/student/dashboard", end: true },
      { icon: "list", label: "Assignments", path: "/student/assignments" },
      { icon: "book", label: "My Classes", path: "/student/classes" },
      { icon: "terminal", label: "Solo Practice", path: "/student/practice" },
    ],
  },
  {
    label: "Progress",
    links: [
      { icon: "chart", label: "My Analytics", path: "/student/analytics" },
      { icon: "file", label: "Submissions", path: "/student/submissions" },
    ],
  },
  {
    label: "Account",
    links: [
      { icon: "bell", label: "Notifications", path: "/student/notifications" },
      { icon: "shield", label: "Audit History", path: "/student/audit-logs" },
      { icon: "settings", label: "Settings", path: "/student/settings" },
    ],
  },
];

export default function Sidebar({ assignmentCount = 0 }) {
  return (
    <AppSidebar
      sections={STUDENT_NAV}
      ariaLabel="Student navigation"
      roleLabel="Student"
      badges={{ "/student/assignments": assignmentCount }}
      renderThemeControl={(collapsed) => <ThemeToggle collapsed={collapsed} />}
    />
  );
}
