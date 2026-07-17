from typing import NoReturn

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    get_current_instructor,
    get_current_student,
)
from app.models.domain_models import (
    Classroom,
    Enrollment,
    User,
)
from app.schemas.classroom_schema import (
    ClassroomCodeResponse,
    ClassroomCreate,
    ClassroomResponse,
    ClassroomUpdate,
)
from app.schemas.enrollment_schema import (
    ClassMemberResponse,
    EnrollmentJoinRequest,
    EnrollmentResponse,
    EnrollmentStatusUpdate,
    StudentClassroomResponse,
)
from app.services.classroom_service import (
    ClassroomAccessDeniedError,
    ClassroomAuditWorkflowError,
    ClassroomCodeGenerationError,
    ClassroomInactiveError,
    ClassroomNotFoundError,
    ClassroomNotificationWorkflowError,
    EnrollmentAccessDeniedError,
    EnrollmentConflictError,
    EnrollmentNotFoundError,
    create_classroom,
    get_owned_classroom,
    join_classroom,
    list_class_members,
    list_instructor_classrooms,
    list_student_classrooms,
    regenerate_class_code,
    update_classroom,
    update_enrollment_status,
)


router = APIRouter(
    prefix="/classrooms",
    tags=["Classrooms"],
)


def raise_classroom_service_http_exception(
    exc: Exception,
) -> NoReturn:
    if isinstance(
        exc,
        (
            ClassroomNotFoundError,
            EnrollmentNotFoundError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        (
            ClassroomAccessDeniedError,
            EnrollmentAccessDeniedError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        (
            ClassroomInactiveError,
            EnrollmentConflictError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        (
            ClassroomCodeGenerationError,
            ClassroomNotificationWorkflowError,
            ClassroomAuditWorkflowError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    raise exc


@router.post(
    "/",
    response_model=ClassroomResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_classroom",
    summary="Create a classroom",
    description=(
        "Creates a classroom owned by the authenticated instructor. "
        "The backend generates the unique class code and records a "
        "privacy-safe immutable audit entry for the accountable action."
    ),
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": (
                "A unique class code could not be generated, or the "
                "required accountability record could not be saved."
            ),
        },
    },
)
def create_classroom_endpoint(
    classroom_data: ClassroomCreate,
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Classroom:
    try:
        return create_classroom(
            db=db,
            instructor_id=current_instructor.user_id,
            classroom_data=classroom_data,
        )
    except (
        ClassroomCodeGenerationError,
        ClassroomAuditWorkflowError,
    ) as exc:
        raise_classroom_service_http_exception(exc)


@router.get(
    "/",
    response_model=list[ClassroomResponse],
    status_code=status.HTTP_200_OK,
    operation_id="list_instructor_classrooms",
    summary="List instructor classrooms",
    description=("Returns all classrooms owned by the authenticated instructor."),
)
def list_instructor_classrooms_endpoint(
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> list[Classroom]:
    return list_instructor_classrooms(
        db=db,
        instructor_id=current_instructor.user_id,
    )


@router.post(
    "/join",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="join_classroom",
    summary="Join a classroom",
    description=(
        "Enrolls the authenticated student using a backend-generated "
        "class code. Students cannot supply a student ID or class ID. "
        "A privacy-safe immutable audit record is created with the "
        "enrollment in the same transaction."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": ("No classroom matches the supplied code."),
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The classroom is inactive or the student is already enrolled."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": (
                "The enrollment and its required accountability record "
                "could not be completed."
            ),
        },
    },
)
def join_classroom_endpoint(
    enrollment_data: EnrollmentJoinRequest,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> Enrollment:
    try:
        return join_classroom(
            db=db,
            student_id=current_student.user_id,
            enrollment_data=enrollment_data,
        )
    except (
        ClassroomNotFoundError,
        ClassroomInactiveError,
        EnrollmentConflictError,
        ClassroomAuditWorkflowError,
    ) as exc:
        raise_classroom_service_http_exception(exc)


@router.get(
    "/mine",
    response_model=list[StudentClassroomResponse],
    status_code=status.HTTP_200_OK,
    operation_id="list_student_classrooms",
    summary="List enrolled classrooms",
    description=(
        "Returns classrooms associated with the authenticated "
        "student's own enrollment records."
    ),
)
def list_student_classrooms_endpoint(
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> list[dict]:
    return list_student_classrooms(
        db=db,
        student_id=current_student.user_id,
    )


@router.patch(
    "/enrollments/{enrollment_id}/status",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_200_OK,
    operation_id="update_enrollment_status",
    summary="Update enrollment status",
    description=(
        "Allows the owning instructor to activate, disable, or remove "
        "a student enrollment. A meaningful status transition and its "
        "privacy-safe immutable audit record are committed together."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": ("The enrollment belongs to another instructor's class."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The enrollment or classroom does not exist."),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": (
                "The enrollment status transition and its required "
                "accountability record could not be completed."
            ),
        },
    },
)
def update_enrollment_status_endpoint(
    status_data: EnrollmentStatusUpdate,
    enrollment_id: int = Path(
        ...,
        gt=0,
        description="Enrollment identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Enrollment:
    try:
        return update_enrollment_status(
            db=db,
            enrollment_id=enrollment_id,
            instructor_id=current_instructor.user_id,
            new_status=status_data.status,
        )
    except (
        EnrollmentNotFoundError,
        ClassroomNotFoundError,
        EnrollmentAccessDeniedError,
        ClassroomAuditWorkflowError,
    ) as exc:
        raise_classroom_service_http_exception(exc)


@router.get(
    "/{class_id}/members",
    response_model=list[ClassMemberResponse],
    status_code=status.HTTP_200_OK,
    operation_id="list_class_members",
    summary="List classroom members",
    description=(
        "Returns enrollment and basic account information for students "
        "inside a classroom owned by the authenticated instructor."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": ("The classroom belongs to another instructor."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The classroom does not exist."),
        },
    },
)
def list_class_members_endpoint(
    class_id: int = Path(
        ...,
        gt=0,
        description="Classroom identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> list[dict]:
    try:
        return list_class_members(
            db=db,
            class_id=class_id,
            instructor_id=current_instructor.user_id,
        )
    except (
        ClassroomNotFoundError,
        ClassroomAccessDeniedError,
    ) as exc:
        raise_classroom_service_http_exception(exc)


@router.post(
    "/{class_id}/regenerate-code",
    response_model=ClassroomCodeResponse,
    status_code=status.HTTP_200_OK,
    operation_id="regenerate_classroom_code",
    summary="Regenerate a classroom code",
    description=(
        "Replaces the classroom's existing join code with a new "
        "backend-generated code. The new code is never written to the "
        "audit metadata; only the accountable regeneration action is "
        "recorded."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": ("The classroom belongs to another instructor."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The classroom does not exist."),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": (
                "A unique replacement code could not be generated, or "
                "the required accountability record could not be saved."
            ),
        },
    },
)
def regenerate_class_code_endpoint(
    class_id: int = Path(
        ...,
        gt=0,
        description="Classroom identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Classroom:
    try:
        return regenerate_class_code(
            db=db,
            class_id=class_id,
            instructor_id=current_instructor.user_id,
        )
    except (
        ClassroomNotFoundError,
        ClassroomAccessDeniedError,
        ClassroomCodeGenerationError,
        ClassroomAuditWorkflowError,
    ) as exc:
        raise_classroom_service_http_exception(exc)


@router.get(
    "/{class_id}",
    response_model=ClassroomResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_instructor_classroom",
    summary="Get a classroom",
    description=("Returns a classroom owned by the authenticated instructor."),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": ("The classroom belongs to another instructor."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The classroom does not exist."),
        },
    },
)
def get_classroom_endpoint(
    class_id: int = Path(
        ...,
        gt=0,
        description="Classroom identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Classroom:
    try:
        return get_owned_classroom(
            db=db,
            class_id=class_id,
            instructor_id=current_instructor.user_id,
        )
    except (
        ClassroomNotFoundError,
        ClassroomAccessDeniedError,
    ) as exc:
        raise_classroom_service_http_exception(exc)


@router.patch(
    "/{class_id}",
    response_model=ClassroomResponse,
    status_code=status.HTTP_200_OK,
    operation_id="update_classroom",
    summary="Update a classroom",
    description=(
        "Updates classroom details or active status. The class code "
        "cannot be directly modified by the client. Meaningful changes "
        "create a privacy-safe immutable audit record. Changing the "
        "classroom from active to inactive also creates privacy-safe "
        "in-app notifications for eligible active enrolled students."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": ("The classroom belongs to another instructor."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The classroom does not exist."),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": (
                "The classroom change, required accountability record, "
                "or required archive-notification workflow could not be "
                "completed. The transaction is rolled back."
            ),
        },
    },
)
def update_classroom_endpoint(
    classroom_data: ClassroomUpdate,
    class_id: int = Path(
        ...,
        gt=0,
        description="Classroom identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Classroom:
    try:
        return update_classroom(
            db=db,
            class_id=class_id,
            instructor_id=current_instructor.user_id,
            classroom_data=classroom_data,
        )
    except (
        ClassroomNotFoundError,
        ClassroomAccessDeniedError,
        ClassroomNotificationWorkflowError,
        ClassroomAuditWorkflowError,
    ) as exc:
        raise_classroom_service_http_exception(exc)


# SECURITY BOUNDARY:
# instructor_id and student_id always come from authenticated users.
# Clients cannot create classrooms or enrollments for another account.

# CLASS-CODE BOUNDARY:
# Class codes are generated and regenerated only by the backend.
# Clients may submit a code to join but cannot assign a classroom code.
# Generated class-code values are never stored in audit metadata.

# AUTHORIZATION BOUNDARY:
# Only the classroom owner can view members, update the classroom,
# regenerate its code, or manage enrollment status.

# NOTIFICATION WORKFLOW BOUNDARY:
# Classroom archive notifications are created only when an owned
# classroom changes from active to inactive. A workflow failure maps to
# HTTP 503 and rolls back the archive transaction so the instructor may
# retry safely.

# AUDIT WORKFLOW BOUNDARY:
# Classroom creation, meaningful classroom updates, code regeneration,
# archive/reactivation transitions, student enrollment, and enrollment
# status transitions create immutable audit records. Audit workflow
# failures map to HTTP 503 and roll back the originating domain action.

# PRIVACY BOUNDARY:
# Classroom, enrollment, notification, and audit responses exclude class
# codes from audit payloads, source code, grades, feedback, AST findings,
# similarity records, hidden tests, execution output, coding-session
# telemetry, clipboard contents, pasted text, surveillance data, and
# automated misconduct conclusions.
