/**
 * Settings.jsx
 * Student account settings page.
 *
 * TODO (Backend): GET /api/student/profile — load current settings
 * TODO (Backend): PUT /api/student/profile — save updated settings
 * TODO (Backend): PUT /api/student/password — change password (bcrypt hash server-side)
 * TODO (Frontend): replace MOCK_STUDENT with real data from API
 * TODO (Frontend): wire up save buttons to API calls
 */

import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import StatusBar from "../components/StatusBar";

const MOCK_STUDENT = {
  firstName: "Juan Miguel",
  lastName: "David",
  institutionalId: "2024-00001",
  email: "mjuan@student.edu.ph",
  course: "CCS101",
  section: "CS-3A",
};

export default function Settings() {
  const [mounted, setMounted] = useState(false);
  const [profile, setProfile] = useState(MOCK_STUDENT);
  const [passwords, setPasswords] = useState({ current: "", newPass: "", confirm: "" });
  const [showPasswords, setShowPasswords] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);
  const [passwordSaved, setPasswordSaved] = useState(false);

  // TODO (Frontend): add error states
  // const [profileError, setProfileError] = useState(null);
  // const [passwordError, setPasswordError] = useState(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Save profile — TODO (Frontend): connect to PUT /api/student/profile
  const handleSaveProfile = (e) => {
    e.preventDefault();
    console.log("Save profile:", profile); // remove when API is ready
    setProfileSaved(true);
    setTimeout(() => setProfileSaved(false), 2500);
  };

  // Change password — TODO (Frontend): connect to PUT /api/student/password
  const handleChangePassword = (e) => {
    e.preventDefault();
    if (passwords.newPass !== passwords.confirm) {
      alert("New passwords don't match."); // TODO: replace with inline error
      return;
    }
    console.log("Change password"); // remove when API is ready
    setPasswordSaved(true);
    setPasswords({ current: "", newPass: "", confirm: "" });
    setTimeout(() => setPasswordSaved(false), 2500);
  };

  const inputWrap = "flex items-center gap-2.5 bg-[#0f1117] border border-white/[0.08] rounded-lg px-3 py-2.5 focus-within:border-[#3b82f6]/60 transition-colors duration-200";
  const inputClass = "flex-1 bg-transparent text-sm text-white outline-none select-text cursor-text placeholder-white/20";

  return (
    <div
      className="flex min-h-screen bg-[#0f1117] text-white select-none cursor-default"
      style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.4s ease" }}
    >
      <Sidebar activePage="Settings" />

      <main className="flex-1 overflow-y-auto px-8 py-6 pb-12">

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Settings</h1>
          <p className="text-sm text-white/40 mt-1">Manage your account information.</p>
        </div>

        <div className="max-w-xl space-y-6">

          {/* ── Profile section ── */}
          <div className="bg-[#1a1d27] border border-white/[0.06] rounded-xl p-5">
            <h2 className="text-sm font-semibold text-white mb-4">Profile Information</h2>
            <form onSubmit={handleSaveProfile} className="space-y-4">

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-white/60 mb-1.5">First name</label>
                  <div className={inputWrap}>
                    <input
                      type="text"
                      value={profile.firstName}
                      onChange={(e) => setProfile({ ...profile, firstName: e.target.value })}
                      className={inputClass}
                      style={{ caretColor: "#3b82f6" }}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-white/60 mb-1.5">Last name</label>
                  <div className={inputWrap}>
                    <input
                      type="text"
                      value={profile.lastName}
                      onChange={(e) => setProfile({ ...profile, lastName: e.target.value })}
                      className={inputClass}
                      style={{ caretColor: "#3b82f6" }}
                    />
                  </div>
                </div>
              </div>

              {/* Institutional ID — read only, students can't change this */}
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">
                  Institutional ID <span className="text-white/25">(cannot be changed)</span>
                </label>
                <div className={inputWrap} style={{ opacity: 0.5 }}>
                  <input
                    type="text"
                    value={profile.institutionalId}
                    disabled
                    className={inputClass}
                    style={{ caretColor: "#3b82f6" }}
                  />
                </div>
              </div>

              {/* Email */}
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">Institutional Email</label>
                <div className={inputWrap}>
                  <input
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                    className={inputClass}
                    style={{ caretColor: "#3b82f6" }}
                  />
                </div>
              </div>

              {/* Save button */}
              <div className="flex items-center justify-between pt-1">
                {profileSaved && (
                  <span className="text-xs text-[#22c55e]">Profile saved successfully.</span>
                )}
                <button
                  type="submit"
                  className="ml-auto px-4 py-2 rounded-lg text-sm font-semibold text-white cursor-pointer"
                  style={{
                    background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                    transition: "opacity 0.15s ease, transform 0.15s ease",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.opacity = "0.88";
                    e.currentTarget.style.transform = "translateY(-1px)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.opacity = "1";
                    e.currentTarget.style.transform = "translateY(0)";
                  }}
                >
                  Save changes
                </button>
              </div>
            </form>
          </div>

          {/* ── Change password section ──
              TODO (Backend): PUT /api/student/password
              Body: { current_password, new_password }
              Always hash new password with bcrypt server-side before saving.
          ── */}
          <div className="bg-[#1a1d27] border border-white/[0.06] rounded-xl p-5">
            <h2 className="text-sm font-semibold text-white mb-4">Change Password</h2>
            <form onSubmit={handleChangePassword} className="space-y-4">

              {[
                { label: "Current password",  key: "current",  placeholder: "Enter current password" },
                { label: "New password",       key: "newPass",  placeholder: "At least 8 characters" },
                { label: "Confirm new password", key: "confirm", placeholder: "Repeat new password" },
              ].map((field) => (
                <div key={field.key}>
                  <label className="block text-xs font-medium text-white/60 mb-1.5">{field.label}</label>
                  <div className={inputWrap}>
                    <input
                      type={showPasswords ? "text" : "password"}
                      placeholder={field.placeholder}
                      value={passwords[field.key]}
                      onChange={(e) => setPasswords({ ...passwords, [field.key]: e.target.value })}
                      minLength={field.key !== "current" ? 8 : undefined}
                      required
                      className={inputClass}
                      style={{ caretColor: "#3b82f6" }}
                    />
                  </div>
                </div>
              ))}

              {/* Show passwords toggle */}
              <label className="flex items-center gap-2 cursor-pointer">
                <div
                  className="w-4 h-4 rounded border transition-all duration-150 flex items-center justify-center"
                  style={{
                    background: showPasswords ? "#3b82f6" : "transparent",
                    borderColor: showPasswords ? "#3b82f6" : "rgba(255,255,255,0.2)",
                  }}
                  onClick={() => setShowPasswords(!showPasswords)}
                >
                  {showPasswords && (
                    <svg width="10" height="10" viewBox="0 0 16 16" fill="none">
                      <path d="M3 8l4 4 6-7" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                </div>
                <span
                  className="text-xs text-white/40 cursor-pointer select-text"
                  onClick={() => setShowPasswords(!showPasswords)}
                >
                  Show passwords
                </span>
              </label>

              <div className="flex items-center justify-between pt-1">
                {passwordSaved && (
                  <span className="text-xs text-[#22c55e]">Password changed successfully.</span>
                )}
                <button
                  type="submit"
                  className="ml-auto px-4 py-2 rounded-lg text-sm font-semibold text-white cursor-pointer"
                  style={{
                    background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                    transition: "opacity 0.15s ease, transform 0.15s ease",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.opacity = "0.88";
                    e.currentTarget.style.transform = "translateY(-1px)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.opacity = "1";
                    e.currentTarget.style.transform = "translateY(0)";
                  }}
                >
                  Update password
                </button>
              </div>
            </form>
          </div>

          {/* ── Danger zone ── */}
          <div className="bg-[#1a1d27] border border-red-500/20 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-red-400 mb-1">Danger Zone</h2>
            <p className="text-[11px] text-white/30 mb-4">
              These actions are permanent and cannot be undone.
            </p>
            <button
              type="button"
              className="px-4 py-2 rounded-lg text-sm font-semibold text-red-400 border border-red-500/30 cursor-pointer"
              style={{
                background: "rgba(239,68,68,0.08)",
                transition: "background 0.2s ease, transform 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(239,68,68,0.15)";
                e.currentTarget.style.transform = "translateY(-1px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(239,68,68,0.08)";
                e.currentTarget.style.transform = "translateY(0)";
              }}
              // TODO (Frontend): show a confirmation modal before deleting
              // TODO (Backend): DELETE /api/student/account
              onClick={() => console.log("Delete account — not connected yet")}
            >
              Delete account
            </button>
          </div>
        </div>
      </main>

      <StatusBar />
    </div>
  );
}