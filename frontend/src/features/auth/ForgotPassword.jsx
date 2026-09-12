import { useState, useRef, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { ThemeToggle } from "../theme/ThemeToggle";
import { api, ApiError } from "../../services/api";

function getPasswordStrength(password) {
  if (!password) return null;
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  if (score <= 1) return { label: "Weak - use at least 8 characters", color: "#ef4444", width: "25%" };
  if (score === 2) return { label: "Fair - add uppercase letters, numbers, or symbols", color: "#f59e0b", width: "50%" };
  if (score === 3) return { label: "Good - one more requirement can strengthen it", color: "#3b82f6", width: "75%" };
  return { label: "Strong password", color: "#22c55e", width: "100%" };
}

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  
  // State
  const [email, setEmail] = useState("");
  const [challengeId, setChallengeId] = useState(null);
  
  const [otpCode, setOtpCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPasswords, setShowPasswords] = useState(false);

  // Resend timer
  const [resendTimer, setResendTimer] = useState(0);

  useEffect(() => {
    if (resendTimer > 0) {
      const interval = setInterval(() => setResendTimer((prev) => prev - 1), 1000);
      return () => clearInterval(interval);
    }
  }, [resendTimer]);

  const handleStartReset = async (e) => {
    e.preventDefault();
    if (!email) return;
    
    setLoading(true);
    setErrorMsg("");
    
    try {
      const response = await api.post("/users/password-reset/start", { email });
      setChallengeId(response.challenge_id);
      setResendTimer(response.resend_after_seconds || 60);
      setStep(2);
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMsg(error.details || error.message);
      } else {
        setErrorMsg("An unexpected error occurred. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    if (resendTimer > 0 || !challengeId) return;
    
    setLoading(true);
    setErrorMsg("");
    
    try {
      const response = await api.post("/users/password-reset/resend", {
        challenge_id: challengeId,
      });
      setChallengeId(response.challenge_id);
      setResendTimer(response.resend_after_seconds || 60);
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMsg(error.details || error.message);
      } else {
        setErrorMsg("Failed to resend code.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteReset = async (e) => {
    e.preventDefault();
    if (!otpCode || !newPassword || !confirmPassword) return;

    if (newPassword !== confirmPassword) {
      setErrorMsg("Passwords do not match.");
      return;
    }

    if (newPassword.length < 8) {
      setErrorMsg("Password must be at least 8 characters long.");
      return;
    }
    
    setLoading(true);
    setErrorMsg("");
    
    try {
      await api.post("/users/password-reset/complete", {
        challenge_id: challengeId,
        otp_code: otpCode,
        new_password: newPassword,
      });
      setStep(3); // Success
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMsg(error.details || error.message);
      } else {
        setErrorMsg("Failed to reset password.");
      }
    } finally {
      setLoading(false);
    }
  };

  const inputClass = "flex-1 bg-transparent text-sm text-text-main outline-none placeholder:text-text-muted";
  const inputWrap = "flex items-center gap-2.5 rounded-lg border border-border-subtle bg-bg-base px-3 py-2.5 transition-colors duration-200 focus-within:border-[#3b82f6]/60";

  return (
    <main className="flex min-h-screen items-center justify-center bg-bg-base text-text-main overflow-hidden p-6 relative">
      {/* Background Grid & Glows */}
      <div className="absolute inset-0 z-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>
      <div className="absolute top-0 right-0 -z-10 h-[500px] w-[500px] translate-x-1/3 -translate-y-1/4 rounded-full bg-blue-500/10 blur-[120px]" />
      <div className="absolute bottom-0 left-0 -z-10 h-[500px] w-[500px] -translate-x-1/3 translate-y-1/4 rounded-full bg-emerald-500/10 blur-[120px]" />

      <div className="absolute top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      <div className="relative z-10 w-full max-w-[440px] rounded-2xl border border-border-subtle bg-bg-glass/70 backdrop-blur-2xl p-8 shadow-xl animate-page-fade">
        
        {step === 1 && (
          <form onSubmit={handleStartReset} className="animate-[registerFadeUp_400ms_ease-out_both]">
            <div className="mb-6 text-center">
              <h2 className="text-xl font-bold text-text-main">
                Forgot your password?
              </h2>
              <p className="mt-3 text-sm text-text-muted leading-relaxed">
                Enter your registered university email address to receive a secure recovery code.
              </p>
            </div>

            {errorMsg && (
              <div className="mb-5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-[13px] font-medium text-red-400">
                {errorMsg}
              </div>
            )}

            <div className="mb-6">
              <label htmlFor="email" className="mb-1.5 block text-xs font-medium text-text-muted">
                University Email Address
              </label>
              <div className={inputWrap}>
                <svg className="h-4 w-4 text-text-muted" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="student@pampangastateu.edu.ph"
                  required
                  className={inputClass}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center rounded-xl bg-gradient-to-br from-[#3b82f6] to-[#2563eb] py-3 text-sm font-semibold text-white shadow-lg shadow-blue-500/25 transition-all hover:-translate-y-px hover:opacity-90 active:translate-y-0 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50"
            >
              {loading ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/20 border-t-white" />
              ) : (
                "Send Recovery Code"
              )}
            </button>

            <div className="mt-6 text-center text-[13px]">
              <span className="text-text-muted">Remember your password?</span>{" "}
              <Link to="/login" className="font-semibold text-[#3b82f6] hover:underline">
                Log in instead
              </Link>
            </div>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={handleCompleteReset} className="animate-[registerFadeUp_400ms_ease-out_both]">
            <div className="mb-6">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="mb-4 flex items-center gap-1.5 text-[13px] font-medium text-text-muted transition-colors hover:text-text-main"
              >
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <path d="M10 12L6 8l4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                Back to email
              </button>
              <h2 className="text-xl font-bold text-text-main">
                Secure Password Reset
              </h2>
              <p className="mt-2 text-[13px] text-text-muted">
                We've sent a 6-digit verification code to <span className="font-semibold text-text-main">{email}</span>.
              </p>
            </div>

            {errorMsg && (
              <div className="mb-5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-[13px] font-medium text-red-400">
                {errorMsg}
              </div>
            )}

            <div className="space-y-4 mb-6">
              <div>
                <label className="mb-1.5 flex justify-between text-xs font-medium text-text-muted">
                  <span>Verification Code</span>
                  <button
                    type="button"
                    onClick={handleResendOTP}
                    disabled={resendTimer > 0 || loading}
                    className="text-[#3b82f6] hover:underline disabled:text-text-muted disabled:no-underline"
                  >
                    {resendTimer > 0 ? `Resend code in ${resendTimer}s` : "Resend code"}
                  </button>
                </label>
                <div className={inputWrap}>
                  <input
                    type="text"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value.replace(/[^0-9]/g, "").slice(0, 6))}
                    placeholder="Enter 6-digit code"
                    required
                    className={`${inputClass} tracking-[0.2em] font-mono text-center`}
                  />
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-medium text-text-muted">
                  New Password
                </label>
                <div className={inputWrap}>
                  <input
                    type={showPasswords ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="At least 8 characters"
                    required
                    className={inputClass}
                  />
                </div>
                {newPassword && getPasswordStrength(newPassword) && (() => {
                  const strength = getPasswordStrength(newPassword);
                  return (
                    <div className="mt-2.5">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Strength</span>
                        <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: strength.color }}>
                          {strength.label.split(' - ')[0] || strength.label}
                        </span>
                      </div>
                      <div className="h-1 w-full overflow-hidden rounded-full bg-white/5">
                        <div className="h-full rounded-full transition-all duration-300" style={{ width: strength.width, backgroundColor: strength.color }} />
                      </div>
                    </div>
                  );
                })()}
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-medium text-text-muted">
                  Confirm New Password
                </label>
                <div className={inputWrap}>
                  <input
                    type={showPasswords ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Enter the new password again"
                    required
                    className={inputClass}
                  />
                </div>
              </div>

              <div className="flex items-center gap-3 mt-4 mb-2">
                <label className="text-xs text-text-muted cursor-pointer flex items-center gap-2">
                  <input 
                    type="checkbox" 
                    checked={showPasswords} 
                    onChange={() => setShowPasswords(!showPasswords)} 
                    className="rounded border-border-subtle text-[#3b82f6] focus:ring-[#3b82f6]"
                  />
                  Show passwords
                </label>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || otpCode.length !== 6}
              className="flex w-full items-center justify-center rounded-xl bg-gradient-to-br from-[#3b82f6] to-[#2563eb] py-3 text-sm font-semibold text-white shadow-lg shadow-blue-500/25 transition-all hover:-translate-y-px hover:opacity-90 active:translate-y-0 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50"
            >
              {loading ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/20 border-t-white" />
              ) : (
                "Reset Password"
              )}
            </button>
          </form>
        )}

        {step === 3 && (
          <div className="text-center animate-[registerFadeUp_400ms_ease-out_both]">
            <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-500">
              <svg className="h-7 w-7" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="mb-2 text-xl font-bold text-text-main">
              Password Reset Complete
            </h2>
            <p className="mb-8 text-[13px] leading-relaxed text-text-muted">
              Your password has been successfully updated. You can now use your new password to sign in.
            </p>
            <button
              onClick={() => navigate("/login")}
              className="flex w-full items-center justify-center rounded-xl bg-bg-glass py-3 text-sm font-semibold text-text-main transition-colors hover:bg-bg-glass-hover"
            >
              Continue to Login
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
