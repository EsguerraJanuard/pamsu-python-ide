import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

modal = """
      {pendingTab && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md rounded-3xl border border-border-strong bg-bg-base p-8 shadow-2xl animate-fade-in-up">
            <h3 className="mb-2 text-2xl font-black text-text-main">Unsaved Changes</h3>
            <p className="mb-8 text-sm text-text-muted">
              You have unsaved changes in your System Settings. If you leave this tab, your changes will be discarded.
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setPendingTab(null)} className="rounded-xl px-5 py-2.5 text-sm font-bold text-slate-400 transition-colors hover:bg-bg-glass hover:text-text-main">
                Cancel
              </button>
              <button onClick={() => {
                setSettings(initialSettings);
                setActiveTab(pendingTab);
                setPendingTab(null);
              }} className="rounded-xl bg-psu-maroon px-5 py-2.5 text-sm font-bold text-white shadow-md shadow-psu-maroon/20 hover:scale-105 transition-all">
                Discard & Leave
              </button>
            </div>
          </div>
        </div>
      )}
"""

target = "          </div>\n        </main>\n      </div>\n    </div>\n  );\n}"
if target in content:
    content = content.replace(target, "          </div>\n        </main>\n      </div>\n" + modal + "\n    </div>\n  );\n}")
else:
    # use regex
    import re
    content = re.sub(r"          </div>\n        </main>\n      </div>\n    </div>\n  \);\n\}", "          </div>\n        </main>\n      </div>\n" + modal + "\n    </div>\n  );\n}", content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Modal injected!")
