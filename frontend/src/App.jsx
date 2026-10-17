import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth, homePathForRole } from './features/auth/AuthContext';
import ProtectedRoute from './features/auth/ProtectedRoute';
import RoleRoute from './features/auth/RoleRoute';
import ErrorBoundary from './components/ErrorBoundary';
import { LoadingState } from './components/ui/StateViews';
import { ThemeProvider } from './features/theme/ThemeContext';
import Unauthorized from './pages/Unauthorized';
import NotFound from './pages/NotFound';
import Login from './features/auth/Login';
import ForgotPassword from './features/auth/ForgotPassword';

// Route pages are code-split so each area loads only when visited.
const NotificationsPage = lazy(() => import('./pages/NotificationsPage'));
const AuditLogsPage = lazy(() => import('./pages/AuditLogsPage'));

const StudentDashboard = lazy(() => import('./features/dashboard/StudentDashboard'));
const InstructorDashboard = lazy(() => import('./features/dashboard/InstructorDashboard'));
const InstructorSettings = lazy(() => import('./features/settings/InstructorSettings'));
const Assignments = lazy(() => import('./features/assignments/Assignments'));
const Submissions = lazy(() => import('./features/submissions/Submissions'));
const SubmissionDetails = lazy(() => import('./features/submissions/SubmissionDetails'));
const Analytics = lazy(() => import('./features/dashboard/Analytics'));
const Workspace = lazy(() => import('./features/workspace/Workspace'));
const SoloPractice = lazy(() => import('./features/practice/SoloPractice'));
const PracticeWorkspace = lazy(() => import('./features/practice/PracticeWorkspace'));
const Settings = lazy(() => import('./features/settings/Settings'));
const AdminDashboard = lazy(() => import('./features/admin/AdminDashboard'));
const ClassRosterView = lazy(() => import('./features/dashboard/ClassRosterView'));
const ClassManagement = lazy(() => import('./features/instructor/ClassManagement'));
const ActivityEditor = lazy(() => import('./features/instructor/ActivityEditor'));
const ActivityDetails = lazy(() => import('./features/instructor/ActivityDetails'));
const GradingBenchRoot = lazy(() => import('./features/instructor/grading/GradingBenchRoot'));
const GradingClassView = lazy(() => import('./features/instructor/grading/GradingClassView'));
const SplitPaneGradingWorkspace = lazy(() => import('./features/instructor/grading/SplitPaneGradingWorkspace'));
const LiveMonitoring = lazy(() => import('./features/instructor/LiveMonitoring'));
const PracticeModuleManager = lazy(() => import('./features/instructor/PracticeModuleManager'));
const MyClasses = lazy(() => import('./features/classes/MyClasses'));
const ClassDetails = lazy(() => import('./features/classes/ClassDetails'));


// Route the root URL based on role
const RootRoute = () => {
  const { isAuthenticated, role } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Navigate to={homePathForRole(role)} replace />;
};

// Redirects already-authenticated users away from the public auth pages
const GuestRoute = () => {
  const { isAuthenticated, role } = useAuth();
  if (!isAuthenticated) return <Outlet />;
  return <Navigate to={homePathForRole(role)} replace />;
};

export const App = () => {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <Router>
            <Suspense
              fallback={
                <div className="flex min-h-screen items-center justify-center bg-bg-base">
                  <LoadingState label="Loading…" />
                </div>
              }
            >
            <Routes>
              <Route path="/" element={<RootRoute />} />

              {/* Public authentication routes */}
              <Route element={<GuestRoute />}>
                <Route path="/login" element={<Login />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
              </Route>
              {/* Public self-registration is retired (MIS provisions student
                  accounts); keep old links and bookmarks working. */}
              <Route path="/register" element={<Navigate to="/login" replace />} />
              <Route path="/unauthorized" element={<Unauthorized />} />

              {/* Protected routes — require a valid session */}
              <Route element={<ProtectedRoute />}>
                <Route element={<RoleRoute allowedRole="student" />}>
                  <Route path="/student/dashboard" element={<StudentDashboard />} />
                  <Route path="/student/classes" element={<MyClasses />} />
                  <Route path="/student/classes/:id" element={<ClassDetails />} />
                  <Route path="/student/assignments" element={<Assignments />} />
                  <Route path="/student/workspace" element={<Workspace />} />
                  <Route path="/student/practice" element={<SoloPractice />} />
                  <Route path="/student/practice/workspace" element={<PracticeWorkspace />} />
                  <Route path="/student/submissions" element={<Submissions />} />
                  <Route path="/student/submissions/:id" element={<SubmissionDetails />} />
                  <Route path="/student/notifications" element={<NotificationsPage role="student" />} />
                  <Route path="/student/audit-logs" element={<AuditLogsPage role="student" />} />
                  <Route path="/student/analytics" element={<Analytics />} />
                  <Route path="/student/settings" element={<Settings />} />
                </Route>

                <Route element={<RoleRoute allowedRole="admin" />}>
                  <Route path="/admin/dashboard" element={<AdminDashboard />} />
                </Route>

                <Route element={<RoleRoute allowedRole="instructor" />}>
                  <Route path="/instructor/dashboard" element={<InstructorDashboard />} />
                  <Route path="/instructor/classes" element={<ClassManagement />} />
                  <Route path="/instructor/classes/:id" element={<ClassRosterView />} />
                  <Route path="/instructor/practice" element={<PracticeModuleManager />} />
                  <Route path="/instructor/activities/create" element={<ActivityEditor />} />
                  <Route path="/instructor/activities/:id" element={<ActivityDetails />} />
                  <Route path="/instructor/bench" element={<GradingBenchRoot />} />
                  <Route path="/instructor/bench/:classId" element={<GradingClassView />} />
                  <Route path="/instructor/bench/:classId/:taskId" element={<SplitPaneGradingWorkspace />} />
                  <Route path="/instructor/notifications" element={<NotificationsPage role="instructor" />} />
                  <Route path="/instructor/audit-logs" element={<AuditLogsPage role="instructor" />} />
                  <Route path="/instructor/monitoring" element={<LiveMonitoring />} />
                  <Route path="/instructor/settings" element={<InstructorSettings />} />
                </Route>
              </Route>

              <Route path="*" element={<NotFound />} />
            </Routes>
            </Suspense>
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;
