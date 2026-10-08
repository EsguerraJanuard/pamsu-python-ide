import os
import re

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove max-w limits
content = content.replace('max-w-6xl mx-auto w-full', 'w-full max-w-full lg:px-8')
content = content.replace('max-w-2xl', 'w-full max-w-5xl')

# 2. Fix top padding / banner placeholder
content = re.sub(r'<div className="h-14 mb-2">\s*\{error', '<div className="mb-6 empty:hidden">\n              {error', content)

# 3. Replace settings tab entirely using regex
new_settings = """{activeTab === 'settings' && (
              <div className="space-y-6 animate-fade-in w-full max-w-5xl">
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
            )}"""

content = re.sub(r"\{activeTab === 'settings'.*?\)\}", new_settings, content, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Regex replace applied")
