from typing import NoReturn

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_student
from app.models.domain_models import User
from app.schemas.submission_schema import (
    StudentSubmissionResponse,
    SubmissionCreate,
    SubmissionStatus,
)
from app.services.submission_service import (
    CodingSessionUnavailableError,
    SubmissionAuditWorkflowError,
    SubmissionConflictError,
    SubmissionNotFoundError,
    SubmissionNotificationWorkflowError,
    SubmissionPersistenceError,
    SubmissionServiceError,
    SubmissionTaskNotGradableError,
    SubmissionTaskUnavailableError,
    create_student_submission,
    get_student_official_submission,
    get_student_submission,
    list_student_submissions,
)


router = APIRouter(
    prefix="/submissions",
    tags=["Submissions"],
)


def _raise_submission_service_error(
    error: SubmissionServiceError,
) -> NoReturn:
    if isinstance(
        error,
        (
            SubmissionTaskUnavailableError,
            SubmissionNotFoundError,
            CodingSessionUnavailableError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    if isinstance(
        error,
        (
            SubmissionTaskNotGradableError,
            SubmissionConflictError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    if isinstance(
        error,
        (
            SubmissionNotificationWorkflowError,
            SubmissionAuditWorkflowError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    if isinstance(
        error,
        SubmissionPersistenceError,
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="The submission operation could not be completed.",
    ) from error


@router.post(
    "/",
    response_model=StudentSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a submission attempt",
    operation_id="create_student_submission_attempt",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": ("The activity or coding session is unavailable."),
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The activity does not accept official submissions "
                "or the attempt could not be saved safely."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": (
                "The submission, required accountability record, "
                "academic event, or instructor notification could not "
                "be saved. No new attempt was created."
            ),
        },
    },
)
def create_submission_endpoint(
    payload: SubmissionCreate,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> StudentSubmissionResponse:
    """
    Create a new immutable attempt for the authenticated student.

    The backend calculates student ownership, attempt number,
    official-attempt state, status, and timestamps. The submission,
    immutable accountability record, academic event, and instructor
    notification are saved as one transaction.

    This endpoint does not execute Python code, calculate an automated
    grade, or make an automated misconduct determination.
    """

    try:
        submission = create_student_submission(
            db,
            student_id=current_student.user_id,
            payload=payload,
        )
    except SubmissionServiceError as error:
        _raise_submission_service_error(error)

    return StudentSubmissionResponse.model_validate(submission)


@router.get(
    "/",
    response_model=list[StudentSubmissionResponse],
    status_code=status.HTTP_200_OK,
    summary="List my submission attempts",
    operation_id="list_my_submission_attempts",
)
def list_my_submissions_endpoint(
    task_id: int | None = Query(
        default=None,
        gt=0,
        description=("Optionally return attempts for one activity."),
    ),
    submission_status: SubmissionStatus | None = Query(
        default=None,
        alias="status",
        description=("Optionally filter attempts by workflow status."),
    ),
    official_only: bool = Query(
        default=False,
        description=("Return only attempts currently marked as official."),
    ),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> list[StudentSubmissionResponse]:
    """
    Return only attempts belonging to the authenticated student.

    Student responses exclude instructor-only AST, similarity,
    grading, and internal review information.
    """

    submissions = list_student_submissions(
        db,
        student_id=current_student.user_id,
        task_id=task_id,
        status=submission_status,
        official_only=official_only,
    )

    return [
        StudentSubmissionResponse.model_validate(submission)
        for submission in submissions
    ]


@router.get(
    "/official/{task_id}",
    response_model=StudentSubmissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Read my official attempt for an activity",
    operation_id="read_my_official_submission_attempt",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "No official attempt exists for the authenticated student and activity."
            ),
        },
    },
)
def get_my_official_submission_endpoint(
    task_id: int,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> StudentSubmissionResponse:
    if task_id < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Task ID must be greater than zero.",
        )

    try:
        submission = get_student_official_submission(
            db,
            student_id=current_student.user_id,
            task_id=task_id,
        )
    except SubmissionServiceError as error:
        _raise_submission_service_error(error)

    return StudentSubmissionResponse.model_validate(submission)


@router.get(
    "/{submission_id}",
    response_model=StudentSubmissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Read one of my submission attempts",
    operation_id="read_my_submission_attempt",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The submission was not found for the authenticated student."
            ),
        },
    },
)
def get_my_submission_endpoint(
    submission_id: int,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> StudentSubmissionResponse:
    if submission_id < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Submission ID must be greater than zero.",
        )

    try:
        submission = get_student_submission(
            db,
            student_id=current_student.user_id,
            submission_id=submission_id,
        )
    except SubmissionServiceError as error:
        _raise_submission_service_error(error)

    return StudentSubmissionResponse.model_validate(submission)


# AUTHENTICATION BOUNDARY:
# All routes use the authenticated student account. A client cannot
# create or retrieve submission attempts for another student.

# AUDIT WORKFLOW BOUNDARY:
# SubmissionAuditWorkflowError maps to HTTP 503 because the submission
# and its immutable accountability record must be saved as one
# transaction. A failed audit workflow creates no attempt and restores
# the previous official-attempt state.

# NOTIFICATION WORKFLOW BOUNDARY:
# SubmissionNotificationWorkflowError maps to HTTP 503 because the
# submission, audit record, academic event, and instructor notification
# must succeed as one transaction. A failed workflow creates no attempt,
# allowing the student to retry safely.

# PRIVACY BOUNDARY:
# Student responses and audit metadata exclude source-analysis details,
# hidden test cases, similarity results, internal instructor review
# notes, coding-session telemetry, source code, standard input,
# execution output, grades, feedback, clipboard or paste contents,
# surveillance data, and automated misconduct conclusions.
