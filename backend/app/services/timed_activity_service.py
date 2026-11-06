"""
Timed activities: one server-side timer window per student.

The window is written when the student chooses "Start Now" and is never
changed, so the timer runs on while the tab is closed or reloaded: it
cannot be paused. Submissions are checked against it (see
submission_service), not against anything the browser reports.

A window ends at started_at + its time limit, or at the activity's
deadline if that comes first. A window opened through "Allow another
attempt" ignores the deadline, like any late attempt the instructor allowed.
"""

from datetime import datetime, timedelta, timezone

from app.models.domain_models import Submission, Task, TimedAttempt
from app.services.submission_service import (has_retake_allowance,
                                             is_task_past_due)
from app.services.task_service import get_student_task
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

# The workspace submits by itself when the timer reaches 00:00. The grace
# covers that request's trip to the server (and a slow free-tier instance),
# so a submission sent on time is never refused for arriving a moment late.
TIME_UP_GRACE = timedelta(seconds=120)


class TimedActivityError(Exception):
    """Base exception for timed-activity workflow errors."""


class TimedActivityNotTimedError(TimedActivityError):
    """The activity has no time limit."""


class TimedActivityClosedError(TimedActivityError):
    """No new timer window can be started."""


class TimedActivityPersistenceError(TimedActivityError):
    """The timer window could not be saved."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    # SQLite returns DateTime(timezone=True) values without tzinfo.
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def latest_timed_window(
    db: Session,
    *,
    student_id: int,
    task_id: int,
) -> TimedAttempt | None:
    return (
        db.query(TimedAttempt)
        .filter(
            TimedAttempt.student_id == student_id,
            TimedAttempt.task_id == task_id,
        )
        .order_by(TimedAttempt.window_number.desc())
        .first()
    )


def withheld_content() -> dict:
    """Student-response values for a timed activity's problem before its timer starts."""

    return {
        "description": None,
        "instructions": None,
        "scenario": None,
        "starter_code": "",
        "required_ast_rules": {},
        "content_withheld": True,
    }


def started_timed_task_ids(
    db: Session,
    *,
    student_id: int,
    task_ids: list[int],
) -> set[int]:
    """The activities, among task_ids, whose timer this student has started."""

    if not task_ids:
        return set()

    rows = (
        db.query(TimedAttempt.task_id)
        .filter(
            TimedAttempt.student_id == student_id,
            TimedAttempt.task_id.in_(task_ids),
        )
        .distinct()
        .all()
    )
    return {row[0] for row in rows}


def is_content_withheld(
    db: Session,
    *,
    task: Task,
    student_id: int,
) -> bool:
    """
    A timed activity's problem stays hidden until the student starts the
    timer, so reading it cannot happen outside the time limit. Once a window
    exists (running or over), the problem stays visible.
    """

    if not task.is_timed:
        return False

    return not started_timed_task_ids(db, student_id=student_id, task_ids=[task.task_id])


def timed_window_ends_at(task: Task, window: TimedAttempt) -> datetime:
    ends_at = _as_utc(window.expires_at)
    if not window.opened_with_retake and task.due_at is not None:
        ends_at = min(ends_at, _as_utc(task.due_at))
    return ends_at


def timed_submission_error(
    db: Session,
    *,
    task: Task,
    student_id: int,
    now: datetime | None = None,
) -> str | None:
    """Why a submission to this timed activity is refused, or None if allowed."""

    window = latest_timed_window(db, student_id=student_id, task_id=task.task_id)
    if window is None:
        return "Start the timer before submitting this timed activity."

    if (now or _utc_now()) > timed_window_ends_at(task, window) + TIME_UP_GRACE:
        return "The time limit for this activity has ended."

    return None


def _submitted_since(
    db: Session,
    *,
    student_id: int,
    task_id: int,
    since: datetime,
) -> bool:
    # accepted_at, not submitted_at: the service sets it to the microsecond,
    # while submitted_at's database default may keep only whole seconds, which
    # puts a submission made in the same second as the start before it.
    # Compared in Python: SQLite stores these datetimes without a timezone.
    latest = (
        db.query(func.max(Submission.accepted_at))
        .filter(
            Submission.student_id == student_id,
            Submission.task_id == task_id,
        )
        .scalar()
    )
    return latest is not None and _as_utc(latest) >= since


def describe_timer(
    db: Session,
    *,
    task: Task,
    student_id: int,
    now: datetime | None = None,
) -> dict:
    """
    The student's timer for the workspace.

    state is one of:
    - not_started: the student may start a window (the first one, or one
      more through "Allow another attempt": retake_available);
    - running: a window is open until ends_at;
    - expired: the student's window has ended;
    - closed: the deadline passed before the student started.
    """

    now = now or _utc_now()
    timer = {
        "task_id": task.task_id,
        "state": "not_started",
        "time_limit_minutes": task.time_limit_minutes,
        "server_now": now,
        "window_number": None,
        "started_at": None,
        "ends_at": None,
        "submit_until": None,
        "opened_with_retake": False,
        "retake_available": False,
        "submitted_in_window": False,
    }

    window = latest_timed_window(db, student_id=student_id, task_id=task.task_id)
    retake = has_retake_allowance(db, student_id=student_id, task_id=task.task_id)

    if window is None:
        if is_task_past_due(task, now) and not retake:
            timer["state"] = "closed"
        timer["retake_available"] = retake and is_task_past_due(task, now)
        return timer

    ends_at = timed_window_ends_at(task, window)
    if now >= ends_at and retake:
        timer["retake_available"] = True
        return timer

    started_at = _as_utc(window.started_at)
    timer.update(
        state="running" if now < ends_at else "expired",
        time_limit_minutes=window.time_limit_minutes,
        window_number=window.window_number,
        started_at=started_at,
        ends_at=ends_at,
        submit_until=ends_at + TIME_UP_GRACE,
        opened_with_retake=bool(window.opened_with_retake),
        submitted_in_window=_submitted_since(
            db,
            student_id=student_id,
            task_id=task.task_id,
            since=started_at,
        ),
    )
    return timer


def get_student_timer(
    db: Session,
    *,
    student_id: int,
    task_id: int,
) -> dict:
    task = get_student_task(db=db, task_id=task_id, student_id=student_id)
    if not task.is_timed:
        raise TimedActivityNotTimedError("This activity has no time limit.")
    return describe_timer(db, task=task, student_id=student_id)


def start_student_timer(
    db: Session,
    *,
    student_id: int,
    task_id: int,
) -> dict:
    """
    Start the student's timer, or return the window already running.

    Starting again after the window ended needs "Allow another attempt",
    and uses that allowance up: the extra attempt is the new window.
    """

    task = get_student_task(db=db, task_id=task_id, student_id=student_id)
    if not task.is_timed:
        raise TimedActivityNotTimedError("This activity has no time limit.")

    now = _utc_now()
    window = latest_timed_window(db, student_id=student_id, task_id=task.task_id)

    if window is not None and now < timed_window_ends_at(task, window):
        return describe_timer(db, task=task, student_id=student_id, now=now)

    retake = has_retake_allowance(db, student_id=student_id, task_id=task.task_id)
    if window is not None and not retake:
        raise TimedActivityClosedError("Your time for this activity has ended.")
    if window is None and is_task_past_due(task, now) and not retake:
        raise TimedActivityClosedError("The activity deadline has passed.")

    uses_retake = retake and (window is not None or is_task_past_due(task, now))
    if uses_retake:
        (
            db.query(Submission)
            .filter(
                Submission.student_id == student_id,
                Submission.task_id == task.task_id,
                Submission.retake_allowed.is_(True),
            )
            .update({Submission.retake_allowed: False}, synchronize_session=False)
        )

    db.add(
        TimedAttempt(
            task_id=task.task_id,
            student_id=student_id,
            window_number=(window.window_number + 1) if window else 1,
            time_limit_minutes=task.time_limit_minutes,
            started_at=now,
            expires_at=now + timedelta(minutes=task.time_limit_minutes),
            opened_with_retake=uses_retake,
        )
    )

    try:
        db.commit()
    except IntegrityError:
        # A second "Start Now" (another tab, a double click) saved the same
        # window first: that window is the student's timer.
        db.rollback()
    except SQLAlchemyError as error:
        db.rollback()
        raise TimedActivityPersistenceError("The timer could not be started. Please try again.") from error

    return describe_timer(db, task=task, student_id=student_id)
