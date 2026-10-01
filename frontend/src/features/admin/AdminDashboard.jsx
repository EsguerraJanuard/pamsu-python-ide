import { useState, useEffect } from "react";
import { useAuth } from "../auth/AuthContext";
import api from "../../services/api";

export default function AdminDashboard() {
  const { logout } = useAuth();
  const [activeTab, setActiveTab] = useState("overview");
  const [stats, setStats] = useState({ total_instructors: 0, total_students: 0, total_classrooms: 0 });
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);

  const [form, setForm] = useState({
    email: "",
    first_name: "",
    last_name: "",
    password: "",
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, usersRes, logsRes] = await Promise.all([
        api.get("/admin/stats"),
        api.get("/admin/users"),
        api.get("/admin/audit-logs")
      ]);
      setStats(statsRes.data || statsRes);
      setUsers(usersRes.data || usersRes);
      setAuditLogs(logsRes.data || logsRes);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateFaculty = async (e) => {
    e.preventDefault();
    setIsLoading(true); setError(null); setSuccess(null);
    try {
      await api.post("/admin/instructors", form);
      setForm({ email: "", first_name: "", last_name: "", password: "" });
      setSuccess("Faculty account created successfully!");
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create instructor");
    } finally {
      setIsLoading(false);
    }
  };

  const handleBulkUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;
    setIsLoading(true); setError(null); setSuccess(null);
    const formData = new FormData();
    formData.append("file", uploadFile);
    try {
      const res = await api.post("/admin/students/bulk-register/file", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      const data = res.data || res;
      setSuccess(`Successfully pre-registered ${data.registered} students.`);
      setUploadFile(null);
      fetchData();
    } catch (err) {
      setError("Failed to upload student masterlist.");
    } finally {
      setIsLoading(false);
    }
  };

  const instructors = users.filter((u) => u.role === "instructor");
  const students = users.filter((u) => u.role === "student");

  return (
    <div className="min-h-screen bg-bg-base text-text-main">
      {/* Header */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-border-subtle bg-bg-glass px-8 py-4 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-psu-maroon text-white font-black shadow-lg shadow-psu-maroon/20">
            MIS
          </div>
          <div>
            <h1 className="text-xl font-black text-text-main">System Administration</h1>
            <p className="text-xs font-medium text-text-muted uppercase tracking-wider">Super Admin Dashboard</p>
          </div>
        </div>
        <button onClick={logout} className="rounded-xl border border-border-subtle bg-bg-glass px-4 py-2 text-sm font-bold text-text-muted transition-all hover:bg-bg-glass-hover hover:text-text-main">
          Sign Out
        </button>
      </header>

      <div className="flex">
        {/* Sidebar Navigation */}
        <aside className="w-64 border-r border-border-subtle min-h-[calc(100vh-73px)] p-6 space-y-2">
          <NavButton active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} label="System Overview" icon="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          <NavButton active={activeTab === 'faculty'} onClick={() => setActiveTab('faculty')} label="Faculty Management" icon="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          <NavButton active={activeTab === 'students'} onClick={() => setActiveTab('students')} label="Student Masterlist" icon="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          <NavButton active={activeTab === 'audit'} onClick={() => setActiveTab('audit')} label="Global Audit Trail" icon="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          {error && <div className="mb-6 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-text-rose">{error}</div>}
          {success && <div className="mb-6 rounded-xl border border-green-500/20 bg-green-500/10 p-4 text-sm text-emerald-500">{success}</div>}

          {/* OVERVIEW TAB */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-black">High-Level System Overview</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <StatCard title="Total CS Instructors" value={stats.total_instructors} icon="?????" />
                <StatCard title="Total Registered Students" value={stats.total_students} icon="??" />
                <StatCard title="Total Active Classrooms" value={stats.total_classrooms} icon="??" />
              </div>
            </div>
          )}

          {/* FACULTY TAB */}
          {activeTab === 'faculty' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl lg:col-span-1 h-fit shadow-sm">
                <h3 className="text-lg font-bold mb-4">Provision Faculty</h3>
                <form onSubmit={handleCreateFaculty} className="space-y-4">
                  <Input label="Official PSU Email" type="email" value={form.email} onChange={v => setForm({...form, email: v})} />
                  <div className="grid grid-cols-2 gap-3">
                    <Input label="First Name" value={form.first_name} onChange={v => setForm({...form, first_name: v})} />
                    <Input label="Last Name" value={form.last_name} onChange={v => setForm({...form, last_name: v})} />
                  </div>
                  <Input label="Initial Password" type="text" value={form.password} onChange={v => setForm({...form, password: v})} />
                  <button disabled={isLoading} type="submit" className="w-full mt-2 rounded-xl bg-psu-maroon py-3 text-sm font-bold text-white shadow-lg shadow-psu-maroon/20 hover:-translate-y-0.5 hover:shadow-psu-maroon/40 transition-all disabled:opacity-50">
                    Create Faculty Account
                  </button>
                </form>
              </div>

              <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl lg:col-span-2 shadow-sm">
                <h3 className="text-lg font-bold mb-4">CS Department Faculty</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="text-xs text-text-muted uppercase bg-bg-base">
                      <tr>
                        <th className="px-4 py-3 rounded-tl-lg">Name</th>
                        <th className="px-4 py-3">Email</th>
                        <th className="px-4 py-3 rounded-tr-lg">Role</th>
                      </tr>
                    </thead>
                    <tbody>
                      {instructors.map((inst) => (
                        <tr key={inst.user_id} className="border-b border-border-subtle hover:bg-bg-base/50">
                          <td className="px-4 py-3 font-medium">{inst.first_name} {inst.last_name}</td>
                          <td className="px-4 py-3 text-text-muted">{inst.email}</td>
                          <td className="px-4 py-3"><span className="px-2.5 py-1 bg-psu-maroon/10 text-psu-maroon font-bold rounded-full text-xs">Instructor</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* STUDENTS TAB */}
          {activeTab === 'students' && (
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
              <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl lg:col-span-1 h-fit shadow-sm">
                <h3 className="text-lg font-bold mb-4">Pre-Register Masterlist</h3>
                <p className="text-xs text-text-muted mb-4">Upload an Excel or CSV file containing student emails to auto-provision their accounts before classes start.</p>
                <form onSubmit={handleBulkUpload}>
                  <input type="file" accept=".csv, .xlsx" onChange={(e) => setUploadFile(e.target.files[0])} className="w-full mb-4 text-sm text-text-muted file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-bold file:bg-psu-maroon/10 file:text-psu-maroon hover:file:bg-psu-maroon/20" />
                  <button disabled={isLoading || !uploadFile} type="submit" className="w-full rounded-xl border border-psu-maroon/50 bg-psu-maroon/10 py-3 text-sm font-bold text-psu-maroon hover:bg-psu-maroon/20 transition-all disabled:opacity-50">
                    Upload Masterlist
                  </button>
                </form>
              </div>

              <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl lg:col-span-3 shadow-sm">
                <h3 className="text-lg font-bold mb-4">Student Masterlist</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="text-xs text-text-muted uppercase bg-bg-base">
                      <tr>
                        <th className="px-4 py-3 rounded-tl-lg">Name</th>
                        <th className="px-4 py-3">PSU Email</th>
                        <th className="px-4 py-3">School ID</th>
                        <th className="px-4 py-3 rounded-tr-lg">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {students.map((stu) => (
                        <tr key={stu.user_id} className="border-b border-border-subtle hover:bg-bg-base/50">
                          <td className="px-4 py-3 font-medium">{stu.first_name} {stu.last_name}</td>
                          <td className="px-4 py-3 text-text-muted">{stu.email}</td>
                          <td className="px-4 py-3 font-mono text-xs">{stu.school_id || 'N/A'}</td>
                          <td className="px-4 py-3"><span className="px-2 py-1 bg-green-500/10 text-emerald-500 font-bold rounded text-xs">Active</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* AUDIT LOGS TAB */}
          {activeTab === 'audit' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-black">Global Security & Audit Trail</h2>
              <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl shadow-sm">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="text-xs text-text-muted uppercase bg-bg-base">
                      <tr>
                        <th className="px-4 py-3 rounded-tl-lg">Timestamp</th>
                        <th className="px-4 py-3">Actor</th>
                        <th className="px-4 py-3">Action</th>
                        <th className="px-4 py-3">Resource</th>
                        <th className="px-4 py-3 rounded-tr-lg">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditLogs.map((log) => (
                        <tr key={log.log_id} className="border-b border-border-subtle hover:bg-bg-base/50">
                          <td className="px-4 py-3 text-text-muted whitespace-nowrap">{new Date(log.occurred_at).toLocaleString()}</td>
                          <td className="px-4 py-3">
                            <div className="font-medium">{log.actor_name}</div>
                            <div className="text-[10px] text-text-muted uppercase">{log.actor_role}</div>
                          </td>
                          <td className="px-4 py-3 font-medium text-psu-maroon dark:text-psu-gold">{log.action_type}</td>
                          <td className="px-4 py-3 text-text-muted">{log.resource_type}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 font-bold rounded text-[10px] uppercase tracking-wider ${log.status === 'success' ? 'bg-green-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}`}>
                              {log.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function NavButton({ active, onClick, label, icon }) {
  return (
    <button onClick={onClick} className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-bold transition-all ${active ? 'bg-psu-maroon text-white shadow-md' : 'text-text-muted hover:bg-bg-glass-hover hover:text-text-main'}`}>
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d={icon} /></svg>
      {label}
    </button>
  );
}

function StatCard({ title, value, icon }) {
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-border-subtle bg-bg-glass p-6 shadow-sm">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-bg-base border border-border-strong text-2xl shadow-inner">
        {icon}
      </div>
      <div>
        <p className="text-xs font-bold text-text-muted uppercase tracking-wider">{title}</p>
        <p className="text-3xl font-black text-text-main mt-1">{value}</p>
      </div>
    </div>
  );
}

function Input({ label, ...props }) {
  return (
    <div>
      <label className="mb-1.5 block text-[10px] font-bold text-text-muted uppercase tracking-wider">{label}</label>
      <input required className="w-full rounded-xl border border-border-strong bg-bg-base px-3 py-2.5 text-sm outline-none transition-colors focus:border-psu-maroon focus:shadow-[0_0_10px_rgba(128,0,0,0.1)]" {...props} />
    </div>
  );
}
