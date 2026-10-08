import os
import re

filepath = "backend/app/core/security.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

if "get_current_student" not in content:
    content = content + "\nget_current_student = RequireRole([\"student\", \"admin\"])\n"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

filepath = "backend/app/routers/practice.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("from app.core.security import get_current_user, get_current_instructor", "from app.core.security import get_current_user, get_current_instructor, get_current_student")
content = content.replace("current_user: User = Depends(get_current_user)", "current_user: User = Depends(get_current_student)")
# Revert for the instructor routes if I accidentally changed them? No, instructor routes use current_instructor: User = Depends(get_current_instructor)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Injected get_current_student into practice.py")
