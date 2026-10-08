import os
import re

filepath = "backend/app/routers/auth.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

if "global_system_settings" not in content:
    content = re.sub(
        r"(from fastapi.security import OAuth2PasswordRequestForm)",
        r"\1\nfrom app.routers.admin import global_system_settings",
        content
    )

maintenance_check = """
    if global_system_settings.get("maintenance_mode", False) and user.role == "student":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=("The system is currently undergoing maintenance. Only instructors and MIS personnel can log in at this time."),
        )

    if user.role not in {"""

content = re.sub(r"\s+if user\.role not in \{", maintenance_check, content, count=1)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Maintenance check injected")
