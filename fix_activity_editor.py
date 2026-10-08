import os
import re

filepath = "frontend/src/features/instructor/ActivityEditor.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("console.error('Failed to fetch classrooms', err);", "console.error('Failed to fetch classrooms', err);\n        setError('Failed to fetch classrooms: ' + (err.message || ''));")
content = content.replace("console.error(\"Failed to save expected output test case:\", tcErr);", "console.error(\"Failed to save expected output test case:\", tcErr);\n            setError('Failed to save test case: ' + (tcErr.message || ''));")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed ActivityEditor.jsx error handling")
