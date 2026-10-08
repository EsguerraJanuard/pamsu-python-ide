import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add state
content = content.replace(
    "const [pendingTab, setPendingTab] = useState(null);",
    "const [pendingTab, setPendingTab] = useState(null);\n  const [showLogoutModal, setShowLogoutModal] = useState(false);"
)

# Replace Sign Out button action
content = content.replace(
    '<button onClick={logout} className="rounded-xl border border-border-subtle bg-bg-base px-5 py-2.5 text-sm font-bold shadow-sm transition-all hover:bg-bg-glass-hover hover:border-border-strong hover:shadow-md">\n          Sign Out\n        </button>',
    '<button onClick={() => setShowLogoutModal(true)} className="rounded-xl border border-border-subtle bg-bg-base px-5 py-2.5 text-sm font-bold shadow-sm transition-all hover:bg-bg-glass-hover hover:border-border-strong hover:shadow-md">\n          Sign Out\n        </button>'
)

# Add Logout Modal UI
logout_modal = """
      {/* Logout Confirmation Modal */}
      {showLogoutModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-sm rounded-3xl bg-bg-base p-6 shadow-2xl border border-border-strong animate-scale-in">
            <h3 className="text-xl font-black mb-2 text-text-main">Sign Out?</h3>
            <p className="text-sm text-text-muted mb-6">Are you sure you want to end your administration session?</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setShowLogoutModal(false)} className="px-5 py-2.5 rounded-xl text-sm font-bold border border-border-strong text-text-muted hover:text-text-main hover:bg-bg-glass transition-all">Cancel</button>
              <button onClick={logout} className="px-5 py-2.5 rounded-xl text-sm font-bold bg-psu-maroon text-white hover:bg-psu-red transition-all shadow-md">Sign Out</button>
            </div>
          </div>
        </div>
      )}
"""

content = content.replace(
    "{/* Unsaved Changes Modal */}",
    logout_modal + "\n      {/* Unsaved Changes Modal */}"
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Added logout modal")
