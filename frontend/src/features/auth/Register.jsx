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
          className="h-12 w-10 rounded-lg border border-border-subtle bg-bg-glass text-center text-lg font-bold text-white outline-none transition-colors focus:border-[#3b82f6]/60 disabled:opacity-50"
          style={{ caretColor: "#3b82f6" }}
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
    "auth-input-wrap flex items-center gap-2.5 rounded-lg border border-border-subtle bg-bg-glass px-3 py-2.5 transition-colors duration-200 focus-within:border-[#3b82f6]/60";
  const inputClass =
    "flex-1 bg-transparent text-sm text-white outline-none placeholder-white/20";

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
    <main className="min-h-screen bg-bg-base px-4 py-10 text-text-main">
      <style>{`
        @keyframes registerFadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .register-page-card {
          animation: registerFadeUp 500ms cubic-bezier(0.25,0.46,0.45,0.94) both;
        }
        @media (prefers-reduced-motion: reduce) {
          .register-page-card { animation: none; }
        }
      `}</style>

      {/* Theme Toggle */}
      <div className="absolute top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      <div className="register-page-card mx-auto w-full max-w-[560px]">

        {/* ── Step 1 — Registration details ── */}
        {step === 1 && (
          <>
            <header className="mb-6 space-y-5">
              {/* Uniform Top Navigation Bar */}
              <div className="flex items-center justify-between border-b border-border-subtle pb-4">
                <button
                  type="button"
                  onClick={() => navigate("/login")}
                  className="group inline-flex items-center gap-2 rounded-lg border border-blue-500/30 bg-blue-500/10 px-3.5 py-1.5 text-xs font-semibold text-text-blue shadow-sm transition-all duration-150 hover:border-blue-500/60 hover:bg-blue-500/20 hover:text-text-blue active:scale-95"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" className="shrink-0 text-text-blue transition-transform group-hover:-translate-x-0.5" aria-hidden="true">
                    <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <span>Back to Sign In</span>
                </button>

                <div className="flex items-center gap-2 select-none">
                  <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[#3b82f6] font-mono text-xs font-bold text-text-main">
                    &gt;_
                  </div>
                  <span className="text-xs font-semibold tracking-wide text-text-main">PAMSU Python IDE</span>
                </div>
              </div>

              {/* Title & Step Indicator */}
              <div className="flex items-start justify-between gap-4">
                <div className="select-none cursor-default">
                  <h1 className="text-xl font-bold text-text-main">Create your university account</h1>
                  <p className="mt-1 text-sm text-text-muted">
                    Your email will be verified before the account is activated.
                  </p>
                </div>
                <div className="shrink-0 rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1 text-[11px] font-medium text-text-blue select-none cursor-default">
                  Step 1 of 2
                </div>
              </div>
            </header>

            <section className="mb-5 rounded-xl border border-blue-500/20 bg-blue-500/[0.07] px-4 py-3 select-none cursor-default">
              <p className="text-xs leading-relaxed text-text-blue">
                Your account role is assigned securely by the server. Verified university
                users register as students unless their email is included in the approved
                instructor allowlist.
              </p>
            </section>

            {error && (
              <div role="alert" aria-live="polite" className="mb-5 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-text-rose">
                {error}
              </div>
            )}

            <form onSubmit={handleRegistrationSubmit} className="space-y-4" noValidate>
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
                    style={{ caretColor: "#3b82f6" }}
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
                    style={{ caretColor: "#3b82f6" }}
                  />
                </div>
                <p className="mt-1.5 text-[11px] text-text-muted select-none cursor-default">
                  Enter the 10-digit number printed on your school ID. Leading zeros are preserved.
                </p>
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
                    style={{ caretColor: "#3b82f6" }}
                  />
                </div>
                <p className="mt-1.5 text-[11px] text-text-muted select-none cursor-default">Personal email accounts are not accepted.</p>
              </div>

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
                      Caps Lock is on
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
                    placeholder="At least 8 characters"
                    autoComplete="new-password"
                    minLength={8}
                    required
                    disabled={isLoading}
                    className={`${inputClass} disabled:opacity-50`}
                    style={{ caretColor: "#3b82f6" }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="shrink-0 cursor-pointer text-xs text-text-muted transition-colors hover:text-text-muted"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    disabled={isLoading}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
                {passwordStrength && (
                  <div className="mt-2 select-none cursor-default">
                    <div className="h-1 w-full overflow-hidden rounded-full bg-white/[0.06]">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{ width: passwordStrength.width, backgroundColor: passwordStrength.color }}
                      />
                    </div>
                    <p className="mt-1 text-[11px]" style={{ color: passwordStrength.color }}>
                      Strength: {passwordStrength.label}
                    </p>
                  </div>
                )}
              </div>

              {/* Confirm password */}
              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <label htmlFor="confirm-password" className="text-xs font-medium text-text-muted select-none cursor-default">
                    Confirm password
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
                    placeholder="Enter the password again"
                    autoComplete="new-password"
                    minLength={8}
                    required
                    disabled={isLoading}
                    className={`${inputClass} disabled:opacity-50`}
                    style={{ caretColor: "#3b82f6" }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword((v) => !v)}
                    className="shrink-0 cursor-pointer text-xs text-text-muted transition-colors hover:text-text-muted"
                    aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                    disabled={isLoading}
                  >
                    {showConfirmPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              {/* Data collection notice */}
              <section className="rounded-xl border border-border-subtle bg-bg-glass p-4">
                <h2 className="mb-2 text-xs font-semibold text-text-main select-none cursor-default">Data collection notice</h2>
                <p className="mb-3 text-[11px] leading-relaxed text-text-muted select-none cursor-default">
                  The platform records limited activity information during controlled
                  programming activities to support instructor review and system operation.
                </p>
                <ul className="mb-4 list-inside list-disc space-y-1.5 text-[11px] leading-relaxed text-text-muted select-none cursor-default">
                  <li>Tab switches and activity status may be recorded during graded laboratory sessions.</li>
                  <li>Blocked external paste attempts may be counted, but clipboard contents are not stored.</li>
                  <li>Submitted code may be checked using AST rules, test cases, and Jaccard similarity.</li>
                  <li>The system does not record websites visited, screen recordings, webcam data, or every keystroke.</li>
                  <li>Relevant records are available only to authorized instructors and system personnel.</li>
                </ul>
                <label className="flex cursor-pointer items-start gap-3">
                  <input
                    type="checkbox"
                    checked={acknowledged}
                    onChange={(e) => setAcknowledged(e.target.checked)}
                    className="mt-0.5 h-4 w-4 shrink-0 accent-[#3b82f6]"
                    disabled={isLoading}
                  />
                  <span className="text-[11px] leading-relaxed text-text-muted select-none cursor-default">
                    I have read and acknowledge the platform's data collection notice.
                  </span>
                </label>
              </section>

              <div className="flex flex-col-reverse gap-3 pt-1 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs text-text-muted select-none cursor-default">
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={() => navigate("/login")}
                    className="font-medium text-[#3b82f6] transition-colors hover:text-[#60a5fa]"
                    disabled={isLoading}
                  >
                    Sign in
                  </button>
                </p>
                <button
                  type="submit"
                  disabled={!acknowledged || isLoading}
                  className="rounded-lg bg-gradient-to-br from-[#3b82f6] to-[#2563eb] px-5 py-2.5 text-sm font-semibold text-text-main transition duration-150 hover:-translate-y-px hover:opacity-90 active:translate-y-0 active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-none disabled:bg-white/[0.06] disabled:text-white/25 disabled:hover:translate-y-0 disabled:hover:opacity-100 select-none"
                >
                  {isLoading ? "Sending verification..." : "Continue to email verification"}
                </button>
              </div>
            </form>
          </>
        )}

        {/* ── Step 2 — OTP verification ── */}
        {step === 2 && (
          <>
            <header className="mb-6 space-y-5">
              {/* Uniform Top Navigation Bar */}
              <div className="flex items-center justify-between border-b border-border-subtle pb-4">
                <button
                  type="button"
                  onClick={() => { setStep(1); setError(""); setOtpCode(""); setSuccessMessage(""); }}
                  className="group inline-flex items-center gap-2 rounded-lg border border-blue-500/30 bg-blue-500/10 px-3.5 py-1.5 text-xs font-semibold text-text-blue shadow-sm transition-all duration-150 hover:border-blue-500/60 hover:bg-blue-500/20 hover:text-text-blue active:scale-95"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" className="shrink-0 text-text-blue transition-transform group-hover:-translate-x-0.5" aria-hidden="true">
                    <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <span>Back to Details</span>
                </button>

                <div className="flex items-center gap-2 select-none">
                  <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[#3b82f6] font-mono text-xs font-bold text-text-main">
                    &gt;_
                  </div>
                  <span className="text-xs font-semibold tracking-wide text-text-main">PAMSU Python IDE</span>
                </div>
              </div>

              {/* Title & Step Indicator */}
              <div className="flex items-start justify-between gap-4">
                <div className="select-none cursor-default">
                  <h1 className="text-xl font-bold text-text-main">Verify your email</h1>
                  <p className="mt-1 text-sm text-text-muted">
                    Enter the 6-digit code sent to{" "}
                    <span className="font-medium text-text-muted">{form.email}</span>
                  </p>
                </div>
                <div className="shrink-0 rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1 text-[11px] font-medium text-text-blue select-none cursor-default">
                  Step 2 of 2
                </div>
              </div>
            </header>

            {successMessage && !error && (
              <div role="status" aria-live="polite" className="mb-5 rounded-lg border border-green-500/20 bg-green-500/10 px-4 py-3 text-sm text-text-emerald">
                {successMessage}
              </div>
            )}

            {error && (
              <div role="alert" aria-live="polite" className="mb-5 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-text-rose">
                {error}
              </div>
            )}

            <form onSubmit={handleOtpVerify} className="space-y-6" noValidate>
              <div>
                <label className="mb-4 block text-center text-xs font-medium text-text-muted select-none cursor-default">
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
                className="w-full rounded-lg bg-gradient-to-br from-[#3b82f6] to-[#2563eb] py-2.5 text-sm font-semibold text-text-main transition duration-150 hover:-translate-y-px hover:opacity-90 active:translate-y-0 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0 select-none"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    Verifying...
                  </span>
                ) : (
                  "Verify and create account"
                )}
              </button>

              <div className="text-center">
                <p className="mb-2 text-xs text-text-muted select-none cursor-default">
                  Did not receive the code?
                </p>
                <button
                  type="button"
                  onClick={handleResendOtp}
                  disabled={resendCooldown > 0 || isLoading}
                  className="text-xs font-medium text-[#3b82f6] transition-colors hover:text-[#60a5fa] disabled:cursor-not-allowed disabled:text-text-muted"
                >
                  {resendCooldown > 0
                    ? `Resend available in ${resendCooldown}s`
                    : "Resend verification code"}
                </button>
              </div>

              <div className="text-center">
                <button
                  type="button"
                  onClick={() => { setStep(1); setError(""); setOtpCode(""); setSuccessMessage(""); }}
                  className="text-xs text-text-muted transition-colors hover:text-text-muted"
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