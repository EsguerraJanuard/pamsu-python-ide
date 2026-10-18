import logging
import secrets
from typing import List, Literal
from uuid import uuid4

from app.core.database import get_db
from app.core.security import get_current_admin, get_password_hash
from app.core.system_settings import (get_all_system_settings,
                                      read_stored_system_settings,
                                      set_system_setting)
from app.models.domain_models import AuditRecord, Classroom, User
from app.schemas.enrollment_schema import PendingEnrollmentResult
from app.services.classroom_service import (StudentNotEligibleForEnrollmentError,
                                            apply_pending_enrollments)
from app.schemas.user_schema import UNIVERSITY_EMAIL_DOMAIN
from fastapi import APIRouter, Depends, BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from app.services.admin_audit_service import (AUDIT_UNAVAILABLE_DETAIL,
                                             AdminAuditError,
                                             record_admin_action,
                                             record_admin_failure,
                                             safe_error_summary)
from app.services.email_service import send_provisioning_email
from app.services.student_provisioning_service import (MAX_MASTERLIST_BYTES,
                                                      MasterlistConflictError,
                                                      MasterlistFileError,
                                                      MasterlistImportResult,
                                                      import_masterlist,
                                                      masterlist_file_type)

router = APIRouter(prefix="/admin", tags=["Admin"])

logger = logging.getLogger(__name__)


def _audit_unavailable(db: Session, error: Exception) -> HTTPException:
    # The change and its audit record share one transaction: roll both back
    # and say so, instead of reporting a change that has no audit record.
    # AdminAuditError text is already reduced to class names (no values).
    db.rollback()
    logger.error("Admin action rolled back: %s", error)
    return HTTPException(status_code=503, detail=AUDIT_UNAVAILABLE_DETAIL)


def _target_user_id(log: AuditRecord) -> int | None:
    resource_id = log.resource_id
    if log.resource_type == "user" and resource_id.isascii() and resource_id.isdigit():
        return int(resource_id)
    return None

def _validate_university_email(value: str) -> str:
    normalized_email = value.strip().lower()
    local_part = normalized_email.removesuffix(UNIVERSITY_EMAIL_DOMAIN)

    if (
        not normalized_email.endswith(UNIVERSITY_EMAIL_DOMAIN)
        or not local_part
        or "@" in local_part
    ):
        raise ValueError("Email must be a valid @pampangastateu.edu.ph address.")

    return normalized_email


class _AccountCreateBase(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    first_name: str = Field(..., min_length=1, max_length=70)
    last_name: str = Field(..., min_length=1, max_length=70)
    password: str = Field(..., min_length=8, max_length=128)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _validate_university_email(value)

    @property
    def full_name(self) -> str:
        return " ".join(f"{self.first_name} {self.last_name}".split())


class InstructorCreate(_AccountCreateBase):
    pass


class StudentCreate(_AccountCreateBase):
    school_id: str = Field(..., pattern=r"^(\d{10}|\d{4}-\d{5})$")


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
    new_password: str = Field(..., min_length=8, max_length=128)

class SettingsUpdate(BaseModel):
    maintenance_mode: bool
    default_ast_strictness: Literal["lax", "moderate", "strict"]
    registration_enabled: bool


def _email_taken(db: Session, email: str) -> bool:
    # Case-insensitive, as at login.
    return db.query(User.user_id).filter(func.lower(User.email) == email).first() is not None


def _generate_unused_school_id(db: Session, prefix: str) -> str:
    """
    A placeholder school_id for accounts the school does not number.

    The letter prefix keeps placeholders from ever matching a real
    all-digit student number from an MIS masterlist.
    """

    digits = 10 - len(prefix)

    for _ in range(10):
        candidate = prefix + "".join(secrets.choice("0123456789") for _ in range(digits))
        if db.query(User.user_id).filter(User.school_id == candidate).first() is None:
            return candidate

    raise HTTPException(status_code=503, detail="Could not allocate an account ID. Please try again.")

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
    if _email_taken(db, request.email) or db.query(User.user_id).filter(User.school_id == request.school_id).first():
        raise HTTPException(status_code=400, detail="Student with this email or school ID already exists")
    
    new_student = User(
        email=request.email,
        name=request.full_name,
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
        record_admin_action(
            db,
            actor_user_id=current_admin.user_id,
            action_type="user_created",
            resource_type="user",
            resource_id=new_student.user_id,
            audit_data={
                "role": "student",
                "source": "admin_student_form",
                "enrolled_from_pending": len(pending_result.enrolled_class_ids),
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Student with this email or school ID already exists") from exc
    except AdminAuditError as exc:
        raise _audit_unavailable(db, exc) from exc
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


class GuestCreate(_AccountCreateBase):
    pass

@router.post("/guests", response_model=UserResponse)
def create_guest(
    request: GuestCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if _email_taken(db, request.email):
        raise HTTPException(status_code=400, detail="Guest with this email already exists")
    
    new_guest = User(
        email=request.email,
        name=request.full_name,
        role="student",
        password_hash=get_password_hash(request.password),
        school_id=_generate_unused_school_id(db, prefix="GST"),
        email_verified=True
    )
    try:
        db.add(new_guest)
        db.flush()
        record_admin_action(
            db,
            actor_user_id=current_admin.user_id,
            action_type="user_created",
            resource_type="user",
            resource_id=new_guest.user_id,
            audit_data={"role": "student", "source": "admin_guest_form", "guest": True},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Guest with this email already exists") from exc
    except AdminAuditError as exc:
        raise _audit_unavailable(db, exc) from exc
    db.refresh(new_guest)
    return new_guest

@router.post("/instructors", response_model=UserResponse)
def create_instructor(
    request: InstructorCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if _email_taken(db, request.email):
        raise HTTPException(status_code=400, detail="User already exists")
    
    new_instructor = User(
        email=request.email,
        name=request.full_name,
        role="instructor",
        password_hash=get_password_hash(request.password),
        school_id=_generate_unused_school_id(db, prefix="FAC"),
        email_verified=True
    )
    try:
        db.add(new_instructor)
        db.flush()
        record_admin_action(
            db,
            actor_user_id=current_admin.user_id,
            action_type="user_created",
            resource_type="user",
            resource_id=new_instructor.user_id,
            # The welcome email is only queued here; its delivery is not audited.
            audit_data={"role": "instructor", "source": "admin_instructor_form", "setup_email": "queued_after_commit"},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="User already exists") from exc
    except AdminAuditError as exc:
        raise _audit_unavailable(db, exc) from exc
    db.refresh(new_instructor)
    background_tasks.add_task(send_provisioning_email, new_instructor.email, request.first_name, request.password, 'Instructor')
    return new_instructor

@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
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
        record_admin_failure(
            db, actor_user_id=current_admin.user_id, action_type="user_status_changed",
            resource_type="user", resource_id=user_id, outcome="denied", reason="own_account",
        )
        raise HTTPException(status_code=400, detail="Cannot modify own admin account status")
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        record_admin_failure(
            db, actor_user_id=current_admin.user_id, action_type="user_status_changed",
            resource_type="user", resource_id=user_id, reason="not_found",
        )
        raise HTTPException(status_code=404, detail="User not found")
    previous = bool(user.is_active)
    try:
        user.is_active = not previous
        record_admin_action(
            db,
            actor_user_id=current_admin.user_id,
            action_type="user_status_changed",
            resource_type="user",
            resource_id=user.user_id,
            audit_data={"role": user.role, "previous_is_active": previous, "is_active": not previous},
        )
        db.commit()
    except AdminAuditError as exc:
        raise _audit_unavailable(db, exc) from exc
    return {"message": "Status updated", "is_active": user.is_active}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if user_id == current_admin.user_id:
        record_admin_failure(
            db, actor_user_id=current_admin.user_id, action_type="user_deleted",
            resource_type="user", resource_id=user_id, outcome="denied", reason="own_account",
        )
        raise HTTPException(status_code=400, detail="Cannot delete own admin account")
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        record_admin_failure(
            db, actor_user_id=current_admin.user_id, action_type="user_deleted",
            resource_type="user", resource_id=user_id, reason="not_found",
        )
        raise HTTPException(status_code=404, detail="User not found")
    # The record keeps the internal id (resource_id) and the role only; the
    # deleted account's email and school ID are deliberately not retained.
    target_role = user.role
    try:
        record_admin_action(
            db,
            actor_user_id=current_admin.user_id,
            action_type="user_deleted",
            resource_type="user",
            resource_id=user.user_id,
            audit_data={"role": target_role, "was_active": bool(user.is_active)},
        )
        db.delete(user)
        db.commit()
    except IntegrityError as exc:
        # Classrooms, submissions, grades and audit records reference the
        # account and are kept (RESTRICT). Such accounts are deactivated.
        db.rollback()
        record_admin_failure(
            db, actor_user_id=current_admin.user_id, action_type="user_deleted",
            resource_type="user", resource_id=user_id, reason="has_dependent_records",
            audit_data={"role": target_role},
        )
        raise HTTPException(
            status_code=409,
            detail="This account has academic or audit records and cannot be deleted. Deactivate it instead.",
        ) from exc
    except AdminAuditError as exc:
        raise _audit_unavailable(db, exc) from exc
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
        record_admin_failure(
            db, actor_user_id=current_admin.user_id, action_type="user_password_reset",
            resource_type="user", resource_id=user_id, reason="not_found",
        )
        raise HTTPException(status_code=404, detail="User not found")
    try:
        user.password_hash = get_password_hash(request.new_password)
        user.password_version += 1
        # Never the password or its hash: only the new version number, which
        # also invalidates every session issued before the reset.
        record_admin_action(
            db,
            actor_user_id=current_admin.user_id,
            action_type="user_password_reset",
            resource_type="user",
            resource_id=user.user_id,
            audit_data={"role": user.role, "password_version": user.password_version},
        )
        db.commit()
    except AdminAuditError as exc:
        raise _audit_unavailable(db, exc) from exc
    return {"message": "Password reset successfully"}

@router.get("/audit-logs")
def get_global_audit_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    # audit_id breaks ties: records written in one transaction share
    # occurred_at on PostgreSQL (now() is the transaction start time).
    logs = db.query(AuditRecord, User.name, User.role).join(
        User, AuditRecord.actor_user_id == User.user_id, isouter=True
    ).order_by(AuditRecord.occurred_at.desc(), AuditRecord.audit_id.desc()).offset(skip).limit(limit).all()

    # The target is identified by the stored resource_id, so a deleted
    # account still shows its id (target_exists is then False).
    target_ids = {target_id for log, _, _ in logs if (target_id := _target_user_id(log)) is not None}
    targets = {
        user_id: (target_name, target_role)
        for user_id, target_name, target_role in db.query(User.user_id, User.name, User.role).filter(
            User.user_id.in_(target_ids)
        )
    } if target_ids else {}

    result = []
    for log, name, role in logs:
        target_user_id = _target_user_id(log)
        target = targets.get(target_user_id) if target_user_id is not None else None
        result.append({
            "log_id": log.audit_id,
            "action_type": log.action_type,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "occurred_at": log.occurred_at,
            "status": log.outcome,
            "actor_name": name if name else "System",
            "actor_role": role if role else "system",
            "target_user_id": target_user_id,
            "target_exists": (target is not None) if target_user_id is not None else None,
            "target_name": target[0] if target else None,
            "target_role": target[1] if target else None,
            # Privacy-validated when the record was written.
            "details": log.audit_data or {},
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
    # Read one byte past the limit so an oversized file is rejected without
    # buffering all of it; parsing and database work run off the event loop.
    content = await file.read(MAX_MASTERLIST_BYTES + 1)
    import_id = str(uuid4())
    failure_data = {"file_type": masterlist_file_type(file.filename)}
    try:
        result, new_users = await run_in_threadpool(
            import_masterlist,
            db=db,
            content=content,
            filename=file.filename,
            actor_user_id=current_admin.user_id,
            import_id=import_id,
        )
    except MasterlistFileError as exc:
        await run_in_threadpool(
            record_admin_failure, db, actor_user_id=current_admin.user_id, action_type="masterlist_imported",
            resource_type="masterlist_import", resource_id=import_id, reason="invalid_file", audit_data=failure_data,
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MasterlistConflictError as exc:
        await run_in_threadpool(
            record_admin_failure, db, actor_user_id=current_admin.user_id, action_type="masterlist_imported",
            resource_type="masterlist_import", resource_id=import_id, reason="database_conflict", audit_data=failure_data,
        )
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AdminAuditError as exc:
        # import_masterlist already rolled back: no account was created.
        logger.error("Masterlist import rolled back: %s", exc)
        raise HTTPException(status_code=503, detail=AUDIT_UNAVAILABLE_DETAIL) from exc

    # Only committed accounts are notified, and no credential is included.
    for new_user in new_users:
        background_tasks.add_task(send_provisioning_email, new_user.email, new_user.name.split()[0], None, 'Student')
    return result

@router.get("/settings")
def get_settings(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return get_all_system_settings(db)

@router.patch("/settings")
def update_settings(
    request: SettingsUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    requested = request.model_dump()
    try:
        current = read_stored_system_settings(db)
        changes = {
            key: {"from": current.get(key), "to": value}
            for key, value in requested.items()
            if current.get(key) != value
        }
        # All keys and the audit record are committed together, so a failure
        # leaves every setting as it was instead of a partial update.
        for key, value in requested.items():
            set_system_setting(db, key, value, commit=False)
        if changes:
            record_admin_action(
                db,
                actor_user_id=current_admin.user_id,
                action_type="system_settings_updated",
                resource_type="system_setting",
                resource_id="global",
                audit_data={"changes": changes},
            )
        db.commit()
    except AdminAuditError as exc:
        raise _audit_unavailable(db, exc) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Settings update rolled back (%s).", safe_error_summary(exc))
        record_admin_failure(
            db, actor_user_id=current_admin.user_id, action_type="system_settings_updated",
            resource_type="system_setting", resource_id="global", reason="database_error",
            audit_data={"requested_keys": sorted(requested)},
        )
        raise HTTPException(status_code=503, detail="The settings could not be saved. Nothing was changed.") from exc
    return get_all_system_settings(db)

