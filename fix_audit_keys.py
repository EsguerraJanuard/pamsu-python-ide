import os

filepath = "backend/app/routers/admin.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("log.log_id", "log.audit_id")
content = content.replace("log.status", "log.outcome")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed audit keys")
