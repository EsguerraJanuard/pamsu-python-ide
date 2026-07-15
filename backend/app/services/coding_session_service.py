from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.domain_models import (
    Classroom,
    CodingSession,
    Enrollment,
    Task,
)
from app.schemas.coding_session_schema import (
    CodingSessionActivityUpdate,
)


MAX_DATABASE_COUNTER_VALUE = 2_147_483_647


class CodingSessionServiceError(Exception):
    """Base exception for coding-session workflow errors."""


class CodingSessionTaskUnavailableError(
    CodingSessionServiceError,
):
    """Raised when a student cannot access an activity."""


class CodingSessionNotFoundError(
    CodingSessionServiceError,
):
    """Raised when an owned coding session cannot be found."""


class CodingSessionAccessDeniedError(
    CodingSessionServiceError,
):
    """Raised when an instructor cannot review a coding session."""


class CodingSessionEndedError(
    CodingSessionServiceError,
):
    """Raised when an ended session cannot accept new activity."""


class CodingSessionStateConflictError(
    CodingSessionServiceError,
):
    """Raised when the session lifecycle is inconsistent."""


class CodingSessionCounterOverflowError(
    CodingSessionStateConflictError,
):
    """Raised when a counter would exceed database limits."""


class CodingSessionPersistenceConflictError(
    CodingSessionServiceError,
):
    """Raised when concurrent session data conflicts."""


class CodingSessionPersistenceError(
    CodingSessionServiceError,
):
    """Raised when an unexpected database error occurs."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_database_datetime(
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(
            tzinfo=timezone.utc,
        )

    return value.astimezone(
        timezone.utc,
    )


def _commit_session_transaction(
    db: Session,
) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()

        raise CodingSessionPersistenceConflictError(
            "The coding-session operation conflicted with another database operation."
        ) from error
    except SQLAlchemyError as error:
        db.rollback()

        raise CodingSessionPersistenceError(
            "The coding-session operation could not be saved."
        ) from error


def _get_student_available_task(
    db: Session,
    *,
    student_id: int,
    task_id: int,
) -> Task:
    """
    Resolve a published activity through an active enrollment.

    A generic unavailable result prevents students from discovering
    unpublished activities or classrooms they cannot access.
    """

    task = (
        db.query(Task)
        .join(
            Classroom,
            Task.class_id == Classroom.class_id,
        )
        .join(
            Enrollment,
            Enrollment.class_id == Classroom.class_id,
        )
        .filter(
            Task.task_id == task_id,
            Task.class_id.is_not(None),
            Task.is_published.is_(True),
            Classroom.is_active.is_(True),
            Enrollment.student_id == student_id,
            Enrollment.status == "active",
        )
        .first()
    )

    if task is None:
        raise CodingSessionTaskUnavailableError(
            "The activity is unavailable for a coding session."
        )

    return task


def _get_owned_student_session(
    db: Session,
    *,
    student_id: int,
    session_id: str,
    lock_for_update: bool = False,
) -> CodingSession:
    query = db.query(CodingSession).filter(
        CodingSession.session_id == session_id,
        CodingSession.student_id == student_id,
    )

    if lock_for_update:
        query = query.with_for_update()

    coding_session = query.first()

    if coding_session is None:
        raise CodingSessionNotFoundError("Coding session not found.")

    return coding_session


def _get_instructor_owned_task(
    db: Session,
    *,
    instructor_id: int,
    task_id: int,
) -> Task:
    task = (
        db.query(Task)
        .filter(
            Task.task_id == task_id,
        )
        .first()
    )

    if task is None or task.instructor_id != instructor_id:
        raise CodingSessionAccessDeniedError(
            "You can only review coding sessions for activities that you own."
        )

    return task


def _safe_counter_total(
    *,
    current_value: int,
    increment: int,
    counter_name: str,
) -> int:
    total = current_value + increment

    if total > MAX_DATABASE_COUNTER_VALUE:
        raise CodingSessionCounterOverflowError(
            f"{counter_name} cannot exceed {MAX_DATABASE_COUNTER_VALUE}."
        )

    return total


def start_or_resume_student_coding_session(
    db: Session,
    *,
    student_id: int,
    task_id: int,
) -> CodingSession:
    """
    Start a new coding session or resume the current active session.

    At most one active session is expected for each student and task.
    Existing counters are preserved when an active session is resumed.
    """

    task = _get_student_available_task(
        db,
        student_id=student_id,
        task_id=task_id,
    )

    active_sessions = (
        db.query(CodingSession)
        .filter(
            CodingSession.student_id == student_id,
            CodingSession.task_id == task.task_id,
            CodingSession.ended_at.is_(None),
        )
        .order_by(
            CodingSession.started_at.desc(),
            CodingSession.session_id.desc(),
        )
        .with_for_update()
        .all()
    )

    if len(active_sessions) > 1:
        db.rollback()

        raise CodingSessionStateConflictError(
            "Multiple active coding sessions were detected "
            "for the same student and activity."
        )

    now = _utc_now()

    if active_sessions:
        coding_session = active_sessions[0]
        coding_session.last_activity_at = now

        _commit_session_transaction(db)
        db.refresh(coding_session)

        return coding_session

    coding_session = CodingSession(
        student_id=student_id,
        task_id=task.task_id,
        started_at=now,
        ended_at=None,
        last_activity_at=now,
        tab_switch_count=0,
        blocked_paste_count=0,
        run_attempt_count=0,
        idle_duration_seconds=0,
        last_blocked_paste_at=None,
    )

    db.add(coding_session)

    _commit_session_transaction(db)
    db.refresh(coding_session)

    return coding_session


def list_student_coding_sessions(
    db: Session,
    *,
    student_id: int,
    task_id: int | None = None,
    active_only: bool = False,
) -> list[CodingSession]:
    """
    Return only coding sessions owned by the authenticated student.

    Historical sessions remain visible even when the class or activity
    is no longer active.
    """

    query = db.query(CodingSession).filter(
        CodingSession.student_id == student_id,
    )

    if task_id is not None:
        query = query.filter(
            CodingSession.task_id == task_id,
        )

    if active_only:
        query = query.filter(
            CodingSession.ended_at.is_(None),
        )

    return query.order_by(
        CodingSession.started_at.desc(),
        CodingSession.session_id.desc(),
    ).all()


def get_student_coding_session(
    db: Session,
    *,
    student_id: int,
    session_id: str,
) -> CodingSession:
    return _get_owned_student_session(
        db,
        student_id=student_id,
        session_id=session_id,
    )


def update_student_coding_session_activity(
    db: Session,
    *,
    student_id: int,
    session_id: str,
    activity_data: CodingSessionActivityUpdate,
) -> CodingSession:
    """
    Apply privacy-safe aggregate counter increments.

    The request contains no clipboard text, pasted content, browsing
    information, screen capture, microphone data, webcam data, or
    individual keystrokes.
    """

    coding_session = _get_owned_student_session(
        db,
        student_id=student_id,
        session_id=session_id,
        lock_for_update=True,
    )

    if coding_session.ended_at is not None:
        db.rollback()

        raise CodingSessionEndedError("The coding session has already ended.")

    _get_student_available_task(
        db,
        student_id=student_id,
        task_id=coding_session.task_id,
    )

    now = _utc_now()

    coding_session.tab_switch_count = _safe_counter_total(
        current_value=(coding_session.tab_switch_count),
        increment=(activity_data.tab_switch_increment),
        counter_name="Tab-switch count",
    )

    coding_session.blocked_paste_count = _safe_counter_total(
        current_value=(coding_session.blocked_paste_count),
        increment=(activity_data.blocked_paste_increment),
        counter_name="Blocked-paste count",
    )

    coding_session.idle_duration_seconds = _safe_counter_total(
        current_value=(coding_session.idle_duration_seconds),
        increment=(activity_data.idle_duration_increment_seconds),
        counter_name="Idle-duration total",
    )

    if activity_data.blocked_paste_increment > 0:
        coding_session.last_blocked_paste_at = now

    coding_session.last_activity_at = now

    _commit_session_transaction(db)
    db.refresh(coding_session)

    return coding_session


def end_student_coding_session(
    db: Session,
    *,
    student_id: int,
    session_id: str,
) -> CodingSession:
    """
    End a student-owned coding session.

    Ending is idempotent. Repeating the request returns the already
    ended session without replacing its original end timestamp.
    """

    coding_session = _get_owned_student_session(
        db,
        student_id=student_id,
        session_id=session_id,
        lock_for_update=True,
    )

    if coding_session.ended_at is not None:
        return coding_session

    now = _utc_now()

    coding_session.ended_at = now
    coding_session.last_activity_at = now

    _commit_session_transaction(db)
    db.refresh(coding_session)

    return coding_session


def list_instructor_task_coding_sessions(
    db: Session,
    *,
    instructor_id: int,
    task_id: int,
    student_id: int | None = None,
    active_only: bool = False,
) -> list[CodingSession]:
    task = _get_instructor_owned_task(
        db,
        instructor_id=instructor_id,
        task_id=task_id,
    )

    query = db.query(CodingSession).filter(
        CodingSession.task_id == task.task_id,
    )

    if student_id is not None:
        query = query.filter(
            CodingSession.student_id == student_id,
        )

    if active_only:
        query = query.filter(
            CodingSession.ended_at.is_(None),
        )

    return query.order_by(
        CodingSession.started_at.desc(),
        CodingSession.session_id.desc(),
    ).all()


def get_instructor_coding_session(
    db: Session,
    *,
    instructor_id: int,
    session_id: str,
) -> CodingSession:
    coding_session = (
        db.query(CodingSession)
        .filter(
            CodingSession.session_id == session_id,
        )
        .first()
    )

    if coding_session is None:
        raise CodingSessionNotFoundError("Coding session not found.")

    _get_instructor_owned_task(
        db,
        instructor_id=instructor_id,
        task_id=coding_session.task_id,
    )

    return coding_session


def increment_coding_session_run_attempt(
    db: Session,
    *,
    student_id: int,
    task_id: int,
    session_id: str,
    require_active: bool = True,
    commit: bool = True,
) -> CodingSession:
    """
    Increment the server-controlled execution-attempt counter.

    This function is intended for the execution-request service. The
    public telemetry endpoint must never call it using a client-provided
    run-attempt increment.

    When commit is False, the caller must commit or roll back the shared
    transaction.
    """

    coding_session = (
        db.query(CodingSession)
        .filter(
            CodingSession.session_id == session_id,
            CodingSession.student_id == student_id,
            CodingSession.task_id == task_id,
        )
        .with_for_update()
        .first()
    )

    if coding_session is None:
        raise CodingSessionNotFoundError(
            "The coding session is unavailable for this execution request."
        )

    if require_active and coding_session.ended_at is not None:
        raise CodingSessionEndedError("The coding session has already ended.")

    coding_session.run_attempt_count = _safe_counter_total(
        current_value=(coding_session.run_attempt_count),
        increment=1,
        counter_name="Run-attempt count",
    )

    # An execution request counts as current activity only while the
    # coding session remains active. Historical submit execution
    # requests may still increment the linked session counter without
    # moving last_activity_at beyond ended_at.
    if coding_session.ended_at is None:
        coding_session.last_activity_at = _utc_now()

    if commit:
        _commit_session_transaction(db)
        db.refresh(coding_session)

    return coding_session


# PRIVACY BOUNDARY:
# This service stores only aggregate counters and lifecycle timestamps.
# It never accepts or stores clipboard text, pasted code, browsing
# history, individual keystrokes, screen recordings, webcam data, or
# microphone data.

# REVIEW BOUNDARY:
# Session indicators are informational and instructor-review-only. This
# service does not assign grades, behavior scores, cheating findings,
# plagiarism findings, or misconduct verdicts.
