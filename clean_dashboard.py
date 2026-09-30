import re

filepath = "frontend/src/features/dashboard/InstructorDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Remove Audit Trail section
content = re.sub(r'<div className="mb-5 h-px bg-border-subtle" />\s*<section>\s*<h2 className="mb-4 text-xs font-semibold">System Audit Trail</h2>.*?</ul>\s*</section>', '', content, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Removed Audit Trail from InstructorDashboard.")
