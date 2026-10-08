import os
import re

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"\s*<button\s*onClick=\{async \(\) => \{\s*try \{\s*await api\.get\(\"/admin/seed-production\"\);\s*alert\(\"Admin account created!\"\);\s*\} catch \(err\) \{\s*alert\(\"Backend still deploying\. Please try again in 1 minute\. \" \+ \(err\.message \|\| \"\"\)\);\s*\}\s*\}\}\s*className=\"absolute bottom-4 right-4 text-\[10px\] text-slate-500 hover:text-psu-maroon underline\"\s*>\s*Initialize Admin Account \(Demo\)\s*</button>"
content = re.sub(pattern, "", content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Removed demo button")
