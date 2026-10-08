import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

insert_idx = -1
for i, line in enumerate(lines):
    if 'return (' in line and '<div className="min-h-screen bg-bg-base' in lines[i+1]:
        insert_idx = i + 2
        break

logout_modal = """
      {/* Logout Confirmation Modal */}
      {showLogoutModal && (
        <div className="fixed inset-0 z-[150] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-sm rounded-3xl border border-border-strong bg-bg-base p-8 shadow-2xl animate-scale-in">
            <h3 className="mb-2 text-xl font-black text-text-main tracking-tight">Sign Out?</h3>
            <p className="mb-8 text-sm text-text-muted">Are you sure you want to end your administration session?</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setShowLogoutModal(false)} className="rounded-xl px-5 py-2.5 text-sm font-bold text-slate-400 transition-colors hover:bg-bg-glass hover:text-text-main border border-border-strong">Cancel</button>
              <button onClick={logout} className="rounded-xl bg-psu-maroon px-5 py-2.5 text-sm font-bold text-white shadow-lg transition-transform hover:scale-105 hover:bg-psu-red">Sign Out</button>
            </div>
          </div>
        </div>
      )}
"""

if insert_idx != -1:
    lines.insert(insert_idx, logout_modal)
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Logout modal added perfectly!")
else:
    print("Could not find insertion point.")
