import os

filepath = "frontend/src/features/theme/ThemeToggle.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('"bg-white text-text-brand shadow-sm"', '"bg-bg-glass text-text-brand shadow-sm border border-border-subtle"')
content = content.replace('"bg-slate-800 text-text-brand shadow-sm border border-white/10"', '"bg-bg-glass text-text-brand shadow-sm border border-border-subtle"')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored ThemeToggle")
