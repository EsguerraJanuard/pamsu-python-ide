import secrets
from datetime import datetime, timezone
from typing import Any

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
        classroom = Classroom(
            instructor_id=instructor_id,
            name=classroom_data.name,
            subject_code=classroom_data.subject_code,
            section=classroom_data.section,
            class_code=generate_class_code(),
            is_active=True,
        )

        try:
            db.add(classroom)
            db.commit()
            db.refresh(classroom)

            return classroom

        except IntegrityError:
            db.rollback()

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
    classroom = get_owned_classroom(
        db=db,
        class_id=class_id,
        instructor_id=instructor_id,
    )

    update_data = classroom_data.model_dump(
        exclude_unset=True,
    )

    for field_name, value in update_data.items():
        setattr(
            classroom,
            field_name,
            value,
        )

    try:
        db.commit()
        db.refresh(classroom)

        return classroom

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
        classroom.class_code = generate_class_code()

        try:
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

    enrollment = Enrollment(
        class_id=classroom.class_id,
        student_id=student_id,
        status="active",
        deactivated_at=None,
    )

    try:
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

        return enrollment

    except IntegrityError as exc:
        db.rollback()

        raise EnrollmentConflictError(
            "You already have an enrollment record in this classroom."
        ) from exc


def list_student_classrooms(
    *,
    db: Session,
    student_id: int,
) -> list[dict[str, Any]]:
    enrollment_rows = (
        db.query(Enrollment, Classroom)
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
        db.query(Enrollment, User)
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
) -> None:
    previous_status = enrollment.status
    enrollment.status = new_status

    if new_status == "active":
        enrollment.deactivated_at = None
        return

    if previous_status != new_status or enrollment.deactivated_at is None:
        enrollment.deactivated_at = get_utc_now()


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

    apply_enrollment_status(
        enrollment=enrollment,
        new_status=new_status,
    )

    try:
        db.commit()
        db.refresh(enrollment)

        return enrollment

    except Exception:
        db.rollback()
        raise


# SECURITY BOUNDARY:
# instructor_id and student_id always come from authenticated users.
# Clients cannot create classrooms or enrollments on behalf of other users.

# CLASS-CODE BOUNDARY:
# Class codes are generated using cryptographically secure randomness.
# Clients cannot manually assign or modify a classroom class code.

# ENROLLMENT BOUNDARY:
# Enrollment status is limited to active, disabled, or removed.
# Disabled and removed records retain their historical enrollment row.
# Only the owning instructor can reactivate an enrollment.
