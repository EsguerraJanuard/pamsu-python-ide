"""
Self-service guest accounts ("Continue as Guest Student" on the login page).

Owner decisions (2026-10-19, backend audit "Still open" item 4):
- the public button stays, with a cap on new guests per rolling 24 hours;
- guests stay in the Guest Sandbox Classroom and cannot join real classes;
- a guest stops working 7 days after creation (deactivated, never deleted,
  so its history stays intact);
- the sandbox classroom is owned by an admin account, so it never appears
  in an instructor's dashboard.

Guests created by an admin (POST /admin/guests) are not self-service guests
and keep the normal student rules.
"""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.domain_models import Classroom, User
from app.schemas.user_schema import UNIVERSITY_EMAIL_DOMAIN
from app.services.audit_service import create_audit_record
from app.services.student_provisioning_service import make_unusable_password_hash
from sqlalchemy import and_, not_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

GUEST_EMAIL_PREFIX = "guest_"
GUEST_SCHOOL_ID_PREFIX = "GST"
GUEST_DAILY_LIMIT = 100
GUEST_LIFETIME = timedelta(days=7)

SANDBOX_CLASS_CODE = "SANDBOX01"

GUEST_LIMIT_REACHED_DETAIL = (
    "Guest access has reached today's limit. Please sign in with your university account."
)
GUEST_EXPIRED_DETAIL = "This guest account has expired. Start a new guest session or sign in."
GUEST_CANNOT_JOIN_DETAIL = (
    "Guest accounts can only use the Guest Sandbox Classroom. "
    "Sign in with your university account to join a class."
)


def _is_guest_identity(email: str, school_id: str) -> bool:
    return (
        email.startswith(GUEST_EMAIL_PREFIX)
        and email.endswith(UNIVERSITY_EMAIL_DOMAIN)
        and school_id.startswith(GUEST_SCHOOL_ID_PREFIX)
    )


def is_self_service_guest(user: User) -> bool:
    return user.role == "student" and _is_guest_identity(user.email or "", user.school_id or "")


def self_service_guest_filter():
    return (
        User.role == "student",
        # "_" is a LIKE wildcard, so it is escaped.
        User.email.like("guest\\_%", escape="\\"),
        User.email.like(f"%{UNIVERSITY_EMAIL_DOMAIN}"),
        User.school_id.like(f"{GUEST_SCHOOL_ID_PREFIX}%"),
    )


def not_self_service_guest():
    return not_(and_(*self_service_guest_filter()))


def _as_utc(value: datetime) -> datetime:
    # SQLite returns naive UTC timestamps; PostgreSQL returns aware ones.
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def guest_has_expired(user: User, now: datetime | None = None) -> bool:
    if not is_self_service_guest(user) or user.created_at is None:
        return False

    now = now or datetime.now(timezone.utc)
    return _as_utc(user.created_at) <= now - GUEST_LIFETIME


def guest_limit_reached(db: Session, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    created_last_day = (
        db.query(User.user_id)
        .filter(*self_service_guest_filter(), User.created_at > now - timedelta(days=1))
        .count()
    )
    return created_last_day >= GUEST_DAILY_LIMIT


def deactivate_expired_guests(db: Session, now: datetime | None = None) -> int:
    """Flush-only: deactivates self-service guests older than GUEST_LIFETIME."""

    now = now or datetime.now(timezone.utc)
    result = db.execute(
        update(User)
        .where(*self_service_guest_filter(), User.is_active.is_(True), User.created_at <= now - GUEST_LIFETIME)
        .values(is_active=False)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount or 0


def _unused_guest_school_id(db: Session) -> str:
    for _ in range(10):
        candidate = GUEST_SCHOOL_ID_PREFIX + "".join(secrets.choice("0123456789") for _ in range(7))
        if db.query(User.user_id).filter(User.school_id == candidate).first() is None:
            return candidate
    raise RuntimeError("Could not allocate a guest school ID.")


def create_self_service_guest(db: Session) -> User:
    """Create and commit one guest; expired guests are deactivated in the same commit."""

    deactivate_expired_guests(db)

    short_id = secrets.token_hex(6)
    guest = User(
        email=f"{GUEST_EMAIL_PREFIX}{short_id}{UNIVERSITY_EMAIL_DOMAIN}",
        name=f"Guest {short_id[:6].upper()}",
        role="student",
        # Guests sign in only through /guest. No password can ever verify
        # against this marker, and it costs no bcrypt work per guest.
        password_hash=make_unusable_password_hash(),
        school_id=_unused_guest_school_id(db),
        # Guests have no university mailbox to verify.
        email_verified=True,
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest


def _sandbox_owner(db: Session) -> User | None:
    return (
        db.query(User)
        .filter(User.role == "admin", User.is_active.is_(True))
        .order_by(User.user_id)
        .first()
    )


def get_or_create_sandbox_classroom(db: Session) -> Classroom | None:
    """
    The admin-owned Guest Sandbox Classroom, created on first use.

    An existing sandbox owned by an instructor (created before this rule) is
    moved to an admin, with an audit record. Returns None if no active admin
    exists. Commits its own changes.
    """

    sandbox = db.query(Classroom).filter(Classroom.class_code == SANDBOX_CLASS_CODE).first()
    owner = _sandbox_owner(db)

    if owner is None:
        return sandbox

    if sandbox is None:
        sandbox = Classroom(
            name="Guest Sandbox Classroom",
            subject_code="DEMO101",
            section="Sandbox",
            class_code=SANDBOX_CLASS_CODE,
            instructor_id=owner.user_id,
            is_active=True,
        )
        db.add(sandbox)
        try:
            db.commit()
        except IntegrityError:
            # Another guest created it at the same moment: use that one.
            db.rollback()
            return db.query(Classroom).filter(Classroom.class_code == SANDBOX_CLASS_CODE).first()
        db.refresh(sandbox)
        return sandbox

    current_owner_role = (
        db.query(User.role).filter(User.user_id == sandbox.instructor_id).scalar()
    )
    if current_owner_role != "admin":
        sandbox.instructor_id = owner.user_id
        create_audit_record(
            db,
            {
                "audit_key": f"audit:classroom_updated:classroom:{sandbox.class_id}:{uuid4()}",
                "actor_user_id": None,
                "action_type": "classroom_updated",
                "resource_type": "classroom",
                "resource_id": str(sandbox.class_id),
                "outcome": "succeeded",
                "audit_data": {
                    "changed_fields": ["instructor_id"],
                    "reason": "guest_sandbox_owned_by_admin",
                    "previous_owner_role": current_owner_role,
                },
            },
            commit=False,
        )
        db.commit()

    return sandbox
