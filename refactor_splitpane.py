import os

filepath = "frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('hover:bg-psu-maroon', 'hover:bg-psu-red')
content = content.replace('text-slate-300', 'text-text-muted')
content = content.replace('text-slate-500', 'text-text-muted')
content = content.replace('bg-white/5', 'bg-bg-panel')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored SplitPaneGradingWorkspace")
