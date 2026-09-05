import secrets
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.domain_models import (
    Classroom,
    Enrollment,
    User,
)
from app.schemas.classroom_schema import (
    ClassroomCreate,
    ClassroomUpdate,
)
from app.schemas.enrollment_schema import (
    EnrollmentJoinRequest,
    EnrollmentStatus,
)
from app.services.academic_event_service import (
    AcademicEventWorkflowError,
    notify_classroom_archived,
)
from app.services.audit_service import (
    AuditServiceError,
    create_audit_record,
)
from app.services.notification_service import (
    NotificationServiceError,
)


CLASS_CODE_LENGTH = 8
CLASS_CODE_MAX_ATTEMPTS = 10
CLASS_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class ClassroomServiceError(Exception):
    """Base exception for classroom and enrollment operations."""


class ClassroomNotFoundError(ClassroomServiceError):
    pass


class ClassroomAccessDeniedError(ClassroomServiceError):
    pass


class ClassroomInactiveError(ClassroomServiceError):
    pass


class ClassroomCodeGenerationError(ClassroomServiceError):
    pass


class ClassroomNotificationWorkflowError(ClassroomServiceError):
    """
    Raised when a classroom archive and its required notifications
    cannot be saved as one transaction.
    """


class ClassroomAuditWorkflowError(ClassroomServiceError):
    """
    Raised when a classroom or enrollment action and its required
    audit record cannot be saved as one transaction.
    """


class EnrollmentNotFoundError(ClassroomServiceError):
    pass


class EnrollmentConflictError(ClassroomServiceError):
    pass


class EnrollmentAccessDeniedError(ClassroomServiceError):
    pass


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_class_code(
    length: int = CLASS_CODE_LENGTH,
) -> str:
    return "".join(secrets.choice(CLASS_CODE_ALPHABET) for _ in range(length))


def _build_audit_key(
    *,
    action_type: str,
    resource_type: str,
    resource_id: int | str,
    repeatable: bool,
) -> str:
    base_key = f"audit:{action_type}:{resource_type}:{resource_id}"

    if not repeatable:
        return base_key

    return f"{base_key}:{uuid4()}"


def _record_audit(
    *,
    db: Session,
    audit_key: str,
    actor_user_id: int,
    action_type: str,
    resource_type: str,
    resource_id: int | str,
    audit_data: dict[str, Any],
    occurred_at: datetime,
) -> None:
    create_audit_record(
        db,
        {
            "audit_key": audit_key,
            "actor_user_id": actor_user_id,
            "action_type": action_type,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "outcome": "succeeded",
            "audit_data": audit_data,
            "occurred_at": occurred_at,
        },
        commit=False,
    )


def get_classroom_by_id(
    *,
    db: Session,
    class_id: int,
) -> Classroom:
    classroom = db.query(Classroom).filter(Classroom.class_id == class_id).first()

    if classroom is None:
        raise ClassroomNotFoundError("Classroom not found.")

    return classroom


def get_classroom_by_code(
    *,
    db: Session,
    class_code: str,
) -> Classroom:
    normalized_code = class_code.strip().upper()

    classroom = (
        db.query(Classroom)
        .filter(func.upper(Classroom.class_code) == normalized_code)
        .first()
    )

    if classroom is None:
        raise ClassroomNotFoundError("No classroom was found for this class code.")

    return classroom


def get_owned_classroom(
    *,
    db: Session,
    class_id: int,
    instructor_id: int,
) -> Classroom:
    classroom = get_classroom_by_id(
        db=db,
        class_id=class_id,
    )

    if classroom.instructor_id != instructor_id:
        raise ClassroomAccessDeniedError("You can only manage your own classrooms.")

    return classroom


def create_classroom(
    *,
    db: Session,
    instructor_id: int,
    classroom_data: ClassroomCreate,
) -> Classroom:
    for _ in range(CLASS_CODE_MAX_ATTEMPTS):
        occurred_at = get_utc_now()

        classroom = Classroom(
            instructor_id=instructor_id,
            name=classroom_data.name,
            subject_code=classroom_data.subject_code,
            section=classroom_data.section,
            class_code=generate_class_code(),
            is_active=True,
            archived_at=None,
        )

        try:
            db.add(classroom)
            db.flush()

            _record_audit(
                db=db,
                audit_key=_build_audit_key(
                    action_type="classroom_created",
                    resource_type="classroom",
                    resource_id=classroom.class_id,
                    repeatable=False,
                ),
                actor_user_id=instructor_id,
                action_type="classroom_created",
                resource_type="classroom",
                resource_id=classroom.class_id,
                audit_data={
                    "subject_code": classroom.subject_code,
                    "section": classroom.section,
                    "is_active": True,
                },
                occurred_at=occurred_at,
            )

            db.commit()
            db.refresh(classroom)

            return classroom
        except IntegrityError:
            db.rollback()
        except AuditServiceError as error:
            db.rollback()

            raise ClassroomAuditWorkflowError(
                "The classroom could not be created because its "
                "required accountability record could not be saved. "
                "Please try again."
            ) from error
        except Exception:
            db.rollback()
            raise

    raise ClassroomCodeGenerationError(
        "A unique class code could not be generated. Please retry the request."
    )


def list_instructor_classrooms(
    *,
    db: Session,
    instructor_id: int,
) -> list[Classroom]:
    return (
        db.query(Classroom)
        .filter(Classroom.instructor_id == instructor_id)
        .order_by(Classroom.created_at.desc())
        .all()
    )


def update_classroom(
    *,
    db: Session,
    class_id: int,
    instructor_id: int,
    classroom_data: ClassroomUpdate,
) -> Classroom:
    """
    Update an instructor-owned classroom.

    Accountable classroom changes and their audit record are committed
    together. An archive transition also creates its approved academic
    event and student notifications in the same transaction.
    """

    classroom = get_owned_classroom(
        db=db,
        class_id=class_id,
        instructor_id=instructor_id,
    )

    update_data = classroom_data.model_dump(
        exclude_unset=True,
    )

    changed_fields = sorted(
        field_name
        for field_name, value in update_data.items()
        if getattr(classroom, field_name) != value
    )

    if not changed_fields:
        return classroom

    was_active = bool(classroom.is_active)

    for field_name, value in update_data.items():
        setattr(
            classroom,
            field_name,
            value,
        )

    is_active_now = bool(classroom.is_active)

    archive_transition = was_active and not is_active_now

    reactivation_transition = not was_active and is_active_now

    occurred_at = get_utc_now()

    if archive_transition:
        classroom.archived_at = occurred_at
        action_type = "classroom_archived"
    elif reactivation_transition:
        classroom.archived_at = None
        action_type = "classroom_reactivated"
    else:
        action_type = "classroom_updated"

    audit_data: dict[str, Any] = {
        "changed_fields": changed_fields,
        "previous_active": was_active,
        "new_active": is_active_now,
    }

    if archive_transition:
        audit_data["archived_at"] = occurred_at.isoformat(
            timespec="microseconds",
        )
    elif reactivation_transition:
        audit_data["archived_at_cleared"] = True

    try:
        db.flush()

        _record_audit(
            db=db,
            audit_key=_build_audit_key(
                action_type=action_type,
                resource_type="classroom",
                resource_id=classroom.class_id,
                repeatable=True,
            ),
            actor_user_id=instructor_id,
            action_type=action_type,
            resource_type="classroom",
            resource_id=classroom.class_id,
            audit_data=audit_data,
            occurred_at=occurred_at,
        )

        if archive_transition:
            notify_classroom_archived(
                db,
                actor_instructor_id=instructor_id,
                class_id=classroom.class_id,
            )

        # The notification workflow commits when recipients exist.
        # This explicit commit also handles ordinary updates,
        # reactivation, and the valid archive-with-no-recipients case.
        db.commit()
        db.refresh(classroom)

        return classroom
    except AuditServiceError as error:
        db.rollback()

        raise ClassroomAuditWorkflowError(
            "The classroom change could not be saved because its "
            "required accountability record could not be completed. "
            "Please try again."
        ) from error
    except (
        AcademicEventWorkflowError,
        NotificationServiceError,
    ) as error:
        db.rollback()

        raise ClassroomNotificationWorkflowError(
            "The classroom could not be archived because its "
            "required in-app notification workflow could not be "
            "completed. The classroom remains active. Please try "
            "again."
        ) from error
    except Exception:
        db.rollback()
        raise


def regenerate_class_code(
    *,
    db: Session,
    class_id: int,
    instructor_id: int,
) -> Classroom:
    classroom = get_owned_classroom(
        db=db,
        class_id=class_id,
        instructor_id=instructor_id,
    )

    for _ in range(CLASS_CODE_MAX_ATTEMPTS):
        occurred_at = get_utc_now()
        classroom.class_code = generate_class_code()

        try:
            db.flush()

            _record_audit(
                db=db,
                audit_key=_build_audit_key(
                    action_type="classroom_updated",
                    resource_type="classroom",
                    resource_id=classroom.class_id,
                    repeatable=True,
                ),
                actor_user_id=instructor_id,
                action_type="classroom_updated",
                resource_type="classroom",
                resource_id=classroom.class_id,
                audit_data={
                    "changed_fields": [
                        "class_code",
                    ],
                    "reason_code": ("backend_code_regeneration"),
                },
                occurred_at=occurred_at,
            )

            db.commit()
            db.refresh(classroom)

            return classroom
        except IntegrityError:
            db.rollback()

            classroom = get_owned_classroom(
                db=db,
                class_id=class_id,
                instructor_id=instructor_id,
            )
        except AuditServiceError as error:
            db.rollback()

            raise ClassroomAuditWorkflowError(
                "The replacement class code could not be saved "
                "because its required accountability record could "
                "not be completed. Please try again."
            ) from error
        except Exception:
            db.rollback()
            raise

    raise ClassroomCodeGenerationError(
        "A unique replacement class code could not be generated. "
        "Please retry the request."
    )


def join_classroom(
    *,
    db: Session,
    student_id: int,
    enrollment_data: EnrollmentJoinRequest,
) -> Enrollment:
    classroom = get_classroom_by_code(
        db=db,
        class_code=enrollment_data.class_code,
    )

    if not classroom.is_active:
        raise ClassroomInactiveError(
            "This classroom is inactive and cannot accept new enrollments."
        )

    existing_enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.class_id == classroom.class_id,
            Enrollment.student_id == student_id,
        )
        .first()
    )

    if existing_enrollment is not None:
        raise EnrollmentConflictError(
            "You already have an enrollment record in this classroom."
        )

    occurred_at = get_utc_now()

    enrollment = Enrollment(
        class_id=classroom.class_id,
        student_id=student_id,
        status="active",
        deactivated_at=None,
    )

    try:
        db.add(enrollment)
        db.flush()

        _record_audit(
            db=db,
            audit_key=_build_audit_key(
                action_type="student_enrolled",
                resource_type="enrollment",
                resource_id=enrollment.enrollment_id,
                repeatable=False,
            ),
            actor_user_id=student_id,
            action_type="student_enrolled",
            resource_type="enrollment",
            resource_id=enrollment.enrollment_id,
            audit_data={
                "class_id": classroom.class_id,
                "status": "active",
            },
            occurred_at=occurred_at,
        )

        db.commit()
        db.refresh(enrollment)

        return enrollment
    except IntegrityError as exc:
        db.rollback()

        raise EnrollmentConflictError(
            "You already have an enrollment record in this classroom."
        ) from exc
    except AuditServiceError as error:
        db.rollback()

        raise ClassroomAuditWorkflowError(
            "The enrollment could not be completed because its "
            "required accountability record could not be saved. "
            "Please try again."
        ) from error
    except Exception:
        db.rollback()
        raise


def list_student_classrooms(
    *,
    db: Session,
    student_id: int,
) -> list[dict[str, Any]]:
    enrollment_rows = (
        db.query(
            Enrollment,
            Classroom,
        )
        .join(
            Classroom,
            Classroom.class_id == Enrollment.class_id,
        )
        .filter(Enrollment.student_id == student_id)
        .order_by(Classroom.created_at.desc())
        .all()
    )

    return [
        {
            "enrollment_id": enrollment.enrollment_id,
            "enrollment_status": enrollment.status,
            "classroom": classroom,
        }
        for enrollment, classroom in enrollment_rows
    ]


def list_class_members(
    *,
    db: Session,
    class_id: int,
    instructor_id: int,
) -> list[dict[str, Any]]:
    get_owned_classroom(
        db=db,
        class_id=class_id,
        instructor_id=instructor_id,
    )

    member_rows = (
        db.query(
            Enrollment,
            User,
        )
        .join(
            User,
            User.user_id == Enrollment.student_id,
        )
        .filter(Enrollment.class_id == class_id)
        .order_by(User.name.asc())
        .all()
    )

    return [
        {
            "enrollment_id": enrollment.enrollment_id,
            "student_id": user.user_id,
            "school_id": user.school_id,
            "name": user.name,
            "email": user.email,
            "status": enrollment.status,
        }
        for enrollment, user in member_rows
    ]


def get_enrollment(
    *,
    db: Session,
    enrollment_id: int,
) -> Enrollment:
    enrollment = (
        db.query(Enrollment).filter(Enrollment.enrollment_id == enrollment_id).first()
    )

    if enrollment is None:
        raise EnrollmentNotFoundError("Enrollment not found.")

    return enrollment


def apply_enrollment_status(
    *,
    enrollment: Enrollment,
    new_status: EnrollmentStatus,
    changed_at: datetime | None = None,
) -> None:
    previous_status = enrollment.status
    enrollment.status = new_status

    if new_status == "active":
        enrollment.deactivated_at = None
        return

    if previous_status != new_status or enrollment.deactivated_at is None:
        enrollment.deactivated_at = (
            changed_at if changed_at is not None else get_utc_now()
        )


def update_enrollment_status(
    *,
    db: Session,
    enrollment_id: int,
    instructor_id: int,
    new_status: EnrollmentStatus,
) -> Enrollment:
    enrollment = get_enrollment(
        db=db,
        enrollment_id=enrollment_id,
    )

    classroom = get_classroom_by_id(
        db=db,
        class_id=enrollment.class_id,
    )

    if classroom.instructor_id != instructor_id:
        raise EnrollmentAccessDeniedError(
            "You can only manage enrollments in your own classrooms."
        )

    previous_status = enrollment.status
    previous_deactivated_at = enrollment.deactivated_at
    occurred_at = get_utc_now()

    apply_enrollment_status(
        enrollment=enrollment,
        new_status=new_status,
        changed_at=occurred_at,
    )

    status_changed = previous_status != enrollment.status

    timestamp_repaired = previous_deactivated_at != enrollment.deactivated_at

    if not status_changed:
        if not timestamp_repaired:
            return enrollment

        try:
            db.commit()
            db.refresh(enrollment)

            return enrollment
        except Exception:
            db.rollback()
            raise

    try:
        db.flush()

        _record_audit(
            db=db,
            audit_key=_build_audit_key(
                action_type="enrollment_status_changed",
                resource_type="enrollment",
                resource_id=enrollment.enrollment_id,
                repeatable=True,
            ),
            actor_user_id=instructor_id,
            action_type="enrollment_status_changed",
            resource_type="enrollment",
            resource_id=enrollment.enrollment_id,
            audit_data={
                "class_id": enrollment.class_id,
                "student_id": enrollment.student_id,
                "previous_status": previous_status,
                "new_status": enrollment.status,
            },
            occurred_at=occurred_at,
        )

        db.commit()
        db.refresh(enrollment)

        return enrollment
    except AuditServiceError as error:
        db.rollback()

        raise ClassroomAuditWorkflowError(
            "The enrollment status could not be changed because "
            "its required accountability record could not be saved. "
            "Please try again."
        ) from error
    except Exception:
        db.rollback()
        raise


# SECURITY BOUNDARY:
# instructor_id and student_id always come from authenticated users.
# Clients cannot create classrooms or enrollments on behalf of other
# users.

# CLASS-CODE BOUNDARY:
# Class codes are generated using cryptographically secure randomness.
# Clients cannot manually assign or modify a classroom class code.
# Audit metadata records only that regeneration occurred and never
# stores the generated code.

# ENROLLMENT BOUNDARY:
# Enrollment status is limited to active, disabled, or removed.
# Disabled and removed records retain their historical enrollment row.
# Only the owning instructor can reactivate an enrollment.

# ARCHIVE STATE BOUNDARY:
# archived_at is set only by the backend when a classroom transitions
# from active to inactive. Reactivating the classroom clears it.
# Repeated inactive updates preserve the original archive timestamp.

# NOTIFICATION WORKFLOW BOUNDARY:
# A classroom-archived event is created only when an instructor-owned
# classroom transitions from active to inactive. The classroom update,
# audit record, academic event, and notifications for active enrolled
# students are persisted as one transaction. Repeated inactive updates
# do not create duplicate archive notifications.

# AUDIT WORKFLOW BOUNDARY:
# Classroom creation, meaningful classroom updates, class-code
# regeneration, archive/reactivation transitions, student enrollment,
# and enrollment-status transitions create immutable audit records.
# No-op requests do not create misleading duplicate audit rows.

# AUDIT PRIVACY BOUNDARY:
# Classroom and enrollment audit records exclude class codes, student
# names and email addresses, passwords, OTP values, source code, test
# data, grades, feedback, AST findings, similarity records, execution
# output, coding-session telemetry, clipboard contents, pasted text,
# surveillance data, and misconduct conclusions.
