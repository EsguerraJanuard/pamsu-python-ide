/**
 * App.jsx
 * Connects all pages together with React Router.
 *
 * HOW ROUTING WORKS:
 * - / → goes to /login automatically
 * - /login → Login page
 * - /register → Register page
 * - /dashboard/student → Student Dashboard
 * - /assignments → Assignments page
 * - /analytics → Analytics page
 * - /submissions → Submissions list
 * - /submissions/:id → Single submission report (TODO)
 * - /workspace → Student IDE (placeholder for now)
 * - /settings → Settings page
 *
 * AnimatedRoutes handles the smooth fade transition between pages.
 * The background stays #0f1117 during transitions so there's no white flash.
 *
 * TODO (Frontend): add instructor routes when Kenneth's pages are ready
 * TODO (Frontend): add AuthGuard to protect /dashboard, /assignments, etc.
 *   Example: if (!sessionStorage.getItem("token")) navigate("/login")
 */

import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";

import Login from "./pages/Login";
import Register from "./pages/Register";
import StudentDashboard from "./pages/StudentDashboard";
import Assignments from "./pages/Assignments";
import Analytics from "./pages/Analytics";
import Submissions from "./pages/Submissions";
import Settings from "./pages/Settings";
import Workspace from "./pages/Workspace";

// Smooth fade transition between pages — no white flash
function AnimatedRoutes() {
  const location = useLocation();
  const [displayLocation, setDisplayLocation] = useState(location);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    setVisible(false);
    const t = setTimeout(() => {
      setDisplayLocation(location);
      setVisible(true);
    }, 150);
    return () => clearTimeout(t);
  }, [location]);

  return (
    <div
      style={{
        opacity: visible ? 1 : 0.01, // never fully transparent — prevents white flash
        transform: visible ? "translateY(0)" : "translateY(5px)",
        transition: "opacity 0.28s cubic-bezier(0.25,0.46,0.45,0.94), transform 0.28s cubic-bezier(0.25,0.46,0.45,0.94)",
        background: "#0f1117",
        minHeight: "100vh",
        willChange: "opacity, transform", // tells browser to composite this layer
      }}
    >
      <Routes location={displayLocation}>
        {/* Default → login */}
        <Route path="/" element={<Navigate to="/login" replace />} />

        {/* Auth */}
        <Route path="/login"    element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Student pages */}
        <Route path="/dashboard/student" element={<StudentDashboard />} />
        <Route path="/assignments"       element={<Assignments />} />
        <Route path="/analytics"         element={<Analytics />} />
        <Route path="/submissions"       element={<Submissions />} />
        <Route path="/submissions/:id"   element={<Submissions />} />
        <Route path="/workspace"         element={<Workspace />} />
        <Route path="/settings"          element={<Settings />} />

        {/* TODO (Frontend): add instructor pages when ready */}
        {/* <Route path="/dashboard/instructor" element={<InstructorDashboard />} /> */}

        {/* Unknown URL → login */}
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