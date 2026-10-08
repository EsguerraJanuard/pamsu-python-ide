import os

filepath = "backend/app/routers/users.py"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    content = content.replace(
        "def update_integrity_score(\n    payload:\n    # Panel Requirement: Telemetry no longer deducts points.\n    return",
        "def update_integrity_score(\n    payload: IntegrityUpdate,\n    db: Session = Depends(get_db),\n    current_user: User = Depends(get_current_user),\n):\n    # Panel Requirement: Telemetry no longer deducts points.\n    return"
    )
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed users.py syntax")
