import os
import re

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

old_text = "A browser-based Python environment that supports structural feedback, safe code execution, personal practice, and instructor-guided review."
new_text = "An intelligent, browser-based Python workspace built exclusively for the Pampanga State University Computer Science department."

content = content.replace(old_text, new_text)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated redundant paragraph")
