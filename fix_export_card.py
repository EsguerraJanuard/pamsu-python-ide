import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

old_export_card = """                    <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl shadow-sm flex flex-col justify-between">
                      <div>
                        <h3 className="text-lg font-black mb-4 tracking-tight">Export Data</h3>
                        <p className="text-sm text-text-muted mb-4">Download the full user masterlist to CSV.</p>
                      </div>
                      <button onClick={exportMasterlist} className="w-full rounded-xl bg-bg-base border border-border-strong py-4 text-sm font-bold shadow-sm hover:bg-bg-glass hover:shadow transition-all">
                        Download CSV
                      </button>
                    </div>"""

new_export_card = """                    <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl shadow-sm relative overflow-hidden">
                      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-slate-400 to-slate-300 dark:from-slate-600 dark:to-slate-500"></div>
                      <h3 className="text-lg font-black mb-6 tracking-tight">Export Data</h3>
                      <p className="text-sm text-text-muted mb-4">Download the full user masterlist to CSV.</p>
                      
                      <button onClick={exportMasterlist} className="flex flex-col items-center justify-center w-full h-32 border-2 border-border-strong rounded-xl cursor-pointer bg-bg-base hover:bg-bg-glass hover:border-psu-maroon dark:hover:border-psu-gold transition-all group">
                        <svg className="w-8 h-8 mb-3 text-text-muted group-hover:text-psu-maroon dark:group-hover:text-psu-gold transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                        <p className="mb-2 text-sm font-semibold text-text-main group-hover:text-psu-maroon dark:group-hover:text-psu-gold transition-colors">Download CSV</p>
                        <p className="text-xs text-text-muted/70">Export all records</p>
                      </button>
                    </div>"""

content = content.replace(old_export_card, new_export_card)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed export card")
