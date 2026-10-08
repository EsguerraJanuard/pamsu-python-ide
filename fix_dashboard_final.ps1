$file = "frontend/src/features/admin/AdminDashboard.jsx"
$content = Get-Content $file -Raw

# 1. State injection
$content = $content -replace "const \[activeTab, setActiveTab\] = useState\('overview'\);", @"
  const [activeTab, setActiveTab] = useState('overview');
  const [pendingTab, setPendingTab] = useState(null);
  
  const [initialSettings, setInitialSettings] = useState({
    registration_enabled: false,
    default_ast_strictness: 'moderate',
    maintenance_mode: false
  });
"@

# 2. fetchData update
$content = $content -replace "setSettings\(settingsRes\.data\);", @"
        setSettings(settingsRes.data);
        setInitialSettings(settingsRes.data);
"@

# 3. handleTabChange
$content = $content -replace "  const toggleTheme = \(\) => \{", @"
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

  const toggleTheme = () => {
"@

# 4. NavButtons
$content = $content.Replace("onClick={() => setActiveTab('overview')}", "onClick={() => handleTabChange('overview')}")
$content = $content.Replace("onClick={() => setActiveTab('faculty')}", "onClick={() => handleTabChange('faculty')}")
$content = $content.Replace("onClick={() => setActiveTab('students')}", "onClick={() => handleTabChange('students')}")
$content = $content.Replace("onClick={() => setActiveTab('audit')}", "onClick={() => handleTabChange('audit')}")
$content = $content.Replace("onClick={() => setActiveTab('settings')}", "onClick={() => handleTabChange('settings')}")

# 5. UI Fixes
$content = $content.Replace('className="w-full max-w-[1600px] lg:px-8 mx-auto"', 'className="w-full lg:px-4 mx-auto"')
$content = $content.Replace('text-[10px] font-bold text-text-muted', 'text-[10px] font-bold text-slate-400')
$content = $content.Replace('text-xs font-bold text-psu-gold', 'text-xs font-black text-psu-gold')
$content = $content.Replace('text-xs font-bold text-text-muted', 'text-xs font-bold text-slate-400')
$content = $content.Replace('bg-bg-base px-4 py-3', 'bg-[#0f1117] px-4 py-3')
$content = $content.Replace('bg-bg-base border border-border-subtle shadow-sm', 'bg-bg-base border border-border-strong shadow-md')

$content = $content.Replace('className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === ''lenient'' ? ''border-emerald-500 bg-emerald-500/5 shadow-sm'' : ''border-border-subtle hover:border-border-strong hover:bg-bg-base''}`}', 'className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === ''lenient'' ? ''border-emerald-500 bg-emerald-500/5 shadow-sm'' : ''border-border-strong bg-[#0f1117]/50 hover:border-slate-500 hover:bg-[#0f1117]''}`}')
$content = $content.Replace('className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === ''moderate'' ? ''border-psu-maroon bg-psu-maroon/5 shadow-sm'' : ''border-border-subtle hover:border-border-strong hover:bg-bg-base''}`}', 'className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === ''moderate'' ? ''border-psu-maroon bg-psu-maroon/5 shadow-sm'' : ''border-border-strong bg-[#0f1117]/50 hover:border-slate-500 hover:bg-[#0f1117]''}`}')
$content = $content.Replace('className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === ''strict'' ? ''border-red-500 bg-red-500/5 shadow-sm'' : ''border-border-subtle hover:border-border-strong hover:bg-bg-base''}`}', 'className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === ''strict'' ? ''border-red-500 bg-red-500/5 shadow-sm'' : ''border-border-strong bg-[#0f1117]/50 hover:border-slate-500 hover:bg-[#0f1117]''}`}')

# 6. Save Global Settings
$content = $content -replace "setSettings\(res\.data\);\s*alert\('Global settings updated successfully'\);", @"
      setSettings(res.data);
      setInitialSettings(res.data);
      alert('Global settings updated successfully');
"@

# 7. Add Modal at the end of AdminDashboard
# Regex to match the end of the AdminDashboard component exactly, ignoring whitespace issues
$content = $content -replace "(?s)          </div>\s*</main>\s*</div>\s*</div>\s*\);\s*\}", @"
          </div>
        </main>
      </div>

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
  );
}
"@

Set-Content $file $content
