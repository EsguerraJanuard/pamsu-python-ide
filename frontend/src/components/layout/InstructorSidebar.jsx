import AppSidebar from "./AppSidebar";
import ThemeToggle from "../../features/theme/ThemeToggle";

const INSTRUCTOR_NAV = [
  {
    label: "Management",
    links: [
      { icon: "grid", label: "Overview", path: "/instructor/dashboard", end: true },
      { icon: "book", label: "Classes", path: "/instructor/classes" },
      { icon: "plus", label: "New Activity", path: "/instructor/activities/create" },
      { icon: "monitor", label: "Practice Modules", path: "/instructor/practice" },
    ],
  },
  {
    label: "Monitoring & Grading",
    links: [
      { icon: "check", label: "Grading Bench", path: "/instructor/bench" },
      { icon: "terminal", label: "Live Monitoring", path: "/instructor/monitoring" },
    ],
  },
  {
    label: "Account",
    links: [
      { icon: "bell", label: "Notifications", path: "/instructor/notifications" },
      { icon: "shield", label: "Audit Logs", path: "/instructor/audit-logs" },
      { icon: "settings", label: "Settings", path: "/instructor/settings" },
    ],
  },
];

export default function InstructorSidebar() {
  return (
    <AppSidebar
      sections={INSTRUCTOR_NAV}
      ariaLabel="Instructor navigation"
      roleLabel="Faculty"
      renderThemeControl={(collapsed) => <ThemeToggle collapsed={collapsed} />}
    />
  );
}
