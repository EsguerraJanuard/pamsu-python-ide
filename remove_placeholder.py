import os
import re

filepath = "frontend/src/App.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Remove PlaceholderView function definition
pattern = r"function PlaceholderView.*?return.*?</main>\s*</div>\s*\);\s*}\n*"
content = re.sub(pattern, "", content, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Removed PlaceholderView from App.jsx")
