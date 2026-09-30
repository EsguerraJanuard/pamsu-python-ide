import os

filepath = "frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("bg-green-500/10 text-green-600 dark:text-green-400 border border-green-500/20", "bg-psu-maroon/10 text-psu-maroon dark:text-psu-gold border border-psu-maroon/20 dark:border-psu-gold/20")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed Grading WS.")
