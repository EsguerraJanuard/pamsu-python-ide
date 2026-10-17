import random
from typing import List

from app.core.database import get_db
from app.core.security import get_current_admin, get_password_hash
from app.core.system_settings import get_all_system_settings, set_system_setting
from app.models.domain_models import AuditRecord, Classroom, User
from app.schemas.enrollment_schema import PendingEnrollmentResult
from app.services.classroom_service import (StudentNotEligibleForEnrollmentError,
                                            apply_pending_enrollments)
from fastapi import APIRouter, Depends, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, computed_field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.services.email_service import send_provisioning_email
from app.services.student_provisioning_service import (MasterlistConflictError,
                                                      MasterlistFileError,
                                                      MasterlistImportResult,
                                                      import_masterlist)

router = APIRouter(prefix="/admin", tags=["Admin"])

class InstructorCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str

class StudentCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    school_id: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    email: str
    name: str
    role: str
    school_id: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def first_name(self) -> str:
        parts = self.name.split()
        return parts[0] if parts else ""

    @computed_field
    @property
    def last_name(self) -> str:
        parts = self.name.split()
        return " ".join(parts[1:]) if len(parts) > 1 else ""

class StudentCreateResponse(UserResponse):
    pending_enrollments: PendingEnrollmentResult


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

@router.post("/students", response_model=StudentCreateResponse)
def create_student(
    request: StudentCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    existing = db.query(User).filter((User.email == request.email) | (User.school_id == request.school_id)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student with this email or school ID already exists")
    
    new_student = User(
        email=request.email,
        name=f"{request.first_name} {request.last_name}".strip(),
        role="student",
        password_hash=get_password_hash(request.password),
        school_id=request.school_id,
        email_verified=True,
        is_active=True,
    )
    try:
        db.add(new_student)
        db.flush()
        # Classes that queued this email are joined in the same transaction;
        # any class that cannot be joined stays pending without blocking the account.
        pending_result = apply_pending_enrollments(
            db=db,
            student=new_student,
            actor_user_id=current_admin.user_id,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Student with this email or school ID already exists") from exc
    except Exception:
        db.rollback()
        raise
    db.refresh(new_student)
    return StudentCreateResponse(
        **UserResponse.model_validate(new_student).model_dump(),
        pending_enrollments=pending_result,
    )


@router.post(
    "/students/{user_id}/pending-enrollments/apply",
    response_model=PendingEnrollmentResult,
)
def apply_student_pending_enrollments(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Retry pending enrollments for an existing student account.

    Safe to repeat: consumed rows are gone and existing enrollments are never
    duplicated or changed. Covers accounts created before pending enrollments
    were applied on creation, and classes reactivated after the account was made.
    """
    student = db.query(User).filter(User.user_id == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        result = apply_pending_enrollments(
            db=db,
            student=student,
            actor_user_id=current_admin.user_id,
        )
        db.commit()
    except StudentNotEligibleForEnrollmentError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception:
        db.rollback()
        raise
    return result


class GuestCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str

@router.post("/guests", response_model=UserResponse)
def create_guest(
    request: GuestCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Guest with this email already exists")
    
    new_guest = User(
        email=request.email,
        name=f"{request.first_name} {request.last_name}".strip(),
        role="student",
        password_hash=get_password_hash(request.password),
        school_id=f"GST{random.randint(1000000, 9999999)}",
        email_verified=True
    )
    db.add(new_guest)
    db.commit()
    db.refresh(new_guest)
    return new_guest

@router.post("/instructors", response_model=UserResponse)
def create_instructor(
    request: InstructorCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    new_instructor = User(
        email=request.email,
        name=f"{request.first_name} {request.last_name}".strip(),
        role="instructor",
        password_hash=get_password_hash(request.password),
        school_id=str(random.randint(1000000000, 9999999999)),
        email_verified=True
    )
    db.add(new_instructor)
    db.commit()
    db.refresh(new_instructor)
    background_tasks.add_task(send_provisioning_email, new_instructor.email, request.first_name, request.password, 'Instructor')
    return new_instructor

@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    users = db.query(User).filter(User.role != "admin", ~User.email.startswith("guest_")).offset(skip).limit(limit).all()
    return users

@router.patch("/users/{user_id}/status")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if user_id == current_admin.user_id:
        raise HTTPException(status_code=400, detail="Cannot modify own admin account status")
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
    if user_id == current_admin.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete own admin account")
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
    user.password_version += 1
    db.commit()
    return {"message": "Password reset successfully"}

@router.get("/audit-logs")
def get_global_audit_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    logs = db.query(AuditRecord, User.name, User.role).join(
        User, AuditRecord.actor_user_id == User.user_id, isouter=True
    ).order_by(AuditRecord.occurred_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for log, name, role in logs:
        result.append({
            "log_id": log.audit_id,
            "action_type": log.action_type,
            "resource_type": log.resource_type,
            "occurred_at": log.occurred_at,
            "status": log.outcome,
            "actor_name": name if name else "System",
            "actor_role": role if role else "system"
        })
    return result

@router.post("/students/bulk-register/file", response_model=MasterlistImportResult)
async def bulk_register_students_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Create student accounts from an MIS masterlist (CSV or .xlsx).

    Each row needs email, school_id and a name. Rows are reported as
    created, skipped (account already exists) or failed (with a reason).
    No password is set or sent: students set one through the password-reset
    OTP flow on the sign-in page.
    """
    content = await file.read()
    try:
        result, new_users = import_masterlist(
            db=db,
            content=content,
            filename=file.filename,
            actor_user_id=current_admin.user_id,
        )
    except MasterlistFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MasterlistConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    # Only committed accounts are notified, and no credential is included.
    for new_user in new_users:
        background_tasks.add_task(send_provisioning_email, new_user.email, new_user.name.split()[0], None, 'Student')
    return result

@router.get("/settings")
def get_settings(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    settings = get_all_system_settings(db)
    global_system_settings.update(settings)
    return settings

@router.patch("/settings")
def update_settings(
    request: SettingsUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    set_system_setting(db, "maintenance_mode", request.maintenance_mode)
    set_system_setting(db, "default_ast_strictness", request.default_ast_strictness)
    set_system_setting(db, "registration_enabled", request.registration_enabled)
    global_system_settings["maintenance_mode"] = request.maintenance_mode
    global_system_settings["default_ast_strictness"] = request.default_ast_strictness
    global_system_settings["registration_enabled"] = request.registration_enabled
    return get_all_system_settings(db)

