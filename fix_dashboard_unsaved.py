import os
import re

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add states
state_injection = """  const [activeTab, setActiveTab] = useState('overview');
  const [pendingTab, setPendingTab] = useState(null);
  
  const [initialSettings, setInitialSettings] = useState({
    registration_enabled: false,
    default_ast_strictness: 'moderate',
    maintenance_mode: false
  });"""
content = re.sub(r"const \[activeTab, setActiveTab\] = useState\('overview'\);", state_injection, content)

# 2. Update fetchData to set both initial and current settings
fetch_replace = """        setSettings(settingsRes.data);
        setInitialSettings(settingsRes.data);"""
content = re.sub(r"setSettings\(settingsRes\.data\);", fetch_replace, content)

# 3. Create handleTabChange
handle_tab = """
  const handleTabChange = (tabId) => {
    if (activeTab === 'settings') {
      const isDirty = JSON.stringify(settings) !== JSON.stringify(initialSettings);
      if (isDirty) {
        setPendingTab(tabId);
        return;
      }
    }
    setActiveTab(tabId);
  };
"""
# Insert after useEffect
content = content.replace("  const toggleTheme = () => {", handle_tab + "\n  const toggleTheme = () => {")

# 4. Replace setActiveTab with handleTabChange in sidebar
content = content.replace("onClick={() => setActiveTab('overview')}", "onClick={() => handleTabChange('overview')}")
content = content.replace("onClick={() => setActiveTab('faculty')}", "onClick={() => handleTabChange('faculty')}")
content = content.replace("onClick={() => setActiveTab('students')}", "onClick={() => handleTabChange('students')}")
content = content.replace("onClick={() => setActiveTab('audit')}", "onClick={() => handleTabChange('audit')}")
content = content.replace("onClick={() => setActiveTab('settings')}", "onClick={() => handleTabChange('settings')}")

# 5. Add pendingTab modal at the end of the main div
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
    </div>
  );"""
content = content.replace("    </div>\n  );\n}", modal + "\n}")

# 6. When Save Global Settings is clicked, update initialSettings
save_settings_replace = """      setSettings(res.data);
      setInitialSettings(res.data);
      alert('Global settings updated successfully');"""
content = re.sub(r"setSettings\(res\.data\);\s*alert\('Global settings updated successfully'\);", save_settings_replace, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Unsaved changes logic injected!")
