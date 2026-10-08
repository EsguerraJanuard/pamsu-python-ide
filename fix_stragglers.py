import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Standardize the Export Data gradient line to look like the others
    content = content.replace(
        'bg-gradient-to-r from-slate-400 to-slate-300 dark:from-slate-600 dark:to-slate-500',
        'bg-gradient-to-r from-psu-maroon to-psu-red dark:from-psu-gold dark:to-yellow-500'
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed straggling styles")
