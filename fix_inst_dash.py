import os

filepath = "frontend/src/features/dashboard/InstructorDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("text-emerald-400", "text-text-brand")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed InstructorDashboard.")
