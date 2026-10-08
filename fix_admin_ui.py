import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "'border-border-strong bg-[#0f1117]/50 hover:border-slate-500 hover:bg-[#0f1117]'",
    "'border-border-strong bg-bg-glass hover:border-border-strong hover:bg-bg-panel'"
)

# Also fix the moderate selected border color for dark mode just in case
content = content.replace(
    "'border-psu-maroon bg-psu-maroon/5 shadow-sm' :",
    "'border-psu-maroon dark:border-psu-gold bg-psu-maroon/5 dark:bg-psu-gold/5 shadow-sm' :"
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed admin UI colors")
