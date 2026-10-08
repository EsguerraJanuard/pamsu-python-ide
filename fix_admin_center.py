import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix layout to perfectly center
content = content.replace(
    'className="space-y-6 animate-fade-in w-full max-w-5xl"',
    'className="space-y-6 animate-fade-in w-full mx-auto max-w-6xl"'
)
content = content.replace(
    'className="flex flex-col gap-8 animate-fade-in w-full"',
    'className="flex flex-col gap-8 animate-fade-in w-full mx-auto max-w-6xl"'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed centering")
