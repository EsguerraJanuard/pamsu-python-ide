import os
import re

files_to_clean = [
    "frontend/src/features/classes/MyClasses.jsx",
    "frontend/src/features/dashboard/InstructorDashboard.jsx",
    "frontend/src/features/dashboard/StudentDashboard.jsx"
]

for filepath in files_to_clean:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Remove all console.log statements
        content = re.sub(r"^\s*console\.log\(.*?\);\s*$", "", content, flags=re.MULTILINE)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Cleaned {filepath}")
    else:
        print(f"Not found: {filepath}")
