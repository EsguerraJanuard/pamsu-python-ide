import os
import re

filepath = "backend/app/routers/admin.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

users_replacement = """@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    users = db.query(User).filter(User.role != "admin").offset(skip).limit(limit).all()
    return users"""

content = re.sub(
    r"@router\.get\(\"/users\", response_model=List\[UserResponse\]\)\ndef list_users\(\n    db: Session = Depends\(get_db\),\n    current_admin: User = Depends\(get_current_admin\),\n\):\n    users = db\.query\(User\)\.filter\(User\.role != \"admin\"\)\.all\(\)\n    return users",
    users_replacement,
    content
)

audit_replacement = """@router.get("/audit-logs")
def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    from app.models.domain_models import AuditRecord
    logs = db.query(AuditRecord).order_by(AuditRecord.occurred_at.desc()).offset(skip).limit(limit).all()
    return logs"""

content = re.sub(
    r"@router\.get\(\"/audit-logs\"\)\ndef get_audit_logs\(\n    db: Session = Depends\(get_db\),\n    current_admin: User = Depends\(get_current_admin\),\n\):\n    from app\.models\.domain_models import AuditRecord\n    logs = db\.query\(AuditRecord\)\.order_by\(AuditRecord\.occurred_at\.desc\(\)\)\.all\(\)\n    return logs",
    audit_replacement,
    content
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated admin.py with skip and limit")
