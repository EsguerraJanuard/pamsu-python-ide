"""
Solo-practice submissions, judged in the background.

POST /practice/tasks/{id}/submit saves a *pending* attempt and queues it
(Celery task ``dispatch_practice_attempt``). The task sends the code to Judge0
with a callback URL; Judge0 runs it and PUTs the result to
/practice/internal/judge0-callback, which records the verdict here. The page
polls GET /practice/attempts/{id}. The HTTP request never waits on Judge0
(the 3-second rule), and each attempt is still exactly one Judge0 submission:
nobody polls Judge0 itself (each check would be a paid RapidAPI request).

States (practice_attempts.status, migration b7e4c2a91f03):
- pending:   saved, waiting for Judge0;
- completed: judged; is_successful says whether it passed;
- failed:    the code could not be run (queue or Judge0 unavailable, or no
             answer within PENDING_ATTEMPT_TIMEOUT). Not the student's fault,
             so it does not count as a try and is left out of the statistics.

The callback is public (Judge0 sends no credentials) and is bound to one
attempt by its correlation_id, a random UUID that only the server and Judge0
see. Terminal attempts accept no further callback.
"""

import base64
import logging
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.core.system_settings import get_default_ast_strictness
from app.models.domain_models import (PracticeAttempt, PracticeProgress,
                                      PracticeTask)
from app.schemas.execution_schema import (MAX_EXECUTION_OUTPUT_LENGTH,
                                          Judge0CallbackPayload)
from app.schemas.practice_schema import PracticeSubmissionResponse
from app.services.ast_evaluator import evaluate_ast_details
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# A pending attempt older than this is closed as "failed" when it is read.
# It covers the dispatch retries (3 tries of up to 10 s each, 3 s apart),
# Judge0's queue and its 10 s wall-time limit, with room to spare.
PENDING_ATTEMPT_TIMEOUT = timedelta(seconds=120)

PYTHON_LANGUAGE_ID = 71
JUDGE0_LIMITS = {
    "cpu_time_limit": 5.0,
    "memory_limit": 256000,
    "wall_time_limit": 10.0,
    "max_processes_and_or_threads": 64,
    "enable_network": False,
}

PENDING_MESSAGE = "Checking your code…"
PASSED_MESSAGE = "Practice task completed successfully!"
NOT_PASSED_MESSAGE = "Keep trying!"
NOT_CHECKED_MESSAGE = "Your code could not be checked this time. It does not count as a try."
DEFAULT_FAILURE_FEEDBACK = "Execution failed or output did not match expected output."
STRUCTURE_FEEDBACK = "Code runs successfully but does not meet the structural requirements of this lesson."
STRUCTURE_CHECK_FAILED = "The structure check could not be completed. Please try again."

# Shown to the student in the output panel. No provider URL or error detail.
RUNNER_UNAVAILABLE_MESSAGE = (
    "System error: the code execution service could not be reached. "
    "This attempt does not count; please try again shortly."
)
RUNNER_ERROR_MESSAGE = (
    "System error: the code execution service could not run this attempt. "
    "It does not count; please try again."
)
NO_ANSWER_MESSAGE = (
    "System error: the code execution service did not answer in time. "
    "This attempt does not count; please try again."
)

JUDGE0_ACCEPTED = 3
# 4 wrong answer, 5 time limit, 6 compile error, 7-12 runtime errors: the
# student's code was judged. Anything else (1-2 still queued, 13 internal
# error, 14 exec format error, missing) means Judge0 itself failed.
JUDGE0_JUDGED_STATUSES = {4, 5, 6, 7, 8, 9, 10, 11, 12}


class PracticeAttemptNotFoundError(Exception):
    """No attempt has this id and correlation id."""


class PracticeAttemptFinishedError(Exception):
    """The attempt is already completed or failed."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    # SQLite returns naive UTC timestamps; PostgreSQL returns aware ones.
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _decode(value: str | None) -> str:
    if not value:
        return ""
    try:
        return base64.b64decode(value).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return str(value)


def new_pending_attempt(db: Session, *, student_id: int, task_id: int, code: str) -> PracticeAttempt:
    """Save a pending attempt (committed) so the worker and the page can find it."""

    attempt = PracticeAttempt(
        student_id=student_id,
        task_id=task_id,
        submitted_code=code,
        is_successful=False,
        status="pending",
        correlation_id=str(uuid4()),
        execution_feedback=None,
        ast_feedback=[],
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def queue_practice_attempt(db: Session, attempt: PracticeAttempt) -> bool:
    """Hand a pending attempt to the worker; on failure close it as failed."""

    from app.tasks.celery_worker import dispatch_practice_attempt

    try:
        dispatch_practice_attempt.delay(attempt.attempt_id)
        return True
    except Exception:
        logger.exception("Failed to enqueue practice attempt %s.", attempt.attempt_id)

    mark_attempt_failed(db, attempt_id=attempt.attempt_id, message=RUNNER_UNAVAILABLE_MESSAGE)
    db.refresh(attempt)
    return False


def callback_url(attempt: PracticeAttempt) -> str:
    base = os.getenv("WEBHOOK_BASE_URL", "http://backend:8000").rstrip("/")
    return (
        f"{base}/practice/internal/judge0-callback"
        f"?attempt_id={attempt.attempt_id}&correlation_id={attempt.correlation_id}"
    )


def judge0_payload(attempt: PracticeAttempt, task: PracticeTask) -> dict:
    """The Judge0 submission for an attempt; Judge0 compares the output itself."""

    return {
        "source_code": _b64(attempt.submitted_code),
        "language_id": PYTHON_LANGUAGE_ID,
        "expected_output": _b64(task.expected_output) if task.expected_output else None,
        "callback_url": callback_url(attempt),
        **JUDGE0_LIMITS,
    }


def prepare_dispatch(db: Session, attempt_id: int) -> dict | None:
    """The Judge0 payload for a pending attempt, or None when there is nothing to send."""

    attempt = db.get(PracticeAttempt, attempt_id)
    if attempt is None or attempt.status != "pending":
        return None
    task = db.get(PracticeTask, attempt.task_id)
    if task is None:
        return None
    return judge0_payload(attempt, task)


def mark_attempt_failed(db: Session, *, attempt_id: int, message: str) -> bool:
    """
    Close a pending attempt as failed. Returns False when it was no longer
    pending (a callback won the race), in which case nothing changes.

    The UPDATE carries the "still pending" condition itself, so it cannot
    overwrite a verdict that a concurrent callback has just recorded.
    """

    try:
        updated = (
            db.query(PracticeAttempt)
            .filter(PracticeAttempt.attempt_id == attempt_id, PracticeAttempt.status == "pending")
            .update(
                {
                    PracticeAttempt.status: "failed",
                    PracticeAttempt.is_successful: False,
                    PracticeAttempt.execution_feedback: message,
                    PracticeAttempt.completed_at: _utc_now(),
                },
                synchronize_session=False,
            )
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to record the failure of practice attempt %s.", attempt_id)
        return False
    return updated == 1


def expire_if_stale(db: Session, attempt: PracticeAttempt, *, now: datetime | None = None) -> PracticeAttempt:
    """Close an attempt that has waited too long for Judge0, so the page stops waiting."""

    if attempt.status != "pending" or attempt.created_at is None:
        return attempt
    if (now or _utc_now()) - _as_utc(attempt.created_at) < PENDING_ATTEMPT_TIMEOUT:
        return attempt
    if mark_attempt_failed(db, attempt_id=attempt.attempt_id, message=NO_ANSWER_MESSAGE):
        logger.warning("Practice attempt %s got no Judge0 answer in time; closed as failed.", attempt.attempt_id)
    db.refresh(attempt)
    return attempt


def _judge(db: Session, attempt: PracticeAttempt, task: PracticeTask, status_id: int, payload: Judge0CallbackPayload):
    """(is_successful, execution_feedback, ast_feedback) for a judged run."""

    is_successful = status_id == JUDGE0_ACCEPTED
    execution_feedback = None
    if not is_successful:
        error_text = _decode(payload.stderr or payload.compile_output or payload.message)
        execution_feedback = error_text[:MAX_EXECUTION_OUTPUT_LENGTH] if error_text else DEFAULT_FAILURE_FEEDBACK

    ast_feedback: list[str] = []
    if is_successful and task.expected_ast_patterns:
        try:
            # Practice tasks have no instructor: the admin default applies.
            result = evaluate_ast_details(
                attempt.submitted_code,
                task.expected_ast_patterns,
                strictness_level=get_default_ast_strictness(db),
            )
            if result.get("syntax_error"):
                ast_feedback.append(
                    f"Syntax Error: {result['syntax_error'].get('message', 'Unknown syntax error')}"
                )
            for finding in result.get("findings", []):
                if not finding.get("passed", False):
                    ast_feedback.append(f"Missing {finding.get('label')}: {finding.get('message')}")
            if not result.get("passed"):
                is_successful = False
                execution_feedback = execution_feedback or STRUCTURE_FEEDBACK
        except Exception:
            logger.exception("Practice AST evaluation failed for attempt %s.", attempt.attempt_id)
            ast_feedback = [STRUCTURE_CHECK_FAILED]
            is_successful = False

    return is_successful, execution_feedback, ast_feedback


def _lock_progress(db: Session, *, student_id: int, task_id: int) -> PracticeProgress:
    """
    The student's progress row for a task, locked until commit.

    Two callbacks for the same student and task can arrive together. The
    row lock serializes their read-modify-write; when neither row exists
    yet, the unique (student_id, task_id) constraint lets one insert win and
    the other re-read it inside a savepoint.
    """

    def locked():
        return (
            db.query(PracticeProgress)
            .filter(PracticeProgress.student_id == student_id, PracticeProgress.task_id == task_id)
            .with_for_update()
            .first()
        )

    progress = locked()
    if progress is not None:
        return progress

    try:
        with db.begin_nested():
            progress = PracticeProgress(student_id=student_id, task_id=task_id, attempts_count=0, is_completed=False)
            db.add(progress)
            db.flush()
        return progress
    except IntegrityError:
        progress = locked()
        if progress is None:
            raise
        return progress


def record_judge0_result(
    db: Session,
    *,
    attempt_id: int,
    correlation_id: str,
    payload: Judge0CallbackPayload,
) -> PracticeAttempt:
    """Apply Judge0's callback to its attempt and the student's progress (one transaction)."""

    attempt = (
        db.query(PracticeAttempt)
        .filter(PracticeAttempt.attempt_id == attempt_id, PracticeAttempt.correlation_id == correlation_id)
        # Serializes duplicate deliveries and the stale-attempt expiry.
        .with_for_update()
        .first()
    )
    if attempt is None:
        raise PracticeAttemptNotFoundError()
    if attempt.status != "pending":
        db.rollback()
        raise PracticeAttemptFinishedError()

    raw_status = payload.status.get("id") if isinstance(payload.status, dict) else None
    status_id = raw_status if isinstance(raw_status, int) and not isinstance(raw_status, bool) else None
    now = _utc_now()

    try:
        if status_id != JUDGE0_ACCEPTED and status_id not in JUDGE0_JUDGED_STATUSES:
            logger.warning("Judge0 could not run practice attempt %s (status %s).", attempt.attempt_id, status_id)
            attempt.status = "failed"
            attempt.is_successful = False
            attempt.execution_feedback = RUNNER_ERROR_MESSAGE
            attempt.completed_at = now
            db.commit()
            db.refresh(attempt)
            return attempt

        task = db.get(PracticeTask, attempt.task_id)
        is_successful, execution_feedback, ast_feedback = _judge(db, attempt, task, status_id, payload)

        progress = _lock_progress(db, student_id=attempt.student_id, task_id=attempt.task_id)
        progress.attempts_count = (progress.attempts_count or 0) + 1
        if is_successful and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = now

        attempt.status = "completed"
        attempt.is_successful = is_successful
        attempt.execution_feedback = execution_feedback
        attempt.ast_feedback = ast_feedback
        attempt.completed_at = now
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(attempt)
    return attempt


def to_response(attempt: PracticeAttempt) -> PracticeSubmissionResponse:
    if attempt.status == "pending":
        message = PENDING_MESSAGE
    elif attempt.status == "failed":
        message = NOT_CHECKED_MESSAGE
    else:
        message = PASSED_MESSAGE if attempt.is_successful else NOT_PASSED_MESSAGE

    return PracticeSubmissionResponse(
        attempt_id=attempt.attempt_id,
        status=attempt.status,
        is_successful=bool(attempt.is_successful) and attempt.status == "completed",
        execution_feedback=attempt.execution_feedback,
        ast_feedback=list(attempt.ast_feedback or []),
        message=message,
    )
