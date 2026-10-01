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
import { useTheme } from "../theme/ThemeContext";
import { api, ApiError } from "../../services/api";
import { ThemeToggle } from "../theme/ThemeToggle";

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
    const handler = (e) => {
        if (typeof e.getModifierState === "function") {
            setCapsLock(e.getModifierState("CapsLock"));
        }
    };
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

  const [isDarkMode, setIsDarkMode] = useState(() => {
    return document.documentElement.classList.contains("dark");
  });

  const toggleTheme = () => {
    const isDark = document.documentElement.classList.contains("dark");
    if (isDark) {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
      setIsDarkMode(false);
    } else {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
      setIsDarkMode(true);
    }
  };

  const handleGuestLogin = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.post("/auth/guest");
      const { access_token, user } = response.data || response;
      login(access_token, user, user.role);
    } catch (err) {
      setError(err.response?.data?.detail || "Guest login failed.");
    } finally {
      setIsLoading(false);
    }
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
    <main className="flex min-h-screen bg-bg-base text-text-main">
      <style>{`
        @keyframes loginFade {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-login-fade {
          animation: loginFade 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }
        .delay-100 { animation-delay: 100ms; }
        .delay-200 { animation-delay: 200ms; }
        .delay-300 { animation-delay: 300ms; }
      `}</style>

      {/* Left Side: Brand Panel (Hidden on Mobile) */}
      <div className="relative hidden lg:flex lg:w-[45%] flex-col justify-between bg-psu-maroon overflow-hidden px-14 py-16 text-white shadow-2xl z-10">
        {/* Subtle Background Pattern / Gradient */}
        <div className="absolute inset-0 z-0 opacity-20">
          <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-psu-gold blur-[100px]"></div>
          <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-psu-red blur-[120px]"></div>
        </div>

        <div className="relative z-10 animate-login-fade opacity-0">
          <div className="flex items-center gap-3">
            <img src="/school_logo.png" alt="PSU Logo" className="h-10 w-10 object-contain drop-shadow-md" />
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-psu-gold/90">Pampanga State University</p>
              <p className="text-lg font-black tracking-tight text-white">Python IDE</p>
            </div>
          </div>
        </div>

        <div className="relative z-10 my-auto animate-login-fade delay-100 opacity-0">
          <span className="mb-6 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-psu-gold border border-white/20 backdrop-blur-md">
            <span className="w-1.5 h-1.5 rounded-full bg-psu-gold animate-pulse"></span>
            Enterprise Platform
          </span>
          <h1 className="text-4xl font-black tracking-tight text-white sm:text-5xl xl:text-6xl leading-[1.1]">
            Code with integrity.<br />
            <span className="text-psu-gold">Learn to think.</span>
          </h1>
          <p className="mt-6 max-w-md text-sm leading-relaxed text-white/80">
            An intelligent, browser-based Python workspace built exclusively for the Pampanga State University Computer Science department.
          </p>
          
          <ul className="mt-8 space-y-4">
            {features.map((feature, idx) => (
              <li key={idx} className="flex items-center gap-3 text-sm font-medium text-white/90">
                <div 
                  className="flex h-6 w-6 items-center justify-center rounded-full bg-white/10" 
                  style={{ color: feature.color }}
                >
                  {feature.icon}
                </div>
                {feature.label}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative z-10 flex items-center justify-between text-xs font-medium text-white/50 animate-login-fade delay-200 opacity-0">
          <p>&copy; 2026 Pampanga State University</p>
        </div>
      </div>

      {/* Right Side: Login Form */}
      <div className="flex flex-1 items-center justify-center bg-bg-base px-6 py-12 lg:px-8 relative z-0">
          {/* TEMP SEED BUTTON FOR DEMO */}
          <button 
            type="button"
            onClick={async () => {
              try {
                const res = await api.get("/admin/seed-production");
                alert(res.data?.message || "Success!");
              } catch (err) {
                alert("Backend still deploying. Please try again in 1 minute. " + (err.message || ""));
              }
            }}
            className="absolute bottom-4 right-4 text-[10px] text-text-muted hover:text-psu-maroon underline"
          >
            Initialize Admin Account (Demo)
          </button>

        
        {/* Mobile Logo Header */}
        <div className="absolute top-8 left-6 lg:hidden flex items-center gap-3 animate-login-fade opacity-0">
          <img src="/school_logo.png" alt="PSU Logo" className="h-8 w-8 object-contain drop-shadow-md" />
          <div>
            <p className="text-[9px] font-bold uppercase tracking-widest text-text-muted">Pampanga State University</p>
            <p className="text-base font-black tracking-tight text-text-main">Python IDE</p>
          </div>
        </div>

        

        <div className="w-full max-w-[480px] animate-login-fade delay-100 opacity-0">
          <div className="mb-8 text-center sm:text-left">
            <h2 className="text-2xl font-black text-text-main">
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
              className="mb-6 flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-text-rose shadow-sm"
            >
              <svg className="mt-0.5 h-4 w-4 shrink-0 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p>{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            {/* Email */}
            <div>
              <label htmlFor="school-email" className="mb-1.5 block text-xs font-bold text-text-muted uppercase tracking-wider">
                School email
              </label>
              <div
                className="group flex items-center gap-3 rounded-xl border border-border-subtle bg-bg-glass px-4 py-3 transition-all duration-300 focus-within:border-psu-maroon/50 focus-within:bg-bg-glass focus-within:shadow-[0_0_15px_rgba(128,0,0,0.1)] hover:border-border-strong cursor-text"
                onClick={(e) => e.currentTarget.querySelector('input').focus()}
              >
                <svg width="16" height="16" viewBox="0 0 15 15" fill="none" className="shrink-0 text-text-muted pointer-events-none transition-colors group-focus-within:text-psu-maroon" aria-hidden="true">
                  <path d="M1 4l6.5 4.5L14 4M1 3h13a.5.5 0 01.5.5v8a.5.5 0 01-.5.5H1a.5.5 0 01-.5-.5v-8A.5.5 0 011 3z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
                </svg>
                <input
                  id="school-email"
                  type="email"
                  value={form.email}
                  onChange={(e) => updateField("email", e.target.value)}
                  placeholder="name@pampangastateu.edu.ph"
                  autoComplete="email"
                  required
                  disabled={isLoading}
                  className="flex-1 bg-transparent text-sm font-medium text-text-main outline-none placeholder:text-text-muted/50 disabled:opacity-50"
                  style={{ caretColor: "var(--color-psu-gold, #eeb319)" }}
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <label htmlFor="password" className="text-xs font-bold text-text-muted uppercase tracking-wider">
                  Password
                </label>
              </div>
              <div
                className="group flex items-center gap-3 rounded-xl border border-border-subtle bg-bg-glass px-4 py-3 transition-all duration-300 focus-within:border-psu-maroon/50 focus-within:bg-bg-glass focus-within:shadow-[0_0_15px_rgba(128,0,0,0.1)] hover:border-border-strong cursor-text"
                onClick={(e) => { if (e.target.closest('button')) return; e.currentTarget.querySelector('input').focus(); }}
              >
                <svg width="16" height="16" viewBox="0 0 14 14" fill="none" className="shrink-0 text-text-muted pointer-events-none transition-colors group-focus-within:text-psu-maroon" aria-hidden="true">
                  <rect x="2" y="6" width="10" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
                  <path d="M4.5 6V4.5a2.5 2.5 0 015 0V6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={form.password}
                  onChange={(e) => updateField("password", e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  required
                  disabled={isLoading}
                  className="flex-1 bg-transparent text-sm font-medium tracking-widest text-text-main outline-none placeholder:text-text-muted/50 placeholder:tracking-normal disabled:opacity-50"
                  style={{ caretColor: "var(--color-psu-gold, #eeb319)" }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="shrink-0 cursor-pointer text-text-muted transition-colors hover:text-text-main"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  disabled={isLoading}
                >
                  {showPassword ? (
                    <svg width="18" height="18" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                      <path d="M2 8s2.5-4 6-4 6 4 6 4-2.5 4-6 4-6-4-6-4z" stroke="currentColor" strokeWidth="1.5" />
                      <circle cx="8" cy="8" r="1.5" stroke="currentColor" strokeWidth="1.5" />
                      <path d="M3 3l10 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                      <path d="M2 8s2.5-4 6-4 6 4 6 4-2.5 4-6 4-6-4-6-4z" stroke="currentColor" strokeWidth="1.5" />
                      <circle cx="8" cy="8" r="1.5" stroke="currentColor" strokeWidth="1.5" />
                    </svg>
                  )}
                </button>
              </div>
              {capsLock && (
                <p className="mt-2 flex items-center gap-1.5 text-[10px] font-bold text-amber-500">
                  <svg width="10" height="10" viewBox="0 0 10 12" fill="none" aria-hidden="true">
                    <path d="M5 1L9.5 6H7V9H3V6H0.5L5 1Z" fill="currentColor"/>
                    <rect x="3" y="10.5" width="4" height="1.5" rx="0.5" fill="currentColor"/>
                  </svg>
                  Caps Lock is ON
                </p>
              )}
            </div>

            {/* Buttons */}
            <div className="pt-2 animate-login-fade delay-200 opacity-0">
              <button
                type="submit"
                disabled={isLoading}
                className="group relative overflow-hidden flex w-full items-center justify-center gap-2 rounded-xl bg-psu-maroon px-4 py-3.5 text-sm font-bold tracking-wide text-white shadow-lg shadow-psu-maroon/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-psu-maroon/50 active:translate-y-0 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-60"
              >
                <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent group-hover:animate-[shimmer_1.5s_infinite] transition-transform"></div>
                {isLoading ? (
                  <>
                    <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    Signing in...
                  </>
                ) : (
                  "Sign In to Workspace"
                )}
              </button>
              
              <div className="relative mt-6 mb-6">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-border-subtle"></div></div>
                <div className="relative flex justify-center"><span className="bg-bg-base px-3 text-[10px] font-bold uppercase tracking-wider text-text-muted">Or</span></div>
              </div>

              <button
                type="button"
                onClick={handleGuestLogin}
                disabled={isLoading}
                className="group flex w-full items-center justify-center gap-2 rounded-xl border border-border-strong bg-bg-glass px-4 py-3 text-sm font-bold text-text-main shadow-sm transition-all duration-300 hover:-translate-y-1 hover:bg-bg-glass-hover hover:shadow-md active:translate-y-0 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-60"
              >
                Continue as Guest Student
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  );
}
