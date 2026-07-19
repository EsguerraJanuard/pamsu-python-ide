export const InstructorDashboard = () => {
  return (
    <div className="space-y-6 text-slate-100">
      <header className="border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-bold text-white">Instructor Dashboard</h1>
        <p className="text-sm text-slate-400">
          Welcome to the Faculty Bench and Classroom Management Center.
        </p>
      </header>
      
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <h2 className="text-lg font-semibold text-white">Active Classrooms Overview</h2>
        <p className="mt-2 text-sm text-slate-400">
          Select a workspace from the faculty sidebar to configure AST grading rules or monitor active student sessions.
        </p>
      </div>
    </div>
  );
};

export default InstructorDashboard;