import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('text-slate-500', 'text-text-muted')
content = content.replace('text-slate-400', 'text-text-muted')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored AdminDashboard")
