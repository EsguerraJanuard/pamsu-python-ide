from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.domain_models import (
    Classroom,
    CodingSession,
    Enrollment,
    Submission,
    Task,
)
from app.schemas.submission_schema import (
    SubmissionCreate,
    SubmissionStatus,
)


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


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _commit_submission_transaction(
    db: Session,
) -> None:
    try:
        db.commit()
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
        .with_for_update()
        .first()
    )

    if task is None or task.class_id is None or not task.is_published:
        raise SubmissionTaskUnavailableError(
            "The activity is unavailable for submission."
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
    that the latest accepted attempt becomes the official attempt.
    """

    task = _get_student_submission_task(
        db,
        student_id=student_id,
        task_id=payload.task_id,
    )

    _validate_coding_session(
        db,
        coding_session_id=payload.coding_session_id,
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

    accepted_at = _utc_now()

    submission = Submission(
        student_id=student_id,
        task_id=task.task_id,
        coding_session_id=payload.coding_session_id,
        attempt_number=next_attempt_number,
        raw_code=payload.raw_code,
        standard_input=payload.standard_input,
        status="submitted",
        is_official=True,
        accepted_at=accepted_at,
    )

    db.add(submission)

    _commit_submission_transaction(db)

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
