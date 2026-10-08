import os

filepath = "frontend/src/features/workspace/Workspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('dotClass: "bg-white/30"', 'dotClass: "bg-border-strong"')
content = content.replace('hover:bg-psu-maroon', 'hover:bg-psu-red')
content = content.replace('bg-violet-600', 'bg-psu-gold text-black')
content = content.replace('bg-gradient-to-r from-psu-maroon to-indigo-600', 'bg-gradient-to-r from-psu-maroon to-psu-gold')
content = content.replace('hover:to-indigo-500', 'hover:to-yellow-500')
content = content.replace('bg-white/20', 'bg-border-strong')
content = content.replace('bg-white/[0.08]', 'bg-border-subtle')
content = content.replace('bg-black/30', 'bg-bg-base/50 border border-border-subtle backdrop-blur')
content = content.replace('border-white', 'border-text-main')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored Workspace.jsx")
