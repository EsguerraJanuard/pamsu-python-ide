import os
import re

filepath = "backend/app/routers/instructor.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"\s*if current_user\.role != UserRole\.INSTRUCTOR:\s*raise HTTPException\(status_code=403, detail=\"Not authorized\"\)"
content = re.sub(pattern, "", content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

filepath = "backend/app/routers/practice.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"\s*if current_user\.role != \"student\":\s*raise HTTPException\(status_code=403, detail=\"Access forbidden: student only\"\)"
content = re.sub(pattern, "", content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Removed manual role checks!")
