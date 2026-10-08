import os
import re

filepath = "frontend/src/App.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"const PlaceholderView = \(\{ title, description \}\) => \(\n.*?</div>\n\);\n*"
content = re.sub(pattern, "", content, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Removed PlaceholderView from App.jsx")
