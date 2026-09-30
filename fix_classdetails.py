import os

filepath = "frontend/src/features/classes/ClassDetails.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("border-green-500/30 bg-green-500/10", "border-psu-maroon/30 bg-psu-maroon/10 dark:border-psu-gold/30 dark:bg-psu-gold/10")
content = content.replace("hover:bg-blue-50", "hover:bg-psu-maroon/10")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed ClassDetails.")
