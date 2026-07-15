from typing import NoReturn

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_student
from app.models.domain_models import Task, TaskTestCase, User
from app.schemas.task_schema import (
    ActivityType,
    StudentTaskResponse,
)
from app.schemas.task_test_case_schema import (
    StudentSampleTestCaseResponse,
)
from app.services.task_service import (
    StudentTaskUnavailableError,
    get_student_task,
    list_student_sample_test_cases,
    list_student_tasks,
)


router = APIRouter(
    prefix="/activities",
    tags=["Activities"],
)


def raise_student_activity_http_exception(
    exc: Exception,
) -> NoReturn:
    if isinstance(
        exc,
        StudentTaskUnavailableError,
    ):
        # A single generic response avoids revealing whether an activity
        # exists but is unavailable because of ownership, enrollment,
        # publication, or classroom state.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    raise exc


@router.get(
    "/",
    response_model=list[StudentTaskResponse],
    status_code=status.HTTP_200_OK,
    operation_id="list_student_activities",
    summary="List available student activities",
    description=(
        "Returns published laboratory and homework activities from active "
        "classrooms where the authenticated student has an active enrollment. "
        "Hidden test cases and instructor-only ownership details are excluded."
    ),
)
def list_student_activities_endpoint(
    class_id: int | None = Query(
        default=None,
        gt=0,
        description="Optional classroom identifier filter.",
    ),
    activity_type: ActivityType | None = Query(
        default=None,
        description=("Optional filter for laboratory or homework activities."),
    ),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> list[Task]:
    return list_student_tasks(
        db=db,
        student_id=current_student.user_id,
        class_id=class_id,
        activity_type=activity_type,
    )


@router.get(
    "/{task_id}/sample-test-cases",
    response_model=list[StudentSampleTestCaseResponse],
    status_code=status.HTTP_200_OK,
    operation_id="list_student_sample_test_cases",
    summary="List public sample test cases",
    description=(
        "Returns only non-hidden sample test cases for an available activity. "
        "Hidden test inputs, expected outputs, and hidden-test metadata are "
        "never included in student-facing responses."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The activity does not exist or is unavailable to the "
                "authenticated student."
            ),
        },
    },
)
def list_student_sample_test_cases_endpoint(
    task_id: int = Path(
        ...,
        gt=0,
        description="Activity identifier.",
    ),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> list[TaskTestCase]:
    try:
        return list_student_sample_test_cases(
            db=db,
            task_id=task_id,
            student_id=current_student.user_id,
        )
    except StudentTaskUnavailableError as exc:
        raise_student_activity_http_exception(exc)


@router.get(
    "/{task_id}",
    response_model=StudentTaskResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_student_activity",
    summary="Get an available student activity",
    description=(
        "Returns student-safe activity details only when the activity is "
        "published, its classroom is active, and the authenticated student "
        "has an active enrollment. Test cases are retrieved separately."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The activity does not exist or is unavailable to the "
                "authenticated student."
            ),
        },
    },
)
def get_student_activity_endpoint(
    task_id: int = Path(
        ...,
        gt=0,
        description="Activity identifier.",
    ),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> Task:
    try:
        return get_student_task(
            db=db,
            task_id=task_id,
            student_id=current_student.user_id,
        )
    except StudentTaskUnavailableError as exc:
        raise_student_activity_http_exception(exc)


# AUTHORIZATION BOUNDARY:
# student_id always comes from the authenticated student.
# Activities are available only through active classroom enrollments.

# STUDENT-SAFE BOUNDARY:
# Student activity responses exclude instructor ownership internals.
# Public sample-test endpoints return only records where is_hidden is false.

# TEST-CASE PRIVACY BOUNDARY:
# Hidden test records, inputs, expected outputs, and metadata must never be
# returned by any route in this student-facing router.

# EXECUTION BOUNDARY:
# These endpoints provide activity configuration only. They never execute
# starter code, test cases, or student-submitted Python source.
