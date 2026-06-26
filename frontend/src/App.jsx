/**
 * App.jsx
 * This is the main file that connects all the pages together.
 *
 * HOW ROUTING WORKS:
 * - When the URL is /login     → shows the Login page
 * - When the URL is /register  → shows the Register page
 * - When the URL is /          → automatically goes to /login
 *
 * PageTransition wraps each page so switching between them
 * has a smooth Apple-style fade instead of a flash.
 *
 * TODO (Frontend): add more routes here as you build more pages:
 *   <Route path="/ide"       element={<PageTransition><StudentIDE /></PageTransition>} />
 *   <Route path="/dashboard" element={<PageTransition><InstructorDashboard /></PageTransition>} />
 */

import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import Login from "./pages/Login";
import Register from "./pages/Register";

// Smooth fade transition between pages
function AnimatedRoutes() {
  const location = useLocation();
  const [displayLocation, setDisplayLocation] = useState(location);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    // Fade out first
    setVisible(false);
    const t = setTimeout(() => {
      setDisplayLocation(location); // swap the page
      setVisible(true);             // fade back in
    }, 180);
    return () => clearTimeout(t);
  }, [location]);

  return (
    <div
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(6px)",
        transition: "opacity 0.3s cubic-bezier(0.25,0.46,0.45,0.94), transform 0.3s cubic-bezier(0.25,0.46,0.45,0.94)",
      }}
    >
      <Routes location={displayLocation}>
        {/* Default — goes to /login */}
        <Route path="/" element={<Navigate to="/login" replace />} />

        {/* Auth pages */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* TODO (Frontend): add these when the pages are ready */}
        {/* <Route path="/ide" element={<StudentIDE />} /> */}
        {/* <Route path="/dashboard" element={<InstructorDashboard />} /> */}

        {/* Any unknown URL goes back to login */}
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