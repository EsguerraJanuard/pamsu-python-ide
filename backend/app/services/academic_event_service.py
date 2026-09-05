from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.domain_models import (
    Classroom,
    Enrollment,
    InstructorGrade,
    Submission,
    Task,
    User,
)
from app.schemas.notification_schema import (
    AcademicEventCreate,
)
from app.services.notification_service import (
    create_academic_event_notifications,
)


class AcademicEventWorkflowError(Exception):
    """Base exception for approved academic-event workflows."""


class AcademicEventResourceUnavailableError(
    AcademicEventWorkflowError,
):
    """Raised when the academic resource does not exist."""


class AcademicEventAccessDeniedError(
    AcademicEventWorkflowError,
):
    """Raised when an actor does not own the academic resource."""


class AcademicEventStateConflictError(
    AcademicEventWorkflowError,
):
    """Raised when the resource has not reached the required state."""


def _normalize_datetime(
    value: datetime,
) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(
            tzinfo=timezone.utc,
        )

    return value.astimezone(
        timezone.utc,
    )


def _datetime_event_token(
    value: datetime | None,
    *,
    field_name: str,
) -> str:
    if value is None:
        raise AcademicEventStateConflictError(
            f"{field_name} is required to create an idempotent academic event."
        )

    normalized_value = _normalize_datetime(value)

    return normalized_value.isoformat(
        timespec="microseconds",
    )


def _build_no_recipient_result(
    *,
    event_key: str,
) -> dict[str, Any]:
    """
    Return a safe no-op result when an approved event currently has
    no active notification recipients.

    The originating academic action must not fail merely because a
    classroom has no active students.
    """

    return {
        "academic_event": None,
        "notifications": [],
        "academic_event_created": False,
        "created_notification_count": 0,
        "event_key": event_key,
        "skipped_reason": "no_active_recipients",
    }


def _get_instructor_owned_task(
    db: Session,
    *,
    actor_instructor_id: int,
    task_id: int,
) -> tuple[Task, Classroom]:
    result = (
        db.query(
            Task,
            Classroom,
        )
        .join(
            Classroom,
            Task.class_id == Classroom.class_id,
        )
        .filter(
            Task.task_id == task_id,
        )
        .first()
    )

    if result is None:
        raise AcademicEventResourceUnavailableError("Activity not found.")

    task, classroom = result

    if (
        task.instructor_id != actor_instructor_id
        or classroom.instructor_id != actor_instructor_id
    ):
        raise AcademicEventAccessDeniedError(
            "You can only create academic events for activities that you own."
        )

    return task, classroom


def _get_instructor_owned_classroom(
    db: Session,
    *,
    actor_instructor_id: int,
    class_id: int,
) -> Classroom:
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.class_id == class_id,
        )
        .first()
    )

    if classroom is None:
        raise AcademicEventResourceUnavailableError("Classroom not found.")

    if classroom.instructor_id != actor_instructor_id:
        raise AcademicEventAccessDeniedError(
            "You can only create academic events for classrooms that you own."
        )

    return classroom


def _get_instructor_owned_grade(
    db: Session,
    *,
    actor_instructor_id: int,
    grade_id: int,
) -> tuple[
    InstructorGrade,
    Submission,
    Task,
    Classroom,
]:
    result = (
        db.query(
            InstructorGrade,
            Submission,
            Task,
            Classroom,
        )
        .join(
            Submission,
            InstructorGrade.submission_id == Submission.sub_id,
        )
        .join(
            Task,
            Submission.task_id == Task.task_id,
        )
        .join(
            Classroom,
            Task.class_id == Classroom.class_id,
        )
        .filter(
            InstructorGrade.grade_id == grade_id,
        )
        .first()
    )

    if result is None:
        raise AcademicEventResourceUnavailableError("Instructor grade not found.")

    (
        grade,
        submission,
        task,
        classroom,
    ) = result

    if (
        grade.instructor_id != actor_instructor_id
        or task.instructor_id != actor_instructor_id
        or classroom.instructor_id != actor_instructor_id
    ):
        raise AcademicEventAccessDeniedError(
            "You can only create academic events "
            "for grades from activities that you own."
        )

    return (
        grade,
        submission,
        task,
        classroom,
    )


def _get_submission_context(
    db: Session,
    *,
    student_id: int,
    submission_id: int,
) -> tuple[
    Submission,
    Task,
    Classroom,
    User,
]:
    result = (
        db.query(
            Submission,
            Task,
            Classroom,
            User,
        )
        .join(
            Task,
            Submission.task_id == Task.task_id,
        )
        .join(
            Classroom,
            Task.class_id == Classroom.class_id,
        )
        .join(
            User,
            Submission.student_id == User.user_id,
        )
        .filter(
            Submission.sub_id == submission_id,
        )
        .first()
    )

    if result is None:
        raise AcademicEventResourceUnavailableError("Submission not found.")

    (
        submission,
        task,
        classroom,
        student,
    ) = result

    if submission.student_id != student_id:
        raise AcademicEventAccessDeniedError(
            "You can only create submission events for your own submissions."
        )

    return (
        submission,
        task,
        classroom,
        student,
    )


def _list_active_class_student_ids(
    db: Session,
    *,
    class_id: int,
) -> list[int]:
    rows = (
        db.query(Enrollment.student_id)
        .join(
            User,
            Enrollment.student_id == User.user_id,
        )
        .filter(
            Enrollment.class_id == class_id,
            Enrollment.status == "active",
            User.role == "student",
            User.is_active.is_(True),
            User.email_verified.is_(True),
        )
        .order_by(
            Enrollment.student_id.asc(),
        )
        .all()
    )

    return [int(row.student_id) for row in rows]


def notify_activity_published(
    db: Session,
    *,
    actor_instructor_id: int,
    task_id: int,
) -> dict[str, Any]:
    """
    Notify active enrolled students that an owned activity was
    published.

    Source code, starter code, instructions, hidden tests, AST rules,
    and grading information are excluded from the event and message.
    """

    task, classroom = _get_instructor_owned_task(
        db,
        actor_instructor_id=actor_instructor_id,
        task_id=task_id,
    )

    if not task.is_published:
        raise AcademicEventStateConflictError(
            "The activity must be published before "
            "publication notifications can be created."
        )

    published_token = _datetime_event_token(
        task.published_at,
        field_name="published_at",
    )

    event_key = f"activity_published:task:{task.task_id}:{published_token}"

    recipient_ids = _list_active_class_student_ids(
        db,
        class_id=classroom.class_id,
    )

    if not recipient_ids:
        return _build_no_recipient_result(
            event_key=event_key,
        )

    event_payload = AcademicEventCreate(
        event_key=event_key,
        event_type="activity_published",
        actor_user_id=actor_instructor_id,
        resource_type="task",
        resource_id=str(task.task_id),
        event_data={
            "task_id": task.task_id,
            "class_id": classroom.class_id,
            "activity_type": task.activity_type,
            "published_at": published_token,
        },
    )

    return create_academic_event_notifications(
        db,
        event_payload=event_payload,
        recipient_ids=recipient_ids,
        title="New activity published",
        message=(f"{task.title} is now available in {classroom.name}."),
    )


def notify_submission_created(
    db: Session,
    *,
    student_id: int,
    submission_id: int,
) -> dict[str, Any]:
    """
    Notify the owning instructor that a student submission attempt
    was created.

    The notification excludes source code, standard input, execution
    output, AST details, similarity details, and session telemetry.
    """

    (
        submission,
        task,
        classroom,
        student,
    ) = _get_submission_context(
        db,
        student_id=student_id,
        submission_id=submission_id,
    )

    event_key = f"submission_created:submission:{submission.sub_id}"

    event_payload = AcademicEventCreate(
        event_key=event_key,
        event_type="submission_created",
        actor_user_id=student_id,
        resource_type="submission",
        resource_id=str(submission.sub_id),
        event_data={
            "submission_id": submission.sub_id,
            "task_id": task.task_id,
            "class_id": classroom.class_id,
            "attempt_number": submission.attempt_number,
            "is_official": submission.is_official,
        },
    )

    return create_academic_event_notifications(
        db,
        event_payload=event_payload,
        recipient_ids=[classroom.instructor_id],
        title="Submission received",
        message=(
            f"{student.name} submitted "
            f"{task.title}, attempt "
            f"{submission.attempt_number}."
        ),
    )


def notify_grade_released(
    db: Session,
    *,
    actor_instructor_id: int,
    grade_id: int,
) -> dict[str, Any]:
    """
    Notify the student that a manual instructor grade was released.

    The message intentionally excludes the score, maximum score,
    percentage, feedback, and all automated review indicators.
    """

    (
        grade,
        submission,
        task,
        classroom,
    ) = _get_instructor_owned_grade(
        db,
        actor_instructor_id=actor_instructor_id,
        grade_id=grade_id,
    )

    if not grade.is_released:
        raise AcademicEventStateConflictError(
            "The manual grade must be released before "
            "a grade-release notification can be created."
        )

    release_token = _datetime_event_token(
        grade.updated_at,
        field_name="grade updated_at",
    )

    event_key = f"grade_released:grade:{grade.grade_id}:{release_token}"

    event_payload = AcademicEventCreate(
        event_key=event_key,
        event_type="grade_released",
        actor_user_id=actor_instructor_id,
        resource_type="grade",
        resource_id=str(grade.grade_id),
        event_data={
            "grade_id": grade.grade_id,
            "submission_id": submission.sub_id,
            "task_id": task.task_id,
            "class_id": classroom.class_id,
            "released_at": release_token,
        },
    )

    return create_academic_event_notifications(
        db,
        event_payload=event_payload,
        recipient_ids=[submission.student_id],
        title="Grade released",
        message=(f"A manual grade for {task.title} is now available."),
    )


def notify_classroom_archived(
    db: Session,
    *,
    actor_instructor_id: int,
    class_id: int,
) -> dict[str, Any]:
    """
    Notify active enrolled students that an owned classroom was
    archived.
    """

    classroom = _get_instructor_owned_classroom(
        db,
        actor_instructor_id=actor_instructor_id,
        class_id=class_id,
    )

    if classroom.is_active or classroom.archived_at is None:
        raise AcademicEventStateConflictError(
            "The classroom must be archived before "
            "archive notifications can be created."
        )

    archived_token = _datetime_event_token(
        classroom.archived_at,
        field_name="archived_at",
    )

    event_key = f"classroom_archived:classroom:{classroom.class_id}:{archived_token}"

    recipient_ids = _list_active_class_student_ids(
        db,
        class_id=classroom.class_id,
    )

    if not recipient_ids:
        return _build_no_recipient_result(
            event_key=event_key,
        )

    event_payload = AcademicEventCreate(
        event_key=event_key,
        event_type="classroom_archived",
        actor_user_id=actor_instructor_id,
        resource_type="classroom",
        resource_id=str(classroom.class_id),
        event_data={
            "class_id": classroom.class_id,
            "archived_at": archived_token,
        },
    )

    return create_academic_event_notifications(
        db,
        event_payload=event_payload,
        recipient_ids=recipient_ids,
        title="Classroom archived",
        message=(f"{classroom.name} has been archived."),
    )


# APPROVED-EVENT BOUNDARY:
# This service exposes only explicit academic workflow templates.
# Clients cannot supply arbitrary event types, recipients, titles,
# messages, or event payloads.

# RECIPIENT BOUNDARY:
# Recipients are resolved from classroom ownership, active enrollment,
# submission ownership, and grade ownership. Clients never select them.

# PRIVACY BOUNDARY:
# Events and notifications exclude source code, starter code, standard
# input, hidden test cases, AST details, similarity records, execution
# output, session telemetry, clipboard contents, pasted text,
# surveillance data, and unreleased grade information.

# GRADING BOUNDARY:
# Grade-release notifications are created only after a manual
# InstructorGrade is explicitly released by an authorized instructor.
# The notification does not disclose the score or feedback.

# DELIVERY BOUNDARY:
# These workflows create in-app notifications only. Email, SMS, and
# push delivery remain outside Pillar 11.
