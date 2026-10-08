import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add state for student form
state_find = "const [form, setForm] = useState({ email: '', first_name: '', last_name: '', password: '' });"
state_replace = """const [form, setForm] = useState({ email: '', first_name: '', last_name: '', password: '' });
  const [studentForm, setStudentForm] = useState({ email: '', first_name: '', last_name: '', school_id: '', password: 'Pass@123' });"""
content = content.replace(state_find, state_replace)

# Add handler
handler_find = "const handleCreateFaculty = async (e) => {"
handler_replace = """const handleCreateStudent = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await api.post("/admin/students", studentForm);
      showMessage(`Student account for ${studentForm.email} provisioned successfully!`);
      setStudentForm({ email: '', first_name: '', last_name: '', school_id: '', password: 'Pass@123' });
      await fetchData();
    } catch (err) {
      showMessage(err.response?.data?.detail || err.message, true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateFaculty = async (e) => {"""
content = content.replace(handler_find, handler_replace)

# Add UI inside students tab
ui_find = '<div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm mt-4">'
ui_replace = """<div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl shadow-sm relative overflow-hidden mt-4">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-psu-maroon to-psu-red dark:from-psu-gold dark:to-yellow-500"></div>
                    <h3 className="text-lg font-black mb-6 tracking-tight">Manual Provisioning</h3>
                    <form onSubmit={handleCreateStudent} className="space-y-4">
                      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        <input type="text" placeholder="First Name" required value={studentForm.first_name} onChange={e => setStudentForm({...studentForm, first_name: e.target.value})} className="rounded-xl border border-border-subtle bg-bg-base px-4 py-2.5 text-sm focus:border-psu-maroon focus:outline-none" />
                        <input type="text" placeholder="Last Name" required value={studentForm.last_name} onChange={e => setStudentForm({...studentForm, last_name: e.target.value})} className="rounded-xl border border-border-subtle bg-bg-base px-4 py-2.5 text-sm focus:border-psu-maroon focus:outline-none" />
                        <input type="email" placeholder="PSU Email" required value={studentForm.email} onChange={e => setStudentForm({...studentForm, email: e.target.value})} className="rounded-xl border border-border-subtle bg-bg-base px-4 py-2.5 text-sm focus:border-psu-maroon focus:outline-none" />
                        <input type="text" placeholder="School ID (e.g. 2020-0001)" required value={studentForm.school_id} onChange={e => setStudentForm({...studentForm, school_id: e.target.value})} className="rounded-xl border border-border-subtle bg-bg-base px-4 py-2.5 text-sm focus:border-psu-maroon focus:outline-none" />
                      </div>
                      <button type="submit" disabled={isLoading} className="w-full rounded-xl bg-psu-maroon px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-psu-maroon/90 disabled:opacity-50">
                        {isLoading ? "Provisioning..." : "Provision Student"}
                      </button>
                    </form>
                  </div>
                  
                  <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm mt-4">"""

content = content.replace(ui_find, ui_replace)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated AdminDashboard.jsx")
