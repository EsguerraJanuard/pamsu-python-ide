import os

filepath = "frontend/src/features/workspace/Workspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('"bg-psu-gold text-black text-white shadow-sm"', '"bg-psu-gold text-black shadow-sm"')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored Workspace.jsx")
