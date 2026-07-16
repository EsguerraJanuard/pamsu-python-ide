from typing import Any, NoReturn

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    status,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    get_current_instructor,
    get_current_user,
)
from app.models.domain_models import User
from app.schemas.evaluation_schema import (
    EvaluationStatusUpdate,
    InstructorGradeCreate,
    InstructorGradeResponse,
    InstructorGradeUpdate,
    InstructorSubmissionEvaluationResponse,
    StudentSubmissionEvaluationResponse,
)
from app.services.evaluation_service import (
    EvaluationAccessDeniedError,
    EvaluationPersistenceConflictError,
    EvaluationPersistenceError,
    EvaluationServiceError,
    EvaluationStateConflictError,
    GradeNotFoundError,
    GradeUnavailableError,
    GradeValidationError,
    InvalidEvaluationResultError,
    OfficialSubmissionRequiredError,
    SubmissionNotFoundError,
    TaskNotFoundError,
    create_or_update_grade,
    evaluate_submission_by_id,
    get_instructor_evaluation_details,
    get_student_evaluation_details,
    patch_grade,
    update_submission_status,
)


router = APIRouter(
    prefix="/evaluation",
    tags=["Evaluation"],
)


REVIEW_NOTICE = (
    "Automated AST and similarity results are review indicators only. "
    "They do not independently determine plagiarism, misconduct, "
    "or the official grade."
)


class EvaluationResponse(BaseModel):
    """
    Instructor-only result of a newly performed static evaluation.

    This response contains review indicators only. It does not contain
    or create an official grade, plagiarism verdict, or misconduct
    decision.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    sub_id: int = Field(
        ...,
        gt=0,
        description="Evaluated submission identifier.",
    )

    student_id: int = Field(
        ...,
        gt=0,
        description="Owner of the evaluated submission.",
    )

    task_id: int = Field(
        ...,
        gt=0,
        description="Associated activity identifier.",
    )

    ast_pass_fail: bool | None = Field(
        default=None,
        description=(
            "Whether the source satisfied the configured structural AST rules."
        ),
    )

    jaccard_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description=("Highest source-code similarity score expressed as a percentage."),
    )

    highest_match_sub_id: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Submission identifier with the highest comparison "
            "score, when a comparison exists."
        ),
    )

    ast_details: dict[str, Any] = Field(
        default_factory=dict,
        description=("Detailed static structural-analysis findings."),
    )

    jaccard_details: dict[str, Any] = Field(
        default_factory=dict,
        description=("Detailed source-similarity review information."),
    )

    review_notice: str = REVIEW_NOTICE

    @field_validator(
        "jaccard_score",
    )
    @classmethod
    def validate_jaccard_score(
        cls,
        value: float | None,
    ) -> float | None:
        if value is not None and not 0 <= value <= 100:
            raise ValueError("Jaccard score must be between 0 and 100.")

        return value


EvaluationDetailsResponse = (
    StudentSubmissionEvaluationResponse | InstructorSubmissionEvaluationResponse
)


def raise_evaluation_service_http_exception(
    exc: EvaluationServiceError,
) -> NoReturn:
    if isinstance(
        exc,
        (
            SubmissionNotFoundError,
            TaskNotFoundError,
            GradeNotFoundError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        EvaluationAccessDeniedError,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        GradeValidationError,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        (
            OfficialSubmissionRequiredError,
            GradeUnavailableError,
            EvaluationStateConflictError,
            EvaluationPersistenceConflictError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        (
            InvalidEvaluationResultError,
            EvaluationPersistenceError,
        ),
    ):
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail=str(exc),
        ) from exc

    raise HTTPException(
        status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
        detail=("The evaluation operation could not be completed."),
    ) from exc


@router.post(
    "/submissions/{sub_id}",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    operation_id="evaluate_submission",
    summary="Evaluate a submission",
    description=(
        "Runs static AST checks and source-code similarity analysis "
        "for a submission belonging to an activity owned by the "
        "authenticated instructor. Results are stored and returned "
        "only as review indicators. Student code is never executed, "
        "and no official grade or misconduct verdict is generated."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "The submission belongs to an activity owned by another instructor."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The submission or associated activity does not exist."),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": (
                "The static evaluator returned invalid data or "
                "the evaluation could not be persisted."
            ),
        },
    },
)
def evaluate_submission(
    sub_id: int = Path(
        ...,
        gt=0,
        description="Submission identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> EvaluationResponse:
    try:
        evaluation_result = evaluate_submission_by_id(
            db=db,
            sub_id=sub_id,
            instructor_id=current_instructor.user_id,
        )
    except EvaluationServiceError as exc:
        raise_evaluation_service_http_exception(exc)

    return EvaluationResponse.model_validate(evaluation_result)


@router.get(
    "/submissions/{sub_id}",
    response_model=EvaluationDetailsResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_submission_evaluation",
    summary="Get authorized evaluation details",
    description=(
        "Students may view only their own student-safe evaluation "
        "record. Unreleased grades, instructor identity, full AST "
        "findings, similarity comparison records, and comparison "
        "submission identifiers are excluded from student responses. "
        "Instructors may view full review details only for activities "
        "that they own."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "The authenticated user does not own or manage "
                "the requested submission."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The submission does not exist."),
        },
    },
)
def get_submission_evaluation(
    sub_id: int = Path(
        ...,
        gt=0,
        description="Submission identifier.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvaluationDetailsResponse:
    try:
        if current_user.role == "student":
            evaluation_details = get_student_evaluation_details(
                db,
                sub_id=sub_id,
                student_id=current_user.user_id,
            )

            return StudentSubmissionEvaluationResponse.model_validate(
                evaluation_details
            )

        if current_user.role == "instructor":
            evaluation_details = get_instructor_evaluation_details(
                db,
                sub_id=sub_id,
                instructor_id=current_user.user_id,
            )

            return InstructorSubmissionEvaluationResponse.model_validate(
                evaluation_details
            )

        raise EvaluationAccessDeniedError(
            "Evaluation access is unavailable for this account."
        )

    except EvaluationServiceError as exc:
        raise_evaluation_service_http_exception(exc)


@router.patch(
    "/submissions/{sub_id}/status",
    response_model=InstructorSubmissionEvaluationResponse,
    status_code=status.HTTP_200_OK,
    operation_id="update_evaluation_status",
    summary="Update submission review status",
    description=(
        "Explicitly updates the review status of a submission "
        "belonging to an activity owned by the authenticated "
        "instructor. Marking a submission as graded requires an "
        "existing manual grade. Grade creation itself does not "
        "silently change submission status."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": ("The submission belongs to another instructor."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The submission does not exist."),
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The requested review status is inconsistent "
                "with the submission or manual-grade state."
            ),
        },
    },
)
def update_eval_status(
    status_update: EvaluationStatusUpdate,
    sub_id: int = Path(
        ...,
        gt=0,
        description="Submission identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> InstructorSubmissionEvaluationResponse:
    try:
        update_submission_status(
            db=db,
            sub_id=sub_id,
            status_update=status_update,
            current_user=current_instructor,
        )

        updated_submission = get_instructor_evaluation_details(
            db,
            sub_id=sub_id,
            instructor_id=current_instructor.user_id,
        )

    except EvaluationServiceError as exc:
        raise_evaluation_service_http_exception(exc)

    return InstructorSubmissionEvaluationResponse.model_validate(updated_submission)


@router.put(
    "/submissions/{sub_id}/grade",
    response_model=InstructorGradeResponse,
    status_code=status.HTTP_200_OK,
    operation_id="set_instructor_grade",
    summary="Set an official manual instructor grade",
    description=(
        "Creates or fully replaces a manual grade for the latest "
        "accepted official submission of a graded activity owned by "
        "the authenticated instructor. Automated AST, similarity, "
        "execution, and session indicators are never used to populate "
        "the grade. This operation does not change submission status."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": ("The submission belongs to another instructor."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The submission does not exist."),
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The activity is not graded, the submission is "
                "unofficial, unaccepted, rejected, or a concurrent "
                "grade operation conflicted."
            ),
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": ("The grade values violate the manual-grade contract."),
        },
    },
)
def set_grade(
    grade_in: InstructorGradeCreate,
    sub_id: int = Path(
        ...,
        gt=0,
        description="Submission identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> InstructorGradeResponse:
    try:
        grade = create_or_update_grade(
            db=db,
            sub_id=sub_id,
            grade_in=grade_in,
            current_user=current_instructor,
        )
    except EvaluationServiceError as exc:
        raise_evaluation_service_http_exception(exc)

    return InstructorGradeResponse.model_validate(grade)


@router.patch(
    "/submissions/{sub_id}/grade",
    response_model=InstructorGradeResponse,
    status_code=status.HTTP_200_OK,
    operation_id="patch_instructor_grade",
    summary="Patch an official manual instructor grade",
    description=(
        "Updates selected fields of an existing manual instructor "
        "grade. At least one field is required, and the final score "
        "cannot exceed the final maximum score. This operation does "
        "not change submission status."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "The submission or existing grade belongs to another instructor."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The submission or manual grade does not exist."),
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The activity or submission is unavailable for official grading."
            ),
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": (
                "No grade fields were supplied or the final "
                "score exceeds the final maximum score."
            ),
        },
    },
)
def patch_eval_grade(
    grade_update: InstructorGradeUpdate,
    sub_id: int = Path(
        ...,
        gt=0,
        description="Submission identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> InstructorGradeResponse:
    try:
        grade = patch_grade(
            db=db,
            sub_id=sub_id,
            grade_update=grade_update,
            current_user=current_instructor,
        )
    except EvaluationServiceError as exc:
        raise_evaluation_service_http_exception(exc)

    return InstructorGradeResponse.model_validate(grade)


# AUTHORIZATION BOUNDARY:
# Students may view only their own student-safe evaluation response.
# Instructors may evaluate, review, grade, and update status only for
# submissions belonging to activities that they own.

# STUDENT VISIBILITY BOUNDARY:
# Student responses exclude full AST findings, similarity comparison
# records, compared-submission identifiers, instructor identity, and
# all unreleased manual-grade information.

# EXECUTION BOUNDARY:
# Evaluation performs static structural and source-similarity analysis
# only. Student Python must never execute inside FastAPI.

# GRADING BOUNDARY:
# Official grades are manually created or updated by an authorized
# instructor for the latest accepted official submission. Grade changes
# do not silently change the submission review status.

# REVIEW BOUNDARY:
# AST findings and Jaccard similarity values support instructor review
# only. They never independently determine plagiarism, misconduct,
# cheating, copying, or the official academic grade.
