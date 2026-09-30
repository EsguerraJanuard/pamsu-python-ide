import os

filepath = "frontend/src/features/settings/EditorSettings.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'peer-checked:bg-psu-maroon group-hover:bg-psu-red/50 peer-checked:group-hover:bg-psu-red',
    'peer-checked:bg-psu-maroon dark:peer-checked:bg-psu-gold'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed toggle hovers.")
