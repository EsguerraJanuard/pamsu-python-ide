import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove max-w limits to fix left alignment
content = content.replace('max-w-6xl mx-auto w-full', 'w-full max-w-[1600px] mx-auto')
content = content.replace('max-w-2xl', '')

# 2. Fix top padding / banner placeholder
content = content.replace('<div className="h-14 mb-2">\n              {error', '<div className="mb-4">\n              {error')
content = content.replace('</svg>{success}</div>}\n            </div>', '</svg>{success}</div>}\n            </div>')
content = content.replace('className="h-14 mb-2"', 'className="mb-4 empty:hidden"') # Add empty:hidden just in case

# 3. Replace System Settings section
old_settings = """            {activeTab === 'settings' && (
              <div className="space-y-6 animate-fade-in max-w-2xl">
                <header className="border-b border-border-subtle pb-6 mb-8">
                  <p className="mb-1 font-mono text-xs text-text-brand tracking-widest">CONFIGURATION</p>
                  <h1 className="text-3xl font-black text-text-main tracking-tight">System Settings</h1>
                  <p className="mt-2 text-sm text-text-muted">Manage global policies, UI preferences, and maintenance state.</p>
                </header>
                
                <div className="bg-bg-glass border border-border-subtle p-8 rounded-2xl shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-text-main to-text-muted"></div>
                  <form onSubmit={handleSaveSettings} className="space-y-8">
                    
                    {/* UI Toggle */}
                    <div className="flex items-center justify-between border-b border-border-subtle pb-6">
                      <div className="pr-8">
                        <h4 className="font-black text-lg tracking-tight">Dark Mode (Local UI)</h4>
                        <p className="text-sm text-text-muted mt-1">Toggle between light and dark mode specifically for this dashboard.</p>
                      </div>
                      <label className="relative inline-flex cursor-pointer items-center shrink-0">
                        <input type="checkbox" className="peer sr-only" checked={isDark} onChange={toggleTheme} />
                        <div className="h-7 w-12 rounded-full bg-border-strong peer-checked:bg-text-main after:absolute after:left-[2px] after:top-[2px] after:h-6 after:w-6 after:rounded-full after:bg-white after:transition-all peer-checked:after:translate-x-full"></div>
                      </label>
                    </div>

                    {/* Maintenance Mode */}
                    <div className="flex items-center justify-between border-b border-border-subtle pb-6">
                      <div className="pr-8">
                        <h4 className="font-black text-lg tracking-tight">Maintenance Mode</h4>
                        <p className="text-sm text-text-muted mt-1">Suspend all student logins and task execution. Only MIS and Instructors can access the platform while this is on.</p>
                      </div>
                      <label className="relative inline-flex cursor-pointer items-center shrink-0">
                        <input type="checkbox" className="peer sr-only" checked={settings.maintenance_mode} onChange={e => setSettings({...settings, maintenance_mode: e.target.checked})} />
                        <div className="h-7 w-12 rounded-full bg-border-strong peer-checked:bg-red-500 after:absolute after:left-[2px] after:top-[2px] after:h-6 after:w-6 after:rounded-full after:bg-white after:transition-all peer-checked:after:translate-x-full shadow-inner"></div>
                      </label>
                    </div>

                    <div className="flex items-center justify-between border-b border-border-subtle pb-6">
                      <div className="pr-8">
                        <h4 className="font-black text-lg tracking-tight">Allow Public Registration</h4>
                        <p className="text-sm text-text-muted mt-1">Allow students to sign up manually without MIS pre-registration via masterlist upload.</p>
                      </div>
                      <label className="relative inline-flex cursor-pointer items-center shrink-0">
                        <input type="checkbox" className="peer sr-only" checked={settings.registration_enabled} onChange={e => setSettings({...settings, registration_enabled: e.target.checked})} />
                        <div className="h-7 w-12 rounded-full bg-border-strong peer-checked:bg-psu-maroon after:absolute after:left-[2px] after:top-[2px] after:h-6 after:w-6 after:rounded-full after:bg-white after:transition-all peer-checked:after:translate-x-full shadow-inner"></div>
                      </label>
                    </div>

                    <div className="pb-4">
                      <h4 className="font-black text-lg tracking-tight mb-2">Default AST Strictness</h4>
                      <p className="text-sm text-text-muted mb-4">Global strictness level for structural code feedback.</p>
                      <select value={settings.default_ast_strictness} onChange={e => setSettings({...settings, default_ast_strictness: e.target.value})} className="w-full rounded-xl border border-border-strong bg-bg-base px-4 py-3 text-sm font-medium outline-none focus:border-psu-maroon focus:ring-2 focus:ring-psu-maroon/20 transition-all cursor-pointer">
                        <option value="lenient">Lenient (Allows standard variations & formatting differences)</option>
                        <option value="moderate">Moderate (Standard university policy)</option>
                        <option value="strict">Strict (Requires exact structural AST match)</option>
                      </select>
                    </div>

                    <div className="pt-2">
                      <button type="submit" className="rounded-2xl bg-psu-maroon px-8 py-3.5 text-base font-bold text-white shadow-lg shadow-psu-maroon/20 hover:scale-[1.02] hover:shadow-psu-maroon/40 transition-all">
                        Save Global Settings
                      </button>
                    </div>

                  </form>
                </div>
              </div>
            )}"""

new_settings = """            {activeTab === 'settings' && (
              <div className="space-y-6 animate-fade-in w-full max-w-4xl">
                <header className="border-b border-border-subtle pb-6 mb-6">
                  <p className="mb-1 font-mono text-xs text-text-brand tracking-widest">CONFIGURATION</p>
                  <h1 className="text-3xl font-black text-text-main tracking-tight">System Settings</h1>
                  <p className="mt-2 text-sm text-text-muted">Manage global policies and maintenance state.</p>
                </header>
                
                <div className="bg-bg-glass border border-border-subtle p-8 rounded-2xl shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-text-main to-text-muted"></div>
                  <form onSubmit={handleSaveSettings} className="space-y-10">
                    
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
                        <label className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === 'lenient' ? 'border-emerald-500 bg-emerald-500/5' : 'border-border-subtle hover:border-border-strong hover:bg-bg-base'}`}>
                          <input type="radio" name="ast_strictness" value="lenient" checked={settings.default_ast_strictness === 'lenient'} onChange={e => setSettings({...settings, default_ast_strictness: e.target.value})} className="hidden" />
                          <div className="flex items-center gap-3 mb-2">
                            <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${settings.default_ast_strictness === 'lenient' ? 'border-emerald-500' : 'border-border-strong'}`}>
                              {settings.default_ast_strictness === 'lenient' && <div className="w-2 h-2 rounded-full bg-emerald-500"></div>}
                            </div>
                            <span className="font-black text-text-main">Lenient</span>
                          </div>
                          <p className="text-xs text-text-muted leading-relaxed">Allows standard variations & formatting differences.</p>
                        </label>

                        <label className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === 'moderate' ? 'border-psu-maroon bg-psu-maroon/5' : 'border-border-subtle hover:border-border-strong hover:bg-bg-base'}`}>
                          <input type="radio" name="ast_strictness" value="moderate" checked={settings.default_ast_strictness === 'moderate'} onChange={e => setSettings({...settings, default_ast_strictness: e.target.value})} className="hidden" />
                          <div className="flex items-center gap-3 mb-2">
                            <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${settings.default_ast_strictness === 'moderate' ? 'border-psu-maroon' : 'border-border-strong'}`}>
                              {settings.default_ast_strictness === 'moderate' && <div className="w-2 h-2 rounded-full bg-psu-maroon"></div>}
                            </div>
                            <span className="font-black text-text-main">Moderate</span>
                          </div>
                          <p className="text-xs text-text-muted leading-relaxed">Standard university policy with balanced checks.</p>
                        </label>

                        <label className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === 'strict' ? 'border-red-500 bg-red-500/5' : 'border-border-subtle hover:border-border-strong hover:bg-bg-base'}`}>
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
            )}"""

content = content.replace(old_settings, new_settings)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Admin dashboard UI updated")
