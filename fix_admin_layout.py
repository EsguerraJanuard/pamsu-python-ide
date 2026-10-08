import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix Input background
content = content.replace('bg-[#0f1117]', 'bg-bg-base')

# Add max-w-6xl to the main wrapper if not present
if 'className="w-full lg:px-4 mx-auto"' in content:
    content = content.replace('className="w-full lg:px-4 mx-auto"', 'className="w-full max-w-6xl lg:px-4 mx-auto"')

# Fix Faculty layout (from stack to grid)
old_faculty = """<div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full max-w-xl shadow-sm relative overflow-hidden">
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
  
                  <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm">"""

new_faculty = """<div className="grid grid-cols-1 xl:grid-cols-3 gap-8 w-full">
                  <div className="xl:col-span-1">
                    <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm relative overflow-hidden sticky top-6">
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
                  </div>
  
                  <div className="xl:col-span-2">
                    <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm">"""

# Close the new grid tag at the end of the faculty tab
content = content.replace(old_faculty, new_faculty)

old_faculty_end = """                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              )}
  
              {activeTab === 'students'"""

new_faculty_end = """                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
                </div>
              )}
  
              {activeTab === 'students'"""
content = content.replace(old_faculty_end, new_faculty_end)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed layout")
