import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './features/auth/AuthContext';

// --- AUTHENTICATION CONTROLS ---
const DEV_BYPASS = false;          // Production authentication enabled

const ProtectedRoute = () => {
  const { isAuthenticated } = useAuth();
  if (DEV_BYPASS) return <Outlet />;
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};

const RoleRoute = ({ allowedRole }) => {
  const { role } = useAuth();
  if (DEV_BYPASS) return <Outlet />;
  return role === allowedRole ? <Outlet /> : <Navigate to="/unauthorized" replace />;
};

// Redirects already-authenticated users away from login/register
const GuestRoute = () => {
  const { isAuthenticated, role } = useAuth();
  if (!isAuthenticated) return <Outlet />;
  return <Navigate to={role === 'instructor' ? '/instructor/dashboard' : '/student/dashboard'} replace />;
};

// Shared Layouts & Error Pages
import InstructorLayout from './components/layout/InstructorLayout';
import Unauthorized from './pages/Unauthorized';
import NotFound from './pages/NotFound';
import NotificationsPage from './pages/NotificationsPage';
import AuditLogsPage from './pages/AuditLogsPage';

// Feature Components
import Login from './features/auth/Login';
import Register from './features/auth/Register';
import StudentDashboard from './features/dashboard/StudentDashboard';
import InstructorDashboard from './features/dashboard/InstructorDashboard';
import InstructorSettings from "./features/settings/InstructorSettings";
import Assignments from './features/assignments/Assignments';
import Submissions from './features/submissions/Submissions';
import SubmissionDetails from './features/submissions/SubmissionDetails';
import Analytics from './features/dashboard/Analytics';
import Workspace from './features/workspace/Workspace';
import Settings from './features/settings/Settings';
import ClassRosterView from './features/dashboard/ClassRosterView';
import ClassManagement from './features/instructor/ClassManagement';
import ActivityEditor from './features/instructor/ActivityEditor';
import ActivityDetails from './features/instructor/ActivityDetails';
import InstructorReviewQueue from './features/instructor/InstructorReviewQueue';
import InstructorGradebook from './features/instructor/InstructorGradebook';
import GradingWorkspace from './features/instructor/GradingWorkspace';
import LiveMonitoring from './features/instructor/LiveMonitoring';
import MyClasses from './features/classes/MyClasses';
import ClassDetails from './features/classes/ClassDetails';
import SoloPractice from './features/practice/SoloPractice';

const PlaceholderView = ({ title, description }) => (
  <div className="rounded-xl border border-border-subtle bg-bg-glass/50 p-8 text-center">
    <h2 className="text-xl font-bold text-text-main">{title}</h2>
    <p className="mt-2 text-sm text-text-muted">{description}</p>
    <div className="mt-6 inline-block rounded-full bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-400">
      Scheduled for pipeline integration
    </div>
  </div>
);

import { ThemeProvider } from './features/theme/ThemeContext';

export const App = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Root redirect */}
            <Route path="/" element={<Navigate to="/student/dashboard" replace />} />

            {/* Public Authentication Routes — redirect to dashboard if already logged in */}
            <Route element={<GuestRoute />}>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
            </Route>
            <Route path="/unauthorized" element={<Unauthorized />} />

             {/* Protected Route Tree - Requires Valid JWT/Session */}
            <Route element={<ProtectedRoute />}>

              {/* Student Role Tree */}
              <Route element={<RoleRoute allowedRole="student" />}>
                <Route path="/student/dashboard" element={<StudentDashboard />} />
                <Route path="/student/classes" element={<MyClasses />} />
                <Route path="/student/classes/:id" element={<ClassDetails />} />
                <Route path="/student/assignments" element={<Assignments />} />
                <Route path="/student/workspace" element={<Workspace />} />
                <Route path="/student/practice" element={<SoloPractice />} />
                <Route path="/student/submissions" element={<Submissions />} />
                <Route path="/student/submissions/:id" element={<SubmissionDetails />} />
                <Route path="/student/notifications" element={<NotificationsPage role="student" />} />
                <Route path="/student/audit-logs" element={<AuditLogsPage role="student" />} />
                <Route path="/student/analytics" element={<Analytics />} />
                <Route path="/student/settings" element={<Settings />} />
              </Route>

              {/* Instructor Role Tree */}
              <Route element={<RoleRoute allowedRole="instructor" />}>
                <Route path="/instructor/dashboard" element={<InstructorDashboard />} />
                <Route path="/instructor/classes" element={<ClassManagement />} />
                <Route path="/instructor/classes/:id" element={<ClassRosterView />} />
                <Route path="/instructor/activities" element={<ActivityEditor />} />
                <Route path="/instructor/activities/:id" element={<ActivityDetails />} />
                <Route path="/instructor/submissions" element={<InstructorReviewQueue />} />
                <Route path="/instructor/gradebook" element={<InstructorGradebook />} />
                <Route path="/instructor/submissions/:id" element={<GradingWorkspace />} />
                <Route path="/instructor/notifications" element={<NotificationsPage role="instructor" />} />
                <Route path="/instructor/audit-logs" element={<AuditLogsPage role="instructor" />} />
                <Route path="/instructor/monitoring" element={<LiveMonitoring />} />
                <Route path="/instructor/settings" element={<InstructorSettings />} />
              </Route>

            </Route>

            {/* Fallback 404 Route */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;