import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

logout_modal = """
      {/* Logout Confirmation Modal */}
      {showLogoutModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-sm rounded-3xl border border-border-strong bg-bg-base p-8 shadow-2xl animate-fade-in-up">
            <h3 className="mb-2 text-2xl font-black text-text-main">Sign Out?</h3>
            <p className="mb-8 text-sm text-text-muted">Are you sure you want to end your administration session?</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setShowLogoutModal(false)} className="rounded-xl px-5 py-2.5 text-sm font-bold text-slate-400 transition-colors hover:bg-bg-glass hover:text-text-main">Cancel</button>
              <button onClick={logout} className="rounded-xl bg-psu-maroon px-5 py-2.5 text-sm font-bold text-white shadow-lg transition-transform hover:scale-105">Sign Out</button>
            </div>
          </div>
        </div>
      )}
"""

content = content.replace(
    '  return (\n    <div className="min-h-screen bg-bg-base text-text-main font-sans">',
    '  return (\n    <div className="min-h-screen bg-bg-base text-text-main font-sans">' + logout_modal
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Added logout modal correctly")
