from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    get_current_instructor,
    get_current_student,
)
from app.models.domain_models import User
from app.schemas.reporting_schema import (
    ActivityCompletionSummaryResponse,
    ClassroomCompletionSummaryResponse,
    GradeDistributionResponse,
    MissingSubmissionListResponse,
    MissingSubmissionSortField,
    ReportingSortDirection,
    StudentProgressSummaryResponse,
)
from app.services.reporting_service import (
    MAX_REPORT_PAGE_SIZE,
    MIN_REPORT_PAGE_SIZE,
    ReportingAccessDeniedError,
    ReportingClassroomNotFoundError,
    ReportingExportError,
    ReportingFilterConflictError,
    ReportingPaginationError,
    ReportingServiceError,
    ReportingTaskNotFoundError,
    ReportingTaskUnavailableError,
    build_gradebook_csv_export,
    get_activity_completion_summary,
    get_classroom_completion_summary,
    get_grade_distribution,
    get_student_progress_summary,
    list_missing_submissions,
)


router = APIRouter(
    prefix="/reports",
    tags=["Reporting"],
)


def raise_reporting_service_http_exception(
    error: ReportingServiceError,
) -> None:
    if isinstance(
        error,
        (
            ReportingClassroomNotFoundError,
            ReportingTaskNotFoundError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    if isinstance(
        error,
        ReportingAccessDeniedError,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    if isinstance(
        error,
        (
            ReportingFilterConflictError,
            ReportingPaginationError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    if isinstance(
        error,
        ReportingTaskUnavailableError,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    if isinstance(
        error,
        ReportingExportError,
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="The reporting operation could not be completed.",
    ) from error


@router.get(
    "/classrooms/{class_id}/completion",
    response_model=ClassroomCompletionSummaryResponse,
    summary="Get classroom completion summary",
    description=(
        "Return an ownership-scoped completion summary for published, "
        "graded activities in an instructor-owned classroom. The response "
        "contains counts and percentages only and excludes submitted source "
        "code, standard input, evaluation analytics, session telemetry, and "
        "automated misconduct conclusions."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid reporting filters.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "The instructor does not own the classroom.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The classroom does not exist.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The reporting operation is temporarily unavailable.",
        },
    },
)
def read_classroom_completion_summary(
    class_id: int = Path(
        ...,
        gt=0,
        description="Instructor-owned classroom identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> ClassroomCompletionSummaryResponse:
    try:
        result = get_classroom_completion_summary(
            db,
            instructor_id=current_instructor.user_id,
            class_id=class_id,
        )
    except ReportingServiceError as error:
        raise_reporting_service_http_exception(error)

    return ClassroomCompletionSummaryResponse.model_validate(result)


@router.get(
    "/activities/{task_id}/completion",
    response_model=ActivityCompletionSummaryResponse,
    summary="Get activity completion summary",
    description=(
        "Return an ownership-scoped completion summary for one published, "
        "graded activity. Only official submissions and manually created "
        "instructor grades contribute to the report."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid reporting filters.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "The instructor does not own the activity.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The activity does not exist.",
        },
        status.HTTP_409_CONFLICT: {
            "description": ("The activity is not both published and graded."),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The reporting operation is temporarily unavailable.",
        },
    },
)
def read_activity_completion_summary(
    task_id: int = Path(
        ...,
        gt=0,
        description="Instructor-owned activity identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> ActivityCompletionSummaryResponse:
    try:
        result = get_activity_completion_summary(
            db,
            instructor_id=current_instructor.user_id,
            task_id=task_id,
        )
    except ReportingServiceError as error:
        raise_reporting_service_http_exception(error)

    return ActivityCompletionSummaryResponse.model_validate(result)


@router.get(
    "/classrooms/{class_id}/grade-distribution",
    response_model=GradeDistributionResponse,
    summary="Get manual-grade distribution",
    description=(
        "Return a classroom-wide or activity-scoped distribution derived "
        "only from manual instructor grades attached to official submission "
        "attempts. The endpoint does not calculate automated grades, risk "
        "scores, plagiarism rankings, or misconduct rankings."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": ("The selected classroom and activity filters conflict."),
        },
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "The instructor does not own the selected classroom or activity."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The classroom or activity does not exist.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The reporting operation is temporarily unavailable.",
        },
    },
)
def read_grade_distribution(
    class_id: int = Path(
        ...,
        gt=0,
        description="Instructor-owned classroom identifier.",
    ),
    task_id: int | None = Query(
        default=None,
        gt=0,
        description=(
            "Optional instructor-owned activity identifier within the classroom."
        ),
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> GradeDistributionResponse:
    try:
        result = get_grade_distribution(
            db,
            instructor_id=current_instructor.user_id,
            class_id=class_id,
            task_id=task_id,
        )
    except ReportingServiceError as error:
        raise_reporting_service_http_exception(error)

    return GradeDistributionResponse.model_validate(result)


@router.get(
    "/missing-submissions",
    response_model=MissingSubmissionListResponse,
    summary="List missing submissions",
    description=(
        "Return a bounded, deterministically sorted list of active students "
        "who do not have an official submission for published, graded "
        "activities owned by the authenticated instructor."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid pagination or reporting filters.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "The instructor does not own the selected classroom or activity."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The selected classroom or activity does not exist.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The reporting operation is temporarily unavailable.",
        },
    },
)
def read_missing_submissions(
    page: int = Query(
        default=1,
        ge=1,
        description="One-based report page.",
    ),
    page_size: int = Query(
        default=25,
        ge=MIN_REPORT_PAGE_SIZE,
        le=MAX_REPORT_PAGE_SIZE,
        description="Bounded number of report rows per page.",
    ),
    class_id: int | None = Query(
        default=None,
        gt=0,
        description="Optional instructor-owned classroom filter.",
    ),
    task_id: int | None = Query(
        default=None,
        gt=0,
        description="Optional instructor-owned activity filter.",
    ),
    sort_by: MissingSubmissionSortField = Query(
        default="student_name",
        description="Approved deterministic missing-submission sort field.",
    ),
    sort_direction: ReportingSortDirection = Query(
        default="asc",
        description="Ascending or descending sort direction.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> MissingSubmissionListResponse:
    try:
        result = list_missing_submissions(
            db,
            instructor_id=current_instructor.user_id,
            page=page,
            page_size=page_size,
            class_id=class_id,
            task_id=task_id,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
    except ReportingServiceError as error:
        raise_reporting_service_http_exception(error)

    return MissingSubmissionListResponse.model_validate(result)


@router.get(
    "/students/me/progress",
    response_model=StudentProgressSummaryResponse,
    summary="Get authenticated student progress",
    description=(
        "Return the authenticated student's personal progress across active "
        "classrooms. The response contains only the student's own completion "
        "counts and released manual-grade summaries. It excludes unreleased "
        "grades, source code, evaluation analytics, telemetry, and automated "
        "misconduct conclusions."
    ),
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The reporting operation is temporarily unavailable.",
        },
    },
)
def read_authenticated_student_progress(
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> StudentProgressSummaryResponse:
    try:
        result = get_student_progress_summary(
            db,
            student_id=current_student.user_id,
        )
    except ReportingServiceError as error:
        raise_reporting_service_http_exception(error)

    return StudentProgressSummaryResponse.model_validate(result)


@router.get(
    "/classrooms/{class_id}/gradebook.csv",
    response_class=Response,
    summary="Export privacy-safe gradebook CSV",
    description=(
        "Export official submission and manual-grade summary rows for an "
        "instructor-owned classroom or activity. The CSV excludes source "
        "code, standard input, feedback text, hidden tests, AST findings, "
        "similarity details, execution output, session telemetry, and "
        "automated misconduct rankings. Spreadsheet formula injection is "
        "escaped before serialization."
    ),
    responses={
        status.HTTP_200_OK: {
            "content": {
                "text/csv": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    },
                },
            },
            "description": "Privacy-safe gradebook CSV.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": ("The selected classroom and activity filters conflict."),
        },
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "The instructor does not own the selected classroom or activity."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The classroom or activity does not exist.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "The CSV export could not be generated.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The reporting operation is temporarily unavailable.",
        },
    },
)
def export_gradebook_csv(
    class_id: int = Path(
        ...,
        gt=0,
        description="Instructor-owned classroom identifier.",
    ),
    task_id: int | None = Query(
        default=None,
        gt=0,
        description=(
            "Optional instructor-owned activity identifier within the classroom."
        ),
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Response:
    try:
        export = build_gradebook_csv_export(
            db,
            instructor_id=current_instructor.user_id,
            class_id=class_id,
            task_id=task_id,
        )
    except ReportingServiceError as error:
        raise_reporting_service_http_exception(error)

    return Response(
        content=export["content"],
        media_type=export["media_type"],
        headers={
            "Content-Disposition": (f'attachment; filename="{export["filename"]}"'),
            "X-Report-Row-Count": str(export["row_count"]),
            "X-Report-Generated-At": export["generated_at"].isoformat(),
            "X-Report-Includes-Raw-Source": "false",
        },
    )


# AUTHORIZATION BOUNDARY:
# Instructor endpoints use only current_instructor.user_id. Student
# progress uses only current_student.user_id. Clients cannot select or
# impersonate another report owner.

# PRIVACY BOUNDARY:
# Reporting responses and CSV exports exclude raw source code, standard
# input, hidden tests, AST findings, similarity records, execution
# output, coding-session telemetry, clipboard or paste contents,
# browsing history, surveillance data, credentials, OTPs, JWTs,
# unreleased student-grade data, and misconduct conclusions.

# GRADING BOUNDARY:
# Grade distributions and exported grade values come only from manual
# InstructorGrade records. Automated indicators never set report grades,
# rank students, or determine plagiarism, cheating, or misconduct.
