import Sidebar from "./Sidebar";
import InstructorSidebar from "./InstructorSidebar";
import Statusbar from "./Statusbar";

/**
 * Standard page frame: navigation rail, scrollable content column and the
 * status footer. `role` selects the student or instructor navigation.
 */
export default function PageShell({
  role = "student",
  children,
  assignmentCount,
  statusContext,
  maxWidth = "max-w-6xl",
  showStatusbar = true,
}) {
  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main">
      {role === "instructor" ? <InstructorSidebar /> : <Sidebar assignmentCount={assignmentCount} />}
      <div className="flex min-w-0 flex-1 flex-col">
        <main id="main-content" className="min-w-0 flex-1 overflow-y-auto px-4 py-6 sm:px-8">
          <div className={`animate-page-fade mx-auto w-full ${maxWidth}`}>{children}</div>
        </main>
        {showStatusbar && <Statusbar contextLabel={statusContext} />}
      </div>
    </div>
  );
}
