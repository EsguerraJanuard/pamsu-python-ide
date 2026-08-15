/**
 * Register.jsx
 * Two-step registration flow with OTP email verification.
 *
 * Step 1 — Fill in details → POST /registration/start
 *   Body: { name, school_id, email, password, confirm_password, data_collection_acknowledged: true }
 *   Returns: { challenge_id, email, expires_in_seconds, resend_after_seconds, message }
 *
 * Step 2 — Enter 6-digit OTP → POST /registration/verify
 *   Body: { challenge_id, otp_code }
 *   Returns: { user, message }
 *
 * Resend OTP → POST /registration/resend
 *   Body: { challenge_id }
 *
 * Role is assigned by the backend — never sent from the frontend.
 */

import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../../services/api";
import { ThemeToggle } from "../theme/ThemeToggle";

const SCHOOL_EMAIL_DOMAIN = "@pampangastateu.edu.ph";
const SCHOOL_ID_PATTERN = /^\d{10}$/;
const SCHOOL_EMAIL_PATTERN = /^[^\s@]+@pampangastateu\.edu\.ph$/i;
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


// ─── Password strength helper ─────────────────────────────────────────────────
function getPasswordStrength(password) {
  if (!password) return null;
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  if (score <= 1) return { label: "Weak — use at least 8 characters", color: "#ef4444", width: "25%" };
  if (score === 2) return { label: "Fair — add uppercase letters, numbers, or symbols", color: "#f59e0b", width: "50%" };
  if (score === 3) return { label: "Good — one more requirement can strengthen it", color: "#3b82f6", width: "75%" };
  return { label: "Strong password", color: "#22c55e", width: "100%" };
}

// ─── OTP Input component — 6 individual digit boxes ──────────────────────────
function OtpInput({ value, onChange, disabled }) {
  const inputsRef = useRef([]);

  const handleChange = (index, char) => {
    const digit = char.replace(/\D/g, "").slice(-1);
    const newValue = value.split("");
    newValue[index] = digit;
    onChange(newValue.join(""));
    if (digit && index < 5) {
      inputsRef.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === "Backspace" && !value[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    onChange(pasted.padEnd(6, "").slice(0, 6));
    inputsRef.current[Math.min(pasted.length, 5)]?.focus();
  };

  return (
    <div className="flex gap-2 justify-center" onPaste={handlePaste}>
      {Array.from({ length: 6 }).map((_, i) => (
        <input
          key={i}
          ref={(el) => (inputsRef.current[i] = el)}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={value[i] || ""}
          onChange={(e) => handleChange(i, e.target.value)}
          onKeyDown={(e) => handleKeyDown(i, e)}
          disabled={disabled}
          className="h-12 w-10 rounded-lg border border-border-subtle bg-bg-glass text-center text-lg font-bold text-text-main outline-none transition-colors focus:border-[#3b82f6]/60 disabled:opacity-50"
          style={{ caretColor: "#10b981" }}
          aria-label={`OTP digit ${i + 1}`}
        />
      ))}
    </div>
  );
}

export default function Register() {
  const navigate = useNavigate();

  // ─── Step 1 state ───────────────────────────────────────────────────────────
  const [form, setForm] = useState({
    fullName: "",
    schoolId: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);

  // ─── Step 2 state ───────────────────────────────────────────────────────────
  const [step, setStep] = useState(1); // 1 = details form, 2 = OTP verification
  const [challengeId, setChallengeId] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [resendCooldown, setResendCooldown] = useState(0);

  // ─── Shared state ───────────────────────────────────────────────────────────
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
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

  const passwordStrength = getPasswordStrength(form.password);

  const inputWrapClass =
    "auth-input-wrap flex items-center gap-2.5 rounded-lg border border-border-subtle bg-bg-glass px-3 py-2.5 transition-colors duration-200 focus-within:border-emerald-500/50 focus-within:bg-bg-glass";
  const inputClass =
    "flex-1 bg-transparent text-sm text-text-main outline-none placeholder:text-text-muted/50";

  // Countdown timer for OTP resend cooldown
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setTimeout(() => setResendCooldown((v) => v - 1), 1000);
    return () => clearTimeout(timer);
  }, [resendCooldown]);

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (error) setError("");
  };

  const updateSchoolId = (value) => {
    const digitsOnly = value.replace(/\D/g, "").slice(0, 10);
    updateField("schoolId", digitsOnly);
  };

  // ─── Step 1 — Submit registration details ────────────────────────────────────
  const handleRegistrationSubmit = async (event) => {
    event.preventDefault();

    const normalizedEmail = form.email.trim().toLowerCase();
    const normalizedName = form.fullName.trim();

    // Client-side validation
    if (normalizedName.length < 3) { setError("Enter your complete name."); return; }
    if (!SCHOOL_ID_PATTERN.test(form.schoolId)) { setError("Your school ID must contain exactly 10 digits."); return; }
    if (!SCHOOL_EMAIL_PATTERN.test(normalizedEmail)) { setError(`Use your official university email ending in ${SCHOOL_EMAIL_DOMAIN}.`); return; }
    if (form.password.length < 8) { setError("Your password must contain at least 8 characters."); return; }
    if (form.password !== form.confirmPassword) { setError("The passwords do not match."); return; }
    if (!acknowledged) { setError("Please read and acknowledge the data collection notice."); return; }

    setIsLoading(true);
    setError("");

    try {
      // POST /registration/start
      // Body must match RegistrationStartRequest (extends UserCreate)
      const data = await api.post("/registration/start", {
        name: normalizedName,
        school_id: form.schoolId, // string, preserves leading zeros
        email: normalizedEmail,
        password: form.password,
        confirm_password: form.confirmPassword,
        data_collection_acknowledged: true, // must be exactly true (Literal[True])
      });

      // Success — move to OTP step
      setChallengeId(data.challenge_id);
      setResendCooldown(data.resend_after_seconds || 60);
      setStep(2);
      setSuccessMessage(data.message || `A 6-digit verification code was sent to ${normalizedEmail}.`);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409) {
          setError(err.data?.detail || "This email or school ID is already registered.");
        } else if (err.status === 422) {
          if (Array.isArray(err.data?.detail)) {
            const msg = err.data.detail.map((e) => e.msg).join(". ");
            setError(msg);
          } else {
            setError(err.data?.detail || "Please check your details and try again.");
          }
        } else if (err.status === 503) {
          setError("Email verification service is temporarily unavailable. Try again later.");
        } else {
          setError(err.data?.detail || err.message || "Registration failed. Please try again.");
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

  // ─── Step 2 — Verify OTP ─────────────────────────────────────────────────────
  const handleOtpVerify = async (event) => {
    event.preventDefault();

    if (otpCode.length !== 6) {
      setError("Enter the complete 6-digit verification code.");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      // POST /registration/verify
      const data = await api.post("/registration/verify", {
        challenge_id: challengeId,
        otp_code: otpCode,
      });

      // Account created successfully — go to login
      navigate("/login", {
        state: { registrationSuccess: true, email: form.email.trim().toLowerCase() },
        replace: true,
      });
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 400) {
          const remaining = err.data?.detail?.remaining_attempts;
          setError(
            remaining !== undefined
              ? `Incorrect code. ${remaining} attempt${remaining !== 1 ? "s" : ""} remaining.`
              : "Incorrect verification code."
          );
          setOtpCode("");
        } else if (err.status === 410) {
          setError("Your verification code has expired. Please request a new one.");
        } else if (err.status === 429) {
          setError("Too many incorrect attempts. Please start registration again.");
        } else if (err.status === 409) {
          setError(err.data?.detail || "This account may already exist. Try signing in.");
        } else {
          setError(err.data?.detail || err.message || "Verification failed. Please try again.");
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

  // ─── Resend OTP ──────────────────────────────────────────────────────────────
  const handleResendOtp = async () => {
    if (resendCooldown > 0 || isLoading) return;

    setIsLoading(true);
    setError("");
    setOtpCode("");

    try {
      // POST /registration/resend
      const data = await api.post("/registration/resend", { challenge_id: challengeId });

      setResendCooldown(data.resend_after_seconds || 60);
      setSuccessMessage("A new verification code was sent to your email.");
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 429) {
          const retryAfter = err.data?.detail?.retry_after_seconds;
          if (retryAfter) {
            setResendCooldown(retryAfter);
            setError(`Please wait ${retryAfter} seconds before resending.`);
          } else {
            setError(err.data?.detail || "Resend limit reached. Please start registration again.");
          }
        } else if (err.status === 404) {
          setError("Your session has expired. Please start registration again.");
          setStep(1);
        } else {
          setError(err.data?.detail || err.message || "Could not resend the code. Please try again.");
        }
      } else {
        setError("Could not resend the code. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="relative flex min-h-screen flex-col overflow-x-hidden overflow-y-auto bg-bg-base px-4 py-8 text-text-main">
      <style>{`
        @keyframes registerFadeUp {
          from { opacity: 0; transform: translateY(18px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @media (prefers-reduced-motion: reduce) {
          .register-animated { animation: none !important; }
        }
      `}</style>

      {/* Premium Background Grid */}
      <div className="absolute inset-0 z-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_50%,#000_70%,transparent_100%)]"></div>

      {/* Glow effects */}
      <div className="absolute top-0 right-0 -z-10 h-[600px] w-[600px] translate-x-1/4 -translate-y-1/4 rounded-full bg-emerald-500/10 blur-[120px]" />
      <div className="absolute bottom-0 left-0 -z-10 h-[600px] w-[600px] -translate-x-1/4 translate-y-1/4 rounded-full bg-cyan-500/10 blur-[120px]" />

      {/* Theme Toggle */}
      <div className="absolute top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      <div
        className="register-animated m-auto relative z-10 w-full max-w-[880px] rounded-2xl border border-border-subtle bg-bg-glass/70 p-6 shadow-[0_0_40px_-10px_rgba(16,185,129,0.15)] backdrop-blur-2xl sm:p-10 transition-all duration-500 hover:border-emerald-500/30 hover:shadow-[0_0_50px_-10px_rgba(16,185,129,0.25)]"
        style={{ animation: "registerFadeUp 650ms cubic-bezier(0.25,0.46,0.45,0.94) both" }}
      >
        {/* ── Step 1 — Registration details ── */}
        {step === 1 && (
          <>
            <header className="mb-6 space-y-6">
              {/* Uniform Top Navigation Bar */}
              <div className="flex items-center justify-between border-b border-border-subtle pb-5">
                <button
                  type="button"
                  onClick={() => navigate("/login")}
                  className="group inline-flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-1.5 text-xs font-semibold text-text-emerald shadow-sm transition-all duration-150 hover:border-emerald-500/60 hover:bg-emerald-500/20 active:scale-95"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" className="shrink-0 transition-transform group-hover:-translate-x-0.5" aria-hidden="true">
                    <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <span>Back to Sign In</span>
                </button>

                <div className="flex items-center gap-2 select-none">
                  <div className="flex h-7 w-7 items-center justify-center rounded-md bg-emerald-500 font-mono text-xs font-bold text-white shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                    &gt;_
                  </div>
                  <span className="text-xs font-semibold tracking-wide text-text-main">PAMSU Python IDE</span>
                </div>
              </div>

              {/* Title & Step Indicator */}
              <div className="flex items-start justify-between gap-4">
                <div className="select-none cursor-default">
                  <h1 className="text-2xl font-bold text-text-main">Create your university account</h1>
                  <p className="mt-1.5 text-sm text-text-muted">
                    Your email will be verified before the account is activated.
                  </p>
                </div>
                <div className="shrink-0 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3.5 py-1.5 text-[11px] font-medium text-text-emerald select-none cursor-default">
                  Step 1 of 2
                </div>
              </div>
            </header>

            <section className="mb-6 rounded-xl border border-emerald-500/20 bg-emerald-500/[0.04] px-4 py-3 select-none cursor-default">
              <p className="text-[13px] leading-relaxed text-text-emerald">
                Your account role is assigned securely by the server. Verified university
                users register as students unless their email is included in the approved
                instructor allowlist.
              </p>
            </section>

            {error && (
              <div role="alert" aria-live="polite" className="mb-6 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm font-medium text-text-rose">
                {error}
              </div>
            )}

            <form onSubmit={handleRegistrationSubmit} className="mt-2" noValidate>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-5">
                
                {/* LEFT COLUMN: Personal Details */}
                <div className="space-y-5">
                  {/* Full name */}
                  <div>
                    <label htmlFor="full-name" className="mb-1.5 block text-xs font-medium text-text-muted select-none cursor-default">
                      Complete name
                    </label>
                    <div className={inputWrapClass}>
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="shrink-0 text-text-muted" aria-hidden="true">
                        <circle cx="7" cy="4.5" r="2.5" stroke="currentColor" strokeWidth="1.2" />
                        <path d="M1.5 12.5c0-3 2.5-5 5.5-5s5.5 2 5.5 5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                      </svg>
                      <input
                        id="full-name"
                        type="text"
                        value={form.fullName}
                        onChange={(e) => updateField("fullName", e.target.value)}
                        placeholder="Juan Dela Cruz"
                        autoComplete="name"
                        required
                        disabled={isLoading}
                        className={`${inputClass} disabled:opacity-50`}
                        style={{ caretColor: "#10b981" }}
                      />
                    </div>
                  </div>

                  {/* School ID */}
                  <div>
                    <label htmlFor="school-id" className="mb-1.5 block text-xs font-medium text-text-muted select-none cursor-default">
                      School ID
                    </label>
                    <div className={inputWrapClass}>
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="shrink-0 text-text-muted" aria-hidden="true">
                        <rect x="1" y="2" width="12" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
                        <path d="M4 6h2M4 8.5h6M8 6h2" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
                      </svg>
                      <input
                        id="school-id"
                        type="text"
                        inputMode="numeric"
                        value={form.schoolId}
                        onChange={(e) => updateSchoolId(e.target.value)}
                        placeholder="0000000000"
                        pattern="[0-9]{10}"
                        minLength={10}
                        maxLength={10}
                        autoComplete="off"
                        required
                        disabled={isLoading}
                        className={`${inputClass} disabled:opacity-50`}
                        style={{ caretColor: "#10b981" }}
                      />
                    </div>
                  </div>

                  {/* Email */}
                  <div>
                    <label htmlFor="school-email" className="mb-1.5 block text-xs font-medium text-text-muted select-none cursor-default">
                      University email
                    </label>
                    <div className={inputWrapClass}>
                      <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className="shrink-0 text-text-muted" aria-hidden="true">
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
                        className={`${inputClass} disabled:opacity-50`}
                        style={{ caretColor: "#10b981" }}
                      />
                    </div>
                    <p className="mt-2 text-[11px] text-text-muted select-none cursor-default">Personal email accounts are not accepted.</p>
                  </div>
                  
                  {/* Restored Data Collection Notice (Moved slightly down on desktop using layout structure) */}
                  <div className="pt-2 hidden md:block">
                    <section className="rounded-xl border border-border-subtle bg-bg-glass p-4">
                      <h2 className="mb-2 text-xs font-semibold text-text-main select-none cursor-default">Data collection notice</h2>
                      <p className="mb-2 text-[11px] leading-relaxed text-text-muted select-none cursor-default">
                        The platform records limited activity information during controlled
                        programming activities to support instructor review and system operation.
                      </p>
                      <ul className="mb-4 pl-4 list-outside list-disc space-y-1 text-[11px] leading-relaxed text-text-muted select-none cursor-default">
                        <li>Tab switches and activity status may be recorded during graded laboratory sessions.</li>
                        <li>Blocked external paste attempts may be counted, but clipboard contents are not stored.</li>
                        <li>Submitted code may be checked using AST rules, test cases, and Jaccard similarity.</li>
                        <li>The system does not record websites visited, screen recordings, webcam data, or every keystroke.</li>
                        <li>Relevant records are available only to authorized instructors and system personnel.</li>
                      </ul>
                      <label className="flex cursor-pointer items-start gap-2 border-t border-border-subtle pt-3">
                        <input
                          type="checkbox"
                          checked={acknowledged}
                          onChange={(e) => setAcknowledged(e.target.checked)}
                          className="mt-[3px] h-3.5 w-3.5 shrink-0 accent-[#10b981] rounded cursor-pointer"
                          disabled={isLoading}
                        />
                        <span className="text-[11px] font-medium leading-tight text-text-main select-none cursor-pointer">
                          I have read and acknowledge the platform's data collection notice.
                        </span>
                      </label>
                    </section>
                  </div>
                </div>

                {/* RIGHT COLUMN: Security & Terms */}
                <div className="space-y-5">
                  {/* Password */}
                  <div>
                    <div className="mb-1.5 flex items-center justify-between">
                      <label htmlFor="registration-password" className="text-xs font-medium text-text-muted select-none cursor-default">
                        Password
                      </label>
                      {capsLock && (
                        <span className="flex items-center gap-1 text-[10px] font-semibold text-text-amber select-none">
                          <svg width="9" height="9" viewBox="0 0 10 12" fill="none" aria-hidden="true">
                            <path d="M5 1L9.5 6H7V9H3V6H0.5L5 1Z" fill="currentColor"/>
                            <rect x="3" y="10.5" width="4" height="1.5" rx="0.5" fill="currentColor"/>
                          </svg>
                          Caps Lock
                        </span>
                      )}
                    </div>
                    <div className={inputWrapClass}>
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="shrink-0 text-text-muted" aria-hidden="true">
                        <rect x="2" y="6" width="10" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
                        <path d="M4.5 6V4.5a2.5 2.5 0 015 0V6" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                      </svg>
                      <input
                        id="registration-password"
                        type={showPassword ? "text" : "password"}
                        value={form.password}
                        onChange={(e) => updateField("password", e.target.value)}
                        placeholder="At least 8 chars"
                        autoComplete="new-password"
                        minLength={8}
                        required
                        disabled={isLoading}
                        className={`${inputClass} disabled:opacity-50`}
                        style={{ caretColor: "#10b981" }}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword((v) => !v)}
                        className="shrink-0 cursor-pointer text-xs text-text-muted transition-colors hover:text-text-main"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                        disabled={isLoading}
                      >
                        {showPassword ? "Hide" : "Show"}
                      </button>
                    </div>
                  </div>

                  {/* Confirm password */}
                  <div>
                    <div className="mb-1.5 flex items-center justify-between">
                      <label htmlFor="confirm-password" className="text-xs font-medium text-text-muted select-none cursor-default">
                        Confirm password
                      </label>
                    </div>
                    <div className={inputWrapClass}>
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="shrink-0 text-text-muted" aria-hidden="true">
                        <rect x="2" y="6" width="10" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
                        <path d="M4.5 6V4.5a2.5 2.5 0 015 0V6" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                      </svg>
                      <input
                        id="confirm-password"
                        type={showConfirmPassword ? "text" : "password"}
                        value={form.confirmPassword}
                        onChange={(e) => updateField("confirmPassword", e.target.value)}
                        placeholder="Repeat password"
                        autoComplete="new-password"
                        minLength={8}
                        required
                        disabled={isLoading}
                        className={`${inputClass} disabled:opacity-50`}
                        style={{ caretColor: "#10b981" }}
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword((v) => !v)}
                        className="shrink-0 cursor-pointer text-xs text-text-muted transition-colors hover:text-text-main"
                        aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                        disabled={isLoading}
                      >
                        {showConfirmPassword ? "Hide" : "Show"}
                      </button>
                    </div>
                  </div>

                  {/* Password strength bar */}
                  {passwordStrength && (
                    <div className="select-none cursor-default">
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/[0.06]">
                        <div
                          className="h-full rounded-full transition-all duration-300"
                          style={{ width: passwordStrength.width, backgroundColor: passwordStrength.color }}
                        />
                      </div>
                      <p className="mt-1.5 text-[11px] font-medium" style={{ color: passwordStrength.color }}>
                        {passwordStrength.label}
                      </p>
                    </div>
                  )}

                  {/* Restored Data Collection Notice (Mobile view only) */}
                  <div className="md:hidden">
                    <section className="rounded-xl border border-border-subtle bg-bg-glass p-4 mt-2">
                      <h2 className="mb-2 text-xs font-semibold text-text-main select-none cursor-default">Data collection notice</h2>
                      <p className="mb-2 text-[11px] leading-relaxed text-text-muted select-none cursor-default">
                        The platform records limited activity information during controlled
                        programming activities to support instructor review and system operation.
                      </p>
                      <ul className="mb-4 pl-4 list-outside list-disc space-y-1 text-[11px] leading-relaxed text-text-muted select-none cursor-default">
                        <li>Tab switches and activity status may be recorded during graded laboratory sessions.</li>
                        <li>Blocked external paste attempts may be counted, but clipboard contents are not stored.</li>
                        <li>Submitted code may be checked using AST rules, test cases, and Jaccard similarity.</li>
                        <li>The system does not record websites visited, screen recordings, webcam data, or every keystroke.</li>
                        <li>Relevant records are available only to authorized instructors and system personnel.</li>
                      </ul>
                      <label className="flex cursor-pointer items-start gap-2 border-t border-border-subtle pt-3">
                        <input
                          type="checkbox"
                          checked={acknowledged}
                          onChange={(e) => setAcknowledged(e.target.checked)}
                          className="mt-[3px] h-3.5 w-3.5 shrink-0 accent-[#10b981] rounded cursor-pointer"
                          disabled={isLoading}
                        />
                        <span className="text-[11px] font-medium leading-tight text-text-main select-none cursor-pointer">
                          I have read and acknowledge the platform's data collection notice.
                        </span>
                      </label>
                    </section>
                  </div>
                </div>
              </div>

              <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-t border-border-subtle pt-6">
                <p className="text-xs text-text-muted select-none cursor-default text-center sm:text-left">
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={() => navigate("/login")}
                    className="font-semibold text-text-emerald transition-colors hover:text-emerald-400 hover:underline"
                    disabled={isLoading}
                  >
                    Sign in
                  </button>
                </p>
                <button
                  type="submit"
                  disabled={!acknowledged || isLoading}
                  className="group relative overflow-hidden rounded-xl bg-emerald-600 hover:bg-emerald-500 px-8 py-3.5 text-sm font-bold tracking-wide text-white transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_0_30px_rgba(16,185,129,0.5)] active:translate-y-0 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:hover:shadow-none shadow-[0_0_20px_rgba(16,185,129,0.3)] select-none w-full sm:w-auto"
                >
                  <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent group-hover:animate-[shimmer_1.5s_infinite] transition-transform"></div>
                  <span className="relative z-10 flex items-center justify-center gap-2">
                    {isLoading ? "Sending verification..." : "Continue"}
                  </span>
                </button>
              </div>
            </form>
          </>
        )}

        {/* ── Step 2 — OTP verification ── */}
        {step === 2 && (
          <>
            <header className="mb-8 space-y-6">
              {/* Uniform Top Navigation Bar */}
              <div className="flex items-center justify-between border-b border-border-subtle pb-5">
                <button
                  type="button"
                  onClick={() => { setStep(1); setError(""); setOtpCode(""); setSuccessMessage(""); }}
                  className="group inline-flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-1.5 text-xs font-semibold text-text-emerald shadow-sm transition-all duration-150 hover:border-emerald-500/60 hover:bg-emerald-500/20 active:scale-95"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" className="shrink-0 transition-transform group-hover:-translate-x-0.5" aria-hidden="true">
                    <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <span>Back to Details</span>
                </button>

                <div className="flex items-center gap-2 select-none">
                  <div className="flex h-7 w-7 items-center justify-center rounded-md bg-emerald-500 font-mono text-xs font-bold text-white shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                    &gt;_
                  </div>
                  <span className="text-xs font-semibold tracking-wide text-text-main">PAMSU Python IDE</span>
                </div>
              </div>

              {/* Title & Step Indicator */}
              <div className="flex items-start justify-between gap-4">
                <div className="select-none cursor-default">
                  <h1 className="text-2xl font-bold text-text-main">Verify your email</h1>
                  <p className="mt-1.5 text-sm text-text-muted">
                    Enter the 6-digit code sent to{" "}
                    <span className="font-medium text-text-main">{form.email}</span>
                  </p>
                </div>
                <div className="shrink-0 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3.5 py-1.5 text-[11px] font-medium text-text-emerald select-none cursor-default">
                  Step 2 of 2
                </div>
              </div>
            </header>

            {successMessage && !error && (
              <div role="status" aria-live="polite" className="mb-6 rounded-lg border border-green-500/20 bg-green-500/10 px-4 py-3 text-sm font-medium text-text-emerald">
                {successMessage}
              </div>
            )}

            {error && (
              <div role="alert" aria-live="polite" className="mb-6 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm font-medium text-text-rose">
                {error}
              </div>
            )}

            <form onSubmit={handleOtpVerify} className="space-y-8" noValidate>
              <div>
                <label className="mb-5 block text-center text-sm font-semibold text-text-muted select-none cursor-default uppercase tracking-wider">
                  Verification code
                </label>
                <OtpInput
                  value={otpCode}
                  onChange={(val) => { setOtpCode(val); if (error) setError(""); }}
                  disabled={isLoading}
                />
              </div>

              <button
                type="submit"
                disabled={otpCode.length !== 6 || isLoading}
                className="group relative overflow-hidden w-full rounded-xl bg-emerald-600 hover:bg-emerald-500 py-3.5 text-sm font-bold tracking-wide text-white transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_0_30px_rgba(16,185,129,0.5)] active:translate-y-0 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:hover:shadow-none shadow-[0_0_20px_rgba(16,185,129,0.3)] select-none"
              >
                <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent group-hover:animate-[shimmer_1.5s_infinite] transition-transform"></div>
                <span className="relative z-10 flex items-center justify-center gap-2">
                  {isLoading ? (
                    <>
                      <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                      </svg>
                      Verifying...
                    </>
                  ) : (
                    "Verify and create account"
                  )}
                </span>
              </button>

              <div className="text-center space-y-4">
                <div>
                  <p className="mb-1 text-xs text-text-muted select-none cursor-default">
                    Did not receive the code?
                  </p>
                  <button
                    type="button"
                    onClick={handleResendOtp}
                    disabled={resendCooldown > 0 || isLoading}
                    className="text-xs font-semibold text-text-emerald transition-colors hover:text-emerald-400 hover:underline disabled:cursor-not-allowed disabled:text-text-muted disabled:no-underline"
                  >
                    {resendCooldown > 0
                      ? `Resend available in ${resendCooldown}s`
                      : "Resend verification code"}
                  </button>
                </div>
                
                <button
                  type="button"
                  onClick={() => { setStep(1); setError(""); setOtpCode(""); setSuccessMessage(""); }}
                  className="text-xs font-medium text-text-muted transition-colors hover:text-text-main"
                  disabled={isLoading}
                >
                  ← Back to registration details
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </main>
  );
}
