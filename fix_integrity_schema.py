import os
import re

filepath = "backend/app/schemas/enrollment_schema.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("is_online: bool = False\n\n    model_config", "is_online: bool = False\n    academic_integrity_score: float = 100.0\n\n    model_config")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

filepath = "backend/app/services/classroom_service.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('"is_online": user.user_id in online_users,', '"is_online": user.user_id in online_users,\n            "academic_integrity_score": user.academic_integrity_score,')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Added integrity to roster backend")
