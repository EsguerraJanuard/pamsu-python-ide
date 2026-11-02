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
        {/* The vertical padding sits on the inner wrapper, not on <main> (the
            scroll container), so sticky table headers and the editor's save
            bar line up with the visible edge instead of 24px inside it. */}
        <main id="main-content" className="min-w-0 flex-1 overflow-y-auto px-4 sm:px-8">
          <div className={`animate-page-fade mx-auto w-full py-6 ${maxWidth}`}>{children}</div>
        </main>
        {showStatusbar && <Statusbar contextLabel={statusContext} />}
      </div>
    </div>
  );
}
