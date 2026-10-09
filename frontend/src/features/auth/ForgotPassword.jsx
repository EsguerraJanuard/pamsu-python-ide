import { useState, useRef, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
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

  // Lock page to Light Mode
  useEffect(() => {
    document.documentElement.classList.remove("dark");
    localStorage.setItem("pamsu_theme", "light");
  }, []);



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

  const inputClass = "flex-1 bg-transparent text-[15px] font-medium text-text-main outline-none placeholder:text-text-muted/50 placeholder:font-normal disabled:opacity-50";
  const inputWrap = "flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm transition-all duration-300 focus-within:border-psu-maroon/50 focus-within:bg-white focus-within:ring-2 focus-within:ring-psu-maroon/20 hover:border-slate-300 cursor-text";
  const buttonClass = "group relative overflow-hidden flex w-full items-center justify-center gap-2 rounded-xl bg-psu-maroon px-5 py-4 text-[15px] font-bold tracking-wide text-white shadow-md shadow-psu-maroon/20 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-psu-maroon/30 active:translate-y-0 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-60";

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 text-text-main overflow-hidden p-6 relative">
      {/* Subtle Ambient Glows */}
      <div className="absolute top-0 right-0 -z-10 h-[800px] w-[800px] translate-x-1/4 -translate-y-1/4 rounded-full bg-psu-gold/10 blur-[150px]" />
      <div className="absolute bottom-0 left-0 -z-10 h-[800px] w-[800px] -translate-x-1/4 translate-y-1/4 rounded-full bg-psu-maroon/10 blur-[150px]" />

      <div className="relative z-10 w-full max-w-[500px] rounded-[28px] border border-slate-200/50 bg-white/90 backdrop-blur-2xl p-10 sm:p-14 shadow-2xl shadow-slate-200 animate-page-fade">
        
        {/* Brand Header */}
        <div className="mb-10 text-center flex flex-col items-center">
          <div className="mb-6 flex items-center justify-center h-16 w-16 rounded-2xl bg-white shadow-md border border-slate-100">
            <img src="/school_logo.png" alt="PSU Logo" className="h-10 w-10 object-contain drop-shadow-sm" />
          </div>
          <h2 className="text-3xl sm:text-[34px] font-black tracking-tight text-text-main leading-tight">
            {step === 1 && "Account Recovery"}
            {step === 2 && "Secure Reset"}
            {step === 3 && "Reset Complete"}
          </h2>
          <p className="mt-4 text-[15px] text-text-muted leading-relaxed max-w-[320px] mx-auto">
            {step === 1 && "Enter your registered university email to receive a secure recovery code."}
            {step === 2 && <>We've sent a 6-digit code to <span className="font-semibold text-psu-maroon">{email}</span></>}
            {step === 3 && "Your password has been successfully updated. You may now sign in."}
          </p>
        </div>

        {errorMsg && (
          <div className="mb-8 rounded-xl border border-red-500/20 bg-red-50 px-5 py-4 text-[14px] font-medium text-red-600 shadow-sm">
            {errorMsg}
          </div>
        )}

        {step === 1 && (
          <form onSubmit={handleStartReset} className="animate-[registerFadeUp_400ms_ease-out_both] space-y-6">
            <div>
              <label htmlFor="email" className="mb-2 block text-[13px] font-bold text-text-muted uppercase tracking-wider">
                University Email Address
              </label>
              <div className={inputWrap} onClick={(e) => e.currentTarget.querySelector('input').focus()}>
                <svg width="18" height="18" viewBox="0 0 15 15" fill="none" className="shrink-0 text-text-muted pointer-events-none transition-colors group-focus-within:text-psu-maroon" aria-hidden="true">
                  <path d="M1 4l6.5 4.5L14 4M1 3h13a.5.5 0 01.5.5v8a.5.5 0 01-.5.5H1a.5.5 0 01-.5-.5v-8A.5.5 0 011 3z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
                </svg>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@pampangastateu.edu.ph"
                  required
                  disabled={loading}
                  className={inputClass}
                  style={{ caretColor: "var(--color-psu-gold, #eeb319)" }}
                />
              </div>
            </div>

            <div className="pt-2">
              <button type="submit" disabled={loading} className={buttonClass}>
                {loading ? (
                  <svg className="h-5 w-5 animate-spin text-white" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" /></svg>
                ) : (
                  "Send Recovery Code"
                )}
              </button>
            </div>

            <div className="mt-8 text-center">
              <Link to="/login" className="text-[14px] font-semibold text-text-muted hover:text-psu-maroon transition-colors">
                Remember your password? <span className="text-psu-maroon">Log in instead</span>
              </Link>
            </div>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={handleCompleteReset} className="animate-[registerFadeUp_400ms_ease-out_both] space-y-6">
            <div>
              <div className="mb-2 flex items-center justify-between">
                <label className="text-[13px] font-bold text-text-muted uppercase tracking-wider">
                  Verification Code
                </label>
                <button
                  type="button"
                  onClick={handleResendOTP}
                  disabled={resendTimer > 0 || loading}
                  className="text-[12px] font-bold text-psu-maroon hover:text-psu-gold transition-colors disabled:text-text-muted/50"
                >
                  {resendTimer > 0 ? `Resend in ${resendTimer}s` : "Resend code"}
                </button>
              </div>
              <div className={inputWrap} onClick={(e) => e.currentTarget.querySelector('input').focus()}>
                <input
                  type="text"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/[^0-9]/g, "").slice(0, 6))}
                  placeholder="------"
                  required
                  className={`${inputClass} tracking-[0.5em] text-center font-mono text-lg font-bold`}
                  style={{ caretColor: "var(--color-psu-gold, #eeb319)" }}
                />
              </div>
            </div>

            <div>
              <label className="mb-2 block text-[13px] font-bold text-text-muted uppercase tracking-wider">
                New Password
              </label>
              <div className={inputWrap} onClick={(e) => { if (e.target.closest('button')) return; e.currentTarget.querySelector('input').focus(); }}>
                <svg width="18" height="18" viewBox="0 0 14 14" fill="none" className="shrink-0 text-text-muted pointer-events-none transition-colors group-focus-within:text-psu-maroon" aria-hidden="true">
                  <rect x="2" y="6" width="10" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
                  <path d="M4.5 6V4.5a2.5 2.5 0 015 0V6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
                <input
                  type={showPasswords ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  required
                  className={`${inputClass} tracking-widest`}
                  style={{ caretColor: "var(--color-psu-gold, #eeb319)" }}
                />
                <button type="button" onClick={() => setShowPasswords(!showPasswords)} className="shrink-0 text-text-muted hover:text-text-main" aria-label="Toggle password visibility">
                  {showPasswords ? (
                    <svg width="18" height="18" viewBox="0 0 16 16" fill="none"><path d="M2 8s2.5-4 6-4 6 4 6 4-2.5 4-6 4-6-4-6-4z" stroke="currentColor" strokeWidth="1.5" /><circle cx="8" cy="8" r="1.5" stroke="currentColor" strokeWidth="1.5" /><path d="M3 3l10 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 16 16" fill="none"><path d="M2 8s2.5-4 6-4 6 4 6 4-2.5 4-6 4-6-4-6-4z" stroke="currentColor" strokeWidth="1.5" /><circle cx="8" cy="8" r="1.5" stroke="currentColor" strokeWidth="1.5" /></svg>
                  )}
                </button>
              </div>
              {newPassword && getPasswordStrength(newPassword) && (() => {
                const strength = getPasswordStrength(newPassword);
                return (
                  <div className="mt-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Strength</span>
                      <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: strength.color }}>{strength.label.split(' - ')[0] || strength.label}</span>
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full rounded-full transition-all duration-300" style={{ width: strength.width, backgroundColor: strength.color }} />
                    </div>
                  </div>
                );
              })()}
            </div>

            <div>
              <label className="mb-2 block text-[13px] font-bold text-text-muted uppercase tracking-wider">
                Confirm New Password
              </label>
              <div className={inputWrap} onClick={(e) => { if (e.target.closest('button')) return; e.currentTarget.querySelector('input').focus(); }}>
                <svg width="18" height="18" viewBox="0 0 14 14" fill="none" className="shrink-0 text-text-muted pointer-events-none transition-colors group-focus-within:text-psu-maroon" aria-hidden="true">
                  <rect x="2" y="6" width="10" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
                  <path d="M4.5 6V4.5a2.5 2.5 0 015 0V6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
                <input
                  type={showPasswords ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Enter the new password again"
                  required
                  className={`${inputClass} tracking-widest`}
                  style={{ caretColor: "var(--color-psu-gold, #eeb319)" }}
                />
              </div>
            </div>

            <div className="pt-4 space-y-4">
              <button type="submit" disabled={loading || otpCode.length !== 6} className={buttonClass}>
                {loading ? (
                  <svg className="h-5 w-5 animate-spin text-white" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" /></svg>
                ) : (
                  "Reset Password"
                )}
              </button>
              
              <button
                type="button"
                onClick={() => setStep(1)}
                className="group flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-4 text-[15px] font-bold text-text-main shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:bg-slate-50 hover:shadow active:translate-y-0 active:scale-[0.98]"
              >
                Back to email
              </button>
            </div>
          </form>
        )}

        {step === 3 && (
          <div className="animate-[registerFadeUp_400ms_ease-out_both] flex flex-col items-center pt-2">
            <div className="mb-8 flex h-20 w-20 items-center justify-center rounded-full bg-emerald-50 text-emerald-500 ring-8 ring-emerald-50/50">
              <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div className="w-full">
              <button
                onClick={() => navigate("/login")}
                className={buttonClass}
              >
                Continue to Login
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
