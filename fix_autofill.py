import os
import re

filepath = "frontend/src/index.css"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "-webkit-box-shadow: 0 0 0 1000px var(--bg-panel) inset !important;",
    "-webkit-box-shadow: 0 0 0 1000px transparent inset !important;\n    transition: background-color 5000s ease-in-out 0s;"
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed autofill")
