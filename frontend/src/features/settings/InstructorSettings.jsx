import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthContext";
import InstructorSidebar from "../../components/layout/InstructorSidebar";
import CustomSelect from "../../components/ui/CustomSelect";
import ConfirmationModal from "../../components/modals/ConfirmationModal";
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

export default function InstructorSettings() {
  const navigate = useNavigate();
  const { user, updateUser } = useAuth();
  const [saved, setSaved] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isConfirmSaveOpen, setIsConfirmSaveOpen] = useState(false);

  const inputClass = "flex-1 bg-transparent text-sm text-text-main outline-none placeholder:text-text-muted";
  const inputWrap = "flex items-center gap-2.5 rounded-lg border border-border-subtle bg-bg-base px-3 py-2.5 transition-colors duration-200 focus-within:border-emerald-500/60";

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

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

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
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
            
            <div className="mx-auto max-w-3xl">
        <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-border-subtle pb-6">
          <div>
            <p className="mb-1 font-mono text-xs text-emerald-500">ACCOUNT & SYSTEM</p>
            <h1 className="text-2xl font-bold flex items-center gap-3 text-text-main">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6 text-emerald-500"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
              Settings
            </h1>
            <p className="mt-1 text-sm text-text-muted">
              Manage your faculty profile and evaluation preferences.
            </p>
          </div>
        </header>

        {errorMsg && (
          <div className="mb-6 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-text-rose" role="alert">
            {errorMsg}
          </div>
        )}

        {saved && (
          <div className="mb-6 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-text-emerald" role="status">
            Settings updated successfully. Changes have been saved.
          </div>
        )}

        <div className="space-y-6">
          <form onSubmit={handleSubmit}>
            <section className="rounded-xl border border-border-subtle bg-bg-glass overflow-hidden">
              <div className="p-6 sm:p-8">
                <div className="mb-6">
                  <h2 className="text-base font-semibold text-text-main">Faculty Profile</h2>
                  <p className="mt-1 text-[11px] text-text-muted">Verified identity details cannot be changed from this page.</p>
                </div>
                
                <div className="space-y-5 max-w-lg">
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-text-muted">Full Name</label>
                    <div className={`${inputWrap} opacity-100 bg-bg-glass cursor-not-allowed`}>
                      <input type="text" name="name" value={formData.name} disabled className="flex-1 cursor-not-allowed bg-transparent text-sm text-text-muted outline-none select-none" />
                    </div>
                  </div>
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-text-muted">Email Address</label>
                    <div className={`${inputWrap} opacity-100 bg-bg-glass cursor-not-allowed`}>
                      <input type="email" name="email" value={formData.email} disabled className="flex-1 cursor-not-allowed bg-transparent text-sm text-text-muted outline-none select-none" />
                    </div>
                  </div>
                  <div>
                    <label className="mb-1.5 flex items-center justify-between text-xs font-medium text-text-muted">
                      Department
                      <span className="text-[10px] text-emerald-500/80 font-normal">Managed by Admin</span>
                    </label>
                    <div className={`${inputWrap} opacity-100 bg-bg-glass cursor-not-allowed`}>
                      <input type="text" name="department" value="College of Computing Studies" disabled className="flex-1 cursor-not-allowed bg-transparent text-sm text-text-muted outline-none select-none" />
                    </div>
                  </div>
                  <div>
                    <label className="mb-1.5 flex items-center justify-between text-xs font-medium text-text-muted">
                      Default Course
                      <span className="text-[10px] text-emerald-500/80 font-normal">Managed by Admin</span>
                    </label>
                    <div className={`${inputWrap} opacity-100 bg-bg-glass cursor-not-allowed`}>
                      <input type="text" name="defaultCourse" value="CCS101" disabled className="flex-1 cursor-not-allowed bg-transparent text-sm text-text-muted outline-none select-none" />
                    </div>
                  </div>
                </div>

                <div className="mt-8 mb-6 border-t border-border-subtle pt-8">
                  <h2 className="text-base font-semibold text-text-main mb-1">AST & Automated Grading Policy</h2>
                  <p className="text-[11px] text-text-muted mb-6">Configure the default strictness level for evaluating student code structures.</p>
                  
                  <div className="max-w-lg">
                    <label className="mb-1.5 block text-xs font-medium text-text-muted">Default AST Strictness Level</label>
                    <CustomSelect
                      value={formData.astStrictness}
                      onChange={(val) => setFormData(prev => ({ ...prev, astStrictness: val }))}
                      className="w-full text-sm"
                      options={[
                        { value: "lax", label: "Lenient (Execution output only)" },
                        { value: "moderate", label: "Moderate (Standard AST checks)" },
                        { value: "strict", label: "Strict (Enforce rigid rules)" }
                      ]}
                    />
                  </div>
                </div>
              </div>

              <div className="border-t border-border-subtle bg-bg-glass px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <p className="text-[11px] text-text-muted">Changes apply to all future assignments by default.</p>
                <button
                  type="submit"
                  className="rounded-lg bg-emerald-600 px-5 py-2.5 text-xs font-semibold text-white transition-all hover:bg-emerald-500 hover:-translate-y-0.5 active:translate-y-0"
                >
                  Save Changes
                </button>
              </div>
            </section>
          </form>

          <section className="rounded-xl border border-border-subtle bg-bg-glass overflow-hidden">
            <div className="p-6 sm:p-8">
              <div className="mb-6">
                <h2 className="text-base font-semibold text-text-main">Change Password</h2>
                <p className="mt-1 text-[11px] text-text-muted">Your current password must be verified by the server before updating.</p>
              </div>

              {passwordMessage && (
                <div
                  role={passwordMessageType === "error" ? "alert" : "status"}
                  aria-live="polite"
                  className={`mb-6 flex items-center gap-3 rounded-lg border px-4 py-3 text-sm ${
                    passwordMessageType === "error"
                      ? "border-red-500/20 bg-red-500/10 text-text-rose"
                      : "border-emerald-500/20 bg-emerald-500/10 text-text-emerald"
                  }`}
                >
                  {passwordMessageType === "error" ? (
                    <svg className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  ) : (
                    <svg className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  )}
                  {passwordMessage}
                </div>
              )}

              <form id="password-form" onSubmit={handleChangePassword} className="space-y-5" noValidate>
                <div className="max-w-lg space-y-5">
                  <div>
                    <label htmlFor="current-password" className="mb-1.5 block text-xs font-medium text-text-muted">Current password</label>
                    <div className={inputWrap}>
                      <input
                        id="current-password"
                        type={showPasswords ? "text" : "password"}
                        value={passwords.currentPassword}
                        onChange={(event) => updatePasswordField("currentPassword", event.target.value)}
                        placeholder="Enter your current password"
                        autoComplete="current-password"
                        required
                        className={inputClass}
                        style={{ caretColor: "#10b981" }}
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="new-password" className="mb-1.5 block text-xs font-medium text-text-muted">New password</label>
                    <div className={inputWrap}>
                      <input
                        id="new-password"
                        type={showPasswords ? "text" : "password"}
                        value={passwords.newPassword}
                        onChange={(event) => updatePasswordField("newPassword", event.target.value)}
                        placeholder="At least 8 characters"
                        autoComplete="new-password"
                        minLength={8}
                        required
                        className={inputClass}
                        style={{ caretColor: "#10b981" }}
                      />
                    </div>
                    {passwords.newPassword && getPasswordStrength(passwords.newPassword) && (() => {
                      const strength = getPasswordStrength(passwords.newPassword);
                      return (
                        <div className="mt-3">
                          <div className="mb-1.5 flex items-center justify-between">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">Strength</span>
                            <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: strength.color }}>
                              {strength.label.split(' - ')[0] || strength.label}
                            </span>
                          </div>
                          <div className="h-1.5 w-full overflow-hidden rounded-full bg-border-strong">
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
                    <label htmlFor="confirm-new-password" className="mb-1.5 block text-xs font-medium text-text-muted">Confirm new password</label>
                    <div className={inputWrap}>
                      <input
                        id="confirm-new-password"
                        type={showPasswords ? "text" : "password"}
                        value={passwords.confirmPassword}
                        onChange={(event) => updatePasswordField("confirmPassword", event.target.value)}
                        placeholder="Enter the new password again"
                        autoComplete="new-password"
                        minLength={8}
                        required
                        className={inputClass}
                        style={{ caretColor: "#10b981" }}
                      />
                    </div>
                  </div>

                  <div className="pt-2">
                    <label className="group flex cursor-pointer select-none items-center gap-2 text-xs font-medium text-text-muted">
                      <div className="relative flex items-center">
                        <input
                          type="checkbox"
                          checked={showPasswords}
                          onChange={() => setShowPasswords(!showPasswords)}
                          className="peer sr-only"
                        />
                        <div className="h-5 w-9 rounded-full bg-border-strong shadow-inner transition-colors peer-checked:bg-emerald-500 after:absolute after:left-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-all peer-checked:after:translate-x-full group-hover:opacity-80"></div>
                      </div>
                      Show passwords
                    </label>
                  </div>
                </div>
              </form>
            </div>
            <div className="flex justify-end border-t border-border-subtle bg-bg-glass px-6 py-4">
              <button
                type="submit"
                form="password-form"
                className="rounded-lg bg-emerald-600 px-5 py-2.5 text-xs font-semibold text-white transition-all hover:bg-emerald-500 hover:-translate-y-0.5 active:translate-y-0"
              >
                Update password
              </button>
            </div>
          </section>
        </div>
      </div>
      </main>
        </div>
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


