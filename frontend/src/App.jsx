import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider } from './features/auth/AuthContext';

// ==========================================
// DEV BYPASS: Route Protection Disabled
// ==========================================
const ProtectedRoute = () => <Outlet />;
const RoleRoute = () => <Outlet />;
// ==========================================

// Shared Layouts & Error Pages
// StudentLayout remains removed since student pages render their own custom Sidebar
import InstructorLayout from './components/layout/InstructorLayout';
import Unauthorized from './pages/Unauthorized';
import NotFound from './pages/NotFound';

// Feature Components
import Login from './features/auth/Login';
import Register from './features/auth/Register';
import StudentDashboard from './features/dashboard/StudentDashboard';
import InstructorDashboard from './features/dashboard/InstructorDashboard';
import InstructorSettings from "./features/settings/InstructorSettings";
import Assignments from './features/assignments/Assignments';
import Submissions from './features/submissions/Submissions';
import Analytics from './features/dashboard/Analytics';
import Workspace from './features/workspace/Workspace';
import Settings from './features/settings/Settings';
import ClassRosterView from './features/dashboard/ClassRosterView';

const PlaceholderView = ({ title, description }) => (
  <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-8 text-center">
    <h2 className="text-xl font-bold text-white">{title}</h2>
    <p className="mt-2 text-sm text-slate-400">{description}</p>
    <div className="mt-6 inline-block rounded-full bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-400">
      Scheduled for pipeline integration
    </div>
  </div>
);

export const App = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Authentication Routes */}
          <Route path="/" element={<Navigate to="/student/dashboard" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

           {/* Protected Route Tree - Requires Valid JWT/Session */}
          <Route element={<ProtectedRoute />}>
            
            {/* Student Role Tree (Standalone Pages without StudentLayout) */}
            <Route element={<RoleRoute allowedRole="student" />}>
              <Route path="/student/dashboard" element={<StudentDashboard />} />
              <Route path="/student/classes" element={<PlaceholderView title="My Classes" description="Join classrooms using 6-character instructor codes." />} />
              <Route path="/student/classes/:id" element={<PlaceholderView title="Classroom Details" description="View active laboratory activities and announcements." />} />
              <Route path="/student/assignments" element={<Assignments />} />
              <Route path="/student/workspace" element={<Workspace />} />
              <Route path="/student/practice" element={<PlaceholderView title="Solo Python Practice" description="Independent coding sandbox without graded AST monitoring." />} />
              <Route path="/student/submissions" element={<Submissions />} />
              <Route path="/student/submissions/:id" element={<PlaceholderView title="Submission Details" description="Review AST feedback, test cases, and instructor grades." />} />
              <Route path="/student/analytics" element={<Analytics />} />
              <Route path="/student/settings" element={<Settings />} />
              </Route>

            {/* Instructor Role Tree */}
            <Route element={<RoleRoute allowedRole="instructor" />}>
              <Route path="/instructor/dashboard" element={<InstructorDashboard />} />
              <Route path="/instructor/classes" element={<PlaceholderView title="Class Management" description="Create new classes and generate enrollment codes." />} />
              <Route path="/instructor/classes/:id" element={<ClassRosterView />} />
              <Route path="/instructor/activities" element={<PlaceholderView title="Activity Authoring" description="Configure starter code, AST rules, and hidden test cases." />} />
              <Route path="/instructor/activities/:id" element={<PlaceholderView title="Activity Details" description="Edit publication state and paste policy modes." />} />
              <Route path="/instructor/submissions" element={<PlaceholderView title="Grading Bench" description="Review student source code, execution results, and similarity indicators." />} />
              <Route path="/instructor/submissions/:id" element={<PlaceholderView title="Manual Grading" description="Assign official grades and feedback." />} />
              <Route path="/instructor/monitoring" element={<PlaceholderView title="Live Student Monitoring" description="Controlled 5-10s polling of active IDE sessions and tab switches." />} />
              <Route path="/instructor/settings" element={<InstructorSettings />} />
              </Route>

          </Route>

          {/* Fallback 404 Route */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;