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
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white select-none">
      <InstructorSidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="dashboard-page min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
            <style>
              {`
                @keyframes dashboardFadeUp {
                  from { opacity: 0; transform: translateY(10px); }
                  to { opacity: 1; transform: translateY(0); }
                }
                .dashboard-page {
                  animation: dashboardFadeUp 450ms cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
                }
                @media (prefers-reduced-motion: reduce) {
                  .dashboard-page, .dashboard-card { animation: none !important; }
                }
              `}
            </style>
            <div className="mx-auto max-w-6xl dashboard-page">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <p className="mb-1 font-mono text-xs text-emerald-400">FACULTY MANAGEMENT</p>
            <h1 className="text-2xl font-bold">Instructor Settings</h1>
            <p className="mt-1 text-sm text-white/40">
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

          <section className="rounded-xl border border-white/[0.06] bg-[#1a1d27] p-5">
            <h2 className="text-sm font-semibold text-white mb-4">AST & Automated Grading Policy</h2>
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
      </div>
    </div>
  );
}