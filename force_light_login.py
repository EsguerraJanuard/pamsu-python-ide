import os

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    "bg-bg-base": "bg-white",
    "text-text-main": "text-slate-900",
    "text-text-muted": "text-slate-500",
    "border-border-subtle": "border-slate-200",
    "border-border-strong": "border-slate-300",
    "bg-bg-glass": "bg-slate-50",
    "bg-bg-glass-hover": "bg-slate-100",
    "text-text-rose": "text-red-600"
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Forced light mode on Login.jsx")
