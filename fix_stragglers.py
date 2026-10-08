import os

files = {
    "frontend/src/features/practice/SoloPractice.jsx": '<main className="flex-1 overflow-y-auto px-6 py-6 sm:px-8">',
    "frontend/src/features/settings/Settings.jsx": '<main className="settings-page flex-1 overflow-y-auto px-6 py-6 sm:px-8">',
    "frontend/src/features/submissions/Submissions.jsx": '<main className="submissions-page flex-1 overflow-y-auto px-6 py-6 sm:px-8">',
    "frontend/src/features/dashboard/Analytics.jsx": '<main className="flex-1 overflow-y-auto px-6 py-6 sm:px-8">'
}

for filepath, old in files.items():
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        content = content.replace(old, old.replace('flex-1', 'min-w-0 flex-1'))
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

print("Fixed stragglers")
