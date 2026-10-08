import os

filepath = "frontend/src/components/modals/StudentGradebookModal.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace("Global Integrity Score:", "Academic Integrity:")
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

filepath = "frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace("Global Integrity:", "Academic Integrity:")
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Renamed labels to Academic Integrity")
