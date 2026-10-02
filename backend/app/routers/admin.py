from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from app.core.database import get_db
from app.core.security import get_current_admin, get_password_hash
from app.models.domain_models import User, Classroom, AuditRecord
from pydantic import BaseModel
import re
import random

router = APIRouter(prefix="/admin", tags=["Admin"])

class InstructorCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    email: str
    first_name: str
    last_name: str
    role: str
    school_id: str | None = None
    is_active: bool

    class Config:
        from_attributes = True

class PasswordReset(BaseModel):
    new_password: str

class SettingsUpdate(BaseModel):
    maintenance_mode: bool
    default_ast_strictness: str
    registration_enabled: bool

# Global mock settings for MVP
global_system_settings = {
    "maintenance_mode": False,
    "default_ast_strictness": "moderate",
    "registration_enabled": False
}

@router.get("/stats")
def get_system_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    total_instructors = db.query(User).filter(User.role == "instructor").count()
    total_students = db.query(User).filter(User.role == "student").count()
    total_classrooms = db.query(Classroom).count()
    
    return {
        "total_instructors": total_instructors,
        "total_students": total_students,
        "total_classrooms": total_classrooms
    }

@router.post("/instructors", response_model=UserResponse)
def create_instructor(
    request: InstructorCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    new_instructor = User(
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        role="instructor",
        password_hash=get_password_hash(request.password),
        school_id=str(random.randint(1000000000, 9999999999)),
        email_verified=True
    )
    db.add(new_instructor)
    db.commit()
    db.refresh(new_instructor)
    return new_instructor

@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    users = db.query(User).filter(User.role != "admin").all()
    return users

@router.patch("/users/{user_id}/status")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.commit()
    return {"message": "Status updated", "is_active": user.is_active}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}

@router.patch("/users/{user_id}/password")
def reset_user_password(
    user_id: int,
    request: PasswordReset,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = get_password_hash(request.new_password)
    db.commit()
    return {"message": "Password reset successfully"}

@router.get("/audit-logs")
def get_global_audit_logs(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    logs = db.query(AuditRecord, User.first_name, User.last_name, User.role).join(
        User, AuditRecord.actor_user_id == User.user_id, isouter=True
    ).order_by(AuditRecord.occurred_at.desc()).limit(100).all()
    
    result = []
    for log, fname, lname, role in logs:
        result.append({
            "log_id": log.audit_id,
            "action_type": log.action_type,
            "resource_type": log.resource_type,
            "occurred_at": log.occurred_at,
            "status": log.outcome,
            "actor_name": f"{fname} {lname}" if fname else "System",
            "actor_role": role if role else "system"
        })
    return result

@router.post("/students/bulk-register/file")
async def bulk_register_students_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    content = await file.read()
    text = content.decode("utf-8")
    
    emails = []
    for line in text.splitlines():
        line = line.strip()
        if not line or "@" not in line:
            continue
        match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', line)
        if match:
            emails.append(match.group(0).lower())
            
    emails = list(set(emails))
    valid_emails = [e for e in emails if e.endswith("@pampangastateu.edu.ph")]
    
    if not valid_emails:
        return {"registered": 0, "invalid": len(emails)}
        
    existing_users = db.query(User).filter(User.email.in_(valid_emails)).all()
    existing_emails = {u.email for u in existing_users}
    
    registered_count = 0
    
    for email in valid_emails:
        if email not in existing_emails:
            new_user = User(
                email=email,
                first_name=email.split("@")[0].replace(".", " ").title(),
                last_name="Student",
                role="student",
                password_hash=get_password_hash("PamsU@2026"),
                school_id=str(random.randint(1000000000, 9999999999)),
                email_verified=True
            )
            db.add(new_user)
            registered_count += 1
            
    db.commit()
    return {"registered": registered_count, "invalid": len(emails) - len(valid_emails)}

@router.get("/settings")
def get_settings(current_admin: User = Depends(get_current_admin)):
    return global_system_settings

@router.patch("/settings")
def update_settings(request: SettingsUpdate, current_admin: User = Depends(get_current_admin)):
    global_system_settings["maintenance_mode"] = request.maintenance_mode
    global_system_settings["default_ast_strictness"] = request.default_ast_strictness
    global_system_settings["registration_enabled"] = request.registration_enabled
    return global_system_settings


@router.get("/seed-production")
def seed_production_admin(db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == "admin@pampangastateu.edu.ph").first()
    if existing:
        return {"message": "Admin already exists in this database!"}
    
    admin = User(
        email="admin@pampangastateu.edu.ph",
        first_name="System",
        last_name="Administrator",
        middle_name="",
        role="admin",
        password_hash=get_password_hash("Admin@2026"),
        school_id="0000000000",
        email_verified=True
    )
    db.add(admin)
    db.commit()
    return {"message": "Admin account successfully seeded into production database!"}
