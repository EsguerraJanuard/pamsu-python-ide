import os
import re

def replace_in_file(filepath, old, new):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def regex_replace_in_file(filepath, pattern, new):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(pattern, new, content)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. React Anti-Patterns & Hook Misuse
replace_in_file("frontend/src/pages/AuditLogsPage.jsx", "|| Date.now()", "")
replace_in_file("frontend/src/pages/AuditLogsPage.jsx", 'import Statusbar from "../components/layout/Statusbar";\n', "")
replace_in_file("frontend/src/pages/AuditLogsPage.jsx", "<Statusbar />", "")
# Fix unused err in AuditLogsPage and NotificationsPage (will just comment out or handle if needed later)

# 2. Leftover Generic Tailwind Colors in AdminDashboard.jsx
ad_path = "frontend/src/features/admin/AdminDashboard.jsx"
replace_in_file(ad_path, "bg-green-500/10 text-emerald-500 border-emerald-500/20", "bg-psu-maroon/10 text-text-brand border-psu-maroon/20")
replace_in_file(ad_path, "bg-red-500/10 text-red-500 border-red-500/20", "bg-bg-glass text-text-muted border-border-subtle")
replace_in_file(ad_path, "bg-green-500/10 text-emerald-500", "bg-psu-maroon/10 text-text-brand")
replace_in_file(ad_path, "bg-red-500/10 text-red-500", "bg-bg-glass text-text-muted")
replace_in_file(ad_path, "border-emerald-500", "border-psu-maroon dark:border-psu-gold")

# 3. Production & Architectural Flaws (Localhost Fallbacks)
files_with_localhost = [
    "frontend/src/services/api.js",
    "frontend/src/features/auth/Login.jsx",
    "frontend/src/components/terminal/InteractiveTerminal.jsx",
    "frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx"
]
for f in files_with_localhost:
    replace_in_file(f, "|| 'http://localhost:8000'", "")
    replace_in_file(f, '|| "http://localhost:8000"', '')

# 4. Stray TODO in Workspace.jsx
replace_in_file("frontend/src/features/workspace/Workspace.jsx", "# TODO: implement the solution", "")

print("Initial replacements complete.")
