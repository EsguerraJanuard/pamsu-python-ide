import { useState, useEffect } from "react";
import { useAuth } from "../auth/AuthContext";
import api from "../../services/api";

export default function AdminDashboard() {
  const { logout } = useAuth();
  const [activeTab, setActiveTab] = useState("overview");
  const [stats, setStats] = useState({ total_instructors: 0, total_students: 0, total_classrooms: 0 });
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [settings, setSettings] = useState({ maintenance_mode: false, default_ast_strictness: "moderate", registration_enabled: false });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);

  const [searchStudent, setSearchStudent] = useState("");
  const [searchAudit, setSearchAudit] = useState("");

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
      const [statsRes, usersRes, logsRes, settingsRes] = await Promise.all([
        api.get("/admin/stats"),
        api.get("/admin/users"),
        api.get("/admin/audit-logs"),
        api.get("/admin/settings")
      ]);
      setStats(statsRes.data || statsRes);
      setUsers(usersRes.data || usersRes);
      setAuditLogs(logsRes.data || logsRes);
      setSettings(settingsRes.data || settingsRes);
    } catch (err) {
      console.error(err);
    }
  };

  const showMsg = (msg, isError = false) => {
    if (isError) setError(msg);
    else setSuccess(msg);
    setTimeout(() => { setError(null); setSuccess(null); }, 3000);
  };

  const handleCreateFaculty = async (e) => {
    e.preventDefault();
    setIsLoading(true); 
    try {
      await api.post("/admin/instructors", form);
      setForm({ email: "", first_name: "", last_name: "", password: "" });
      showMsg("Faculty account created successfully!");
      fetchData();
    } catch (err) {
      showMsg(err.response?.data?.detail || "Failed to create instructor", true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBulkUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;
    setIsLoading(true); 
    const formData = new FormData();
    formData.append("file", uploadFile);
    try {
      const res = await api.post("/admin/students/bulk-register/file", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      const data = res.data || res;
      showMsg(`Successfully pre-registered ${data.registered} students.`);
      setUploadFile(null);
      fetchData();
    } catch (err) {
      showMsg("Failed to upload student masterlist.", true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleStatus = async (userId) => {
    try {
      await api.patch(`/admin/users/${userId}/status`);
      fetchData();
    } catch (e) {
      showMsg("Failed to toggle status", true);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm("Are you sure you want to permanently delete this user?")) return;
    try {
      await api.delete(`/admin/users/${userId}`);
      showMsg("User deleted");
      fetchData();
    } catch (e) {
      showMsg("Failed to delete user", true);
    }
  };

  const handleResetPassword = async (userId) => {
    const newPwd = prompt("Enter new password for this user (min 8 chars):");
    if (!newPwd || newPwd.length < 8) return alert("Password must be at least 8 characters");
    try {
      await api.patch(`/admin/users/${userId}/password`, { new_password: newPwd });
      showMsg("Password reset successfully");
    } catch (e) {
      showMsg("Failed to reset password", true);
    }
  };

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    try {
      await api.patch("/admin/settings", settings);
      showMsg("Global settings saved");
    } catch (e) {
      showMsg("Failed to save settings", true);
    }
  };

  const exportCSV = () => {
    const headers = ["ID", "First Name", "Last Name", "Email", "School ID", "Role", "Active"];
    const rows = users.map(u => [u.user_id, u.first_name, u.last_name, u.email, u.school_id, u.role, u.is_active]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "pamsu_users_export.csv");
    document.body.appendChild(link);
    link.click();
  };

  const instructors = users.filter((u) => u.role === "instructor");
  const students = users.filter((u) => u.role === "student" && (
    u.email.toLowerCase().includes(searchStudent.toLowerCase()) || 
    u.first_name.toLowerCase().includes(searchStudent.toLowerCase()) || 
    u.last_name.toLowerCase().includes(searchStudent.toLowerCase())
  ));
  const filteredLogs = auditLogs.filter(log => 
    log.actor_name.toLowerCase().includes(searchAudit.toLowerCase()) ||
    log.action_type.toLowerCase().includes(searchAudit.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-bg-base text-text-main">
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
        <aside className="w-64 border-r border-border-subtle min-h-[calc(100vh-73px)] p-6 space-y-2">
          <NavButton active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} label="System Overview" icon="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          <NavButton active={activeTab === 'faculty'} onClick={() => setActiveTab('faculty')} label="Faculty Management" icon="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          <NavButton active={activeTab === 'students'} onClick={() => setActiveTab('students')} label="Student Masterlist" icon="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          <NavButton active={activeTab === 'audit'} onClick={() => setActiveTab('audit')} label="Global Audit Trail" icon="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          <NavButton active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} label="System Settings" icon="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        </aside>

        <main className="flex-1 p-8">
          <div className="h-14">
            {error && <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm font-medium text-red-500 shadow-sm">{error}</div>}
            {success && <div className="rounded-xl border border-green-500/20 bg-green-500/10 p-3 text-sm font-medium text-emerald-500 shadow-sm">{success}</div>}
          </div>

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

          {activeTab === 'faculty' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl lg:col-span-1 h-fit shadow-sm">
                <h3 className="text-lg font-bold mb-4">Provision Faculty</h3>
                <form onSubmit={handleCreateFaculty} className="space-y-4">
                  <Input label="Official PSU Email" type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} />
                  <div className="grid grid-cols-2 gap-3">
                    <Input label="First Name" value={form.first_name} onChange={e => setForm({...form, first_name: e.target.value})} />
                    <Input label="Last Name" value={form.last_name} onChange={e => setForm({...form, last_name: e.target.value})} />
                  </div>
                  <Input label="Initial Password" type="text" value={form.password} onChange={e => setForm({...form, password: e.target.value})} />
                  <button disabled={isLoading} type="submit" className="w-full mt-2 rounded-xl bg-psu-maroon py-3 text-sm font-bold text-white shadow-lg shadow-psu-maroon/20 hover:-translate-y-0.5 hover:shadow-psu-maroon/40 transition-all disabled:opacity-50">
                    Create Faculty Account
                  </button>
                </form>
              </div>

              <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl lg:col-span-2 shadow-sm">
                <h3 className="text-lg font-bold mb-4">CS Department Faculty</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="text-xs text-text-muted uppercase bg-bg-base border-b border-border-subtle">
                      <tr>
                        <th className="px-4 py-3">Name</th>
                        <th className="px-4 py-3">Email</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {instructors.map((inst) => (
                        <tr key={inst.user_id} className="border-b border-border-subtle hover:bg-bg-base/50">
                          <td className="px-4 py-3 font-medium">{inst.first_name} {inst.last_name}</td>
                          <td className="px-4 py-3 text-text-muted">{inst.email}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2.5 py-1 text-xs font-bold rounded-full ${inst.is_active ? 'bg-green-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}`}>
                              {inst.is_active ? 'Active' : 'Disabled'}
                            </span>
                          </td>
                          <td className="px-4 py-3 flex gap-2 justify-end">
                            <ActionBtn onClick={() => handleResetPassword(inst.user_id)} text="Reset Pwd" />
                            <ActionBtn onClick={() => handleToggleStatus(inst.user_id)} text={inst.is_active ? "Disable" : "Enable"} />
                            <ActionBtn onClick={() => handleDeleteUser(inst.user_id)} text="Delete" danger />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'students' && (
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
              <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl lg:col-span-1 h-fit shadow-sm space-y-6">
                <div>
                  <h3 className="text-lg font-bold mb-2">Pre-Register Masterlist</h3>
                  <p className="text-xs text-text-muted mb-4">Upload an Excel/CSV file with student emails to auto-provision accounts.</p>
                  <form onSubmit={handleBulkUpload}>
                    <input type="file" accept=".csv, .xlsx" onChange={(e) => setUploadFile(e.target.files[0])} className="w-full mb-3 text-sm text-text-muted file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-bold file:bg-psu-maroon/10 file:text-psu-maroon hover:file:bg-psu-maroon/20" />
                    <button disabled={isLoading || !uploadFile} type="submit" className="w-full rounded-xl border border-psu-maroon/50 bg-psu-maroon/10 py-2 text-sm font-bold text-psu-maroon hover:bg-psu-maroon/20 transition-all disabled:opacity-50">
                      Upload Masterlist
                    </button>
                  </form>
                </div>
                <div className="border-t border-border-subtle pt-6">
                  <h3 className="text-lg font-bold mb-2">Export Data</h3>
                  <p className="text-xs text-text-muted mb-4">Download the full user masterlist to CSV.</p>
                  <button onClick={exportCSV} className="w-full rounded-xl border border-border-strong bg-bg-base py-2 text-sm font-bold hover:bg-bg-glass-hover transition-all">
                    Download CSV
                  </button>
                </div>
              </div>

              <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl lg:col-span-3 shadow-sm flex flex-col h-[calc(100vh-180px)]">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-bold">Student Masterlist</h3>
                  <input type="text" placeholder="Search students..." value={searchStudent} onChange={e => setSearchStudent(e.target.value)} className="rounded-lg border border-border-strong bg-bg-base px-3 py-1.5 text-sm outline-none focus:border-psu-maroon" />
                </div>
                <div className="overflow-y-auto flex-1 border border-border-subtle rounded-lg">
                  <table className="w-full text-left text-sm relative">
                    <thead className="sticky top-0 text-xs text-text-muted uppercase bg-bg-base border-b border-border-subtle z-10 shadow-sm">
                      <tr>
                        <th className="px-4 py-3">Name</th>
                        <th className="px-4 py-3">PSU Email</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {students.map((stu) => (
                        <tr key={stu.user_id} className="border-b border-border-subtle hover:bg-bg-base/50">
                          <td className="px-4 py-3 font-medium">{stu.first_name} {stu.last_name}</td>
                          <td className="px-4 py-3 text-text-muted">{stu.email}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 font-bold rounded text-xs ${stu.is_active ? 'bg-green-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}`}>
                              {stu.is_active ? 'Active' : 'Disabled'}
                            </span>
                          </td>
                          <td className="px-4 py-3 flex gap-2 justify-end">
                            <ActionBtn onClick={() => handleResetPassword(stu.user_id)} text="Reset" />
                            <ActionBtn onClick={() => handleToggleStatus(stu.user_id)} text={stu.is_active ? "Disable" : "Enable"} />
                            <ActionBtn onClick={() => handleDeleteUser(stu.user_id)} text="Delete" danger />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'audit' && (
            <div className="space-y-4 h-[calc(100vh-180px)] flex flex-col">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-black">Global Security & Audit Trail</h2>
                <input type="text" placeholder="Search logs (actor, action)..." value={searchAudit} onChange={e => setSearchAudit(e.target.value)} className="rounded-lg border border-border-strong bg-bg-base px-3 py-1.5 text-sm outline-none focus:border-psu-maroon w-64" />
              </div>
              <div className="bg-bg-glass border border-border-subtle rounded-2xl shadow-sm flex-1 overflow-hidden flex flex-col">
                <div className="overflow-y-auto flex-1">
                  <table className="w-full text-left text-sm relative">
                    <thead className="sticky top-0 text-xs text-text-muted uppercase bg-bg-base border-b border-border-subtle shadow-sm z-10">
                      <tr>
                        <th className="px-4 py-3">Timestamp</th>
                        <th className="px-4 py-3">Actor</th>
                        <th className="px-4 py-3">Action</th>
                        <th className="px-4 py-3">Resource</th>
                        <th className="px-4 py-3 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredLogs.map((log) => (
                        <tr key={log.log_id} className="border-b border-border-subtle hover:bg-bg-base/50">
                          <td className="px-4 py-3 text-text-muted whitespace-nowrap">{new Date(log.occurred_at).toLocaleString()}</td>
                          <td className="px-4 py-3">
                            <div className="font-medium">{log.actor_name}</div>
                            <div className="text-[10px] text-text-muted uppercase">{log.actor_role}</div>
                          </td>
                          <td className="px-4 py-3 font-medium text-psu-maroon dark:text-psu-gold">{log.action_type}</td>
                          <td className="px-4 py-3 text-text-muted">{log.resource_type}</td>
                          <td className="px-4 py-3 text-right">
                            <span className={`px-2 py-1 font-bold rounded text-[10px] uppercase tracking-wider ${log.status === 'success' ? 'bg-green-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}`}>
                              {log.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                      {filteredLogs.length === 0 && (
                        <tr>
                          <td colSpan="5" className="p-8 text-center text-text-muted">No logs found matching your search.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-black">Global Platform Settings</h2>
              <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl shadow-sm max-w-2xl">
                <form onSubmit={handleSaveSettings} className="space-y-6">
                  
                  <div className="flex items-center justify-between border-b border-border-subtle pb-4">
                    <div>
                      <h4 className="font-bold">Maintenance Mode</h4>
                      <p className="text-xs text-text-muted mt-1">Suspend all student logins and task execution. Only MIS and Instructors can access the platform.</p>
                    </div>
                    <label className="relative inline-flex cursor-pointer items-center">
                      <input type="checkbox" className="peer sr-only" checked={settings.maintenance_mode} onChange={e => setSettings({...settings, maintenance_mode: e.target.checked})} />
                      <div className="h-6 w-11 rounded-full bg-border-strong peer-checked:bg-red-500 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all peer-checked:after:translate-x-full"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between border-b border-border-subtle pb-4">
                    <div>
                      <h4 className="font-bold">Allow Public Registration</h4>
                      <p className="text-xs text-text-muted mt-1">Allow students to sign up manually without MIS pre-registration.</p>
                    </div>
                    <label className="relative inline-flex cursor-pointer items-center">
                      <input type="checkbox" className="peer sr-only" checked={settings.registration_enabled} onChange={e => setSettings({...settings, registration_enabled: e.target.checked})} />
                      <div className="h-6 w-11 rounded-full bg-border-strong peer-checked:bg-psu-maroon after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all peer-checked:after:translate-x-full"></div>
                    </label>
                  </div>

                  <div className="pb-4">
                    <h4 className="font-bold mb-2">Default AST Strictness</h4>
                    <p className="text-xs text-text-muted mb-3">Global strictness level for structural code feedback.</p>
                    <select value={settings.default_ast_strictness} onChange={e => setSettings({...settings, default_ast_strictness: e.target.value})} className="w-full rounded-lg border border-border-strong bg-bg-base px-3 py-2 text-sm outline-none focus:border-psu-maroon">
                      <option value="lenient">Lenient (Allows standard variations)</option>
                      <option value="moderate">Moderate (Standard university policy)</option>
                      <option value="strict">Strict (Requires exact structural match)</option>
                    </select>
                  </div>

                  <div className="pt-4">
                    <button type="submit" className="rounded-xl bg-psu-maroon px-6 py-2.5 text-sm font-bold text-white shadow-md hover:-translate-y-0.5 transition-all">
                      Save Global Settings
                    </button>
                  </div>

                </form>
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
      <input required className="w-full rounded-xl border border-border-strong bg-bg-base px-3 py-2.5 text-sm outline-none transition-colors focus:border-psu-maroon" {...props} />
    </div>
  );
}

function ActionBtn({ onClick, text, danger }) {
  return (
    <button onClick={onClick} className={`rounded border px-2 py-1 text-[10px] font-bold uppercase tracking-wider transition-colors ${danger ? 'border-red-500/20 text-red-500 hover:bg-red-500/10' : 'border-border-strong text-text-muted hover:text-text-main hover:border-border-subtle'}`}>
      {text}
    </button>
  );
}
