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
    <main className="relative flex min-h-screen w-full flex-col lg:flex-row bg-bg-base text-text-main selection:bg-emerald-500/30">
      <style>{`
        @keyframes registerFadeUp {
          from { opacity: 0; transform: translateY(18px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @media (prefers-reduced-motion: reduce) {
          .register-animated { animation: none !important; }
        }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #52525b; }
      `}</style>

      {/* Theme Toggle */}
      <div className="absolute top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      {/* ── LEFT PANEL: Branding & Context (Hidden on Mobile) ── */}
      <div className="relative hidden lg:flex lg:w-5/12 xl:w-[45%] flex-col justify-between bg-bg-surface border-r border-border-subtle p-8 lg:p-10 xl:p-14 overflow-y-auto custom-scrollbar">
        
        {/* Gorgeous Background Effects */}
        <div className="absolute inset-0 z-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:24px_24px]"></div>
        <div className="absolute top-0 left-0 -z-10 h-full w-full bg-[radial-gradient(ellipse_80%_80%_at_0%_0%,rgba(16,185,129,0.12),transparent_100%)]" />
        
        <div className="relative z-10 flex flex-col min-h-full justify-between gap-8">
          <div>
            {/* Logo */}
            <div className="flex items-center gap-3 select-none mb-12">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500 font-mono text-xl font-bold text-white shadow-[0_0_25px_rgba(16,185,129,0.4)]">
                &gt;_
              </div>
              <span className="text-2xl font-bold tracking-wide text-text-main">PAMSU Python IDE</span>
            </div>

            <h2 className="text-3xl xl:text-[34px] font-bold leading-tight mb-4 text-text-main select-none max-w-md">
              Your definitive platform for Python programming.
            </h2>
            <p className="text-text-muted text-[14px] leading-relaxed max-w-md select-none">
              Your account role is assigned securely by the server. Verified university users register as students unless approved.
            </p>
          </div>

          {/* The Premium Data Collection Notice */}
          <div className="rounded-2xl border border-emerald-500/20 bg-bg-glass p-6 backdrop-blur-md shadow-xl">
            <div className="flex items-center gap-3 mb-3 select-none">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              </div>
              <h3 className="font-bold text-text-main tracking-wide text-sm">Data Collection Notice</h3>
            </div>
            <p className="text-[12px] text-text-muted mb-4 leading-relaxed select-none">
              We record limited activity information during controlled programming activities to support instructor review:
            </p>
            <ul className="space-y-2.5 select-none">
              {[
                "Tab switches and activity status may be recorded during graded laboratory sessions.",
                "Blocked external paste attempts may be counted, but clipboard contents are not stored.",
                "Submitted code may be checked using AST rules, test cases, and Jaccard similarity.",
                "The system does not record websites visited, screen recordings, webcam data, or every keystroke.",
                "Relevant records are available only to authorized instructors and system personnel."
              ].map((text, i) => (
                <li key={i} className="flex items-start gap-3 text-[11px] xl:text-[12px] text-text-muted">
                  <svg className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                  </svg>
                  <span className="leading-snug">{text}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* ── RIGHT PANEL: The Form ── */}
      <div className="relative flex flex-1 flex-col items-center justify-center p-6 sm:p-12 lg:px-16 h-screen overflow-y-auto custom-scrollbar">
        
        {/* Subtle right side glow */}
        <div className="absolute top-0 right-0 -z-10 h-[500px] w-[500px] translate-x-1/3 -translate-y-1/3 rounded-full bg-emerald-500/5 blur-[100px]" />

        {/* Mobile Logo */}
        <div className="lg:hidden flex items-center justify-center gap-3 select-none mb-10 w-full max-w-[420px]">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500 font-mono text-lg font-bold text-white shadow-[0_0_20px_rgba(16,185,129,0.4)]">
            &gt;_
          </div>
          <span className="text-xl font-bold tracking-wide text-text-main">PAMSU Python IDE</span>
        </div>

        <div className="w-full max-w-[420px] register-animated" style={{ animation: "registerFadeUp 600ms cubic-bezier(0.25,0.46,0.45,0.94) both" }}>
          
          {/* Step 1: Form Details */}
          {step === 1 && (
            <>
              <div className="mb-8 text-center lg:text-left">
                <button
                  type="button"
                  onClick={() => navigate("/login")}
                  className="lg:hidden mb-6 group inline-flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-1.5 text-xs font-semibold text-text-emerald transition-all hover:bg-emerald-500/20"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" className="shrink-0 transition-transform group-hover:-translate-x-0.5" aria-hidden="true">
                    <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <span>Back to Sign In</span>
                </button>
                <div className="flex items-center justify-between">
                  <h1 className="text-[28px] font-bold tracking-tight text-text-main select-none">Create account</h1>
                  <span className="hidden lg:flex shrink-0 items-center justify-center rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-emerald-500 select-none">
                    Step 1 of 2
                  </span>
                </div>
                <p className="mt-2 text-[13px] text-text-muted select-none">
                  Already have an account?{" "}
                  <button onClick={() => navigate("/login")} className="font-semibold text-text-emerald hover:text-emerald-400 hover:underline">
                    Sign in here
                  </button>
                </p>
              </div>

              {error && (
                <div role="alert" className="mb-6 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm font-medium text-text-rose animate-in fade-in">
                  {error}
                </div>
              )}

              <form onSubmit={handleRegistrationSubmit} className="space-y-4" noValidate>
                {/* Complete Name */}
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
                    />
                  </div>
                </div>

                {/* Password (Stacked to avoid cramping) */}
                <div>
                  <div className="mb-1.5 flex items-center justify-between">
                    <label htmlFor="registration-password" className="text-xs font-medium text-text-muted select-none cursor-default">
                      Password
                    </label>
                    {capsLock && (
                      <span className="flex items-center gap-1 text-[10px] font-semibold text-text-amber select-none">
                        <svg width="9" height="9" viewBox="0 0 10 12" fill="none"><path d="M5 1L9.5 6H7V9H3V6H0.5L5 1Z" fill="currentColor"/><rect x="3" y="10.5" width="4" height="1.5" rx="0.5" fill="currentColor"/></svg>
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
                      placeholder="Min 8 chars"
                      minLength={8}
                      required
                      disabled={isLoading}
                      className={`${inputClass} disabled:opacity-50`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      className="shrink-0 pr-1 cursor-pointer text-[11px] font-semibold tracking-wide text-text-muted hover:text-text-main"
                      disabled={isLoading}
                    >
                      {showPassword ? "HIDE" : "SHOW"}
                    </button>
                  </div>
                  {passwordStrength && (
                    <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-white/5">
                      <div className="h-full rounded-full transition-all duration-300" style={{ width: passwordStrength.width, backgroundColor: passwordStrength.color }} />
                    </div>
                  )}
                </div>

                {/* Confirm Password */}
                <div>
                  <label htmlFor="confirm-password" className="mb-1.5 block text-xs font-medium text-text-muted select-none cursor-default">
                    Confirm password
                  </label>
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
                      minLength={8}
                      required
                      disabled={isLoading}
                      className={`${inputClass} disabled:opacity-50`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword((v) => !v)}
                      className="shrink-0 pr-1 cursor-pointer text-[11px] font-semibold tracking-wide text-text-muted hover:text-text-main"
                      disabled={isLoading}
                    >
                      {showConfirmPassword ? "HIDE" : "SHOW"}
                    </button>
                  </div>
                </div>

                {/* Mobile Data Collection Notice */}
                <div className="lg:hidden rounded-xl border border-border-subtle bg-bg-glass p-4 mt-4">
                  <h2 className="mb-2 text-xs font-semibold text-text-main select-none">Data collection notice</h2>
                  <div className="h-24 overflow-y-auto pr-2 custom-scrollbar text-[11px] leading-relaxed text-text-muted select-none space-y-2">
                    <p>The platform records limited activity information during controlled programming activities to support instructor review.</p>
                    <ul className="pl-4 list-outside list-disc space-y-1">
                      <li>Tab switches and activity status may be recorded.</li>
                      <li>Blocked external paste attempts are counted.</li>
                      <li>Submitted code is checked using AST rules, test cases, and Jaccard similarity.</li>
                      <li>The system does not record websites visited, screen recordings, webcam data, or every keystroke.</li>
                      <li>Relevant records are available only to authorized personnel.</li>
                    </ul>
                  </div>
                </div>

                {/* Acknowledgment Checkbox */}
                <div className="pt-3 pb-1">
                  <label className="flex cursor-pointer items-start gap-3">
                    <div className="relative flex items-center justify-center mt-0.5">
                      <input
                        type="checkbox"
                        checked={acknowledged}
                        onChange={(e) => setAcknowledged(e.target.checked)}
                        className="peer h-4 w-4 shrink-0 appearance-none rounded border border-border-subtle bg-bg-surface checked:border-emerald-500 checked:bg-emerald-500 transition-all cursor-pointer"
                        disabled={isLoading}
                      />
                      <svg className="pointer-events-none absolute h-3 w-3 text-white opacity-0 peer-checked:opacity-100 transition-opacity" viewBox="0 0 14 14" fill="none">
                        <path d="M3 7.5L5.5 10L11 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </div>
                    <span className="text-[13px] text-text-muted select-none cursor-pointer hover:text-text-main transition-colors leading-tight">
                      I have read and acknowledge the <span className="text-emerald-500 font-medium">data collection notice</span>.
                    </span>
                  </label>
                </div>

                {/* Submit Button */}
                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={!acknowledged || isLoading || !form.password || form.password !== form.confirmPassword}
                    className="group relative overflow-hidden w-full rounded-xl bg-emerald-600 hover:bg-emerald-500 py-[14px] text-[14px] font-bold tracking-wide text-white transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_0_30px_rgba(16,185,129,0.4)] active:translate-y-0 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:hover:shadow-none shadow-[0_0_20px_rgba(16,185,129,0.2)] select-none"
                  >
                    <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent group-hover:animate-[shimmer_1.5s_infinite] transition-transform"></div>
                    <span className="relative z-10 flex items-center justify-center gap-2">
                      {isLoading ? (
                        <>
                          <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                          </svg>
                          Processing...
                        </>
                      ) : (
                        "Create account"
                      )}
                    </span>
                  </button>
                </div>
              </form>
            </>
          )}

          {/* Step 2: OTP Verification */}
          {step === 2 && (
            <div className="animate-[registerFadeUp_400ms_ease-out_both]">
              <div className="mb-8">
                <button
                  type="button"
                  onClick={() => { setStep(1); setError(""); setOtpCode(""); setSuccessMessage(""); }}
                  className="mb-6 group inline-flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-1.5 text-xs font-semibold text-text-emerald transition-all hover:bg-emerald-500/20"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" className="shrink-0 transition-transform group-hover:-translate-x-0.5" aria-hidden="true">
                    <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <span>Back to details</span>
                </button>
                
                <div className="flex items-center justify-between">
                  <h1 className="text-[28px] font-bold tracking-tight text-text-main select-none">Verify email</h1>
                  <span className="hidden lg:flex shrink-0 items-center justify-center rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-emerald-500 select-none">
                    Step 2 of 2
                  </span>
                </div>
                
                <p className="mt-2 text-[14px] leading-relaxed text-text-muted select-none">
                  Enter the 6-digit code sent to <br/><span className="font-semibold text-text-main">{form.email}</span>
                </p>
              </div>

              {successMessage && !error && (
                <div role="status" className="mb-6 rounded-lg border border-green-500/20 bg-green-500/10 px-4 py-3 text-sm font-medium text-text-emerald animate-in fade-in">
                  {successMessage}
                </div>
              )}

              {error && (
                <div role="alert" className="mb-6 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm font-medium text-text-rose animate-in fade-in">
                  {error}
                </div>
              )}

              <form onSubmit={handleOtpVerify} className="space-y-8" noValidate>
                <div>
                  <label className="mb-5 block text-center text-xs font-bold text-text-muted select-none uppercase tracking-widest">
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
                  className="group relative overflow-hidden w-full rounded-xl bg-emerald-600 hover:bg-emerald-500 py-[14px] text-[14px] font-bold tracking-wide text-white transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_0_30px_rgba(16,185,129,0.4)] active:translate-y-0 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:hover:shadow-none shadow-[0_0_20px_rgba(16,185,129,0.2)] select-none"
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
                      "Verify and complete"
                    )}
                  </span>
                </button>

                <div className="text-center">
                  <p className="mb-1.5 text-[13px] text-text-muted select-none">
                    Did not receive the code?
                  </p>
                  <button
                    type="button"
                    onClick={handleResendOtp}
                    disabled={resendCooldown > 0 || isLoading}
                    className="text-[13px] font-semibold text-text-emerald transition-colors hover:text-emerald-400 hover:underline disabled:cursor-not-allowed disabled:text-text-muted disabled:no-underline"
                  >
                    {resendCooldown > 0
                      ? `Resend available in ${resendCooldown}s`
                      : "Resend verification code"}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
