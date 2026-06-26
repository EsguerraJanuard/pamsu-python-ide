/**
 * Register.jsx
 * This is the registration page of the PAMSU Python IDE.
 *
 * HOW IT WORKS:
 * - User picks a role (Student or Instructor)
 * - Fills in their details
 * - Reads and agrees to the Behavioral Tracking Notice
 * - Clicks "Create account" → sends data to the backend
 * - Backend saves the user to the database
 * - Frontend redirects to /login after success
 *
 * TODO (Backend): create this API route in FastAPI → POST /api/auth/register
 * Request body: {
 *   first_name, last_name, institutional_id, email, password, role
 * }
 * Response: { message: "Account created successfully" }
 *
 * NOTE: Hash the password with bcrypt before saving. Never save plain text.
 * NOTE: Instructor accounts — you can allow self-registration here or block it
 *       and require admin creation. Your choice as a team.
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

// Password strength checker — checks how strong the password is
function getPasswordStrength(password) {
  if (!password) return null;
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  if (score === 1) return { label: "Weak — add uppercase or numbers", color: "#ef4444", width: "25%" };
  if (score === 2) return { label: "Fair — add a symbol to strengthen", color: "#f59e0b", width: "50%" };
  if (score === 3) return { label: "Good — almost there", color: "#3b82f6", width: "75%" };
  if (score === 4) return { label: "Strong password", color: "#22c55e", width: "100%" };
}

export default function Register() {
  const [role, setRole] = useState("student");
  const [showPassword, setShowPassword] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const [mounted, setMounted] = useState(false);
  const navigate = useNavigate(); // used to switch pages
  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    institutionalId: "",
    email: "",
    password: "",
  });

  // TODO (Frontend): add these when connecting to backend
  // const [loading, setLoading] = useState(false);
  // const [error, setError] = useState(null);
  // const [success, setSuccess] = useState(false);

  const strength = getPasswordStrength(form.password);

  // Page load animation
  useEffect(() => {
    setMounted(true);
  }, []);

  const handleChange = (field) => (e) => {
    setForm({ ...form, [field]: e.target.value });
  };

  // What happens when user clicks "Create account"
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!agreed) return; // don't submit if checkbox not checked

    // TODO (Backend): connect to POST /api/auth/register
    // TODO (Frontend): uncomment this block when backend is ready
    //
    // setLoading(true);
    // setError(null);
    // try {
    //   const res = await fetch("/api/auth/register", {
    //     method: "POST",
    //     headers: { "Content-Type": "application/json" },
    //     body: JSON.stringify({
    //       first_name: form.firstName,
    //       last_name: form.lastName,
    //       institutional_id: form.institutionalId,
    //       email: form.email,
    //       password: form.password,
    //       role,
    //     }),
    //   });
    //   if (!res.ok) {
    //     const err = await res.json();
    //     setError(err.detail || "Registration failed.");
    //     return;
    //   }
    //   navigate("/login"); // go to login after success
    // } catch {
    //   setError("Cannot connect to server. Try again.");
    // } finally {
    //   setLoading(false);
    // }

    console.log("Register:", { role, ...form });
  };

  // Shared input field style
  const inputWrapClass =
    "flex items-center gap-2.5 bg-[#1a1d27] border border-white/[0.08] rounded-lg px-3 py-2.5 focus-within:border-[#3b82f6]/60 transition-colors duration-200";
  const inputClass =
    "flex-1 bg-transparent text-sm text-white outline-none select-text cursor-text placeholder-white/20";

  return (
    <div
      className="min-h-screen bg-[#0f1117] text-white flex items-start justify-center px-4 py-10 select-none cursor-default"
      style={{
        opacity: mounted ? 1 : 0,
        transition: "opacity 0.5s ease",
      }}
    >
      {/* Card — full width on mobile, fixed width on tablet/desktop */}
      <div className="w-full max-w-[520px]">

        {/* ── Header ── */}
        <div className="flex items-start justify-between mb-6">
          <div>
            {/* Logo — TODO (Frontend): replace with real logo image when ready */}
            <div className="flex items-center gap-2 mb-4">
              <div className="flex items-center justify-center w-7 h-7 rounded-md bg-[#3b82f6] text-white text-xs font-bold font-mono">
                &gt;_
              </div>
              <span className="font-semibold text-white text-sm">
                Py<span className="text-[#3b82f6]">thon</span>
              </span>
            </div>
            <h1 className="text-xl font-bold text-white">Create your account</h1>
            <p className="text-sm text-white/40 mt-0.5">Fill in your details to get started</p>
          </div>

          {/* Step dots — visual only, shows progress feel */}
          <div className="flex items-center gap-1.5 mt-1">
            <div className="w-2 h-2 rounded-full bg-[#22c55e]" />
            <div className="w-2 h-2 rounded-full bg-[#3b82f6]" />
          </div>
        </div>

        {/* TODO (Frontend): show error here if registration fails
            {error && (
              <div className="mb-4 px-4 py-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                {error}
              </div>
            )}
        */}

        <form onSubmit={handleSubmit} className="space-y-4">

          {/* ── Role selector ── */}
          <div>
            <p className="text-xs font-semibold text-white/40 uppercase tracking-widest mb-2">
              I am registering as a
            </p>
            <div className="flex rounded-lg bg-[#1a1d27] p-1 border border-white/[0.08]">
              {["student", "instructor"].map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => {
                    setRole(r);
                    setForm({ firstName: "", lastName: "", institutionalId: "", email: "", password: "" });
                    setAgreed(false);
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

          {/* ── First name + Last name (side by side on tablet+, stacked on mobile) ── */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">First name</label>
              <div className={inputWrapClass}>
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="flex-shrink-0 text-white/30">
                  <circle cx="7" cy="4.5" r="2.5" stroke="currentColor" strokeWidth="1.2" />
                  <path d="M1.5 12.5c0-3 2.5-5 5.5-5s5.5 2 5.5 5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                </svg>
                <input
                  type="text"
                  placeholder="Miguel"
                  value={form.firstName}
                  onChange={handleChange("firstName")}
                  required
                  className={inputClass}
                  style={{ caretColor: "#3b82f6" }}
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Last name</label>
              <div className={inputWrapClass}>
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="flex-shrink-0 text-white/30">
                  <circle cx="7" cy="4.5" r="2.5" stroke="currentColor" strokeWidth="1.2" />
                  <path d="M1.5 12.5c0-3 2.5-5 5.5-5s5.5 2 5.5 5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                </svg>
                <input
                  type="text"
                  placeholder="Juan"
                  value={form.lastName}
                  onChange={handleChange("lastName")}
                  required
                  className={inputClass}
                  style={{ caretColor: "#3b82f6" }}
                />
              </div>
            </div>
          </div>

          {/* ── Institutional ID ──
              TODO (Backend): validate format — students use YYYY-NNNNN (e.g. 2024-00001)
              Instructors may use employee ID or email instead.
          ── */}
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1.5">Institutional ID</label>
            <div className={inputWrapClass}>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="flex-shrink-0 text-white/30">
                <rect x="1" y="2" width="12" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
                <path d="M4 6h2M4 8.5h6M8 6h2" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
              </svg>
              <input
                type="text"
                placeholder="2024-00001"
                value={form.institutionalId}
                onChange={handleChange("institutionalId")}
                required
                className={inputClass}
                style={{ caretColor: "#3b82f6" }}
              />
            </div>
            <p className="text-[11px] text-white/30 mt-1.5 flex items-center gap-1">
              <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                <circle cx="5.5" cy="5.5" r="4.5" stroke="currentColor" strokeWidth="1" />
                <path d="M5.5 4.5v3M5.5 3.5v.5" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
              </svg>
              Your ID is printed on your school ID card
            </p>
          </div>

          {/* ── Institutional Email ── */}
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1.5">Institutional Email</label>
            <div className={inputWrapClass}>
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className="flex-shrink-0 text-white/30">
                <path d="M1 4l6.5 4.5L14 4M1 3h13a.5.5 0 01.5.5v8a.5.5 0 01-.5.5H1a.5.5 0 01-.5-.5v-8A.5.5 0 011 3z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
              </svg>
              <input
                type="email"
                placeholder="mjuan@student.edu.ph"
                value={form.email}
                onChange={handleChange("email")}
                required
                className={inputClass}
                style={{ caretColor: "#3b82f6" }}
              />
            </div>
          </div>

          {/* ── Password ──
              TODO (Backend): enforce minimum 8 chars server-side too, not just frontend.
              Hash with bcrypt before saving to database.
          ── */}
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1.5">Password</label>
            <div className={inputWrapClass}>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="flex-shrink-0 text-white/30">
                <rect x="2" y="6" width="10" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
                <path d="M4.5 6V4.5a2.5 2.5 0 015 0V6" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
              </svg>
              <input
                type={showPassword ? "text" : "password"}
                placeholder="At least 8 characters"
                value={form.password}
                onChange={handleChange("password")}
                minLength={8}
                required
                className={inputClass}
                style={{ caretColor: "#3b82f6" }}
              />
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

            {/* Password strength bar — shows as user types */}
            {form.password && strength && (
              <div className="mt-2">
                <div className="h-1 w-full bg-white/[0.06] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: strength.width, background: strength.color }}
                  />
                </div>
                <p className="text-[11px] mt-1" style={{ color: strength.color }}>
                  Strength: {strength.label}
                </p>
              </div>
            )}
          </div>

          {/* ── Behavioral Tracking Notice ──
              This box explains to users what data is collected.
              Required by the thesis — do not remove.
              TODO (Backend): log that the user consented (store consent timestamp in DB).
          ── */}
          <div className="rounded-xl border border-white/[0.08] bg-[#1a1d27] p-4">
            <div className="flex items-center gap-2 mb-2">
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className="text-[#f59e0b] flex-shrink-0">
                <path d="M7.5 1.5l1.3 2.7 3 .4-2.2 2.1.5 3L7.5 8.2 4.9 9.7l.5-3L3.2 4.6l3-.4L7.5 1.5z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
                <path d="M7.5 11v2.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
              </svg>
              <span className="text-xs font-semibold text-white">Behavioral Tracking Notice</span>
            </div>
            <p className="text-[11px] text-white/50 leading-relaxed mb-3">
              By creating an account, you acknowledge that this platform collects non-intrusive behavioral
              metadata during coding sessions to support academic integrity evaluation.
            </p>
            <ul className="space-y-1.5 mb-4">
              {[
                "Tab-switch frequency and idle time are logged during active sessions",
                "Copy-paste events are restricted and recorded during graded activities",
                "Submitted code is analyzed for structural patterns and similarity checks",
                "Data is visible only to your enrolled course instructors",
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-[11px] text-white/40">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="flex-shrink-0 mt-0.5 text-[#f59e0b]">
                    <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1" />
                    <path d="M6 4v2.5" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
                    <circle cx="6" cy="8.5" r="0.5" fill="currentColor" />
                  </svg>
                  {item}
                </li>
              ))}
            </ul>

            {/* Consent checkbox — required to submit */}
            <label className="flex items-start gap-3 cursor-pointer group">
              <div
                className="flex-shrink-0 mt-0.5 w-4 h-4 rounded border transition-all duration-150"
                style={{
                  background: agreed ? "#3b82f6" : "transparent",
                  borderColor: agreed ? "#3b82f6" : "rgba(255,255,255,0.2)",
                }}
                onClick={() => setAgreed(!agreed)}
              >
                {agreed && (
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M4 8l3 3 5-5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </div>
              <span
                className="text-[11px] leading-relaxed select-text cursor-text"
                style={{ color: agreed ? "rgba(255,255,255,0.6)" : "rgba(255,255,255,0.35)" }}
                onClick={() => setAgreed(!agreed)}
              >
                I have read and understood the behavioral tracking notice. I consent to the collection of this
                data for academic integrity purposes as described above.
              </span>
            </label>
          </div>

          {/* ── Bottom row — Sign in link + Create account button ── */}
          <div className="flex items-center justify-between pt-1">
            <p className="text-xs text-white/40">
              Already have an account?{" "}
              {/* TODO (Frontend): replace with navigate("/login") */}
              <button
                type="button"
                className="text-[#3b82f6] hover:text-[#60a5fa] transition-colors duration-150 font-medium"
                onClick={() => navigate("/login")}
              >
                Sign in
              </button>
            </p>

            {/* Create account button — disabled until checkbox is checked */}
            <button
              type="submit"
              disabled={!agreed}
              className="px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200"
              style={{
                background: agreed
                  ? "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)"
                  : "rgba(255,255,255,0.06)",
                color: agreed ? "#ffffff" : "rgba(255,255,255,0.25)",
                cursor: agreed ? "pointer" : "not-allowed",
                // TODO (Frontend): when loading is true, show "Creating..." and disable
              }}
              onMouseEnter={(e) => {
                if (!agreed) return;
                e.currentTarget.style.opacity = "0.88";
                e.currentTarget.style.transform = "translateY(-1px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = "1";
                e.currentTarget.style.transform = "translateY(0)";
              }}
              onMouseDown={(e) => {
                if (!agreed) return;
                e.currentTarget.style.transform = "scale(0.98)";
              }}
              onMouseUp={(e) => {
                if (!agreed) return;
                e.currentTarget.style.transform = "translateY(-1px)";
              }}
            >
              Create account
            </button>
          </div>

        </form>
      </div>
    </div>
  );
}