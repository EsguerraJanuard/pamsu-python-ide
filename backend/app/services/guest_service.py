"""
Self-service guest accounts ("Continue as Guest Student" on the login page).

Owner decisions (2026-10-19, backend audit "Still open" item 4):
- the public button stays, with a cap on new guests per rolling 24 hours;
- guests stay in the Guest Sandbox Classroom and cannot join real classes;
- the sandbox classroom is owned by an admin account, so it never appears
  in an instructor's dashboard.

Changed 2026-10-24 (Januard): a guest is deleted 24 hours after creation,
with everything it created (enrollment, coding sessions, runs, submissions
and their evaluations, notifications, and the audit and academic records it
is the actor of), so guests cannot fill the free-tier database. This
replaces "deactivated after 7 days, never deleted". The shared sandbox and
its demo activity stay. Guests can never be bound to a permanent account:
accounts come only from MIS.

Guests created by an admin (POST /admin/guests) are not self-service guests
and keep the normal student rules.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.domain_models import (AcademicEvent, ASTAnalysis, ASTFinding,
                                      AuditRecord, BehavioralLog, Classroom,
                                      CodingSession, Enrollment,
                                      ExecutionRequest, InstructorGrade,
                                      Notification,
                                      PartnerExecutionUpdateRecord,
                                      PracticeAttempt, PracticeProgress,
                                      SimilarityResult, Submission, Task,
                                      TaskTestCase, User)
from app.schemas.user_schema import UNIVERSITY_EMAIL_DOMAIN
from app.services.audit_service import create_audit_record
from app.services.student_provisioning_service import make_unusable_password_hash
from sqlalchemy import and_, delete, not_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

GUEST_EMAIL_PREFIX = "guest_"
GUEST_SCHOOL_ID_PREFIX = "GST"
GUEST_DAILY_LIMIT = 100
GUEST_LIFETIME = timedelta(hours=24)
# Expired guests deleted per new guest sign-in. New guests are capped at
# GUEST_DAILY_LIMIT a day, so cleanup always keeps up, and a batch stays a
# few quick bulk deletes inside the sign-in request (3-second rule).
GUEST_CLEANUP_BATCH = 50

SANDBOX_CLASS_CODE = "SANDBOX01"

# The sandbox's ready-made activity, so a guest can try the workspace (Run,
# structure check, submit) and produce review indicators straight away.
DEMO_ACTIVITY_TITLE = "Python Basics: For Loop"
DEMO_ACTIVITY = {
    "title": DEMO_ACTIVITY_TITLE,
    "description": (
        "A short sample activity: count down with a for loop. Guest accounts and "
        "their work are deleted 24 hours after the guest session starts."
    ),
    "scenario": "Mission control needs a program that prints the countdown before a launch.",
    # Plain text: the workspace shows instructions as written (no Markdown),
    # and lists the sample input and expected output under them.
    "instructions": (
        "Read a whole number n from input. Use a for loop to print a countdown from n "
        "down to 1, one number per line, then print Liftoff! on the last line.\n\n"
        "Select Run to try your code with the sample input, Check structure to see "
        "whether your code has the required for loop and print() call, and Submit "
        "when you are done."
    ),
    "solution_explanation": (
        "range(n, 0, -1) starts at n and counts down by 1, stopping before 0, so the "
        "loop prints n, n - 1, ..., 1. The final print(\"Liftoff!\") comes after the "
        "loop, so it runs once."
    ),
    "activity_type": "laboratory",
    "difficulty": "beginner",
    "required_ast_rules": {"require_for_loop": 1, "require_print_call": 1},
    "starter_code": "n = int(input())\n\n# Use a for loop to count down from n to 1, then print Liftoff!\n",
    # Workspace copy and paste work; pastes from outside are blocked and counted.
    "paste_policy": "internal_only",
    "is_graded": True,
}
DEMO_TEST_CASES = (
    {"name": "Sample: countdown from 5", "standard_input": "5\n",
     "expected_output": "5\n4\n3\n2\n1\nLiftoff!\n", "is_hidden": False},
    {"name": "Countdown from 3", "standard_input": "3\n",
     "expected_output": "3\n2\n1\nLiftoff!\n", "is_hidden": True},
)

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


def is_guest_identity(*, role: str | None, email: str | None, school_id: str | None) -> bool:
    """is_self_service_guest() for plain values (API responses, imports)."""
    return role == "student" and _is_guest_identity(email or "", school_id or "")


def is_self_service_guest(user: User) -> bool:
    return is_guest_identity(role=user.role, email=user.email, school_id=user.school_id)


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


def _delete_guest_rows(db: Session, guest_ids: list[int]) -> None:
    """
    Delete the guests and every row that belongs to them. Most foreign keys
    to users, submissions and runs are ON DELETE RESTRICT, so children go
    first. Only self-service guests' own rows are touched: records written by
    other people about them (an admin's grade audit, say) stay.
    """

    def run(statement) -> None:
        db.execute(statement.execution_options(synchronize_session=False))

    submissions = select(Submission.sub_id).where(Submission.student_id.in_(guest_ids))
    executions = select(ExecutionRequest.execution_id).where(ExecutionRequest.student_id.in_(guest_ids))
    analyses = select(ASTAnalysis.analysis_id).where(
        or_(ASTAnalysis.submission_id.in_(submissions), ASTAnalysis.execution_id.in_(executions))
    )
    events = select(AcademicEvent.event_id).where(AcademicEvent.actor_user_id.in_(guest_ids))

    run(delete(ASTFinding).where(ASTFinding.analysis_id.in_(analyses)))
    run(delete(ASTAnalysis).where(
        or_(ASTAnalysis.submission_id.in_(submissions), ASTAnalysis.execution_id.in_(executions))
    ))
    run(delete(PartnerExecutionUpdateRecord).where(PartnerExecutionUpdateRecord.execution_id.in_(executions)))
    run(delete(SimilarityResult).where(or_(
        SimilarityResult.source_submission_id.in_(submissions),
        SimilarityResult.compared_submission_id.in_(submissions),
    )))
    run(delete(InstructorGrade).where(InstructorGrade.submission_id.in_(submissions)))
    run(delete(BehavioralLog).where(BehavioralLog.sub_id.in_(submissions)))
    run(delete(ExecutionRequest).where(ExecutionRequest.student_id.in_(guest_ids)))
    run(delete(Submission).where(Submission.student_id.in_(guest_ids)))
    run(delete(CodingSession).where(CodingSession.student_id.in_(guest_ids)))
    run(delete(Notification).where(or_(Notification.recipient_id.in_(guest_ids), Notification.event_id.in_(events))))
    run(delete(AcademicEvent).where(AcademicEvent.actor_user_id.in_(guest_ids)))
    run(delete(AuditRecord).where(AuditRecord.actor_user_id.in_(guest_ids)))
    run(delete(Enrollment).where(Enrollment.student_id.in_(guest_ids)))
    run(delete(PracticeAttempt).where(PracticeAttempt.student_id.in_(guest_ids)))
    run(delete(PracticeProgress).where(PracticeProgress.student_id.in_(guest_ids)))
    run(delete(User).where(User.user_id.in_(guest_ids)))


def delete_expired_guests(db: Session, now: datetime | None = None, limit: int = GUEST_CLEANUP_BATCH) -> int:
    """
    Flush-only: deletes up to `limit` self-service guests older than
    GUEST_LIFETIME, with all their data. Returns how many were deleted.
    """

    now = now or datetime.now(timezone.utc)
    guest_ids = [
        user_id
        for (user_id,) in db.query(User.user_id)
        .filter(*self_service_guest_filter(), User.created_at <= now - GUEST_LIFETIME)
        .order_by(User.user_id)
        .limit(limit)
    ]
    if not guest_ids:
        return 0

    _delete_guest_rows(db, guest_ids)
    logger.info("Deleted %d expired guest account(s) and their data.", len(guest_ids))
    return len(guest_ids)


def _unused_guest_school_id(db: Session) -> str:
    for _ in range(10):
        candidate = GUEST_SCHOOL_ID_PREFIX + "".join(secrets.choice("0123456789") for _ in range(7))
        if db.query(User.user_id).filter(User.school_id == candidate).first() is None:
            return candidate
    raise RuntimeError("Could not allocate a guest school ID.")


def create_self_service_guest(db: Session) -> User:
    """Create and commit one guest; expired guests are deleted in the same commit."""

    delete_expired_guests(db)

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


def _demo_activity(db: Session, sandbox: Classroom) -> Task | None:
    return (
        db.query(Task)
        .filter(Task.class_id == sandbox.class_id, Task.title == DEMO_ACTIVITY_TITLE)
        .order_by(Task.task_id)
        .first()
    )


def ensure_sandbox_demo_activity(db: Session, sandbox: Classroom) -> Task:
    """
    Give the sandbox its published demo activity if it has none, so a guest
    can use the workspace right away. Found by title in the sandbox, so an
    admin's edits (or unpublishing it) are kept, and the sandbox that already
    exists in production gets it on the next guest sign-in. Commits.
    """

    existing = _demo_activity(db, sandbox)
    if existing is not None:
        return existing

    # Two first guests at once must not both add it: lock the sandbox row and
    # look again (PostgreSQL; SQLite runs one writer at a time anyway).
    db.query(Classroom).filter(Classroom.class_id == sandbox.class_id).with_for_update().one()
    existing = _demo_activity(db, sandbox)
    if existing is not None:
        db.commit()
        return existing

    now = datetime.now(timezone.utc)
    task = Task(
        class_id=sandbox.class_id,
        instructor_id=sandbox.instructor_id,
        is_published=True,
        published_at=now,
        due_at=None,
        **DEMO_ACTIVITY,
    )
    db.add(task)
    db.flush()
    db.add_all(
        TaskTestCase(task_id=task.task_id, display_order=order, **case)
        for order, case in enumerate(DEMO_TEST_CASES)
    )
    create_audit_record(
        db,
        {
            "audit_key": f"audit:activity_created:task:{task.task_id}",
            "actor_user_id": None,
            "action_type": "activity_created",
            "resource_type": "task",
            "resource_id": str(task.task_id),
            "outcome": "succeeded",
            "audit_data": {
                "class_id": sandbox.class_id,
                "activity_type": task.activity_type,
                "is_graded": task.is_graded,
                "is_published": True,
                "paste_policy": task.paste_policy,
                "reason": "guest_sandbox_demo_activity",
            },
        },
        commit=False,
    )
    db.commit()
    db.refresh(task)
    return task
