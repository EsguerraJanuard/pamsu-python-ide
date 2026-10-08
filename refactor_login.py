import os

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Refactor Login.jsx
content = content.replace('bg-white text-slate-900', 'bg-bg-base text-text-main')
content = content.replace('bg-white px-6', 'bg-bg-glass px-6')
content = content.replace('text-slate-500', 'text-text-muted')
content = content.replace('text-slate-900', 'text-text-main')
content = content.replace('border-slate-200', 'border-border-subtle')
content = content.replace('border-slate-300', 'border-border-strong')
content = content.replace('bg-slate-50-hover', 'bg-bg-glass-hover')
content = content.replace('bg-slate-50', 'bg-bg-base')
content = content.replace('bg-white px-3', 'bg-bg-glass px-3')
content = content.replace('hover:text-slate-900', 'hover:text-text-main')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored Login.jsx")
