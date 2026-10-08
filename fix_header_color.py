import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'className="text-xs font-bold text-psu-maroon uppercase tracking-widest"',
    'className="text-xs font-bold text-psu-maroon dark:text-psu-gold uppercase tracking-widest"'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed header color")
