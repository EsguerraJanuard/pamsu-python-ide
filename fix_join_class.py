import os

filepath = "frontend/src/features/classes/MyClasses.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("bg-psu-red", "bg-psu-maroon")
content = content.replace("hover:bg-psu-maroon", "hover:bg-psu-maroon/90")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed MyClasses.jsx")
