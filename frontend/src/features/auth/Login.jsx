/**
 * Login.jsx
 * Connects to POST /login using OAuth2 FormData format.
 *
 * The backend controls role assignment — no role selector here.
 * After successful login, the user is redirected based on their role.
 *
 * API: POST /login
 * Format: application/x-www-form-urlencoded (OAuth2PasswordRequestForm)
 * Fields: username (email), password
 * Returns: { access_token, token_type, expires_in, user: { user_id, name, school_id, email, role, email_verified } }
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { api, ApiError } from "../../services/api";

const SCHOOL_EMAIL_DOMAIN = "@pampangastateu.edu.ph";
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const features = [
  {
    label: "AST-driven structural feedback",
    color: "#22c55e",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <circle cx="8" cy="8" r="7" stroke="#22c55e" strokeWidth="1.5" />
        <path d="M5 8l2 2 4-4" stroke="#22c55e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    label: "Privacy-conscious behavioral indicators",
    color: "#38bdf8",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <circle cx="8" cy="8" r="3" stroke="#38bdf8" strokeWidth="1.5" />
        <circle cx="8" cy="8" r="6.5" stroke="#38bdf8" strokeWidth="1" strokeDasharray="2 2" />
      </svg>
    ),
  },
  {
    label: "Instructor activity monitoring",
    color: "#a78bfa",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <rect x="1" y="3" width="14" height="9" rx="1.5" stroke="#a78bfa" strokeWidth="1.5" />
        <path d="M5 7h6M5 9.5h4" stroke="#a78bfa" strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    label: "Jaccard similarity review indicators",
    color: "#fbbf24",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M8 2l1.5 3 3.5.5-2.5 2.5.5 3.5L8 10l-3 1.5.5-3.5L3 5.5 6.5 5 8 2z" stroke="#fbbf24" strokeWidth="1.3" strokeLinejoin="round" />
      </svg>
    ),
  },
];

function isValidSchoolEmail(email) {
  return email.trim().toLowerCase().endsWith(SCHOOL_EMAIL_DOMAIN);
}

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [form, setForm] = useState({ email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [capsLock, setCapsLock] = useState(false);

  useEffect(() => {
    const handler = (e) => setCapsLock(e.getModifierState("CapsLock"));
    window.addEventListener("keydown", handler);
    window.addEventListener("keyup", handler);
    return () => {
      window.removeEventListener("keydown", handler);
      window.removeEventListener("keyup", handler);
    };
  }, []);

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (error) setError("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const normalizedEmail = form.email.trim().toLowerCase();

    // Client-side validation before hitting the API
    if (!isValidSchoolEmail(normalizedEmail)) {
      setError(`Use your official school email ending in ${SCHOOL_EMAIL_DOMAIN}.`);
      return;
    }

    if (!form.password) {
      setError("Please enter your password.");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      // Login uses OAuth2PasswordRequestForm — must send as FormData, NOT JSON
      // The backend reads "username" field for the email address
      const formData = new FormData();
      formData.append("username", normalizedEmail);
      formData.append("password", form.password);

      const data = await api.post("/login", formData);

      // Save token and user data via AuthContext
      // login() stores in localStorage under pamsu_access_token, pamsu_user_role, pamsu_user_data
      login(data.access_token, data.user, data.user.role);

      // Redirect based on role returned by the backend
      if (data.user.role === "instructor") {
        navigate("/instructor/dashboard", { replace: true });
      } else {
        navigate("/student/dashboard", { replace: true });
      }
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setError("Invalid email or password.");
        } else if (err.status === 403) {
          setError(err.data?.detail || "Your account is inactive or not verified.");
        } else {
          setError(err.data?.detail || err.message || "Login failed. Please try again.");
        }
      } else if (!navigator.onLine) {
        setError("Cannot connect to the server. Check your internet connection.");
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen overflow-hidden bg-bg-base text-text-main">
      <style>{`
        @keyframes loginFadeLeft {
          from { opacity: 0; transform: translateX(-16px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes loginFadeUp {
          from { opacity: 0; transform: translateY(18px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes featureFadeIn {
          from { opacity: 0; transform: translateX(-8px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes shimmer {
          100% { transform: translateX(100%); }
        }
        @media (prefers-reduced-motion: reduce) {
          .login-animated { animation: none !important; }
        }
      `}</style>

      {/* Premium Background Grid */}
      <div className="absolute inset-0 z-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>

      {/* Left panel — platform info */}
      <section
        className="login-animated hidden w-[52%] flex-col justify-between border-r border-border-subtle px-16 py-10 lg:flex relative z-10"
        style={{ animation: "loginFadeLeft 700ms cubic-bezier(0.25,0.46,0.45,0.94) both" }}
        aria-label="Platform introduction"
      >
        <div className="flex items-center gap-2 select-none cursor-default">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-emerald-500 font-mono text-xs font-bold text-text-main shadow-[0_0_15px_rgba(16,185,129,0.3)]">
            &gt;_
          </div>
          <span className="font-semibold tracking-wide text-text-main">PAMSU Python IDE</span>
        </div>

        <div className="max-w-md select-none cursor-default">
          <p className="mb-5 text-xs font-semibold uppercase tracking-[0.2em] text-text-emerald">
            Python Learning Platform
          </p>
          <h1 className="mb-1 text-4xl font-extrabold leading-tight text-text-main">
            Code with integrity.
          </h1>
          <h2 className="mb-6 text-4xl font-extrabold leading-tight text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-200">
            Learn to think.
          </h2>
          <p className="mb-8 text-sm leading-relaxed text-text-muted">
            A browser-based Python environment that supports structural feedback,
            safe code execution, personal practice, and instructor-guided review.
          </p>
          <ul className="space-y-3">
            {features.map((feature, index) => (
              <li
                key={feature.label}
                className="login-animated flex items-center gap-3 text-sm text-text-muted transition-all duration-300 hover:translate-x-2 hover:text-text-main group"
                style={{ animation: `featureFadeIn 450ms ease ${250 + index * 100}ms both` }}
              >
                <span className="shrink-0 transition-transform duration-300 group-hover:scale-110">{feature.icon}</span>
                <span>{feature.label}</span>
              </li>
            ))}
          </ul>
        </div>

        <p className="font-mono text-xs text-text-main/25 select-none cursor-default">
          Python 3 · FastAPI · Isolated execution
        </p>
      </section>

      {/* Right panel — login form */}
      <section className="relative flex flex-1 items-center justify-center px-6 py-12 z-10">
        {/* Glow effects */}
        <div className="absolute top-0 right-0 -z-10 h-[500px] w-[500px] translate-x-1/3 -translate-y-1/4 rounded-full bg-emerald-500/10 blur-[120px]" />
        <div className="absolute bottom-0 left-0 -z-10 h-[500px] w-[500px] -translate-x-1/3 translate-y-1/4 rounded-full bg-cyan-500/10 blur-[120px]" />

        <div
          className="login-animated w-full max-w-[420px] rounded-2xl border border-border-subtle bg-bg-glass/70 backdrop-blur-2xl p-8 shadow-[0_0_40px_-10px_rgba(16,185,129,0.15)] transition-all duration-500 hover:border-emerald-500/30 hover:shadow-[0_0_50px_-10px_rgba(16,185,129,0.25)]"
          style={{ animation: "loginFadeUp 650ms cubic-bezier(0.25,0.46,0.45,0.94) 100ms both" }}
        >
          <div className="mb-8 text-center select-none cursor-default">
            <h2 className="text-xl font-bold text-text-main">
              Sign in to your workspace
            </h2>
            <p className="mt-2 text-sm text-text-muted">
              Use your verified university account
            </p>
          </div>

          {/* Error message */}
          {error && (
            <div
              role="alert"
              aria-live="polite"
              className="mb-4 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-text-rose"
            >
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            {/* Email */}
            <div>
              <label
                htmlFor="school-email"
                className="mb-1.5 block text-xs font-medium text-text-muted select-none cursor-default"
              >
                School email
              </label>
              <div
                className="auth-input-wrap flex items-center gap-2.5 rounded-xl border border-border-subtle bg-bg-glass px-3 py-3 transition-colors duration-200 focus-within:border-emerald-500/50 focus-within:bg-bg-glass"
                onClick={(e) => e.currentTarget.querySelector('input').focus()}
              >
                <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className="shrink-0 text-text-muted pointer-events-none" aria-hidden="true">
                  <path d="M1 4l6.5 4.5L14 4M1 3h13a.5.5 0 01.5.5v8a.5.5 0 01-.5.5H1a.5.5 0 01-.5-.5v-8A.5.5 0 011 3z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
                </svg>
                <input
                  id="school-email"
                  type="email"
                  value={form.email}
                  onChange={(e) => updateField("email", e.target.value)}
                  placeholder={`yourname${SCHOOL_EMAIL_DOMAIN}`}
                  autoComplete="email"
                  required
                  disabled={isLoading}
                  className="flex-1 bg-transparent text-sm text-text-main outline-none placeholder:text-text-muted disabled:opacity-50"
                  style={{ caretColor: "#10b981" }}
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="text-xs font-medium text-text-muted select-none cursor-default"
                >
                  Password
                </label>
                {capsLock && (
                  <span className="flex items-center gap-1 text-[10px] font-semibold text-text-amber select-none">
                    <svg width="9" height="9" viewBox="0 0 10 12" fill="none" aria-hidden="true">
                      <path d="M5 1L9.5 6H7V9H3V6H0.5L5 1Z" fill="currentColor"/>
                      <rect x="3" y="10.5" width="4" height="1.5" rx="0.5" fill="currentColor"/>
                    </svg>
                    Caps Lock is on
                  </span>
                )}
              </div>
              <div
                className="auth-input-wrap flex items-center gap-2.5 rounded-xl border border-border-subtle bg-bg-glass px-3 py-3 transition-colors duration-200 focus-within:border-emerald-500/50 focus-within:bg-bg-glass"
                onClick={(e) => { if (e.target.closest('button')) return; e.currentTarget.querySelector('input').focus(); }}
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="shrink-0 text-text-muted pointer-events-none" aria-hidden="true">
                  <rect x="2" y="6" width="10" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
                  <path d="M4.5 6V4.5a2.5 2.5 0 015 0V6" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                </svg>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={form.password}
                  onChange={(e) => updateField("password", e.target.value)}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                  disabled={isLoading}
                  className="flex-1 bg-transparent text-sm text-text-main outline-none placeholder:text-text-muted disabled:opacity-50"
                  style={{ caretColor: "#10b981" }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="shrink-0 cursor-pointer text-text-muted transition-colors hover:text-text-muted"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  disabled={isLoading}
                >
                  {showPassword ? (
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                      <path d="M2 8s2.5-4 6-4 6 4 6 4-2.5 4-6 4-6-4-6-4z" stroke="currentColor" strokeWidth="1.2" />
                      <circle cx="8" cy="8" r="1.5" stroke="currentColor" strokeWidth="1.2" />
                      <path d="M3 3l10 10" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                    </svg>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                      <path d="M2 8s2.5-4 6-4 6 4 6 4-2.5 4-6 4-6-4-6-4z" stroke="currentColor" strokeWidth="1.2" />
                      <circle cx="8" cy="8" r="1.5" stroke="currentColor" strokeWidth="1.2" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="group relative overflow-hidden mt-4 w-full rounded-xl bg-emerald-600 hover:bg-emerald-500 py-3 text-sm font-bold tracking-wide text-text-main transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_0_30px_rgba(16,185,129,0.5)] active:translate-y-0 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:hover:shadow-none shadow-[0_0_20px_rgba(16,185,129,0.3)] select-none"
            >
              <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent group-hover:animate-[shimmer_1.5s_infinite] transition-transform"></div>
              
              <span className="relative flex items-center justify-center gap-2">
                {isLoading ? (
                  <>
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    Signing in...
                  </>
                ) : (
                  "Sign in"
                )}
              </span>
            </button>

            <p className="text-center text-xs text-text-muted select-none cursor-default">
              Need a verified university account?{" "}
              <button
                type="button"
                onClick={() => navigate("/register")}
                className="font-medium text-text-emerald transition-colors hover:text-text-emerald hover:underline"
                disabled={isLoading}
              >
                Create one
              </button>
            </p>
          </form>
        </div>
      </section>
    </main>
  );
}