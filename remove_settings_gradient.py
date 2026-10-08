import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    '<div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-text-main to-text-muted"></div>',
    ''
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Removed settings gradient")
