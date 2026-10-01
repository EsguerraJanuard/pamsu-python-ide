import { useState, useEffect } from "react";
import { useAuth } from "../../features/auth/AuthContext";
import InstructorSidebar from "../../components/layout/InstructorSidebar";
import EditorSettings from "./EditorSettings";
import CustomSelect from "../../components/ui/CustomSelect";
import ConfirmationModal from "../../components/modals/ConfirmationModal";
import { api, ApiError } from "../../services/api";

/* ── Icons ─────────────────────────────────────────────── */

function SettingsIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
  );
}

function UserIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
  );
}

function CodeIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
  );
}

function LockIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
  );
}

function ShieldIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/></svg>
  );
}

/* ── Helpers ────────────────────────────────────────────── */

function getPasswordStrength(password) {
  if (!password) return null;
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  if (score <= 1) return { label: "Weak - use at least 8 characters", color: "#ef4444", width: "25%" };
  if (score === 2) return { label: "Fair - add uppercase letters, numbers, or symbols", color: "#f59e0b", width: "50%" };
  if (score === 3) return { label: "Good - one more requirement can strengthen it", color: "var(--color-psu-red, #ce0000)", width: "75%" };
  return { label: "Strong password", color: "#22c55e", width: "100%" };
}

/* ── Component ─────────────────────────────────────────── */

export default function InstructorSettings() {
  const { user, updateUser } = useAuth();
  const [saved, setSaved] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isConfirmSaveOpen, setIsConfirmSaveOpen] = useState(false);

  const inputWrap =
    "flex items-center gap-2.5 rounded-lg border border-border-subtle bg-bg-base px-3 py-2.5 transition-colors duration-200 focus-within:border-psu-maroon/60";

  const inputClass =
    "flex-1 bg-transparent text-sm text-text-main outline-none placeholder:text-text-muted";

  const readonlyInputClass =
    "flex-1 cursor-not-allowed bg-transparent text-sm text-text-muted outline-none select-none";

  // Password state
  const [passwords, setPasswords] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [showPasswords, setShowPasswords] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordMessageType, setPasswordMessageType] = useState("");

  const updatePasswordField = (field, value) => {
    setPasswords((prev) => ({ ...prev, [field]: value }));
    setPasswordMessage("");
  };

  const handleChangePassword = async (event) => {
    event.preventDefault();
    setPasswordMessage("");

    if (passwords.newPassword !== passwords.confirmPassword) {
      setPasswordMessageType("error");
      setPasswordMessage("The new passwords do not match.");
      return;
    }

    if (passwords.newPassword.length < 8) {
      setPasswordMessageType("error");
      setPasswordMessage("The new password must be at least 8 characters long.");
      return;
    }

    try {
      await api.post("/users/me/password", {
        current_password: passwords.currentPassword,
        new_password: passwords.newPassword,
      });

      setPasswordMessageType("success");
      setPasswordMessage("Password successfully updated.");
      setTimeout(() => {
        setPasswordMessage("");
      }, 2000);
      setPasswords({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });
    } catch (error) {
      setPasswordMessageType("error");
      setPasswordMessage(
        error instanceof ApiError ? error.message : "Failed to change password."
      );
    }
  };

  const [formData, setFormData] = useState({
    name: "Faculty Instructor",
    email: "instructor@pamsu.edu.ph",
    department: "College of Computing Studies",
    defaultCourse: "CCS101",
    astStrictness: user?.ast_strictness_level || "moderate",
    emailNotifications: true,
    liveMonitoringAlerts: true,
  });

  useEffect(() => {
    if (user) {
      setFormData((prev) => ({
        ...prev,
        name: user.name || user.fullName || prev.name,
        email: user.email || prev.email,
      }));
    }
  }, [user]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsConfirmSaveOpen(true);
  };

  const performSave = async () => {
    setErrorMsg(null);
    setIsConfirmSaveOpen(false);
    setSaved(false);

    try {
      const updatedUser = await api.patch("/users/me", {
        name: formData.name.trim(),
        ast_strictness_level: formData.astStrictness,
      });
      
      // Update global auth context
      updateUser({
        ...user,
        name: updatedUser.name,
        ast_strictness_level: updatedUser.ast_strictness_level,
      });

      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMsg(error.details || error.message);
      } else {
        setErrorMsg("Failed to update profile. Please try again.");
      }
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
      <InstructorSidebar />

      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <main className="settings-page min-w-0 flex-1 overflow-y-auto px-6 py-6 sm:px-8">
          <style>
            {`
              @keyframes settingsFadeUp {
                from {
                  opacity: 0;
                  transform: translateY(10px);
                }
                to {
                  opacity: 1;
                  transform: translateY(0);
                }
              }
              .settings-page {
                animation:
                  settingsFadeUp 450ms
                  cubic-bezier(0.25, 0.46, 0.45, 0.94)
                  both;
              }
              @media (prefers-reduced-motion: reduce) {
                .settings-page {
                  animation: none;
                }
              }
            `}
          </style>

          <div className="w-full">

            {/* ── Page header ───────────────────────────── */}
            <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-border-subtle pb-6">
              <div>
                <p className="mb-1 font-mono text-xs text-text-brand">ACCOUNT &amp; SYSTEM</p>
                <h1 className="text-2xl font-bold flex items-center gap-3">
                  <SettingsIcon className="h-6 w-6 text-text-brand" />
                  Settings
                </h1>
                <p className="mt-1 text-sm text-text-muted">
                  Manage your faculty profile and evaluation preferences.
                </p>
              </div>
            </header>

            {/* ── Alerts ────────────────────────────────── */}
            {errorMsg && (
              <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-xs text-red-400" role="alert">
                {errorMsg}
              </div>
            )}

            {saved && (
              <div className="mb-6 rounded-xl border border-psu-maroon/30 bg-psu-maroon/10 px-4 py-3 text-xs text-text-brand" role="status">
                Settings updated successfully. Changes have been saved.
              </div>
            )}

            <div className="space-y-6">

              {/* ── Section 1: Faculty Profile ──────────── */}
              <section className="rounded-xl border border-border-subtle bg-bg-glass p-5">

                <div className="mb-4">
                  <h2 className="text-sm font-semibold flex items-center gap-2">
                    <UserIcon className="h-4 w-4 text-text-brand" />
                    Profile Information
                  </h2>
                  <p className="mt-1 text-[11px] text-text-muted">
                    Verified identity details cannot be changed from this page.
                  </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">

                  <div>
                    <label htmlFor="instructor-name" className="mb-1.5 block text-xs font-medium text-text-muted">
                      Complete name
                    </label>
                    <div className={`${inputWrap} opacity-100 bg-bg-glass cursor-not-allowed`}>
                      <input
                        id="instructor-name"
                        type="text"
                        value={formData.name}
                        disabled
                        className={readonlyInputClass}
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="instructor-email" className="mb-1.5 block text-xs font-medium text-text-muted">
                      University email
                    </label>
                    <div className={`${inputWrap} opacity-100 bg-bg-glass cursor-not-allowed`}>
                      <input
                        id="instructor-email"
                        type="email"
                        value={formData.email}
                        disabled
                        className={readonlyInputClass}
                      />
                      <span className="shrink-0 text-[10px] text-text-muted">
                        Verified
                      </span>
                    </div>
                    <p className="mt-1.5 text-[11px] text-text-muted">
                      Instructor accounts are provisioned by a system administrator.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div>
                      <label htmlFor="instructor-dept" className="mb-1.5 block text-xs font-medium text-text-muted">
                        Department
                      </label>
                      <div className={`${inputWrap} opacity-100 bg-bg-glass cursor-not-allowed`}>
                        <input
                          id="instructor-dept"
                          type="text"
                          value={formData.department}
                          disabled
                          className={readonlyInputClass}
                        />
                        <span className="shrink-0 text-[10px] text-text-brand/80">
                          Admin
                        </span>
                      </div>
                    </div>

                    <div>
                      <label htmlFor="instructor-course" className="mb-1.5 block text-xs font-medium text-text-muted">
                        Default course
                      </label>
                      <div className={`${inputWrap} opacity-100 bg-bg-glass cursor-not-allowed`}>
                        <input
                          id="instructor-course"
                          type="text"
                          value={formData.defaultCourse}
                          disabled
                          className={readonlyInputClass}
                        />
                        <span className="shrink-0 text-[10px] text-text-brand/80">
                          Admin
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end pt-1">
                    {/* Save button hidden since all fields are read-only for now */}
                  </div>

                </form>

              </section>

              {/* ── Section 2: AST Grading Policy ──────── */}
              <section className="rounded-xl border border-border-subtle bg-bg-glass p-5">

                <div className="mb-4">
                  <h2 className="text-sm font-semibold flex items-center gap-2">
                    <CodeIcon className="h-4 w-4 text-text-brand" />
                    AST &amp; Automated Grading Policy
                  </h2>
                  <p className="mt-1 text-[11px] text-text-muted">
                    Configure the default strictness level for evaluating student code structures.
                  </p>
                </div>

                                  <form onSubmit={handleSubmit} className="flex flex-col gap-5">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[
                        { 
                          value: "lax", 
                          title: "Lenient", 
                          desc: "Requires at least one instance of a requirement to pass, even if more are requested. Focuses on execution output and basic presence of concepts.", 
                          icon: (
                            <svg className="w-5 h-5 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                            </svg>
                          )
                        },
                        { 
                          value: "moderate", 
                          title: "Moderate", 
                          desc: "Standard evaluation. Enforces the exact or minimum required counts of AST rules, ensuring students correctly structure their solutions.", 
                          icon: (
                            <svg className="w-5 h-5 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                            </svg>
                          )
                        },
                        { 
                          value: "strict", 
                          title: "Strict", 
                          desc: "Rigid evaluation. Code must match the exact number of required structures perfectly. Prevents bypassing or over-engineering the algorithm.", 
                          icon: (
                            <svg className="w-5 h-5 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                            </svg>
                          )
                        },
                      ].map((lvl) => (
                        <div 
                          key={lvl.value}
                          onClick={() => setFormData(prev => ({ ...prev, astStrictness: lvl.value }))}
                          className={`cursor-pointer rounded-xl border p-4 transition-all duration-200 ${
                            formData.astStrictness === lvl.value 
                              ? 'border-psu-maroon bg-psu-maroon/10 shadow-md shadow-psu-maroon/20 ring-1 ring-psu-maroon' 
                              : 'border-border-strong bg-bg-panel hover:border-psu-maroon/50 hover:bg-bg-glass-hover'
                          }`}
                        >
                          <div className={`flex flex-col h-full ${formData.astStrictness === lvl.value ? 'text-text-brand' : 'text-text-muted'}`}>
                            {lvl.icon}
                            <h3 className={`text-sm font-bold mb-1 ${formData.astStrictness === lvl.value ? 'text-text-brand' : 'text-text-main'}`}>
                              {lvl.title}
                            </h3>
                            <p className="text-[10px] leading-relaxed flex-1 opacity-90">
                              {lvl.desc}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
  
                    <div className="flex justify-end pt-2">
                      <button
                        type="submit"
                        className="rounded-lg bg-gradient-to-br from-psu-maroon to-psu-maroon px-6 py-2 text-sm font-semibold text-white shadow-md shadow-psu-maroon/20 transition duration-150 hover:-translate-y-px hover:opacity-90 active:translate-y-0 active:scale-[0.98]"
                      >
                        Save Strictness
                      </button>
                    </div>
                  </form>

              </section>

              {/* ── Section 2b: Editor Preferences ────── */}
              <EditorSettings />

              {/* ── Section 3: Change Password ─────────── */}
              <section className="rounded-xl border border-border-subtle bg-bg-glass p-5">

                <div className="mb-4">
                  <h2 className="text-sm font-semibold flex items-center gap-2">
                    <LockIcon className="h-4 w-4 text-text-brand" />
                    Change Password
                  </h2>
                  <p className="mt-1 text-[11px] text-text-muted">
                    Your current password must be verified by the server.
                  </p>
                </div>

                {passwordMessage && (
                  <div
                    role={passwordMessageType === "error" ? "alert" : "status"}
                    aria-live="polite"
                    className={`mb-4 rounded-lg border px-4 py-3 text-sm ${
                      passwordMessageType === "error"
                        ? "border-red-500/20 bg-red-500/10 text-text-rose"
                        : "border-psu-maroon/20 bg-psu-maroon/10 text-text-brand"
                    }`}
                  >
                    {passwordMessage}
                  </div>
                )}

                <form onSubmit={handleChangePassword} className="space-y-4" noValidate>

                  <div>
                    <label htmlFor="current-password" className="mb-1.5 block text-xs font-medium text-text-muted">
                      Current password
                    </label>
                    <div className={inputWrap}>
                      <input
                        id="current-password"
                        type={showPasswords ? "text" : "password"}
                        value={passwords.currentPassword}
                        onChange={(event) => updatePasswordField("currentPassword", event.target.value)}
                        placeholder="Enter your current password"
                        autoComplete="current-password"
                        className={inputClass}
                        style={{ caretColor: "var(--color-psu-gold, #eeb319)" }}
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="new-password" className="mb-1.5 block text-xs font-medium text-text-muted">
                      New password
                    </label>
                    <div className={inputWrap}>
                      <input
                        id="new-password"
                        type={showPasswords ? "text" : "password"}
                        value={passwords.newPassword}
                        onChange={(event) => updatePasswordField("newPassword", event.target.value)}
                        placeholder="At least 8 characters"
                        autoComplete="new-password"
                        minLength={8}
                        className={inputClass}
                        style={{ caretColor: "var(--color-psu-gold, #eeb319)" }}
                      />
                    </div>
                    {passwords.newPassword && getPasswordStrength(passwords.newPassword) && (() => {
                      const strength = getPasswordStrength(passwords.newPassword);
                      return (
                        <div className="mt-2.5">
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Strength</span>
                            <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: strength.color }}>
                              {strength.label.split(' - ')[0] || strength.label}
                            </span>
                          </div>
                          <div className="h-1 w-full overflow-hidden rounded-full bg-border-strong">
                            <div className="h-full rounded-full transition-all duration-300" style={{ width: strength.width, backgroundColor: strength.color }} />
                          </div>
                          {strength.label.includes(' - ') && (
                            <p className="mt-1.5 text-[10px] text-text-muted">{strength.label.split(' - ')[1]}</p>
                          )}
                        </div>
                      );
                    })()}
                  </div>

                  <div>
                    <label htmlFor="confirm-new-password" className="mb-1.5 block text-xs font-medium text-text-muted">
                      Confirm new password
                    </label>
                    <div className={inputWrap}>
                      <input
                        id="confirm-new-password"
                        type={showPasswords ? "text" : "password"}
                        value={passwords.confirmPassword}
                        onChange={(event) => updatePasswordField("confirmPassword", event.target.value)}
                        placeholder="Enter the new password again"
                        autoComplete="new-password"
                        minLength={8}
                        className={inputClass}
                        style={{ caretColor: "var(--color-psu-gold, #eeb319)" }}
                      />
                    </div>
                  </div>

                  <div className="flex items-center gap-3 mt-6 mb-2">
                    <label className="text-xs text-text-muted cursor-pointer flex items-center gap-2">
                      <div className="relative group flex items-center">
                        <input
                          type="checkbox"
                          checked={showPasswords}
                          onChange={() => setShowPasswords(!showPasswords)}
                          className="sr-only peer"
                        />
                        <div className="w-9 h-5 bg-border-strong rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-panel after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-psu-maroon group-hover:bg-text-muted/30 peer-checked:group-hover:opacity-80 shadow-inner"></div>
                      </div>
                      Show passwords
                    </label>
                  </div>

                  <div className="flex justify-end pt-1">
                    <button
                      type="submit"
                      className="rounded-lg bg-gradient-to-br from-psu-maroon to-psu-maroon px-4 py-2 text-sm font-semibold text-white transition duration-150 hover:-translate-y-px hover:opacity-90 active:translate-y-0 active:scale-[0.98]"
                    >
                      Update password
                    </button>
                  </div>

                </form>

              </section>

              {/* ── Section 4: Privacy ──────────────────── */}
              <section className="rounded-xl border border-border-subtle bg-bg-glass p-5">
                <h2 className="text-sm font-semibold flex items-center gap-2">
                  <ShieldIcon className="h-4 w-4 text-text-brand" />
                  Privacy and Session Security
                </h2>

                <ul className="mt-3 list-inside list-disc space-y-2 text-[11px] leading-relaxed text-text-muted">
                  <li>
                    The browser-stored profile is used only for
                    interface display.
                  </li>
                  <li>
                    The backend must validate every protected request
                    using the authenticated token.
                  </li>
                  <li>
                    Passwords must never be stored or logged by the
                    frontend.
                  </li>
                  <li>
                    Signing out removes local session information from
                    this browser.
                  </li>
                </ul>
              </section>

            </div>
          </div>
        </main>
      </div>

      <ConfirmationModal
        isOpen={isConfirmSaveOpen}
        title="Save Changes"
        message="Are you sure you want to update your faculty profile and evaluation settings?"
        confirmText="Save"
        cancelText="Cancel"
        onConfirm={performSave}
        onCancel={() => setIsConfirmSaveOpen(false)}
      />
    </div>
  );
}
