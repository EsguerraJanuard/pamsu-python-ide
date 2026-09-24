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
            
            <div className="mx-auto max-w-4xl">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <p className="mb-1 font-mono text-xs text-text-emerald">ACCOUNT & SYSTEM</p>
            <h1 className="text-2xl font-bold flex items-center gap-3">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6 text-text-emerald"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
              Settings
            </h1>
            <p className="mt-1 text-sm text-text-muted">
              Manage your faculty profile and evaluation preferences.
            </p>
          </div>
        </header>

        {errorMsg && (
          <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-xs text-red-400">
            {errorMsg}
          </div>
        )}

        {saved && (
          <div className="mb-6 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-xs text-text-emerald">
            Settings updated successfully. Changes have been saved.
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <section className="rounded-xl border border-border-subtle bg-bg-glass p-5">
            <h2 className="text-sm font-semibold text-text-main mb-4">Faculty Profile</h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs text-text-muted mb-1">Full Name (Verified)</label>
                  <div className="opacity-100 bg-bg-glass cursor-not-allowed rounded-lg border border-border-subtle px-3 py-2">
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      disabled
                      className="w-full bg-transparent text-xs text-text-main outline-none cursor-not-allowed"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-text-muted mb-1">Email Address (Verified)</label>
                  <div className="opacity-100 bg-bg-glass cursor-not-allowed rounded-lg border border-border-subtle px-3 py-2">
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      disabled
                      className="w-full bg-transparent text-xs text-text-main outline-none cursor-not-allowed"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-text-muted mb-1 flex items-center justify-between">
                    Department
                    <span className="text-[10px] text-emerald-500/80">Managed by Admin</span>
                  </label>
                  <div className="opacity-100 bg-bg-glass cursor-not-allowed rounded-lg border border-border-subtle px-3 py-2">
                    <input
                      type="text"
                      name="department"
                      value="College of Computing Studies"
                      disabled
                      className="w-full bg-transparent text-xs text-text-main outline-none cursor-not-allowed"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-text-muted mb-1 flex items-center justify-between">
                    Default Course
                    <span className="text-[10px] text-emerald-500/80">Managed by Admin</span>
                  </label>
                  <div className="opacity-100 bg-bg-glass cursor-not-allowed rounded-lg border border-border-subtle px-3 py-2">
                    <input
                      type="text"
                      name="defaultCourse"
                      value="CCS101"
                      disabled
                      className="w-full bg-transparent text-xs text-text-main outline-none cursor-not-allowed"
                    />
                  </div>
                </div>
              </div>
          </section>

          <section className="rounded-xl border border-border-subtle bg-bg-glass p-5">
            <h2 className="text-sm font-semibold text-text-main mb-4">AST & Automated Grading Policy</h2>
            <div>
              <label className="block text-xs text-text-muted mb-1">Default AST Strictness Level</label>
              <CustomSelect
                value={formData.astStrictness}
                onChange={(val) => setFormData(prev => ({ ...prev, astStrictness: val }))}
                className="w-full px-3 py-2 text-xs"
                options={[
                  { value: "lax", label: "Lenient (Focus on execution output only)" },
                  { value: "moderate", label: "Moderate (Standard AST pattern checks)" },
                  { value: "strict", label: "Strict (Enforce rigid structural loop/function rules)" }
                ]}
              />
            </div>
          </section>

          <div className="flex justify-end gap-3">
            <button
              type="submit"
              className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500 transition"
            >
              Save Changes
            </button>
          </div>
        </form>

        <section className="rounded-xl border border-border-subtle bg-bg-glass p-5 mt-6">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-text-main">
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
                  : "border-emerald-500/20 bg-emerald-500/10 text-text-emerald"
              }`}
            >
              {passwordMessage}
            </div>
          )}

          <form onSubmit={handleChangePassword} className="space-y-4" noValidate>
            <div className="max-w-lg space-y-4">
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
                  required
                  className={inputClass}
                  style={{ caretColor: "#10b981" }}
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
                  required
                  className={inputClass}
                  style={{ caretColor: "#10b981" }}
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
                    <div className="h-1 w-full overflow-hidden rounded-full bg-white/5">
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
                  required
                  className={inputClass}
                  style={{ caretColor: "#10b981" }}
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
                    <div className="w-9 h-5 bg-border-strong rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-panel after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500 group-hover:bg-text-muted/30 peer-checked:group-hover:bg-emerald-400 shadow-inner"></div>
                  </div>
                Show passwords
              </label>
            </div>
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="submit"
                className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500 transition duration-150"
              >
                Update password
              </button>
            </div>
          </form>
        </section>
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


