import os
import re

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Remove isDark and toggleTheme
content = re.sub(r"const \[isDark.*?;\n", "", content)
content = re.sub(r"const toggleTheme = \(\) => \{.*?\};\n", "", content, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Removed toggleTheme")
