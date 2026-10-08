import os
import re

filepath = "backend/app/routers/admin.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

audit_replacement = """@router.get("/audit-logs")
def get_global_audit_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    logs = db.query(AuditRecord, User.first_name, User.last_name, User.role).join(
        User, AuditRecord.actor_user_id == User.user_id, isouter=True
    ).order_by(AuditRecord.occurred_at.desc()).offset(skip).limit(limit).all()"""

content = re.sub(
    r"@router\.get\(\"/audit-logs\"\)\ndef get_global_audit_logs\(\n    db: Session = Depends\(get_db\),\n    current_admin: User = Depends\(get_current_admin\),\n\):\n    logs = db\.query\(AuditRecord, User\.first_name, User\.last_name, User\.role\)\.join\(\n        User, AuditRecord\.actor_user_id == User\.user_id, isouter=True\n    \)\.order_by\(AuditRecord\.occurred_at\.desc\(\)\)\.limit\(100\)\.all\(\)",
    audit_replacement,
    content
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated audit-logs with skip and limit")
