import os

filepath = "frontend/src/features/dashboard/ClassRosterView.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace('<th className="px-6 py-4 text-center">Integrity</th>', '<th className="px-6 py-4 text-center">Academic Integrity</th>')
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Renamed column to Academic Integrity")
