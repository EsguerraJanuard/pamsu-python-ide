import os

filepath = "frontend/src/features/settings/EditorSettings.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('bg-slate-300 dark:bg-slate-700', 'bg-border-strong')
content = content.replace('after:border-slate-300 dark:after:border-slate-700', 'after:border-transparent')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored EditorSettings")
