import logging
import secrets
from datetime import datetime, timezone
from typing import List, Literal, get_args
from uuid import uuid4

from app.core.database import get_db
from app.core.security import get_current_admin, get_password_hash
from app.core.system_settings import (get_all_system_settings,
                                      invalidate_system_settings_cache,
                                      read_stored_system_settings,
                                      set_system_setting)
from app.models.domain_models import (AuditRecord, Classroom, OTPChallenge,
                                      PendingEnrollment, User)
from app.routers.auth import (UNRECOGNIZED_LOGIN_IDENTIFIER,
                              recordable_login_identifier)
from app.schemas.audit_schema import AuditActionType
from app.schemas.enrollment_schema import PendingEnrollmentResult
from app.services.classroom_service import (StudentNotEligibleForEnrollmentError,
                                            apply_pending_enrollments)
from app.schemas.user_schema import UNIVERSITY_EMAIL_DOMAIN
from app.core.system_settings import get_default_ast_strictness
from fastapi import APIRouter, Depends, BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import (BaseModel, ConfigDict, Field, computed_field, field_validator,
                      model_validator)
from sqlalchemy import and_, func, not_, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from app.services.admin_audit_service import (AUDIT_UNAVAILABLE_DETAIL,
                                             AdminAuditError,
                                             record_admin_action,
                                             record_admin_failure,
                                             safe_error_summary)
from app.services.email_service import send_provisioning_email
from app.services.guest_service import (GUEST_EMAIL_PREFIX, is_guest_identity,
                                        is_self_service_guest,
                                        not_self_service_guest)
from app.services.student_provisioning_service import (MAX_MASTERLIST_BYTES,
                                                      MasterlistConflictError,
                                                      MasterlistFileError,
                                                      MasterlistImportResult,
                                                      import_masterlist,
                                                      make_unusable_password_hash,
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
    if log.resource_type != "user" or not (resource_id.isascii() and resource_id.isdigit()):
        return None
    # A failed sign-in names an account only when it was for that account
    # (it is then also the record's actor). Older records of unknown sign-ins
    # can hold digits typed into the email field, such as a password; they
    # must be masked, not read as a user id.
    if log.action_type == "login_failed" and str(log.actor_user_id) != resource_id:
        return None
    return int(resource_id)


def _displayed_resource_id_and_details(log: AuditRecord) -> tuple[str, dict]:
    # Failed logins recorded before the login handler stopped storing
    # unrecognized identifiers can hold whatever was typed into the email
    # field, such as a password. Audit rows are immutable, so they are
    # masked here instead: only well-formed university emails are shown.
    resource_id = log.resource_id
    details = log.audit_data or {}

    if log.action_type != "login_failed":
        return resource_id, details

    if _target_user_id(log) is None and recordable_login_identifier(resource_id) is None:
        resource_id = UNRECOGNIZED_LOGIN_IDENTIFIER

    email = details.get("email")
    if email is not None and not (isinstance(email, str) and recordable_login_identifier(email)):
        details = {key: value for key, value in details.items() if key != "email"}
        details["identifier"] = UNRECOGNIZED_LOGIN_IDENTIFIER

    return resource_id, details


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


# users.name is VARCHAR(150); the separate name fields are joined into it.
MAX_FULL_NAME_LENGTH = 150


class _AccountCreateBase(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    first_name: str = Field(..., min_length=1, max_length=70)
    middle_name: str | None = Field(default=None, max_length=70)
    last_name: str = Field(..., min_length=1, max_length=70)
    password: str = Field(..., min_length=8, max_length=128)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _validate_university_email(value)

    @model_validator(mode="after")
    def validate_full_name_length(self):
        if len(self.full_name) > MAX_FULL_NAME_LENGTH:
            raise ValueError(
                f"The full name must be at most {MAX_FULL_NAME_LENGTH} characters."
            )
        return self

    @property
    def full_name(self) -> str:
        parts = (self.first_name, self.middle_name or "", self.last_name)
        return " ".join(" ".join(parts).split())


STUDENT_SCHOOL_ID_PATTERN = r"^(\d{10}|\d{4}-\d{5})$"


class InstructorCreate(_AccountCreateBase):
    # Optional since 2026-10-22: faculty set their own password through the
    # reset-code flow linked from the welcome email, and the email never
    # carries a password. A password sent by an older client is still set,
    # so MIS can hand it over in person, but it is not emailed either.
    password: str | None = Field(default=None, min_length=8, max_length=128)


class StudentCreate(_AccountCreateBase):
    school_id: str = Field(..., pattern=STUDENT_SCHOOL_ID_PATTERN)
    # Optional since 2026-10-22, as for faculty: the student sets their own
    # password from the welcome email ("Forgot password?"), and the email
    # never carries one. A password sent by an older client is still set,
    # so MIS can hand it over in person, but it is not emailed.
    password: str | None = Field(default=None, min_length=8, max_length=128)


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
    def is_guest(self) -> bool:
        """A self-service guest ("Continue as Guest Student")."""
        return is_guest_identity(role=self.role, email=self.email, school_id=self.school_id)

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


class AccountUpdate(BaseModel):
    """Corrections MIS may make to a faculty or student account."""

    name: str | None = Field(default=None, min_length=1, max_length=MAX_FULL_NAME_LENGTH)
    email: str | None = Field(default=None, min_length=1, max_length=255)
    # Students only: faculty keep their FAC placeholder.
    school_id: str | None = Field(default=None, pattern=STUDENT_SCHOOL_ID_PATTERN)

    # extra="forbid": role, password and status can't be changed here.
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    @field_validator("name")
    @classmethod
    def collapse_name_spaces(cls, value: str | None) -> str | None:
        if value is None:
            return None
        collapsed = " ".join(value.split())
        if not collapsed:
            raise ValueError("The name can't be blank.")
        return collapsed

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        email = _validate_university_email(value)
        if email.startswith(GUEST_EMAIL_PREFIX):
            raise ValueError(f"Addresses starting with {GUEST_EMAIL_PREFIX} are reserved for guest accounts.")
        return email

    @model_validator(mode="after")
    def require_a_change(self):
        if self.name is None and self.email is None and self.school_id is None:
            raise ValueError("Provide a name, an email or a school ID to change.")
        return self


class AccountUpdateResponse(UserResponse):
    changed_fields: List[str]
    # Classes that had queued the corrected email (students only).
    pending_enrollments: PendingEnrollmentResult | None = None


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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if _email_taken(db, request.email) or db.query(User.user_id).filter(User.school_id == request.school_id).first():
        raise HTTPException(status_code=400, detail="Student with this email or school ID already exists")
    
    new_student = User(
        email=request.email,
        name=request.full_name,
        role="student",
        # Without a password the account can't sign in until the student sets
        # one with the reset code (the welcome email links there).
        password_hash=(
            get_password_hash(request.password) if request.password else make_unusable_password_hash()
        ),
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
                "setup_email": "queued_after_commit",
                # Who sets the first password: the student (reset code from the
                # welcome email) or MIS (an older client sent one).
                "sign_in_setup": "set_by_admin" if request.password else "set_by_student",
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
    # Sent only after the commit, like the faculty welcome email. Never a
    # password: it links to "Forgot password?", like masterlist accounts.
    background_tasks.add_task(
        send_provisioning_email,
        new_student.email,
        request.first_name,
        None,
        "Student",
        last_name=request.last_name,
        school_id=new_student.school_id,
    )
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


class PendingEnrollmentRow(BaseModel):
    pending_id: int
    email: str
    class_id: int
    class_name: str
    subject_code: str | None = None
    section: str | None = None
    class_active: bool
    queued_at: datetime
    # The account that uses this email, once MIS has created it.
    user_id: int | None = None
    student_name: str | None = None
    student_active: bool | None = None
    # "Apply" would enroll the student now: an active student account (not a
    # guest) and an active class. Otherwise the row waits.
    ready: bool


class PendingEnrollmentList(BaseModel):
    total: int
    ready: int
    items: List[PendingEnrollmentRow]


def _pending_enrollment_query(db: Session):
    return (
        db.query(PendingEnrollment, Classroom, User)
        .join(Classroom, Classroom.class_id == PendingEnrollment.class_id)
        # Pending rows store the lowercased email; accounts are matched as at login.
        .outerjoin(User, func.lower(User.email) == PendingEnrollment.email)
    )


def _pending_ready_condition():
    return and_(
        User.user_id.is_not(None),
        User.role == "student",
        User.is_active.is_(True),
        Classroom.is_active.is_(True),
        not_self_service_guest(),
    )


@router.get("/pending-enrollments", response_model=PendingEnrollmentList)
def list_pending_enrollments(
    state: Literal["all", "ready", "waiting"] = Query(default="all"),
    q: str | None = Query(default=None, max_length=255, description="Part of the email, class name or code."),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Class enrollments that instructors queued for addresses (enrollment decision 5).

    Admin only: instructors see counts in their bulk-enroll result, never the
    queued addresses. A "ready" row has an active student account and an
    active class, so POST /admin/students/{user_id}/pending-enrollments/apply
    would enroll it now (accounts made before pending rows were applied on
    creation, or classes reactivated since).
    """
    query = _pending_enrollment_query(db)
    if q and q.strip():
        pattern = f"%{q.strip().lower()}%"
        query = query.filter(or_(
            PendingEnrollment.email.like(pattern),
            func.lower(Classroom.name).like(pattern),
            func.lower(func.coalesce(Classroom.subject_code, "")).like(pattern),
            func.lower(func.coalesce(Classroom.section, "")).like(pattern),
        ))

    ready = _pending_ready_condition()
    ready_count = query.filter(ready).count()
    if state == "ready":
        query = query.filter(ready)
    elif state == "waiting":
        query = query.filter(not_(ready))
    total = query.count()

    rows = (
        query.order_by(PendingEnrollment.created_at.desc(), PendingEnrollment.pending_id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    items = []
    for pending, classroom, account in rows:
        is_ready = bool(
            account is not None
            and account.role == "student"
            and account.is_active
            and classroom.is_active
            and not is_self_service_guest(account)
        )
        items.append(PendingEnrollmentRow(
            pending_id=pending.pending_id,
            email=pending.email,
            class_id=classroom.class_id,
            class_name=classroom.name,
            subject_code=classroom.subject_code,
            section=classroom.section,
            class_active=bool(classroom.is_active),
            queued_at=pending.created_at,
            user_id=account.user_id if account else None,
            student_name=account.name if account else None,
            student_active=bool(account.is_active) if account else None,
            ready=is_ready,
        ))
    return PendingEnrollmentList(total=total, ready=ready_count, items=items)


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
        # Without a password the account can't sign in until the instructor
        # sets one with the reset code (the welcome email links there).
        password_hash=(
            get_password_hash(request.password) if request.password else make_unusable_password_hash()
        ),
        school_id=_generate_unused_school_id(db, prefix="FAC"),
        email_verified=True,
        # New instructors start at the admin's default; they can change it.
        ast_strictness_level=get_default_ast_strictness(db),
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
            audit_data={
                "role": "instructor",
                "source": "admin_instructor_form",
                "setup_email": "queued_after_commit",
                # Who sets the first password: the instructor (reset code from the
                # welcome email) or MIS (an older client sent one).
                "sign_in_setup": "set_by_admin" if request.password else "set_by_instructor",
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="User already exists") from exc
    except AdminAuditError as exc:
        raise _audit_unavailable(db, exc) from exc
    db.refresh(new_instructor)
    # Never a password in the email: it links to "Forgot password?", where
    # the instructor gets a one-time code and sets their own.
    background_tasks.add_task(
        send_provisioning_email,
        new_instructor.email,
        request.first_name,
        None,
        "Instructor",
        last_name=request.last_name,
        school_id=new_instructor.school_id,
    )
    return new_instructor

def _like_pattern(text: str) -> str:
    """A LIKE pattern that matches `text` anywhere, with % and _ taken literally."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    include_guests: bool = Query(default=False, description="Also list self-service guest accounts."),
    role: Literal["student", "instructor"] | None = Query(default=None, description="Only accounts with this role."),
    q: str | None = Query(
        default=None, max_length=100, description="Part of the name, email or school ID (any case)."
    ),
    order: Literal["oldest", "newest"] = Query(
        default="oldest", description="'newest' lists the most recently created accounts first."
    ),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    # Search and role run here, over every account, so a match is found
    # without paging through the directory first (alpha tester, 2026-10-28).
    query = db.query(User).filter(User.role != "admin")
    if not include_guests:
        query = query.filter(not_self_service_guest())
    if role:
        query = query.filter(User.role == role)
    search = (q or "").strip().lower()
    if search:
        pattern = _like_pattern(search)
        query = query.filter(
            or_(
                func.lower(User.name).like(pattern, escape="\\"),
                func.lower(User.email).like(pattern, escape="\\"),
                func.lower(User.school_id).like(pattern, escape="\\"),
            )
        )
    # The default stays oldest first: the CSV export pages through it, and
    # accounts created meanwhile then land after the pages already read.
    sort_key = User.user_id.desc() if order == "newest" else User.user_id
    return query.order_by(sort_key).offset(skip).limit(limit).all()

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

@router.patch("/users/{user_id}", response_model=AccountUpdateResponse)
def update_user_account(
    user_id: int,
    request: AccountUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Correct the name or university email of a faculty or student account,
    or a student's school ID.

    The email is the sign-in name and where password-reset codes go, so a
    change also expires any unused reset code sent to the old or the new
    address. For a student, classes that had queued the corrected email are
    joined, as when the account is created. The school ID is the student
    number that MIS masterlists are matched on; faculty accounts keep their
    FAC placeholder.
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        record_admin_failure(
            db, actor_user_id=current_admin.user_id, action_type="user_updated",
            resource_type="user", resource_id=user_id, reason="not_found",
        )
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin" or is_self_service_guest(user):
        record_admin_failure(
            db, actor_user_id=current_admin.user_id, action_type="user_updated",
            resource_type="user", resource_id=user_id, outcome="denied",
            reason="admin_account" if user.role == "admin" else "guest_account",
        )
        if user.role == "admin":
            raise HTTPException(status_code=403, detail="Administrator accounts can't be edited here.")
        raise HTTPException(status_code=403, detail="Guest accounts can't be edited.")

    if request.school_id is not None and user.role != "student":
        record_admin_failure(
            db, actor_user_id=current_admin.user_id, action_type="user_updated",
            resource_type="user", resource_id=user_id, outcome="denied", reason="school_id_not_editable",
        )
        raise HTTPException(status_code=400, detail="Only student school IDs can be changed.")

    changed_fields: list[str] = []
    if request.name is not None and request.name != user.name:
        user.name = request.name
        changed_fields.append("name")

    if request.school_id is not None and request.school_id != user.school_id:
        school_id_in_use = (
            db.query(User.user_id)
            .filter(User.school_id == request.school_id, User.user_id != user.user_id)
            .first()
        )
        if school_id_in_use:
            # Discard a pending name change: the failure record's own commit
            # must not save it.
            db.rollback()
            record_admin_failure(
                db, actor_user_id=current_admin.user_id, action_type="user_updated",
                resource_type="user", resource_id=user_id, reason="school_id_in_use",
            )
            raise HTTPException(status_code=409, detail="Another account already uses this school ID.")
        user.school_id = request.school_id
        changed_fields.append("school_id")

    old_email = (user.email or "").lower()
    if request.email is not None and request.email != old_email:
        email_in_use = (
            db.query(User.user_id)
            .filter(func.lower(User.email) == request.email, User.user_id != user.user_id)
            .first()
        )
        if email_in_use:
            # Discard a pending name change: the failure record's own commit
            # must not save it.
            db.rollback()
            record_admin_failure(
                db, actor_user_id=current_admin.user_id, action_type="user_updated",
                resource_type="user", resource_id=user_id, reason="email_in_use",
            )
            raise HTTPException(status_code=409, detail="Another account already uses this email.")
        user.email = request.email
        changed_fields.append("email")
        db.query(OTPChallenge).filter(
            OTPChallenge.purpose == "password_reset",
            OTPChallenge.consumed_at.is_(None),
            func.lower(OTPChallenge.email).in_([old_email, request.email]),
        ).update({OTPChallenge.consumed_at: datetime.now(timezone.utc)}, synchronize_session=False)

    pending_result = None
    try:
        db.flush()
        if "email" in changed_fields and user.role == "student" and user.is_active:
            pending_result = apply_pending_enrollments(
                db=db,
                student=user,
                actor_user_id=current_admin.user_id,
            )
        if changed_fields:
            # Which fields changed, never their old or new values.
            record_admin_action(
                db,
                actor_user_id=current_admin.user_id,
                action_type="user_updated",
                resource_type="user",
                resource_id=user.user_id,
                audit_data={
                    "role": user.role,
                    "changed_fields": changed_fields,
                    "enrolled_from_pending": len(pending_result.enrolled_class_ids) if pending_result else 0,
                },
            )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Another account already uses this email or school ID.") from exc
    except AdminAuditError as exc:
        raise _audit_unavailable(db, exc) from exc
    except Exception:
        db.rollback()
        raise
    db.refresh(user)
    return AccountUpdateResponse(
        **UserResponse.model_validate(user).model_dump(),
        changed_fields=changed_fields,
        pending_enrollments=pending_result,
    )

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

    targets = _audit_targets(db, [log for log, _, _ in logs])
    return [_audit_log_row(log, name, role, targets=targets) for log, name, role in logs]


AUDIT_ACTION_TYPES = list(get_args(AuditActionType))


def _audit_targets(db: Session, logs: list[AuditRecord]) -> dict[int, tuple[str, str]]:
    """Name and role of the accounts the records are about, by user id."""

    target_ids = {target_id for log in logs if (target_id := _target_user_id(log)) is not None}
    if not target_ids:
        return {}
    return {
        user_id: (target_name, target_role)
        for user_id, target_name, target_role in db.query(User.user_id, User.name, User.role).filter(
            User.user_id.in_(target_ids)
        )
    }


def _audit_log_row(
    log: AuditRecord,
    name: str | None,
    role: str | None,
    email: str | None = None,
    *,
    targets: dict[int, tuple[str, str]],
) -> dict:
    # The target is identified by the stored resource_id, so a deleted
    # account still shows its id (target_exists is then False).
    target_user_id = _target_user_id(log)
    target = targets.get(target_user_id) if target_user_id is not None else None
    resource_id, details = _displayed_resource_id_and_details(log)
    row = {
        "log_id": log.audit_id,
        "action_type": log.action_type,
        "resource_type": log.resource_type,
        "resource_id": resource_id,
        "occurred_at": log.occurred_at,
        "status": log.outcome,
        "actor_name": name if name else "System",
        "actor_role": role if role else "system",
        "target_user_id": target_user_id,
        "target_exists": (target is not None) if target_user_id is not None else None,
        "target_name": target[0] if target else None,
        "target_role": target[1] if target else None,
        # Privacy-validated when the record was written; stored login
        # identifiers are masked by _displayed_resource_id_and_details.
        "details": details,
    }
    if email is not None:
        row["actor_email"] = email
    return row


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


@router.get("/audit-logs/search")
def search_audit_logs(
    page: int = Query(default=1, ge=1, le=100000),
    page_size: int = Query(default=25, ge=5, le=100),
    q: str | None = Query(default=None, max_length=100, description="Part of the actor's name or email."),
    action_type: AuditActionType | None = Query(default=None),
    outcome: Literal["succeeded", "failed", "denied"] | None = Query(default=None),
    actor_role: Literal["admin", "instructor", "student", "system"] | None = Query(default=None),
    occurred_from: datetime | None = Query(default=None, description="Inclusive. Without a time zone, UTC."),
    occurred_to: datetime | None = Query(default=None, description="Exclusive. Without a time zone, UTC."),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Audit records, newest first, with filters and page numbers.

    GET /admin/audit-logs keeps its plain-list shape for older dashboards.
    """
    if occurred_from and occurred_to and _as_utc(occurred_from) >= _as_utc(occurred_to):
        raise HTTPException(status_code=422, detail="The start of the date range must be before its end.")

    query = db.query(AuditRecord, User.name, User.role, User.email).join(
        User, AuditRecord.actor_user_id == User.user_id, isouter=True
    )

    search = (q or "").strip().lower()
    if search:
        pattern = _like_pattern(search)
        query = query.filter(
            or_(
                func.lower(User.name).like(pattern, escape="\\"),
                func.lower(User.email).like(pattern, escape="\\"),
            )
        )
    if action_type:
        query = query.filter(AuditRecord.action_type == action_type)
    if outcome:
        query = query.filter(AuditRecord.outcome == outcome)
    if actor_role == "system":
        query = query.filter(AuditRecord.actor_user_id.is_(None))
    elif actor_role:
        query = query.filter(User.role == actor_role)
    if occurred_from:
        query = query.filter(AuditRecord.occurred_at >= _as_utc(occurred_from))
    if occurred_to:
        query = query.filter(AuditRecord.occurred_at < _as_utc(occurred_to))

    total = query.order_by(None).count()
    rows = (
        query.order_by(AuditRecord.occurred_at.desc(), AuditRecord.audit_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    targets = _audit_targets(db, [log for log, _, _, _ in rows])
    return {
        "items": [_audit_log_row(log, name, role, email or "", targets=targets) for log, name, role, email in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "action_types": AUDIT_ACTION_TYPES,
    }

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

    # Only committed accounts are notified, and no credential is included:
    # masterlist accounts have no password until the student sets one.
    for student in new_users:
        background_tasks.add_task(
            send_provisioning_email,
            student.email,
            student.first_name or student.full_name,
            None,
            "Student",
            last_name=student.last_name if student.first_name else "",
            school_id=student.school_id,
        )
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
        invalidate_system_settings_cache()
    except AdminAuditError as exc:
        unavailable = _audit_unavailable(db, exc)
        invalidate_system_settings_cache()
        raise unavailable from exc
    except SQLAlchemyError as exc:
        db.rollback()
        invalidate_system_settings_cache()
        logger.error("Settings update rolled back (%s).", safe_error_summary(exc))
        record_admin_failure(
            db, actor_user_id=current_admin.user_id, action_type="system_settings_updated",
            resource_type="system_setting", resource_id="global", reason="database_error",
            audit_data={"requested_keys": sorted(requested)},
        )
        raise HTTPException(status_code=503, detail="The settings could not be saved. Nothing was changed.") from exc
    return get_all_system_settings(db)

