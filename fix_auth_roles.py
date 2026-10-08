import os

filepath = "backend/app/routers/auth.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'if user.role not in {\n        "student",\n        "instructor",\n    }:',
    'if user.role not in {\n        "student",\n        "instructor",\n        "admin",\n    }:'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Added admin to allowed roles in auth.py")
