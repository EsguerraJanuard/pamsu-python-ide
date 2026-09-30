import os

filepath = "frontend/src/features/instructor/ActivityEditor.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("peer-checked:group-hover:bg-emerald-400", "peer-checked:group-hover:bg-psu-red")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Replaced all emerald hover states.")
