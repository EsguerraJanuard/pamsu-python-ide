import { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import InstructorSidebar from "../../components/layout/InstructorSidebar";
import Statusbar from "../../components/layout/Statusbar";

export default function InstructorSettings() {
  const { user } = useAuth();

  const [formData, setFormData] = useState({
    name: user?.name || user?.fullName || "Faculty Instructor",
    email: user?.email || "instructor@pamsu.edu.ph",
    department: user?.department || "College of Computing Studies",
    defaultCourse: user?.courseCode || "CCS101",
    astStrictness: "moderate",
    emailNotifications: true,
    liveMonitoringAlerts: true,
  });

  const [saved, setSaved] = useState(false);

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
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white select-none">
      <InstructorSidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="dashboard-page min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
            <div className="mx-auto max-w-4xl">
              <header className="mb-6">
                <p className="mb-1 font-mono text-xs text-emerald-400">
                  FACULTY MANAGEMENT
                </p>
                <h1 className="text-2xl font-bold">Instructor Settings</h1>
                <p className="mt-1 text-sm text-white/40">
                  Manage your faculty profile, evaluation preferences, and notification defaults.
                </p>
              </header>

              {saved && (
                <div className="mb-6 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-xs text-emerald-300">
                  Settings updated successfully. Changes have been saved.
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Profile Section */}
                <section className="rounded-xl border border-white/[0.06] bg-[#1a1d27] p-5">
                  <h2 className="text-sm font-semibold text-white mb-4">Faculty Profile</h2>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-xs text-white/60 mb-1">Full Name</label>
                      <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-white/60 mb-1">Email Address</label>
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-white/60 mb-1">Department</label>
                      <input
                        type="text"
                        name="department"
                        value={formData.department}
                        onChange={handleChange}
                        className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-white/60 mb-1">Default Course</label>
                      <input
                        type="text"
                        name="defaultCourse"
                        value={formData.defaultCourse}
                        onChange={handleChange}
                        className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                  </div>
                </section>

                {/* Grading & AST Preferences */}
                <section className="rounded-xl border border-white/[0.06] bg-[#1a1d27] p-5">
                  <h2 className="text-sm font-semibold text-white mb-4">AST & Automated Grading Policy</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs text-white/60 mb-1">Default AST Strictness Level</label>
                      <select
                        name="astStrictness"
                        value={formData.astStrictness}
                        onChange={handleChange}
                        className="w-full rounded-lg border border-white/[0.08] bg-[#0f1117] px-3 py-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
                      >
                        <option value="lenient">Lenient (Focus on execution output only)</option>
                        <option value="moderate">Moderate (Standard AST pattern checks)</option>
                        <option value="strict">Strict (Enforce rigid structural loop/function rules)</option>
                      </select>
                    </div>
                  </div>
                </section>

                {/* Notifications */}
                <section className="rounded-xl border border-white/[0.06] bg-[#1a1d27] p-5">
                  <h2 className="text-sm font-semibold text-white mb-4">Notification Preferences</h2>
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        name="emailNotifications"
                        checked={formData.emailNotifications}
                        onChange={handleChange}
                        className="rounded border-white/[0.08] bg-white/[0.03] text-emerald-500 focus:ring-0"
                      />
                      <span className="text-xs text-white/80">Receive batch submission summaries via email</span>
                    </label>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        name="liveMonitoringAlerts"
                        checked={formData.liveMonitoringAlerts}
                        onChange={handleChange}
                        className="rounded border-white/[0.08] bg-white/[0.03] text-emerald-500 focus:ring-0"
                      />
                      <span className="text-xs text-white/80">Enable live monitoring behavioral alerts</span>
                    </label>
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
            </div>
          </main>
        </div>

        <Statusbar
          courseCode={formData.defaultCourse}
          courseName="Faculty Settings"
          studentName={formData.name}
        />
      </div>
    </div>
  );
}