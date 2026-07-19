import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { RoleRoute } from './auth/RoleRoute';

// Shared Layouts & Error Pages
import StudentLayout from './components/layout/StudentLayout';
import InstructorLayout from './components/layout/InstructorLayout';
import Unauthorized from './pages/Unauthorized';
import NotFound from './pages/NotFound';

// Existing Page Components
import Login from './pages/Login';
import Register from './pages/Register';
import StudentDashboard from './pages/StudentDashboard';
import InstructorDashboard from './pages/InstructorDashboard';
import Assignments from './pages/Assignments';
import Submissions from './pages/Submissions';
import Analytics from './pages/Analytics';
import Workspace from './pages/Workspace';
import Settings from './pages/Settings';

/**
 * Temporary visual placeholder for specific classroom and monitoring views
 * scheduled for detailed construction in Phase 5 and Phase 6.
 */
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
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

          {/* Protected Route Tree - Requires Valid JWT Session */}
          <Route element={<ProtectedRoute />}>
            
            {/* Student Role Tree */}
            <Route element={<RoleRoute allowedRole="student" />}>
              <Route element={<StudentLayout />}>
                <Route path="/dashboard/student" element={<StudentDashboard />} />
                <Route path="/classes" element={<PlaceholderView title="My Classes" description="Join classrooms using 6-character instructor codes." />} />
                <Route path="/classes/:id" element={<PlaceholderView title="Classroom Details" description="View active laboratory activities and announcements." />} />
                <Route path="/assignments" element={<Assignments />} />
                <Route path="/workspace" element={<Workspace />} />
                <Route path="/practice" element={<PlaceholderView title="Solo Python Practice" description="Independent coding sandbox without graded AST monitoring." />} />
                <Route path="/submissions" element={<Submissions />} />
                <Route path="/submissions/:id" element={<PlaceholderView title="Submission Details" description="Review AST feedback, test cases, and instructor grades." />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/settings" element={<Settings />} />
              </Route>
            </Route>

            {/* Instructor Role Tree */}
            <Route element={<RoleRoute allowedRole="instructor" />}>
              <Route element={<InstructorLayout />}>
                <Route path="/dashboard/instructor" element={<InstructorDashboard />} />
                <Route path="/instructor/classes" element={<PlaceholderView title="Class Management" description="Create new classes and generate enrollment codes." />} />
                <Route path="/instructor/classes/:id" element={<PlaceholderView title="Roster View" description="Manage enrolled student lists and class activities." />} />
                <Route path="/instructor/activities" element={<PlaceholderView title="Activity Authoring" description="Configure starter code, AST rules, and hidden test cases." />} />
                <Route path="/instructor/activities/:id" element={<PlaceholderView title="Activity Details" description="Edit publication state and paste policy modes." />} />
                <Route path="/instructor/submissions" element={<PlaceholderView title="Grading Bench" description="Review student source code, execution results, and similarity indicators." />} />
                <Route path="/instructor/submissions/:id" element={<PlaceholderView title="Manual Grading" description="Assign official grades and feedback." />} />
                <Route path="/instructor/monitoring" element={<PlaceholderView title="Live Student Monitoring" description="Controlled 5-10s polling of active IDE sessions and tab switches." />} />
                {/* Instructors share access to their own account settings */}
                <Route path="/settings" element={<Settings />} />
              </Route>
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