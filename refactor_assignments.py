import os

filepath = "frontend/src/features/assignments/Assignments.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('"bg-white text-[#0f1117] shadow-sm"', '"bg-psu-maroon text-white dark:bg-psu-gold dark:text-black shadow-sm"')
content = content.replace('bg-white/[0.06]', 'bg-border-subtle')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored Assignments.jsx")
