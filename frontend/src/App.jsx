/**
 * App.jsx
 *
 * Connects the current frontend pages using React Router.
 *
 * Current routes:
 * - / redirects to /login
 * - /login displays the login page
 * - /register displays the registration page
 * - /dashboard/student displays the student dashboard
 * - /assignments displays assigned activities
 * - /analytics displays student analytics
 * - /submissions displays the submission list
 * - /submissions/:id temporarily displays the submission list
 * - /workspace displays the student coding workspace
 * - /settings displays account settings
 *
 * Important future work:
 * - Add authentication and role-based route protection.
 * - Connect the instructor dashboard.
 * - Create a dedicated submission-detail page.
 * - Confirm whether Workspace.jsx or CodingWorkspace.jsx is the official IDE.
 */

import { useEffect, useRef } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";

import Analytics from "./pages/Analytics";
import Assignments from "./pages/Assignments";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Settings from "./pages/Settings";
import StudentDashboard from "./pages/StudentDashboard";
import Submissions from "./pages/Submissions";
import Workspace from "./pages/Workspace";

function AnimatedRoutes() {
  const location = useLocation();
  const pageContainerRef = useRef(null);

  useEffect(() => {
    const pageContainer = pageContainerRef.current;

    if (!pageContainer) {
      return undefined;
    }

    const animation = pageContainer.animate(
      [
        {
          opacity: 0.01,
          transform: "translateY(5px)",
        },
        {
          opacity: 1,
          transform: "translateY(0)",
        },
      ],
      {
        duration: 280,
        easing: "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        fill: "both",
      },
    );

    return () => {
      animation.cancel();
    };
  }, [location.key]);

  return (
    <div
      ref={pageContainerRef}
      style={{
        background: "#0f1117",
        minHeight: "100vh",
        willChange: "opacity, transform",
      }}
    >
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />

        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route
          path="/dashboard/student"
          element={<StudentDashboard />}
        />
        <Route path="/assignments" element={<Assignments />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/submissions" element={<Submissions />} />
        <Route path="/submissions/:id" element={<Submissions />} />
        <Route path="/workspace" element={<Workspace />} />
        <Route path="/settings" element={<Settings />} />

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AnimatedRoutes />
    </BrowserRouter>
  );
}
