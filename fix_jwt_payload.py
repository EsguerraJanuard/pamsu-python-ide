import os
import re

filepath = "backend/app/routers/auth.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace "name": user.name with "name": f"{user.first_name} {user.last_name}"
content = re.sub(
    r'"name":\s*user\.name,',
    r'"name": f"{user.first_name} {user.last_name}",',
    content
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed JWT payload")
