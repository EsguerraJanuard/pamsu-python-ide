import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix Dark Mode toggle
content = content.replace(
    'peer-checked:bg-text-main after:absolute',
    'peer-checked:bg-psu-maroon dark:peer-checked:bg-psu-gold after:absolute'
)

# Fix Maintenance Mode toggle
content = content.replace(
    'peer-checked:bg-red-500 after:absolute',
    'peer-checked:bg-psu-maroon dark:peer-checked:bg-psu-gold after:absolute'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed toggles")
