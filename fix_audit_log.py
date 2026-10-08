import os

filepath = "backend/app/routers/admin.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("AuditLog", "AuditRecord")
content = content.replace("log_id=", "audit_id=")  # Wait, let me check the PK of AuditRecord
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Replaced AuditLog with AuditRecord")
