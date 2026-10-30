from datetime import datetime, timezone
from typing import Any

from app.models.domain_models import (Classroom, CodingSession, Enrollment,
                                      Submission, Task)
from app.schemas.submission_schema import SubmissionCreate, SubmissionStatus
from app.services.academic_event_service import (AcademicEventWorkflowError,
                                                 notify_retake_granted,
                                                 notify_submission_created)
from app.services.audit_service import AuditServiceError, create_audit_record
from app.services.notification_service import (
    NotificationRecipientUnavailableError,
    NotificationServiceError,
)
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session


class SubmissionServiceError(Exception):
    """Base exception for submission workflow errors."""


class SubmissionTaskUnavailableError(
    SubmissionServiceError,
):
    """Raised when a student cannot submit to a task."""


class SubmissionTaskNotGradableError(
    SubmissionServiceError,
):
    """Raised when a task does not accept official submissions."""


class SubmissionNotFoundError(
    SubmissionServiceError,
):
    """Raised when a submission cannot be found."""


class SubmissionAccessDeniedError(
    SubmissionServiceError,
):
    """Raised when an instructor cannot access a task submission."""


class CodingSessionUnavailableError(
    SubmissionServiceError,
):
    """Raised when the coding session is invalid or inaccessible."""


class SubmissionConflictError(
    SubmissionServiceError,
):
    """Raised when an attempt cannot be saved safely."""


class SubmissionPersistenceError(
    SubmissionServiceError,
):
    """Raised when an unexpected database error occurs."""


class SubmissionNotificationWorkflowError(
    SubmissionServiceError,
):
    """
    Raised when the submission and its required in-app notification
    cannot be saved as one transaction.
    """


class SubmissionAuditWorkflowError(
    SubmissionServiceError,
):
    """
    Raised when the submission and its required accountability
    record cannot be saved as one transaction.
    """


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _flush_submission_transaction(
    db: Session,
) -> None:
    """
    Flush the immutable submission before creating its audit record
    and approved academic event.

    The notification workflow performs the final commit so the
    submission, audit record, academic event, and recipient
    notification are saved atomically.
    """

    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()

        raise SubmissionConflictError(
            "The submission could not be saved because another "
            "attempt was created at the same time. Please submit again."
        ) from error
    except SQLAlchemyError as error:
        db.rollback()

        raise SubmissionPersistenceError(
            "The submission could not be saved."
        ) from error


def is_task_past_due(task: Task, now: datetime | None = None) -> bool:
    if task.due_at is None:
        return False

    due_at = task.due_at
    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=timezone.utc)

    return (now or _utc_now()) > due_at


def has_retake_allowance(
    db: Session,
    *,
    student_id: int,
    task_id: int,
) -> bool:
    """True when the instructor allowed this student one more attempt."""

    return (
        db.query(Submission.sub_id)
        .filter(
            Submission.student_id == student_id,
            Submission.task_id == task_id,
            Submission.retake_allowed.is_(True),
        )
        .first()
        is not None
    )


def _get_student_submission_task(
    db: Session,
    *,
    student_id: int,
    task_id: int,
) -> Task:
    """
    Resolve and lock the task receiving the new attempt.

    Locking the task row serializes attempt-number calculation on
    PostgreSQL. SQLite may ignore the lock during local tests.
    """

    task = (
        db.query(Task)
        .filter(
            Task.task_id == task_id,
        )
        .first()
    )

    if task is None or task.class_id is None or not task.is_published:
        raise SubmissionTaskUnavailableError(
            "The activity is unavailable for submission."
        )

    if is_task_past_due(task) and not has_retake_allowance(
        db,
        student_id=student_id,
        task_id=task.task_id,
    ):
        raise SubmissionTaskUnavailableError(
            "The activity deadline has passed."
        )

    active_enrollment = (
        db.query(Enrollment)
        .join(
            Classroom,
            Enrollment.class_id == Classroom.class_id,
        )
        .filter(
            Enrollment.class_id == task.class_id,
            Enrollment.student_id == student_id,
            Enrollment.status == "active",
            Classroom.is_active.is_(True),
        )
        .with_for_update(of=Enrollment)
        .first()
    )

    if active_enrollment is None:
        raise SubmissionTaskUnavailableError(
            "The activity is unavailable for submission."
        )

    if not task.is_graded:
        raise SubmissionTaskNotGradableError(
            "This activity does not accept official submissions."
        )

    return task


def _get_coding_session_identifier_column() -> Any:
    """
    Support the current domain model naming convention while keeping
    this service compatible with either session_id or
    coding_session_id as the CodingSession primary-key attribute.
    """

    for attribute_name in (
        "coding_session_id",
        "session_id",
    ):
        identifier_column = getattr(
            CodingSession,
            attribute_name,
            None,
        )

        if identifier_column is not None:
            return identifier_column

    raise SubmissionPersistenceError(
        "The coding-session model has no supported identifier field."
    )


def _validate_coding_session(
    db: Session,
    *,
    coding_session_id: str | None,
    student_id: int,
    task_id: int,
) -> None:
    if coding_session_id is None:
        return

    identifier_column = _get_coding_session_identifier_column()

    filters = [
        identifier_column == coding_session_id,
    ]

    student_column = getattr(
        CodingSession,
        "student_id",
        None,
    )

    task_column = getattr(
        CodingSession,
        "task_id",
        None,
    )

    if student_column is None:
        raise SubmissionPersistenceError(
            "The coding-session model has no student ownership field."
        )

    filters.append(
        student_column == student_id,
    )

    if task_column is not None:
        filters.append(
            task_column == task_id,
        )

    coding_session = db.query(CodingSession).filter(*filters).first()

    if coding_session is None:
        raise CodingSessionUnavailableError(
            "The coding session is unavailable for this activity."
        )


def _calculate_next_attempt_number(
    db: Session,
    *,
    student_id: int,
    task_id: int,
) -> int:
    latest_attempt_number = (
        db.query(
            func.max(
                Submission.attempt_number,
            )
        )
        .filter(
            Submission.student_id == student_id,
            Submission.task_id == task_id,
        )
        .scalar()
    )

    return int(latest_attempt_number or 0) + 1


def create_student_submission(
    db: Session,
    *,
    student_id: int,
    payload: SubmissionCreate,
) -> Submission:
    """
    Create an immutable submission attempt.

    Source code, standard input, student ownership, task ownership,
    and attempt number are fixed when the record is created.

    Only the is_official flag of an older attempt may be changed so
    that the latest accepted attempt becomes the official attempt. An
    attempt made after the deadline also uses up the retake allowance.

    The new submission, immutable audit record, academic event, and
    instructor notification are committed as one transaction.
    """

    task = _get_student_submission_task(
        db,
        student_id=student_id,
        task_id=payload.task_id,
    )

    _validate_coding_session(
        db,
        coding_session_id=(payload.coding_session_id),
        student_id=student_id,
        task_id=task.task_id,
    )

    next_attempt_number = _calculate_next_attempt_number(
        db,
        student_id=student_id,
        task_id=task.task_id,
    )

    # Official-attempt metadata may change, but the previous attempt's
    # submitted source and attempt number remain immutable.
    (
        db.query(Submission)
        .filter(
            Submission.student_id == student_id,
            Submission.task_id == task.task_id,
            Submission.is_official.is_(True),
        )
        .update(
            {
                Submission.is_official: False,
            },
            synchronize_session=False,
        )
    )

    # A late attempt is only possible through a retake allowance, and the
    # allowance covers exactly one attempt.
    if is_task_past_due(task):
        (
            db.query(Submission)
            .filter(
                Submission.student_id == student_id,
                Submission.task_id == task.task_id,
                Submission.retake_allowed.is_(True),
            )
            .update(
                {
                    Submission.retake_allowed: False,
                },
                synchronize_session=False,
            )
        )

    accepted_at = _utc_now()

    submission = Submission(
        student_id=student_id,
        task_id=task.task_id,
        coding_session_id=(payload.coding_session_id),
        attempt_number=(next_attempt_number),
        raw_code=payload.raw_code,
        standard_input=(payload.standard_input),
        status="submitted",
        is_official=True,
        accepted_at=accepted_at,
    )

    db.add(submission)

    _flush_submission_transaction(db)

    try:
        create_audit_record(
            db,
            {
                "audit_key": (
                    f"audit:submission_created:submission:{submission.sub_id}"
                ),
                "actor_user_id": student_id,
                "action_type": "submission_created",
                "resource_type": "submission",
                "resource_id": str(submission.sub_id),
                "outcome": "succeeded",
                "audit_data": {
                    "task_id": task.task_id,
                    "class_id": task.class_id,
                    "attempt_number": submission.attempt_number,
                    "submission_status": submission.status,
                    "is_official": bool(submission.is_official),
                },
                "occurred_at": accepted_at,
            },
            commit=False,
        )
    except (
        AuditServiceError,
        ValidationError,
        SQLAlchemyError,
    ) as error:
        db.rollback()

        raise SubmissionAuditWorkflowError(
            "The submission and its required accountability record "
            "could not be saved. No submission attempt was created. "
            "Please submit again."
        ) from error

    try:
        notify_submission_created(
            db,
            student_id=student_id,
            submission_id=submission.sub_id,
        )
    except NotificationRecipientUnavailableError:
        # Instructor is deactivated or unavailable; commit the student's submission rather than failing
        db.commit()
    except (
        AcademicEventWorkflowError,
        NotificationServiceError,
        SQLAlchemyError,
    ) as error:
        db.rollback()

        raise SubmissionNotificationWorkflowError(
            "The submission and its in-app notification could not "
            "be saved. No submission attempt was created. "
            "Please submit again."
        ) from error

    # The notification workflow commits the submission, audit record,
    # academic event, and instructor notification as one transaction.
    db.refresh(submission)

    return submission


def list_student_submissions(
    db: Session,
    *,
    student_id: int,
    task_id: int | None = None,
    status: SubmissionStatus | None = None,
    official_only: bool = False,
) -> list[Submission]:
    """
    Return only attempts owned by the authenticated student.

    Historical attempts remain readable even when the classroom later
    becomes inactive or the enrollment is disabled.
    """

    query = db.query(Submission).filter(
        Submission.student_id == student_id,
    )

    if task_id is not None:
        query = query.filter(
            Submission.task_id == task_id,
        )

    if status is not None:
        query = query.filter(
            Submission.status == status,
        )

    if official_only:
        query = query.filter(
            Submission.is_official.is_(True),
        )

    return query.order_by(
        Submission.submitted_at.desc(),
        Submission.sub_id.desc(),
    ).all()


def get_student_submission(
    db: Session,
    *,
    student_id: int,
    submission_id: int,
) -> Submission:
    submission = (
        db.query(Submission)
        .filter(
            Submission.sub_id == submission_id,
            Submission.student_id == student_id,
        )
        .first()
    )

    if submission is None:
        raise SubmissionNotFoundError("Submission not found.")

    return submission


def get_student_official_submission(
    db: Session,
    *,
    student_id: int,
    task_id: int,
) -> Submission:
    submission = (
        db.query(Submission)
        .filter(
            Submission.student_id == student_id,
            Submission.task_id == task_id,
            Submission.is_official.is_(True),
        )
        .order_by(
            Submission.attempt_number.desc(),
        )
        .first()
    )

    if submission is None:
        raise SubmissionNotFoundError("Official submission not found.")

    return submission


def _get_instructor_owned_task(
    db: Session,
    *,
    instructor_id: int,
    task_id: int,
) -> Task:
    task = (
        db.query(Task)
        .join(
            Classroom,
            Task.class_id == Classroom.class_id,
        )
        .filter(
            Task.task_id == task_id,
            Classroom.instructor_id == instructor_id,
        )
        .first()
    )

    if task is None:
        raise SubmissionAccessDeniedError(
            "You can only review submissions from your own classrooms."
        )

    return task


def list_instructor_task_submissions(
    db: Session,
    *,
    instructor_id: int,
    task_id: int,
    student_id: int | None = None,
    status: SubmissionStatus | None = None,
    official_only: bool = False,
) -> list[Submission]:
    task = _get_instructor_owned_task(
        db,
        instructor_id=instructor_id,
        task_id=task_id,
    )

    query = db.query(Submission).filter(
        Submission.task_id == task.task_id,
    )

    if student_id is not None:
        query = query.filter(
            Submission.student_id == student_id,
        )

    if status is not None:
        query = query.filter(
            Submission.status == status,
        )

    if official_only:
        query = query.filter(
            Submission.is_official.is_(True),
        )

    return query.order_by(
        Submission.student_id.asc(),
        Submission.attempt_number.desc(),
    ).all()


def get_instructor_submission(
    db: Session,
    *,
    instructor_id: int,
    submission_id: int,
) -> Submission:
    submission = (
        db.query(Submission)
        .join(
            Task,
            Submission.task_id == Task.task_id,
        )
        .join(
            Classroom,
            Task.class_id == Classroom.class_id,
        )
        .filter(
            Submission.sub_id == submission_id,
            Classroom.instructor_id == instructor_id,
        )
        .first()
    )

    if submission is None:
        raise SubmissionAccessDeniedError(
            "You can only review submissions from your own classrooms."
        )

    return submission


def grant_submission_retake(
    db: Session,
    *,
    instructor_id: int,
    submission_id: int,
) -> Submission:
    """
    Allow the student one more attempt on this activity, even after the
    deadline. The next attempt becomes official and uses up the allowance;
    the released grade of the earlier attempt stays on that attempt.

    Granting twice before the student uses it changes nothing.
    """

    submission = get_instructor_submission(
        db,
        instructor_id=instructor_id,
        submission_id=submission_id,
    )

    if has_retake_allowance(
        db,
        student_id=submission.student_id,
        task_id=submission.task_id,
    ):
        return submission

    granted_at = _utc_now()
    submission.retake_allowed = True

    try:
        db.flush()

        create_audit_record(
            db,
            {
                "audit_key": (
                    f"audit:submission_status_changed:submission:{submission.sub_id}"
                    f":retake:{granted_at.isoformat(timespec='microseconds')}"
                ),
                "actor_user_id": instructor_id,
                "action_type": "submission_status_changed",
                "resource_type": "submission",
                "resource_id": str(submission.sub_id),
                "audit_data": {
                    "task_id": submission.task_id,
                    "student_id": submission.student_id,
                    "change": "retake_allowed",
                },
                "occurred_at": granted_at,
            },
            commit=False,
        )

        db.commit()
    except (AuditServiceError, ValidationError) as error:
        db.rollback()

        raise SubmissionAuditWorkflowError(
            "Another attempt could not be allowed because its "
            "accountability record could not be saved. Please try again."
        ) from error
    except SQLAlchemyError as error:
        db.rollback()

        raise SubmissionPersistenceError(
            "Another attempt could not be allowed."
        ) from error

    db.refresh(submission)

    # The allowance is saved; a notification failure must not undo it.
    try:
        notify_retake_granted(
            db,
            actor_instructor_id=instructor_id,
            submission_id=submission.sub_id,
            granted_at=granted_at,
        )
    except (AcademicEventWorkflowError, NotificationServiceError, ValidationError):
        db.rollback()

    return submission


# AUTHORIZATION BOUNDARY:
# Student submission creation and reads are always scoped to the
# authenticated student. Instructor reads are restricted to submissions
# belonging to classrooms owned by the authenticated instructor.

# IMMUTABILITY BOUNDARY:
# Source code, standard input, student ownership, task ownership, coding
# session ownership, and attempt number are fixed when an attempt is
# created. Only official-attempt metadata may change for older attempts.

# AUDIT WORKFLOW BOUNDARY:
# A new immutable submission and its immutable accountability record
# are saved in the same transaction. Audit failure rolls back the new
# attempt and restores the previous official-attempt state so the next
# successful retry receives the correct attempt number.

# AUDIT PRIVACY BOUNDARY:
# Submission audit metadata contains only the submission identifier,
# task and classroom identifiers, attempt number, workflow status, and
# official-attempt state. It excludes source code, standard input,
# coding-session telemetry, execution output, test data, AST findings,
# similarity details, grades, feedback, clipboard or paste contents,
# surveillance data, and misconduct conclusions.

# NOTIFICATION WORKFLOW BOUNDARY:
# A new immutable submission, its audit record, academic event, and the
# instructor's in-app notification are saved in one transaction. A
# notification workflow failure rolls back all four records and restores
# the previous official-attempt state, making a client retry safe.

# NOTIFICATION PRIVACY BOUNDARY:
# Submission-created notifications exclude source code, standard input,
# AST details, similarity results, execution output, hidden test cases,
# coding-session telemetry, clipboard contents, pasted text, and
# automated misconduct conclusions.

# REVIEW BOUNDARY:
# Submission records and automated indicators support instructor review.
# They never independently assign an official grade or determine
# plagiarism, cheating, copying, or misconduct.
