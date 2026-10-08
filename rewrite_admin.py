import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace StatCard icon logic and layout
new_stat_card = """
const StatCard = ({ title, value, icon, colorClass = "text-text-brand" }) => (
  <div className="dashboard-card rounded-2xl border border-border-subtle bg-bg-glass p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
    <div className="absolute -right-4 -top-4 opacity-5 group-hover:opacity-10 transition-opacity">
      {icon}
    </div>
    <div className="flex items-center gap-4 mb-4">
      <div className={`p-3 rounded-xl bg-bg-base border border-border-subtle shadow-sm ${colorClass}`}>
        {icon}
      </div>
      <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider">{title}</h3>
    </div>
    <p className="text-4xl font-black text-text-main">{value}</p>
  </div>
);
"""

# Replace old StatCard definition
import re
content = re.sub(r'const StatCard =.*?\);\n', new_stat_card, content, flags=re.DOTALL)

# Update the Overview tab render
old_overview = """            {activeTab === 'overview' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-black">High-Level System Overview</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <StatCard title="Total CS Instructors" value={stats.total_instructors} icon="?????" />
                  <StatCard title="Total Registered Students" value={stats.total_students} icon="??" />
                  <StatCard title="Total Active Classrooms" value={stats.total_classrooms} icon="??" />
                </div>
              </div>
            )}"""

icons = {
    "instructor": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>',
    "student": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "classroom": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>'
}

new_overview = f"""            {{activeTab === 'overview' && (
              <div className="space-y-8 animate-fade-in">
                <header className="border-b border-border-subtle pb-6">
                  <p className="mb-1 font-mono text-xs text-text-brand tracking-widest">METRICS</p>
                  <h1 className="text-3xl font-black text-text-main tracking-tight">System Overview</h1>
                  <p className="mt-2 text-sm text-text-muted">High-level statistics across the entire Python IDE platform.</p>
                </header>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <StatCard title="Total Instructors" value={{stats.total_instructors}} colorClass="text-blue-500" icon={{ {icons["instructor"]} }} />
                  <StatCard title="Registered Students" value={{stats.total_students}} colorClass="text-emerald-500" icon={{ {icons["student"]} }} />
                  <StatCard title="Active Classrooms" value={{stats.total_classrooms}} colorClass="text-purple-500" icon={{ {icons["classroom"]} }} />
                </div>
              </div>
            )}}"""

content = content.replace(old_overview, new_overview)

# Update Faculty Tab
old_faculty_header = '<h3 className="text-lg font-bold mb-4">Provision Faculty</h3>'
new_faculty_header = """                <header className="border-b border-border-subtle pb-6 mb-8 col-span-1 lg:col-span-3">
                  <p className="mb-1 font-mono text-xs text-text-brand tracking-widest">MANAGEMENT</p>
                  <h1 className="text-3xl font-black text-text-main tracking-tight">Faculty Management</h1>
                  <p className="mt-2 text-sm text-text-muted">Provision new instructor accounts and manage existing computer science faculty.</p>
                </header>
                <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl lg:col-span-1 h-fit shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-psu-maroon to-psu-red"></div>
                  <h3 className="text-lg font-black mb-6 tracking-tight">Provision Faculty</h3>"""
content = content.replace(old_faculty_header, new_faculty_header)

content = content.replace('<h3 className="text-lg font-bold mb-4">CS Department Faculty</h3>', '<h3 className="text-lg font-black mb-6 tracking-tight">CS Department Faculty</h3>')

# Update Student Masterlist Tab
old_student_header = '<h3 className="text-lg font-bold mb-4">Pre-Register Masterlist</h3>'
new_student_header = """                <header className="border-b border-border-subtle pb-6 mb-8 col-span-1 lg:col-span-3">
                  <p className="mb-1 font-mono text-xs text-text-brand tracking-widest">PROVISIONING</p>
                  <h1 className="text-3xl font-black text-text-main tracking-tight">Student Masterlist</h1>
                  <p className="mt-2 text-sm text-text-muted">Bulk upload student emails or export the current masterlist.</p>
                </header>
                <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl h-fit shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 to-emerald-400"></div>
                  <h3 className="text-lg font-black mb-4 tracking-tight">Pre-Register Masterlist</h3>"""
content = content.replace(old_student_header, new_student_header)

content = content.replace('<h3 className="text-lg font-bold mb-4">Student Masterlist</h3>', '<h3 className="text-lg font-black mb-4 tracking-tight">Student Database</h3>')

# Custom File Input for Student Masterlist
old_file_input = '<input type="file" accept=".csv, .xlsx" onChange={handleFileUpload} className="block w-full text-sm text-text-muted file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-psu-maroon/10 file:text-psu-maroon hover:file:bg-psu-maroon/20" />'
new_file_input = """<label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-border-strong rounded-xl cursor-pointer bg-bg-base hover:bg-bg-glass transition-colors">
                      <div className="flex flex-col items-center justify-center pt-5 pb-6">
                        <svg className="w-8 h-8 mb-3 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                        <p className="mb-2 text-sm text-text-muted"><span className="font-semibold text-text-brand">Click to upload</span> or drag and drop</p>
                        <p className="text-xs text-text-muted/70">CSV or Excel files only</p>
                      </div>
                      <input type="file" accept=".csv, .xlsx" onChange={handleFileUpload} className="hidden" />
                    </label>"""
content = content.replace(old_file_input, new_file_input)

# Improve buttons
content = content.replace('className="w-full rounded-xl bg-bg-base border border-border-subtle py-2 text-sm font-bold hover:bg-bg-glass transition-colors"', 'className="w-full rounded-xl bg-bg-base border border-border-strong py-3 text-sm font-bold shadow-sm hover:bg-bg-glass hover:shadow transition-all"')
content = content.replace('className="w-full mt-4 rounded-xl border border-psu-maroon/20 bg-psu-maroon/10 py-2 text-sm font-bold text-psu-maroon hover:bg-psu-maroon/20 transition-colors disabled:opacity-50"', 'className="w-full mt-4 rounded-xl border border-psu-maroon/20 bg-psu-maroon/10 py-3 text-sm font-bold text-psu-maroon hover:bg-psu-maroon/20 hover:scale-[1.02] transition-all disabled:opacity-50 disabled:hover:scale-100"')

# Audit Trail Header
old_audit_header = '<h2 className="text-2xl font-black">Global Security & Audit Trail</h2>'
new_audit_header = """                <header className="border-b border-border-subtle pb-6 flex flex-col md:flex-row md:justify-between md:items-end gap-4">
                  <div>
                    <p className="mb-1 font-mono text-xs text-text-brand tracking-widest">SECURITY</p>
                    <h1 className="text-3xl font-black text-text-main tracking-tight">Global Audit Trail</h1>
                    <p className="mt-2 text-sm text-text-muted">Immutable log of all critical system actions.</p>
                  </div>
                  <div className="w-full md:w-64">
"""
content = content.replace(old_audit_header, new_audit_header)

# Search input inside Audit
content = content.replace('<input type="text" placeholder="Search logs (actor, action)..." value={auditSearch} onChange={(e) => setAuditSearch(e.target.value)} className="w-full md:w-64 px-4 py-2 bg-bg-base border border-border-subtle rounded-xl text-sm focus:outline-none focus:border-psu-maroon" />', '<div className="relative group"><svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted group-focus-within:text-psu-maroon transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg><input type="text" placeholder="Search logs..." value={auditSearch} onChange={(e) => setAuditSearch(e.target.value)} className="w-full pl-9 pr-4 py-2.5 bg-bg-glass border border-border-subtle rounded-xl text-sm focus:outline-none focus:border-psu-maroon transition-colors shadow-sm" /></div></div>\n                </header>')

# System Settings Header
old_settings_header = '<h2 className="text-2xl font-black mb-6">Global Platform Settings</h2>'
new_settings_header = """                <header className="border-b border-border-subtle pb-6 mb-8">
                  <p className="mb-1 font-mono text-xs text-text-brand tracking-widest">CONFIGURATION</p>
                  <h1 className="text-3xl font-black text-text-main tracking-tight">System Settings</h1>
                  <p className="mt-2 text-sm text-text-muted">Manage global policies and maintenance state.</p>
                </header>"""
content = content.replace(old_settings_header, new_settings_header)

# Empty States for Tables
faculty_empty_state = """                      {instructors.length === 0 && (
                        <tr>
                          <td colSpan="4" className="px-4 py-12 text-center text-text-muted">
                            <div className="flex flex-col items-center justify-center">
                              <svg className="w-10 h-10 mb-3 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                              <p className="font-semibold text-text-main">No faculty members found</p>
                              <p className="text-xs mt-1">Provision an instructor to see them here.</p>
                            </div>
                          </td>
                        </tr>
                      )}"""
content = content.replace('                      {instructors.length === 0 && (\n                        <tr>\n                          <td colSpan="4" className="text-center py-8 text-text-muted">No instructors found.</td>\n                        </tr>\n                      )}', faculty_empty_state)

students_empty_state = """                      {filteredStudents.length === 0 && (
                        <tr>
                          <td colSpan="4" className="px-4 py-12 text-center text-text-muted">
                            <div className="flex flex-col items-center justify-center">
                              <svg className="w-10 h-10 mb-3 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
                              <p className="font-semibold text-text-main">No students found</p>
                              <p className="text-xs mt-1">Upload a masterlist to provision students.</p>
                            </div>
                          </td>
                        </tr>
                      )}"""
content = content.replace('                      {filteredStudents.length === 0 && (\n                        <tr>\n                          <td colSpan="4" className="text-center py-8 text-text-muted">No students found.</td>\n                        </tr>\n                      )}', students_empty_state)

audit_empty_state = """                      {filteredLogs.length === 0 && (
                        <tr>
                          <td colSpan="5" className="px-4 py-16 text-center text-text-muted">
                            <div className="flex flex-col items-center justify-center">
                              <svg className="w-10 h-10 mb-3 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>
                              <p className="font-semibold text-text-main">No audit logs available</p>
                              <p className="text-xs mt-1">Actions taken on the system will appear here.</p>
                            </div>
                          </td>
                        </tr>
                      )}"""
content = content.replace('                      {filteredLogs.length === 0 && (\n                        <tr>\n                          <td colSpan="5" className="text-center py-12 text-text-muted">No logs found matching your search.</td>\n                        </tr>\n                      )}', audit_empty_state)

# Replace <Input /> definitions to be cleaner
old_input = """const Input = ({ label, type = "text", value, onChange }) => (
  <div>
    <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-1.5">{label}</label>
    <input type={type} value={value} onChange={onChange} className="w-full bg-bg-base border border-border-subtle rounded-xl px-4 py-2.5 text-sm focus:border-psu-maroon focus:outline-none focus:ring-1 focus:ring-psu-maroon/30 transition-shadow" required />
  </div>
);"""
new_input = """const Input = ({ label, type = "text", value, onChange }) => (
  <div>
    <label className="block text-[11px] font-bold text-text-muted uppercase tracking-widest mb-1.5">{label}</label>
    <input type={type} value={value} onChange={onChange} className="w-full bg-bg-base border border-border-strong rounded-xl px-4 py-3 text-sm focus:border-psu-maroon focus:outline-none focus:shadow-[0_0_10px_rgba(128,0,0,0.1)] transition-all" required />
  </div>
);"""
content = content.replace(old_input, new_input)


with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Redesigned Admin Dashboard")
