import os

filepath = "frontend/src/features/dashboard/ClassRosterView.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('divide-white/[0.06]', 'divide-border-subtle')
content = content.replace('bg-slate-600', 'bg-text-muted')
content = content.replace('text-text-rose', 'text-red-500')
content = content.replace('hover:bg-psu-maroon', 'hover:bg-psu-red')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored ClassRosterView")
