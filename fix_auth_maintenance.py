import os

filepath = "backend/app/routers/auth.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

import re

# Add import for global_system_settings
if "from app.routers.admin import global_system_settings" not in content:
    content = content.replace("from fastapi.security import OAuth2PasswordRequestForm", "from fastapi.security import OAuth2PasswordRequestForm\nfrom app.routers.admin import global_system_settings")

# Add maintenance mode block before role check
maintenance_check = """
    if global_system_settings.get("maintenance_mode", False) and user.role == "student":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=("The system is currently undergoing maintenance. Only instructors and MIS personnel can log in at this time."),
        )

    if user.role not in {"""

content = content.replace('    if user.role not in {', maintenance_check)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
