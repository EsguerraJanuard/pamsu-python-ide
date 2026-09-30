import os

filepath = "frontend/src/features/dashboard/ClassRosterView.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("border-emerald-400", "border-psu-maroon dark:border-psu-gold")
content = content.replace("bg-emerald-400 opacity-75", "bg-psu-maroon dark:bg-psu-gold opacity-75")
content = content.replace("bg-emerald-500", "bg-psu-maroon dark:bg-psu-gold")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed ClassRosterView.")
