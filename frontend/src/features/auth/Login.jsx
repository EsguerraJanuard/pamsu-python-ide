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

import { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { useAuth, homePathForRole, consumeSessionExpiredNotice } from "./AuthContext";
import { api, ApiError, TIMEOUT_ERROR_STATUS } from "../../services/api";

const SCHOOL_EMAIL_DOMAIN = "@pampangastateu.edu.ph";

// The backend's hosting stops it when idle, and the first request afterwards
// waits about a minute for it to start. The page wakes the server as soon as
// it opens, and sign-in waits longer than the 15 s default instead of failing.
const SIGN_IN_TIMEOUT_MS = 90000;
// With no answer after this long, tell the user the server is starting.
const SLOW_SERVER_HINT_MS = 4000;
const SERVER_STARTING_ERROR = "The server is taking too long to start. Please try again in a moment.";

const features = [
  {
    label: "AST-driven structural feedback",
    color: "#eaae19",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <circle cx="8" cy="8" r="7" stroke="#eaae19" strokeWidth="1.5" />
        <path d="M5 8l2 2 4-4" stroke="#eaae19" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    label: "Privacy-conscious behavioral indicators",
    color: "#eaae19",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <circle cx="8" cy="8" r="3" stroke="#eaae19" strokeWidth="1.5" />
        <circle cx="8" cy="8" r="6.5" stroke="#eaae19" strokeWidth="1" strokeDasharray="2 2" />
      </svg>
    ),
  },
  {
    label: "Instructor activity monitoring",
    color: "#eaae19",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <rect x="1" y="3" width="14" height="9" rx="1.5" stroke="#eaae19" strokeWidth="1.5" />
        <path d="M5 7h6M5 9.5h4" stroke="#eaae19" strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    label: "Jaccard similarity review indicators",
    color: "#eaae19",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M8 2l1.5 3 3.5.5-2.5 2.5.5 3.5L8 10l-3 1.5.5-3.5L3 5.5 6.5 5 8 2z" stroke="#eaae19" strokeWidth="1.3" strokeLinejoin="round" />
      </svg>
    ),
  },
];

function isValidSchoolEmail(email) {
  return email.trim().toLowerCase().endsWith(SCHOOL_EMAIL_DOMAIN);
}

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [notice] = useState(() => {
    if (location.state?.passwordReset) return "Your password was reset. Sign in with your new password.";
    if (consumeSessionExpiredNotice()) return "Your session ended. Please sign in again.";
    return "";
  });

  const [form, setForm] = useState({ email: location.state?.email || "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [capsLock, setCapsLock] = useState(false);
  const [serverStarting, setServerStarting] = useState(false);
  const [slowSignIn, setSlowSignIn] = useState(false);
  const slowSignInTimer = useRef(null);

  useEffect(() => {
    let active = true;
    const hintTimer = window.setTimeout(() => {
      if (active) setServerStarting(true);
    }, SLOW_SERVER_HINT_MS);
    // Errors are ignored here; sign-in reports its own.
    api
      .get("/health", {}, SIGN_IN_TIMEOUT_MS)
      .catch(() => {})
      .finally(() => {
        window.clearTimeout(hintTimer);
        if (active) setServerStarting(false);
      });
    return () => {
      active = false;
      window.clearTimeout(hintTimer);
    };
  }, []);

  useEffect(() => () => window.clearTimeout(slowSignInTimer.current), []);

  const startSlowSignInHint = () => {
    window.clearTimeout(slowSignInTimer.current);
    slowSignInTimer.current = window.setTimeout(() => setSlowSignIn(true), SLOW_SERVER_HINT_MS);
  };

  const stopSlowSignInHint = () => {
    window.clearTimeout(slowSignInTimer.current);
    setSlowSignIn(false);
  };

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

  const redirectAfterLogin = (role) => {
    const from = location.state?.from?.pathname;
    const home = homePathForRole(role);
    // Only return to the attempted page when it belongs to the same role area.
    const target = from && from.startsWith(home.split("/").slice(0, 2).join("/") + "/") ? from + (location.state.from.search || "") : home;
    navigate(target, { replace: true });
  };

  const handleGuestLogin = async () => {
    setIsLoading(true);
    setError("");
    startSlowSignInHint();
    try {
      const data = await api.post("/guest", undefined, {}, SIGN_IN_TIMEOUT_MS);
      login(data.access_token, data.user, data.user.role);
      redirectAfterLogin(data.user.role);
    } catch (err) {
      if (err instanceof ApiError && err.status === 0) {
        setError("Cannot reach the server. Check your connection and try again.");
      } else if (err instanceof ApiError && err.status === TIMEOUT_ERROR_STATUS) {
        setError(SERVER_STARTING_ERROR);
      } else if (err instanceof ApiError && err.status >= 500) {
        setError("Guest access is temporarily unavailable. Please sign in with your university account.");
      } else {
        setError(err instanceof ApiError ? err.message : "Guest access failed. Please try again.");
      }
    } finally {
      stopSlowSignInHint();
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
    startSlowSignInHint();

    try {
      // Login uses OAuth2PasswordRequestForm — must send as FormData, NOT JSON
      // The backend reads "username" field for the email address
      const formData = new FormData();
      formData.append("username", normalizedEmail);
      formData.append("password", form.password);

      const data = await api.post("/login", formData, {}, SIGN_IN_TIMEOUT_MS);

      // Save token and user data via AuthContext
      // login() stores in localStorage under pamsu_access_token, pamsu_user_role, pamsu_user_data
      login(data.access_token, data.user, data.user.role);

      redirectAfterLogin(data.user.role);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 0) {
          setError("Cannot reach the server. Check your connection and try again.");
        } else if (err.status === TIMEOUT_ERROR_STATUS) {
          setError(SERVER_STARTING_ERROR);
        } else if (err.status === 401) {
          setError("Invalid email or password.");
        } else if (err.status === 429) {
          setError("Too many sign-in attempts. Please wait a minute and try again.");
        } else if (err.status === 403) {
          setError(typeof err.data?.detail === "string" ? err.data.detail : "Your account is inactive or not verified.");
        } else {
          setError(err.status >= 500 ? "The server ran into a problem. Please try again shortly." : err.message || "Sign-in failed. Please try again.");
        }
      } else if (!navigator.onLine) {
        setError("Cannot connect to the server. Check your internet connection.");
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      stopSlowSignInHint();
      setIsLoading(false);
    }
  };

  return (
    // Locked to the viewport: 100vh fallback, 100dvh where supported (mobile
    // browser chrome). Spacing below scales with viewport height via clamp(),
    // and the form column scrolls internally only as a last resort on very
    // short screens, so the document itself never scrolls.
    <main className="flex h-screen w-full overflow-hidden bg-bg-base text-text-main supports-[height:100dvh]:h-dvh">
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
      <div className="relative hidden lg:flex lg:w-[45%] flex-col justify-between bg-psu-maroon overflow-hidden px-14 py-[clamp(2rem,6vh,4rem)] text-white shadow-2xl z-10">
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
          <span className="mb-[clamp(0.75rem,3vh,1.5rem)] inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-psu-gold border border-white/20 backdrop-blur-md">
            <span className="w-1.5 h-1.5 rounded-full bg-psu-gold animate-pulse"></span>
            Enterprise Platform
          </span>
          <h1 className="text-[clamp(2rem,min(6.5vh,4.2vw),3.75rem)] font-black tracking-tight text-white leading-[1.1]">
            Code with<br />
            integrity.<br />
            <span className="text-psu-gold">Learn to think.</span>
          </h1>
          <p className="mt-[clamp(0.75rem,3vh,1.5rem)] max-w-md text-base leading-relaxed text-white/80">
            An intelligent, browser-based Python workspace built exclusively for the Pampanga State University College of Computing Studies Department.
          </p>

          {/* Decorative list: dropped on short screens rather than clipped */}
          <ul className="mt-[clamp(1rem,3.5vh,2rem)] space-y-[clamp(0.5rem,1.6vh,1rem)] [@media(max-height:640px)]:hidden">
            {features.map((feat, idx) => (
              <li key={idx} className="flex items-center gap-3 text-sm font-medium text-white/90">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-white/10 backdrop-blur-sm border border-white/5">
                  {feat.icon}
                </div>
                {feat.label}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative z-10 flex items-center justify-between text-xs font-medium text-white/50 animate-login-fade delay-200 opacity-0 mt-[clamp(1rem,4vh,3rem)]">
          <p>&copy; 2026 Pampanga State University</p>
        </div>
      </div>

      {/* Right Side: Login Form */}
      {/* min-h-0 + overflow-y-auto: if content still exceeds a very short
          viewport, this column scrolls instead of the page or clipping. */}
      <div className="relative z-0 flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto overscroll-contain bg-white px-6 py-[clamp(0.75rem,3.5vh,3rem)] lg:px-8">

        {/* Mobile Logo Header (in flow so it never overlaps the form) */}
        <div className="mb-[clamp(0.75rem,2.5vh,2rem)] flex shrink-0 items-center gap-3 lg:hidden animate-login-fade opacity-0">
          <img src="/school_logo.png" alt="PSU Logo" className="h-8 w-8 object-contain drop-shadow-md" />
          <div>
            <p className="text-[9px] font-bold uppercase tracking-widest text-text-muted">Pampanga State University</p>
            <p className="text-base font-black tracking-tight text-text-main">Python IDE</p>
          </div>
        </div>

        {/* m-auto centres the form but collapses to 0 when the column overflows,
            so the top is never cut off. */}
        <div className="m-auto w-full max-w-[440px] shrink-0 animate-login-fade delay-100 opacity-0">
          <div className="mb-[clamp(0.75rem,3.5vh,2rem)] text-center sm:text-left">
            <h2 className="text-[clamp(1.5rem,4.6vh,2.25rem)] sm:text-[clamp(1.5rem,4.6vh,2.5rem)] font-black tracking-tight text-text-main leading-tight">
              Sign in to your workspace
            </h2>
            <p className="mt-[clamp(0.375rem,1.2vh,0.75rem)] text-[15px] text-text-muted">
              Use your verified university account
            </p>
          </div>

          {notice && !error && (
            <div role="status" className="mb-[clamp(0.75rem,2.5vh,1.5rem)] rounded-xl border border-psu-maroon/20 bg-psu-cream p-[clamp(0.625rem,1.6vh,1rem)] text-sm font-medium text-psu-maroon">
              {notice}
            </div>
          )}

          {(serverStarting || slowSignIn) && !error && (
            <div role="status" className="mb-[clamp(0.75rem,2.5vh,1.5rem)] flex items-start gap-3 rounded-xl border border-border-subtle bg-bg-alt p-[clamp(0.625rem,1.6vh,1rem)] text-sm text-text-muted">
              <svg className="mt-0.5 h-4 w-4 shrink-0 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <p>Starting the server. The first sign-in after a quiet period can take up to a minute.</p>
            </div>
          )}

          {/* Error message */}
          {error && (
            <div
              role="alert"
              aria-live="polite"
              id="login-error" className="mb-[clamp(0.75rem,2.5vh,1.5rem)] flex items-start gap-3 rounded-xl border border-psu-red/25 bg-psu-red/[0.06] p-[clamp(0.625rem,1.6vh,1rem)] text-sm text-psu-red"
            >
              <svg className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p>{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-[clamp(0.625rem,2vh,1.25rem)]" noValidate>
            {/* Email */}
            <div>
              <label htmlFor="school-email" className="mb-[clamp(0.25rem,0.8vh,0.5rem)] block text-[13px] font-bold text-text-muted uppercase tracking-wider">
                School email
              </label>
              <div
                className="group flex items-center gap-3 rounded-xl border border-border-strong bg-white px-5 py-[clamp(0.625rem,1.8vh,1rem)] shadow-sm transition-all duration-300 focus-within:border-psu-maroon/50 focus-within:bg-white focus-within:ring-2 focus-within:ring-psu-maroon/20 hover:border-psu-maroon/40 cursor-text"
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
                  aria-invalid={Boolean(error)}
                  aria-describedby={error ? "login-error" : undefined}
                  disabled={isLoading}
                  className="flex-1 bg-transparent text-[15px] font-medium text-text-main outline-none placeholder:text-text-muted/50 disabled:opacity-50"
                  style={{ caretColor: "var(--color-psu-maroon)" }}
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <div className="mb-[clamp(0.25rem,0.8vh,0.5rem)] block">
                <label htmlFor="password" className="text-[13px] font-bold text-text-muted uppercase tracking-wider">
                  Password
                </label>
              </div>
              <div
                className="group flex items-center gap-3 rounded-xl border border-border-strong bg-white px-5 py-[clamp(0.625rem,1.8vh,1rem)] shadow-sm transition-all duration-300 focus-within:border-psu-maroon/50 focus-within:bg-white focus-within:ring-2 focus-within:ring-psu-maroon/20 hover:border-psu-maroon/40 cursor-text"
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
                  placeholder="********"
                  autoComplete="current-password"
                  aria-invalid={Boolean(error)}
                  aria-describedby={error ? "login-error" : undefined}
                  disabled={isLoading}
                  className="flex-1 bg-transparent text-base font-medium tracking-widest text-text-main outline-none placeholder:text-text-muted/50 placeholder:tracking-normal disabled:opacity-50"
                  style={{ caretColor: "var(--color-psu-maroon)" }}
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
              <div className="mt-[clamp(0.375rem,1.2vh,0.75rem)] flex justify-end">
                <Link to="/forgot-password" className="text-[13px] font-bold text-psu-maroon hover:underline transition-colors">
                  Forgot password?
                </Link>
              </div>
              {capsLock && (
                <p className="mt-2 flex items-center gap-1.5 text-xs font-semibold text-text-amber" role="status">
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
                className="group relative overflow-hidden flex w-full items-center justify-center gap-2 rounded-xl bg-psu-maroon px-5 py-[clamp(0.75rem,1.8vh,1rem)] text-[15px] font-bold tracking-wide text-white shadow-md shadow-psu-maroon/20 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-psu-maroon/30 active:translate-y-0 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-60"
              >
                <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent group-hover:animate-[shimmer_1.5s_infinite] transition-transform"></div>
                {isLoading ? (
                  <>
                    <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    {slowSignIn ? "Waking up the server…" : "Signing in..."}
                  </>
                ) : (
                  "Sign In to Workspace"
                )}
              </button>
              
              <div className="relative my-[clamp(0.625rem,2.2vh,1.5rem)]">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-border-subtle"></div></div>
                <div className="relative flex justify-center"><span className="bg-white px-3 text-[10px] font-bold uppercase tracking-wider text-text-muted">Or</span></div>
              </div>

              <button
                type="button"
                onClick={handleGuestLogin}
                disabled={isLoading}
                className="group flex w-full items-center justify-center gap-2 rounded-xl border border-border-strong bg-white px-5 py-[clamp(0.75rem,1.8vh,1rem)] text-[15px] font-bold text-text-main shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:bg-bg-alt hover:shadow active:translate-y-0 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-60"
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

