import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../auth/AuthContext';

export default function AdminDashboard() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState({ total_instructors: 0, total_students: 0, total_classrooms: 0 });
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [settings, setSettings] = useState({
    maintenance_mode: false,
    default_ast_strictness: 'moderate'
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Data States
  const [form, setForm] = useState({ email: '', first_name: '', last_name: '', password: '' });
  const [masterlist, setMasterlist] = useState(null);
  const [searchStudent, setSearchStudent] = useState('');
  const [searchAudit, setSearchAudit] = useState('');
  const [isDark, setIsDark] = useState(() => document.documentElement.classList.contains('dark'));

  // Modal State
  const [modalConfig, setModalConfig] = useState(null);

  const fetchData = async () => {
    try {
      const [statsRes, usersRes, logsRes, settingsRes] = await Promise.all([
        api.get("/admin/stats").catch(() => ({ data: { total_instructors: 0, total_students: 0, total_classrooms: 0 }})),
        api.get("/admin/users").catch(() => ({ data: [] })),
        api.get("/admin/audit-logs").catch(() => ({ data: [] })),
        api.get("/admin/settings").catch(() => ({ data: { maintenance_mode: false, default_ast_strictness: 'moderate' } }))
      ]);
      setStats(statsRes.data || statsRes);
      setUsers(usersRes.data || usersRes);
      setAuditLogs(logsRes.data || logsRes);
      setSettings(settingsRes.data || settingsRes);
    } catch (err) {
      console.error("Dashboard error:", err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const toggleTheme = () => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.remove('dark');
      localStorage.setItem('theme', 'light');
      setIsDark(false);
    } else {
      root.classList.add('dark');
      localStorage.setItem('theme', 'dark');
      setIsDark(true);
    }
  };

  const showMessage = (msg, isError = false) => {
    isError ? setError(msg) : setSuccess(msg);
    setTimeout(() => { setError(null); setSuccess(null); }, 5000);
  };

  const handleCreateFaculty = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await api.post("/admin/instructors", form);
      showMessage(`Faculty account for ${form.email} provisioned successfully!`);
      setForm({ email: '', first_name: '', last_name: '', password: '' });
      await fetchData();
    } catch (err) {
      showMessage(err.response?.data?.detail || err.message, true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    if (!e.target.files[0]) return;
    const file = e.target.files[0];
    setMasterlist(file);
    const formData = new FormData();
    formData.append("file", file);
    setIsLoading(true);
    try {
      const res = await api.post("/admin/students/bulk-register/file", formData);
      showMessage(`Successfully provisioned ${res.data?.registered || res.registered} students!`);
      await fetchData();
    } catch (err) {
      showMessage(err.response?.data?.detail || err.message, true);
    } finally {
      setIsLoading(false);
    }
  };

  const exportMasterlist = () => {
    const headers = ["User ID", "First Name", "Last Name", "Email", "School ID", "Role", "Active"];
    const rows = users.map(u => [u.user_id, u.first_name, u.last_name, u.email, u.school_id, u.role, u.is_active]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "pamsu_users_export.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    try {
      await api.patch("/admin/settings", settings);
      showMessage("Global settings successfully saved.");
    } catch (err) {
      showMessage(err.response?.data?.detail || err.message, true);
    }
  };

  const handleAction = (user, actionType) => {
    if (actionType === 'status') {
      setModalConfig({
        title: user.is_active ? 'Suspend Account' : 'Activate Account',
        message: `Are you sure you want to ${user.is_active ? 'suspend' : 'activate'} ${user.first_name} ${user.last_name}? ${user.is_active ? 'They will not be able to log in.' : 'They will regain access.'}`,
        danger: user.is_active,
        onConfirm: async () => {
          try {
            await api.patch(`/admin/users/${user.user_id}/status`);
            showMessage(`Status updated for ${user.email}`);
            await fetchData();
          } catch (err) {
            showMessage(err.response?.data?.detail || err.message, true);
          }
          setModalConfig(null);
        }
      });
    } else if (actionType === 'reset') {
      setModalConfig({
        title: 'Reset Password',
        message: `Are you sure you want to reset the password for ${user.first_name} ${user.last_name} to the default "Pass@123"?`,
        danger: false,
        onConfirm: async () => {
          try {
            await api.patch(`/admin/users/${user.user_id}/password`, { new_password: 'Pass@123' });
            showMessage(`Password reset to Pass@123 for ${user.email}`);
          } catch (err) {
            showMessage(err.response?.data?.detail || err.message, true);
          }
          setModalConfig(null);
        }
      });
    }
  };

  const instructors = users.filter(u => u.role === 'instructor');
  const students = users.filter(u => u.role === 'student');
  
  const filteredStudents = students.filter(stu => 
    stu.email.toLowerCase().includes(searchStudent.toLowerCase()) || 
    stu.first_name.toLowerCase().includes(searchStudent.toLowerCase()) || 
    stu.last_name.toLowerCase().includes(searchStudent.toLowerCase())
  );

  const filteredLogs = auditLogs.filter(log => 
    (log.action_type || '').toLowerCase().includes(searchAudit.toLowerCase()) || 
    (log.actor_name || '').toLowerCase().includes(searchAudit.toLowerCase()) ||
    (log.resource_type || '').toLowerCase().includes(searchAudit.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-bg-base text-text-main font-sans selection:bg-psu-maroon selection:text-white">
      {modalConfig && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
          <div className="w-full max-w-md rounded-3xl bg-bg-base border border-border-strong shadow-2xl p-8 animate-fade-in-up">
            <h3 className="text-2xl font-black mb-2 tracking-tight">{modalConfig.title}</h3>
            <p className="text-sm text-text-muted mb-8">{modalConfig.message}</p>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setModalConfig(null)} className="px-6 py-2.5 rounded-xl text-sm font-bold border border-border-strong text-text-muted hover:text-text-main hover:bg-bg-glass transition-colors">
                Cancel
              </button>
              <button onClick={modalConfig.onConfirm} className={`px-6 py-2.5 rounded-xl text-sm font-bold text-white shadow-md transition-all hover:scale-105 ${modalConfig.danger ? 'bg-red-500 shadow-red-500/20' : 'bg-psu-maroon shadow-psu-maroon/20'}`}>
                Confirm Action
              </button>
            </div>
          </div>
        </div>
      )}

      <header className="sticky top-0 z-50 flex h-16 sm:h-20 shrink-0 items-center justify-between border-b border-border-subtle bg-bg-glass px-4 sm:px-8 shadow-sm backdrop-blur-md">
        <div className="flex items-center gap-4">
          <img src="/school_logo.png" alt="PSU Logo" className="h-10 w-10 sm:h-12 sm:w-12 drop-shadow-sm" />
          <div className="hidden sm:block">
            <h1 className="text-xl font-black text-text-main tracking-tight">Pampanga State University</h1>
            <p className="text-xs font-bold text-psu-maroon uppercase tracking-widest">MIS Administration</p>
          </div>
        </div>
        <button onClick={logout} className="rounded-xl border border-border-subtle bg-bg-base px-5 py-2.5 text-sm font-bold shadow-sm transition-all hover:bg-bg-glass-hover hover:border-border-strong hover:shadow-md">
          Sign Out
        </button>
      </header>

      <div className="flex min-h-[calc(100vh-80px)]">
        <aside className="w-64 shrink-0 border-r border-border-subtle p-6 space-y-2 bg-bg-base hidden lg:block">
          <NavButton active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} label="System Overview" icon="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          <NavButton active={activeTab === 'faculty'} onClick={() => setActiveTab('faculty')} label="Faculty Management" icon="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          <NavButton active={activeTab === 'students'} onClick={() => setActiveTab('students')} label="Student Database" icon="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          <NavButton active={activeTab === 'audit'} onClick={() => setActiveTab('audit')} label="Global Audit Trail" icon="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          <NavButton active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} label="System Settings" icon="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        </aside>

        <main className="flex-1 min-w-0 p-4 lg:p-10 overflow-x-hidden">
          <div className="w-full max-w-[1600px] lg:px-8 mx-auto">
            
            <div className="mb-4 empty:hidden">
              {error && <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm font-medium text-red-500 shadow-sm flex items-center gap-2 mb-4"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>{error}</div>}
              {success && <div className="rounded-xl border border-green-500/20 bg-green-500/10 p-4 text-sm font-medium text-emerald-500 shadow-sm flex items-center gap-2 mb-4"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>{success}</div>}
            </div>

            {activeTab === 'overview' && (
              <div className="space-y-6 animate-fade-in">
                <header className="border-b border-border-subtle pb-6">
                  <p className="mb-1 font-mono text-xs text-text-brand tracking-widest">METRICS</p>
                  <h1 className="text-3xl font-black text-text-main tracking-tight">System Overview</h1>
                  <p className="mt-2 text-sm text-text-muted">High-level statistics across the entire Python IDE platform.</p>
                </header>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <StatCard title="Total Instructors" value={stats.total_instructors} colorClass="text-blue-500" icon={<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>} />
                  <StatCard title="Registered Students" value={stats.total_students} colorClass="text-emerald-500" icon={<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>} />
                  <StatCard title="Active Classrooms" value={stats.total_classrooms} colorClass="text-purple-500" icon={<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>} />
                </div>
              </div>
            )}

            {activeTab === 'faculty' && (
              <div className="flex flex-col gap-8 animate-fade-in w-full">
                <header className="border-b border-border-subtle pb-6 w-full">
                  <p className="mb-1 font-mono text-xs text-text-brand tracking-widest">MANAGEMENT</p>
                  <h1 className="text-3xl font-black text-text-main tracking-tight">Faculty Management</h1>
                  <p className="mt-2 text-sm text-text-muted">Provision new instructor accounts and manage existing computer science faculty.</p>
                </header>
                
                <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full max-w-xl shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-psu-maroon to-psu-red"></div>
                  <h3 className="text-lg font-black mb-6 tracking-tight">Provision Faculty</h3>
                  <form onSubmit={handleCreateFaculty} className="space-y-5">
                    <Input label="Official PSU Email" type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} />
                    <div className="grid grid-cols-2 gap-3">
                      <Input label="First Name" value={form.first_name} onChange={e => setForm({...form, first_name: e.target.value})} />
                      <Input label="Last Name" value={form.last_name} onChange={e => setForm({...form, last_name: e.target.value})} />
                    </div>
                    <Input label="Initial Password" type="text" value={form.password} onChange={e => setForm({...form, password: e.target.value})} />
                    <button disabled={isLoading} type="submit" className="w-full mt-2 rounded-xl bg-psu-maroon py-3 text-sm font-bold text-white shadow-lg shadow-psu-maroon/20 hover:scale-[1.02] hover:shadow-psu-maroon/40 transition-all disabled:opacity-50">
                      Create Faculty Account
                    </button>
                  </form>
                </div>

                <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm">
                  <h3 className="text-lg font-black mb-6 tracking-tight">CS Department Faculty</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="text-[11px] font-bold tracking-widest text-text-muted uppercase bg-bg-base border-b border-border-subtle">
                        <tr>
                          <th className="px-4 py-3">Name</th>
                          <th className="px-4 py-3">Email</th>
                          <th className="px-4 py-3">Status</th>
                          <th className="px-4 py-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {instructors.length === 0 && (
                          <tr>
                            <td colSpan="4" className="px-4 py-16 text-center text-text-muted">
                              <div className="flex flex-col items-center justify-center">
                                <svg className="w-10 h-10 mb-3 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                                <p className="font-semibold text-text-main">No faculty members found</p>
                                <p className="text-xs mt-1">Provision an instructor to see them here.</p>
                              </div>
                            </td>
                          </tr>
                        )}
                        {instructors.map((inst) => (
                          <tr key={inst.user_id} className="border-b border-border-subtle hover:bg-bg-base/50 transition-colors">
                            <td className="px-4 py-4 font-bold text-text-main">{inst.first_name} {inst.last_name}</td>
                            <td className="px-4 py-4 text-text-muted">{inst.email}</td>
                            <td className="px-4 py-4">
                              <span className={`px-2.5 py-1 text-[10px] uppercase tracking-widest font-bold rounded-full ${inst.is_active ? 'bg-green-500/10 text-emerald-500 border border-green-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'}`}>
                                {inst.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td className="px-4 py-4 text-right space-x-2">
                              <ActionBtn onClick={() => handleAction(inst, 'reset')} text="Reset" />
                              <ActionBtn onClick={() => handleAction(inst, 'status')} text={inst.is_active ? "Suspend" : "Activate"} danger={inst.is_active} />
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
              <div className="flex flex-col gap-8 animate-fade-in w-full">
                <header className="border-b border-border-subtle pb-6 w-full">
                  <p className="mb-1 font-mono text-xs text-text-brand tracking-widest">PROVISIONING</p>
                  <h1 className="text-3xl font-black text-text-main tracking-tight">Student Masterlist</h1>
                  <p className="mt-2 text-sm text-text-muted">Bulk upload student emails or export the current masterlist.</p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl">
                  <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl shadow-sm relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 to-emerald-400"></div>
                    <h3 className="text-lg font-black mb-6 tracking-tight">Pre-Register Masterlist</h3>
                    <p className="text-sm text-text-muted mb-4">Upload an Excel/CSV file with student emails to auto-provision accounts.</p>
                    
                    <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-border-strong rounded-xl cursor-pointer bg-bg-base hover:bg-bg-glass transition-colors group">
                      <div className="flex flex-col items-center justify-center pt-5 pb-6">
                        <svg className="w-8 h-8 mb-3 text-text-muted group-hover:text-emerald-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                        <p className="mb-2 text-sm text-text-muted"><span className="font-semibold text-text-main group-hover:text-emerald-500 transition-colors">Click to upload</span></p>
                        <p className="text-xs text-text-muted/70">CSV or Excel files only</p>
                      </div>
                      <input type="file" accept=".csv, .xlsx" onChange={handleFileUpload} className="hidden" />
                    </label>
                  </div>
                  
                  <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl shadow-sm flex flex-col justify-between">
                    <div>
                      <h3 className="text-lg font-black mb-4 tracking-tight">Export Data</h3>
                      <p className="text-sm text-text-muted mb-4">Download the full user masterlist to CSV.</p>
                    </div>
                    <button onClick={exportMasterlist} className="w-full rounded-xl bg-bg-base border border-border-strong py-4 text-sm font-bold shadow-sm hover:bg-bg-glass hover:shadow transition-all">
                      Download CSV
                    </button>
                  </div>
                </div>

                <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm mt-4">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-black tracking-tight">Student Database</h3>
                    <div className="relative group w-72">
                      <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted group-focus-within:text-emerald-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                      <input type="text" placeholder="Search students..." value={searchStudent} onChange={(e) => setSearchStudent(e.target.value)} className="w-full pl-9 pr-4 py-2.5 bg-bg-base border border-border-strong rounded-xl text-sm focus:outline-none focus:border-emerald-500 transition-colors shadow-sm" />
                    </div>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="text-[11px] font-bold tracking-widest text-text-muted uppercase bg-bg-base border-b border-border-subtle">
                        <tr>
                          <th className="px-4 py-3">Name</th>
                          <th className="px-4 py-3">PSU Email</th>
                          <th className="px-4 py-3">Status</th>
                          <th className="px-4 py-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredStudents.length === 0 && (
                          <tr>
                            <td colSpan="4" className="px-4 py-16 text-center text-text-muted">
                              <div className="flex flex-col items-center justify-center">
                                <svg className="w-10 h-10 mb-3 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
                                <p className="font-semibold text-text-main">No students found</p>
                                <p className="text-xs mt-1">Upload a masterlist to provision students.</p>
                              </div>
                            </td>
                          </tr>
                        )}
                        {filteredStudents.map((stu) => (
                          <tr key={stu.user_id} className="border-b border-border-subtle hover:bg-bg-base/50 transition-colors">
                            <td className="px-4 py-4 font-bold text-text-main">{stu.first_name} {stu.last_name}</td>
                            <td className="px-4 py-4 text-text-muted">{stu.email}</td>
                            <td className="px-4 py-4">
                              <span className={`px-2.5 py-1 font-bold rounded-full text-[10px] uppercase tracking-widest ${stu.is_active ? 'bg-green-500/10 text-emerald-500 border border-green-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'}`}>
                                {stu.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td className="px-4 py-4 text-right space-x-2">
                              <ActionBtn onClick={() => handleAction(stu, 'reset')} text="Reset" />
                              <ActionBtn onClick={() => handleAction(stu, 'status')} text={stu.is_active ? "Suspend" : "Activate"} danger={stu.is_active} />
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
              <div className="h-full flex flex-col space-y-6 animate-fade-in w-full">
                <header className="border-b border-border-subtle pb-6 flex flex-col md:flex-row md:justify-between md:items-end gap-4">
                  <div>
                    <p className="mb-1 font-mono text-xs text-text-brand tracking-widest">SECURITY</p>
                    <h1 className="text-3xl font-black text-text-main tracking-tight">Global Audit Trail</h1>
                    <p className="mt-2 text-sm text-text-muted">Immutable log of all critical system actions.</p>
                  </div>
                  <div className="w-full md:w-80 relative group">
                    <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted group-focus-within:text-psu-maroon transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                    <input type="text" placeholder="Search logs..." value={searchAudit} onChange={(e) => setSearchAudit(e.target.value)} className="w-full pl-9 pr-4 py-3 bg-bg-glass border border-border-strong rounded-xl text-sm font-medium focus:outline-none focus:border-psu-maroon transition-colors shadow-sm" />
                  </div>
                </header>

                <div className="bg-bg-glass border border-border-subtle rounded-2xl shadow-sm flex-1 overflow-hidden flex flex-col min-h-[600px]">
                  <div className="overflow-x-auto overflow-y-auto flex-1">
                    <table className="w-full text-left text-sm relative">
                      <thead className="sticky top-0 text-[11px] font-bold tracking-widest text-text-muted uppercase bg-bg-base border-b border-border-subtle shadow-sm z-10">
                        <tr>
                          <th className="px-4 py-3">Timestamp</th>
                          <th className="px-4 py-3">Actor</th>
                          <th className="px-4 py-3">Action</th>
                          <th className="px-4 py-3">Resource</th>
                          <th className="px-4 py-3 text-right">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredLogs.length === 0 && (
                          <tr>
                            <td colSpan="5" className="px-4 py-32 text-center text-text-muted">
                              <div className="flex flex-col items-center justify-center">
                                <svg className="w-10 h-10 mb-3 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>
                                <p className="font-semibold text-text-main">No audit logs available</p>
                                <p className="text-xs mt-1">Actions taken on the system will appear here.</p>
                              </div>
                            </td>
                          </tr>
                        )}
                        {filteredLogs.map((log) => (
                          <tr key={log.audit_id || Math.random()} className="border-b border-border-subtle hover:bg-bg-base/50 transition-colors">
                            <td className="px-4 py-4 text-text-muted whitespace-nowrap">{new Date(log.occurred_at).toLocaleString()}</td>
                            <td className="px-4 py-4">
                              <div className="font-bold text-text-main">{log.actor_name || 'System Administrator'}</div>
                              <div className="text-[10px] text-text-muted uppercase tracking-widest mt-0.5">{log.actor_role || 'ADMIN'}</div>
                            </td>
                            <td className="px-4 py-4 font-bold text-psu-maroon dark:text-psu-gold">{log.action_type}</td>
                            <td className="px-4 py-4 text-text-muted">{log.resource_type}</td>
                            <td className="px-4 py-4 text-right">
                              <span className={`px-2 py-1 font-bold rounded text-[10px] uppercase tracking-wider ${log.outcome === 'succeeded' || log.status === 'success' ? 'bg-green-500/10 text-emerald-500 border border-green-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'}`}>
                                {log.outcome || log.status || 'succeeded'}
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

            {activeTab === 'settings' && (
              <div className="space-y-6 animate-fade-in w-full max-w-5xl">
                <header className="border-b border-border-subtle pb-6 mb-6">
                  <p className="mb-1 font-mono text-xs text-text-brand tracking-widest">CONFIGURATION</p>
                  <h1 className="text-3xl font-black text-text-main tracking-tight">System Settings</h1>
                  <p className="mt-2 text-sm text-text-muted">Manage global policies, appearance, and maintenance state.</p>
                </header>
                
                <div className="bg-bg-glass border border-border-subtle p-8 rounded-2xl shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-text-main to-text-muted"></div>
                  <form onSubmit={handleSaveSettings} className="space-y-10">
                    
                    {/* UI Toggle */}
                    <div className="flex items-center justify-between border-b border-border-subtle pb-8">
                      <div className="pr-8">
                        <h4 className="font-black text-lg tracking-tight">Platform Theme</h4>
                        <p className="text-sm text-text-muted mt-1">Toggle dark mode appearance for the dashboard.</p>
                      </div>
                      <label className="relative inline-flex cursor-pointer items-center shrink-0">
                        <input type="checkbox" className="peer sr-only" checked={isDark} onChange={toggleTheme} />
                        <div className="h-8 w-14 rounded-full bg-border-strong peer-checked:bg-text-main after:absolute after:left-[3px] after:top-[3px] after:h-6 after:w-6 after:rounded-full after:bg-white after:transition-all peer-checked:after:translate-x-full shadow-inner"></div>
                      </label>
                    </div>

                    {/* Maintenance Mode */}
                    <div className="flex items-center justify-between border-b border-border-subtle pb-8">
                      <div className="pr-8">
                        <h4 className="font-black text-lg tracking-tight">Maintenance Mode</h4>
                        <p className="text-sm text-text-muted mt-1">Suspend all student logins and task execution. Only MIS and Instructors can access the platform while this is on.</p>
                      </div>
                      <label className="relative inline-flex cursor-pointer items-center shrink-0">
                        <input type="checkbox" className="peer sr-only" checked={settings.maintenance_mode} onChange={e => setSettings({...settings, maintenance_mode: e.target.checked})} />
                        <div className="h-8 w-14 rounded-full bg-border-strong peer-checked:bg-red-500 after:absolute after:left-[3px] after:top-[3px] after:h-6 after:w-6 after:rounded-full after:bg-white after:transition-all peer-checked:after:translate-x-full shadow-inner"></div>
                      </label>
                    </div>

                    <div className="pb-4">
                      <h4 className="font-black text-lg tracking-tight mb-2">Default AST Strictness</h4>
                      <p className="text-sm text-text-muted mb-6">Global strictness level for structural code feedback.</p>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <label className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === 'lenient' ? 'border-emerald-500 bg-emerald-500/5 shadow-sm' : 'border-border-subtle hover:border-border-strong hover:bg-bg-base'}`}>
                          <input type="radio" name="ast_strictness" value="lenient" checked={settings.default_ast_strictness === 'lenient'} onChange={e => setSettings({...settings, default_ast_strictness: e.target.value})} className="hidden" />
                          <div className="flex items-center gap-3 mb-2">
                            <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${settings.default_ast_strictness === 'lenient' ? 'border-emerald-500' : 'border-border-strong'}`}>
                              {settings.default_ast_strictness === 'lenient' && <div className="w-2 h-2 rounded-full bg-emerald-500"></div>}
                            </div>
                            <span className="font-black text-text-main">Lenient</span>
                          </div>
                          <p className="text-xs text-text-muted leading-relaxed">Allows standard variations & formatting differences.</p>
                        </label>

                        <label className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === 'moderate' ? 'border-psu-maroon bg-psu-maroon/5 shadow-sm' : 'border-border-subtle hover:border-border-strong hover:bg-bg-base'}`}>
                          <input type="radio" name="ast_strictness" value="moderate" checked={settings.default_ast_strictness === 'moderate'} onChange={e => setSettings({...settings, default_ast_strictness: e.target.value})} className="hidden" />
                          <div className="flex items-center gap-3 mb-2">
                            <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${settings.default_ast_strictness === 'moderate' ? 'border-psu-maroon' : 'border-border-strong'}`}>
                              {settings.default_ast_strictness === 'moderate' && <div className="w-2 h-2 rounded-full bg-psu-maroon"></div>}
                            </div>
                            <span className="font-black text-text-main">Moderate</span>
                          </div>
                          <p className="text-xs text-text-muted leading-relaxed">Standard university policy with balanced checks.</p>
                        </label>

                        <label className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === 'strict' ? 'border-red-500 bg-red-500/5 shadow-sm' : 'border-border-subtle hover:border-border-strong hover:bg-bg-base'}`}>
                          <input type="radio" name="ast_strictness" value="strict" checked={settings.default_ast_strictness === 'strict'} onChange={e => setSettings({...settings, default_ast_strictness: e.target.value})} className="hidden" />
                          <div className="flex items-center gap-3 mb-2">
                            <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${settings.default_ast_strictness === 'strict' ? 'border-red-500' : 'border-border-strong'}`}>
                              {settings.default_ast_strictness === 'strict' && <div className="w-2 h-2 rounded-full bg-red-500"></div>}
                            </div>
                            <span className="font-black text-text-main">Strict</span>
                          </div>
                          <p className="text-xs text-text-muted leading-relaxed">Requires exact structural AST match for submission.</p>
                        </label>
                      </div>
                    </div>

                    <div className="pt-4 border-t border-border-subtle">
                      <button type="submit" className="rounded-2xl bg-psu-maroon px-8 py-3.5 text-base font-bold text-white shadow-lg shadow-psu-maroon/20 hover:scale-[1.02] hover:shadow-psu-maroon/40 transition-all">
                        Save Global Settings
                      </button>
                    </div>

                  </form>
                </div>
              </div>
            )}

          </div>
        </main>
      </div>
    </div>
  );
}

function NavButton({ active, onClick, label, icon }) {
  return (
    <button onClick={onClick} className={`flex w-full items-center gap-4 rounded-xl px-4 py-3.5 text-sm font-bold transition-all ${active ? 'bg-psu-maroon text-white shadow-md shadow-psu-maroon/20 scale-[1.02]' : 'text-text-muted hover:bg-bg-glass-hover hover:text-text-main hover:scale-[1.01]'}`}>
      <svg className="h-5 w-5 opacity-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d={icon} /></svg>
      {label}
    </button>
  );
}

function StatCard({ title, value, icon, colorClass = "text-text-brand" }) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-border-subtle bg-bg-glass p-6 shadow-sm hover:shadow-md transition-all hover:-translate-y-1 cursor-default">
      <div className={`absolute -right-6 -top-6 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity scale-150 ${colorClass}`}>
        {icon}
      </div>
      <div className="flex items-center gap-4 mb-4 relative z-10">
        <div className={`flex h-12 w-12 items-center justify-center rounded-xl bg-bg-base border border-border-subtle shadow-sm ${colorClass}`}>
          {icon}
        </div>
        <h3 className="text-[11px] font-bold text-text-muted uppercase tracking-widest leading-tight">{title}</h3>
      </div>
      <p className="text-4xl font-black text-text-main relative z-10 tracking-tight">{value}</p>
    </div>
  );
}

function Input({ label, ...props }) {
  return (
    <div>
      <label className="mb-2 block text-[10px] font-bold text-text-muted uppercase tracking-widest">{label}</label>
      <input required className="w-full rounded-xl border border-border-strong bg-bg-base px-4 py-3 text-sm font-medium outline-none transition-all focus:border-psu-maroon focus:shadow-[0_0_15px_rgba(128,0,0,0.1)]" {...props} />
    </div>
  );
}

function ActionBtn({ onClick, text, danger }) {
  return (
    <button onClick={onClick} className={`rounded border px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest transition-all hover:scale-105 ${danger ? 'border-red-500/20 text-red-500 hover:bg-red-500/10' : 'border-border-strong text-text-muted hover:text-text-main hover:border-border-subtle hover:bg-bg-glass'}`}>
      {text}
    </button>
  );
}
