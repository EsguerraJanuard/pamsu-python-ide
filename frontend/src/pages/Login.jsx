/**
 * Login.jsx
 * This is the login page of the PAMSU Python IDE.
 *
 * HOW IT WORKS:
 * - User picks a role (Student or Instructor)
 * - User types their ID/email and password
 * - Clicks "Sign in" → sends data to the backend
 * - Backend checks if the user exists and password is correct
 * - If yes → go to the correct page (student goes to IDE, instructor goes to Dashboard)
 * - If no → show an error message
 *
 * PAGES AFTER LOGIN:
 *   Student    → /ide
 *   Instructor → /dashboard
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

// ─── Feature list shown on the left side ─────────────────────────────────────
// To add or remove a feature, just edit this list.
const features = [
  {
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="7" stroke="#22c55e" strokeWidth="1.5" />
        <path d="M5 8l2 2 4-4" stroke="#22c55e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    label: "AST-driven structural feedback",
  },
  {
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="3" stroke="#38bdf8" strokeWidth="1.5" />
        <circle cx="8" cy="8" r="6.5" stroke="#38bdf8" strokeWidth="1" strokeDasharray="2 2" />
      </svg>
    ),
    label: "Non-intrusive behavioral tracking",
  },
  {
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <rect x="1" y="3" width="14" height="9" rx="1.5" stroke="#a78bfa" strokeWidth="1.5" />
        <path d="M5 7h6M5 9.5h4" stroke="#a78bfa" strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    ),
    label: "Live instructor monitoring",
  },
  {
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M8 2l1.5 3 3.5.5-2.5 2.5.5 3.5L8 10l-3 1.5.5-3.5L3 5.5 6.5 5 8 2z" stroke="#fbbf24" strokeWidth="1.3" strokeLinejoin="round" />
      </svg>
    ),
    label: "Jaccard similarity detection",
  },
];

export default function Login() {

  // ─── These are the values we keep track of ───────────────────────────────
  const [role, setRole] = useState("student");         // which tab is selected
  const [showPassword, setShowPassword] = useState(false); // show/hide password
  const [form, setForm] = useState({ id: "", password: "" }); // what the user typed
  const [mounted, setMounted] = useState(false);       // for page load animation
  const [featuresVisible, setFeaturesVisible] = useState([]); // for feature list animation
  const navigate = useNavigate(); // used to switch pages

  // TODO (Frontend): add this when connecting to the backend
  // const [loading, setLoading] = useState(false); // true while waiting for server reply
  // const [error, setError] = useState(null);      // stores error message if login fails

  // ─── Page load animation (runs once when page opens) ─────────────────────
  useEffect(() => {
    setMounted(true);
    features.forEach((_, i) => {
      setTimeout(() => {
        setFeaturesVisible((prev) => [...prev, i]);
      }, 400 + i * 100);
    });
  }, []);

  // ─── What happens when the user clicks "Sign in" ──────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault(); // stop the page from refreshing

    // TODO (Backend): create this API route in FastAPI → POST /api/auth/login
    // It should accept: { identifier, password, role }
    // It should return:  { token, user: { id, name, role } }
    //
    // TODO (Frontend): uncomment this block when the backend route is ready:
    //
    // setLoading(true);
    // setError(null);
    // try {
    //   const res = await fetch("/api/auth/login", {
    //     method: "POST",
    //     headers: { "Content-Type": "application/json" },
    //     body: JSON.stringify({ identifier: form.id, password: form.password, role }),
    //   });
    //   if (!res.ok) {
    //     const err = await res.json();
    //     setError(err.detail || "Wrong ID or password.");
    //     return;
    //   }
    //   const data = await res.json();
    //   sessionStorage.setItem("token", data.token); // save the token
    //   // send user to the right page based on role
    //   if (role === "student") navigate("/ide");
    //   else navigate("/dashboard");
    // } catch {
    //   setError("Cannot connect to server. Try again.");
    // } finally {
    //   setLoading(false);
    // }

    console.log("Login clicked:", { role, id: form.id }); // remove this later
  };

  // ─── GitHub login button ──────────────────────────────────────────────────
  // TODO (Backend): create GET /api/auth/github to handle GitHub login
  // TODO (Frontend): replace console.log with a redirect to that route
  const handleGitHub = () => {
    console.log("GitHub login — not connected yet");
  };

  // ─── Google login button ──────────────────────────────────────────────────
  // TODO (Backend): create GET /api/auth/google to handle Google login
  // TODO (Frontend): replace console.log with a redirect to that route
  const handleGoogle = () => {
    console.log("Google login — not connected yet");
  };

  // ─── Forgot password button ───────────────────────────────────────────────
  // TODO (Frontend): navigate to /forgot-password page
  // TODO (Backend): create POST /api/auth/forgot-password that sends a reset email
  const handleForgotPassword = () => {
    console.log("Forgot password — not connected yet");
  };

  // ─── "Create one" / Register button ──────────────────────────────────────
  // TODO (Frontend): navigate to /register page
  // NOTE: Only students can register on their own.
  //       Instructor accounts should be created by the admin.
  const handleRegister = () => {
    navigate("/register"); // go to the register page
  };

  // ─── PASSWORD SECURITY NOTE (for the Backend team) ───────────────────────
  // Never save the password as plain text in the database!
  // Use bcrypt to hash it before saving:
  //   from passlib.context import CryptContext
  //   pwd_context = CryptContext(schemes=["bcrypt"])
  //   hashed = pwd_context.hash(plain_password)       ← save this to DB
  //   pwd_context.verify(plain_password, hashed)      ← use this to check login
  // ─────────────────────────────────────────────────────────────────────────

  return (
    <div className="flex min-h-screen bg-[#0f1117] text-white overflow-hidden select-none cursor-default">

      {/* ── Left side — just visuals, no logic here ── */}
      <div
        className="hidden lg:flex flex-col justify-between w-[52%] px-16 py-10 border-r border-white/[0.06] select-none cursor-default"
        style={{
          opacity: mounted ? 1 : 0,
          transform: mounted ? "translateX(0)" : "translateX(-16px)",
          transition: "opacity 0.7s cubic-bezier(0.25,0.46,0.45,0.94), transform 0.7s cubic-bezier(0.25,0.46,0.45,0.94)",
        }}
      >
        {/* Logo — TODO (Frontend): swap the ">_" text with a real logo image when it's ready */}
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-8 h-8 rounded-md bg-[#3b82f6] text-white text-xs font-bold font-mono select-none">
            &gt;_
          </div>
          <span className="font-semibold text-white tracking-wide">Python</span>
        </div>

        {/* Headline */}
        <div className="max-w-md">
          <p
            className="text-xs font-semibold tracking-[0.2em] text-[#3b82f6] uppercase mb-5"
            style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.6s ease 0.15s" }}
          >
            # Python IDE Platform
          </p>
          <h1
            className="text-4xl font-bold leading-tight text-white mb-1 select-none"
            style={{
              opacity: mounted ? 1 : 0,
              transform: mounted ? "translateY(0)" : "translateY(10px)",
              transition: "opacity 0.6s ease 0.2s, transform 0.6s cubic-bezier(0.25,0.46,0.45,0.94) 0.2s",
            }}
          >
            Code with
            <br />
            integrity.
          </h1>
          <h1
            className="text-4xl font-bold leading-tight text-[#3b82f6] mb-6 select-none"
            style={{
              opacity: mounted ? 1 : 0,
              transform: mounted ? "translateY(0)" : "translateY(10px)",
              transition: "opacity 0.6s ease 0.28s, transform 0.6s cubic-bezier(0.25,0.46,0.45,0.94) 0.28s",
            }}
          >
            Learn to think.
          </h1>
          <p
            className="text-sm text-white/50 leading-relaxed mb-8"
            style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.6s ease 0.35s" }}
          >
            A browser-based Python IDE that measures how you code —
            <br />
            not just what you submit. Behavioral tracking, AST analysis,
            <br />
            and real-time instructor oversight.
          </p>

          {/* Feature list — appears one by one on load */}
          <ul className="space-y-3">
            {features.map((f, i) => (
              <li
                key={i}
                className="flex items-center gap-3 text-sm text-white/70"
                style={{
                  opacity: featuresVisible.includes(i) ? 1 : 0,
                  transform: featuresVisible.includes(i) ? "translateX(0)" : "translateX(-8px)",
                  transition: "opacity 0.45s ease, transform 0.45s cubic-bezier(0.25,0.46,0.45,0.94)",
                }}
              >
                <span className="flex-shrink-0">{f.icon}</span>
                {f.label}
              </li>
            ))}
          </ul>
        </div>

        {/* Bottom tech stack label */}
        <p
          className="text-xs text-white/25 font-mono"
          style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.6s ease 0.8s" }}
        >
          Python 3.12 · Judge0 Sandbox · FastAPI
        </p>
      </div>

      {/* ── Right side — the actual login form ── */}
      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div
          className="w-full max-w-[380px]"
          style={{
            opacity: mounted ? 1 : 0,
            transform: mounted ? "translateY(0)" : "translateY(20px)",
            transition: "opacity 0.65s cubic-bezier(0.25,0.46,0.45,0.94) 0.1s, transform 0.65s cubic-bezier(0.25,0.46,0.45,0.94) 0.1s",
          }}
        >
          <div className="text-center mb-7">
            <h2 className="text-lg font-semibold text-white">Sign in to your workspace</h2>
            <p className="text-sm text-white/40 mt-1">Choose your role to continue</p>
          </div>

          {/* TODO (Frontend): show an error box here if login fails
              Example:
              {error && (
                <div className="mb-4 px-4 py-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  {error}
                </div>
              )}
          */}

          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Role selector — Student or Instructor */}
            <div>
              <p className="text-[11px] font-semibold text-white/40 uppercase tracking-widest mb-2">
                I am a
              </p>
              <div className="flex rounded-lg bg-[#1a1d27] p-1 border border-white/[0.08]">
                {["student", "instructor"].map((r) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => {
                      setRole(r);
                      setForm({ id: "", password: "" }); // clear the form when switching roles
                    }}
                    className="flex-1 py-2 rounded-md text-sm font-medium capitalize"
                    style={{
                      background: role === r ? "#ffffff" : "transparent",
                      color: role === r ? "#0f1117" : "rgba(255,255,255,0.4)",
                      boxShadow: role === r ? "0 1px 4px rgba(0,0,0,0.3)" : "none",
                      transition: "background 0.25s ease, color 0.25s ease, box-shadow 0.25s ease",
                    }}
                  >
                    {r.charAt(0).toUpperCase() + r.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* ID or Email input */}
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">
                Institutional ID or Email
              </label>
              <div className="flex items-center gap-2.5 bg-[#1a1d27] border border-white/[0.08] rounded-lg px-3 py-2.5 focus-within:border-[#3b82f6]/60 transition-colors duration-200">
                <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className="flex-shrink-0 text-white/30">
                  <path d="M1 4l6.5 4.5L14 4M1 3h13a.5.5 0 01.5.5v8a.5.5 0 01-.5.5H1a.5.5 0 01-.5-.5v-8A.5.5 0 011 3z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
                </svg>
                <input
                  type="text"
                  placeholder="2024-00001 or you@example.com"
                  value={form.id}
                  onChange={(e) => setForm({ ...form, id: e.target.value })}
                  autoComplete="username"
                  required
                  className="flex-1 bg-transparent text-sm text-white outline-none select-text cursor-text placeholder-white/20"
                  style={{ caretColor: "#3b82f6" }}
                />
              </div>
            </div>

            {/* Password input */}
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">
                Password
              </label>
              <div className="flex items-center gap-2.5 bg-[#1a1d27] border border-white/[0.08] rounded-lg px-3 py-2.5 focus-within:border-[#3b82f6]/60 transition-colors duration-200">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="flex-shrink-0 text-white/30">
                  <rect x="2" y="6" width="10" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
                  <path d="M4.5 6V4.5a2.5 2.5 0 015 0V6" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                </svg>
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  autoComplete="current-password"
                  required
                  className="flex-1 bg-transparent text-sm text-white outline-none select-text cursor-text placeholder-white/20"
                  style={{ caretColor: "#3b82f6" }}
                />
                {/* Eye icon — show or hide the password */}
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-white/30 hover:text-white/60 transition-colors duration-150 flex-shrink-0"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M2 8s2.5-4 6-4 6 4 6 4-2.5 4-6 4-6-4-6-4z" stroke="currentColor" strokeWidth="1.2" />
                      <circle cx="8" cy="8" r="1.5" stroke="currentColor" strokeWidth="1.2" />
                      <path d="M3 3l10 10" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                    </svg>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M2 8s2.5-4 6-4 6 4 6 4-2.5 4-6 4-6-4-6-4z" stroke="currentColor" strokeWidth="1.2" />
                      <circle cx="8" cy="8" r="1.5" stroke="currentColor" strokeWidth="1.2" />
                    </svg>
                  )}
                </button>
              </div>

              <div className="text-right mt-2">
                <button
                  type="button"
                  onClick={handleForgotPassword}
                  className="text-xs text-[#3b82f6] hover:text-[#60a5fa] transition-colors duration-150"
                >
                  Forgot password?
                </button>
              </div>
            </div>

            {/* Sign in button
                TODO (Frontend): while waiting for server reply, change text to "Signing in..."
                and disable the button so the user can't click it twice.
                Example: disabled={loading} — change label to {loading ? "Signing in..." : "Sign in"}
            */}
            <button
              type="submit"
              className="w-full py-2.5 rounded-lg text-white text-sm font-semibold"
              style={{
                background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                transition: "opacity 0.15s ease, transform 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = "0.88";
                e.currentTarget.style.transform = "translateY(-1px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = "1";
                e.currentTarget.style.transform = "translateY(0)";
              }}
              onMouseDown={(e) => {
                e.currentTarget.style.transform = "translateY(0) scale(0.98)";
              }}
              onMouseUp={(e) => {
                e.currentTarget.style.transform = "translateY(-1px)";
              }}
            >
              Sign in
            </button>

            {/* Divider */}
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-white/[0.07]" />
              <span className="text-xs text-white/30">or continue with</span>
              <div className="flex-1 h-px bg-white/[0.07]" />
            </div>

            {/* GitHub and Google buttons
                NOTE: These don't work yet. Wire them up once the backend OAuth routes are ready.
                If you're not doing OAuth, you can remove these two buttons entirely.
            */}
            <div className="grid grid-cols-2 gap-3">
              {[
                {
                  label: "GitHub",
                  onClick: handleGitHub,
                  icon: (
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
                    </svg>
                  ),
                },
                {
                  label: "Google",
                  onClick: handleGoogle,
                  icon: (
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M15.68 8.18c0-.57-.05-1.11-.14-1.64H8v3.1h4.3a3.67 3.67 0 01-1.6 2.41v2h2.6c1.52-1.4 2.38-3.46 2.38-5.87z" fill="#4285F4" />
                      <path d="M8 16c2.16 0 3.97-.71 5.3-1.94l-2.6-2c-.71.48-1.63.76-2.7.76-2.08 0-3.84-1.4-4.47-3.28H.85v2.07A8 8 0 008 16z" fill="#34A853" />
                      <path d="M3.53 9.54A4.8 4.8 0 013.28 8c0-.54.09-1.06.25-1.54V4.39H.85A8 8 0 000 8c0 1.29.31 2.51.85 3.61l2.68-2.07z" fill="#FBBC05" />
                      <path d="M8 3.18c1.17 0 2.22.4 3.05 1.2l2.28-2.28C11.97.79 10.16 0 8 0A8 8 0 00.85 4.39l2.68 2.07C4.16 4.58 5.92 3.18 8 3.18z" fill="#EA4335" />
                    </svg>
                  ),
                },
              ].map(({ label, icon, onClick }) => (
                <button
                  key={label}
                  type="button"
                  onClick={onClick}
                  className="flex items-center justify-center gap-2 py-2.5 rounded-lg bg-[#1a1d27] border border-white/[0.08] text-sm text-white/70"
                  style={{ transition: "border-color 0.2s ease, color 0.2s ease, transform 0.15s ease" }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = "rgba(255,255,255,0.2)";
                    e.currentTarget.style.color = "rgba(255,255,255,1)";
                    e.currentTarget.style.transform = "translateY(-1px)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
                    e.currentTarget.style.color = "rgba(255,255,255,0.7)";
                    e.currentTarget.style.transform = "translateY(0)";
                  }}
                >
                  {icon}
                  {label}
                </button>
              ))}
            </div>

            {/* Register link — only for students */}
            <p className="text-center text-xs text-white/40">
              Don't have an account?{" "}
              <button
                type="button"
                onClick={handleRegister}
                className="text-[#3b82f6] hover:text-[#60a5fa] transition-colors duration-150 font-medium"
              >
                Create one
              </button>
            </p>

          </form>
        </div>
      </div>
    </div>
  );
}