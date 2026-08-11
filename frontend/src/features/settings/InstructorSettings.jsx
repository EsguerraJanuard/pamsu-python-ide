import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthContext";
import InstructorSidebar from "../../components/layout/InstructorSidebar";
export default function InstructorSettings() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [saved, setSaved] = useState(false);

  const [formData, setFormData] = useState({
    name: "Faculty Instructor",
    email: "instructor@pamsu.edu.ph",
    department: "College of Computing Studies",
    defaultCourse: "CCS101",
    astStrictness: "moderate",
    emailNotifications: true,
    liveMonitoringAlerts: true,
  });

  useEffect(() => {
    if (user) {
      setFormData((prev) => ({
        ...prev,
        name: user.name || user.fullName || "Faculty Instructor",
        email: user.email || "instructor@pamsu.edu.ph",
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
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
      <InstructorSidebar />
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
            
            <div className="mx-auto max-w-6xl ">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <p className="mb-1 font-mono text-xs text-emerald-400">ACCOUNT & SYSTEM</p>
            <h1 className="text-2xl font-bold">Settings</h1>
            <p className="mt-1 text-sm text-text-muted">
              Manage your faculty profile and evaluation preferences.
            </p>
          </div>
        </header>

        {saved && (
          <div className="mb-6 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-xs text-emerald-300">
            Settings updated successfully. Changes have been saved.
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <section className="rounded-xl border border-border-subtle bg-bg-glass p-5">
            <h2 className="text-sm font-semibold text-text-main mb-4">Faculty Profile</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs text-text-muted mb-1">Full Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-border-subtle bg-bg-glass px-3 py-2 text-xs text-text-main focus:border-emerald-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs text-text-muted mb-1">Email Address</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-border-subtle bg-bg-glass px-3 py-2 text-xs text-text-main focus:border-emerald-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs text-text-muted mb-1">Department</label>
                <input
                  type="text"
                  name="department"
                  value={formData.department}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-border-subtle bg-bg-glass px-3 py-2 text-xs text-text-main focus:border-emerald-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs text-text-muted mb-1">Default Course</label>
                <input
                  type="text"
                  name="defaultCourse"
                  value={formData.defaultCourse}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-border-subtle bg-bg-glass px-3 py-2 text-xs text-text-main focus:border-emerald-500 focus:outline-none"
                />
              </div>
            </div>
          </section>

          <section className="rounded-xl border border-border-subtle bg-bg-glass p-5">
            <h2 className="text-sm font-semibold text-text-main mb-4">AST & Automated Grading Policy</h2>
            <div>
              <label className="block text-xs text-text-muted mb-1">Default AST Strictness Level</label>
              <select
                name="astStrictness"
                value={formData.astStrictness}
                onChange={handleChange}
                className="w-full rounded-lg border border-border-subtle bg-bg-base px-3 py-2 text-xs text-text-main focus:border-emerald-500 focus:outline-none"
              >
                <option value="lenient">Lenient (Focus on execution output only)</option>
                <option value="moderate">Moderate (Standard AST pattern checks)</option>
                <option value="strict">Strict (Enforce rigid structural loop/function rules)</option>
              </select>
            </div>
          </section>

          <div className="flex justify-end gap-3">
            <button
              type="submit"
              className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-text-main hover:bg-emerald-500 transition"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
          </main>
        </div>
      </div>
    </div>
  );
}