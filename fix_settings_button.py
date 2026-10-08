import os

filepath = "frontend/src/features/settings/Settings.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

old_str = "bg-gradient-to-br from-[var(--color-psu-red, #ce0000)] to-[#2563eb]"
new_str = "bg-psu-maroon hover:bg-psu-maroon/90"

content = content.replace(old_str, new_str)
content = content.replace(" hover:opacity-90", "")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed Settings.jsx")
