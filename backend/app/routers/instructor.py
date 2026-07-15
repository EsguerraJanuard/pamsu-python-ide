from typing import NoReturn

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
from app.core.security import get_current_instructor
from app.models.domain_models import (
    Task,
    TaskTestCase,
    User,
)
from app.schemas.task_schema import (
    ActivityType,
    TaskCreate,
    TaskPublishRequest,
    TaskResponse,
    TaskUpdate,
)
from app.schemas.task_test_case_schema import (
    InstructorTaskTestCaseResponse,
    TaskTestCaseCreate,
    TaskTestCaseUpdate,
)
from app.services.task_service import (
    TaskAccessDeniedError,
    TaskClassAccessDeniedError,
    TaskClassInactiveError,
    TaskClassNotFoundError,
    TaskNotFoundError,
    TaskPublicationError,
    TaskTestCaseNotFoundError,
    TaskUpdateEmptyError,
    create_task as create_task_service,
    create_task_test_case,
    delete_task_test_case,
    get_instructor_task,
    get_instructor_test_case,
    list_instructor_tasks,
    list_instructor_test_cases,
    set_task_publication,
    update_task as update_task_service,
    update_task_test_case,
)


router = APIRouter(
    prefix="/instructors",
    tags=["Instructor"],
)


def raise_task_service_http_exception(
    exc: Exception,
) -> NoReturn:
    if isinstance(
        exc,
        (
            TaskNotFoundError,
            TaskClassNotFoundError,
            TaskTestCaseNotFoundError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        (
            TaskAccessDeniedError,
            TaskClassAccessDeniedError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if isinstance(exc, TaskUpdateEmptyError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        (
            TaskClassInactiveError,
            TaskPublicationError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    raise exc


@router.post(
    "/tasks/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_instructor_task",
    summary="Create an activity",
    description=(
        "Creates a draft laboratory or homework activity inside an active "
        "classroom owned by the authenticated instructor. Instructor identity, "
        "publication state, and publication timestamp are backend-controlled."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "The classroom belongs to another instructor.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The classroom does not exist.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "The classroom is inactive.",
        },
    },
)
def create_task_endpoint(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Task:
    try:
        return create_task_service(
            db=db,
            instructor_id=current_instructor.user_id,
            task_data=task_data,
        )
    except (
        TaskClassNotFoundError,
        TaskClassAccessDeniedError,
        TaskClassInactiveError,
    ) as exc:
        raise_task_service_http_exception(exc)


@router.get(
    "/tasks/",
    response_model=list[TaskResponse],
    status_code=status.HTTP_200_OK,
    operation_id="list_instructor_tasks",
    summary="List instructor activities",
    description=(
        "Returns activities owned by the authenticated instructor. "
        "Results may optionally be filtered by an owned classroom."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "The selected classroom belongs to another instructor.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The selected classroom does not exist.",
        },
    },
)
def list_tasks_endpoint(
    class_id: int | None = Query(
        default=None,
        gt=0,
        description="Optional classroom filter.",
    ),
    activity_type: ActivityType | None = Query(
        default=None,
        description="Optional activity-type filter.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> list[Task]:
    try:
        tasks = list_instructor_tasks(
            db=db,
            instructor_id=current_instructor.user_id,
            class_id=class_id,
        )
    except (
        TaskClassNotFoundError,
        TaskClassAccessDeniedError,
    ) as exc:
        raise_task_service_http_exception(exc)

    if activity_type is None:
        return tasks

    return [task for task in tasks if task.activity_type == activity_type]


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_instructor_task",
    summary="Get an instructor activity",
    description=(
        "Returns an activity only when it belongs to the authenticated instructor."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "The activity belongs to another instructor.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The activity does not exist.",
        },
    },
)
def get_task_endpoint(
    task_id: int = Path(
        ...,
        gt=0,
        description="Activity identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Task:
    try:
        return get_instructor_task(
            db=db,
            task_id=task_id,
            instructor_id=current_instructor.user_id,
        )
    except (
        TaskNotFoundError,
        TaskAccessDeniedError,
    ) as exc:
        raise_task_service_http_exception(exc)


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    operation_id="update_instructor_task",
    summary="Update an instructor activity",
    description=(
        "Updates selected activity fields. Moving an activity to another "
        "classroom is permitted only when that classroom is active and owned "
        "by the authenticated instructor."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "No activity fields were supplied.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "The activity or destination classroom belongs to another instructor."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The activity or destination classroom does not exist."),
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The destination classroom is inactive or the update would "
                "invalidate a published activity."
            ),
        },
    },
)
def update_task_endpoint(
    task_data: TaskUpdate,
    task_id: int = Path(
        ...,
        gt=0,
        description="Activity identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Task:
    try:
        return update_task_service(
            db=db,
            task_id=task_id,
            instructor_id=current_instructor.user_id,
            task_data=task_data,
        )
    except (
        TaskNotFoundError,
        TaskAccessDeniedError,
        TaskClassNotFoundError,
        TaskClassAccessDeniedError,
        TaskClassInactiveError,
        TaskUpdateEmptyError,
        TaskPublicationError,
    ) as exc:
        raise_task_service_http_exception(exc)


@router.patch(
    "/tasks/{task_id}/publication",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    operation_id="update_task_publication",
    summary="Publish or unpublish an activity",
    description=(
        "Publishes a valid activity or returns it to draft status. Publishing "
        "requires an active instructor-owned classroom and a future deadline "
        "when a deadline is configured."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": ("The activity or classroom belongs to another instructor."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The activity or classroom does not exist.",
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The activity cannot be published because its classroom or "
                "deadline is invalid."
            ),
        },
    },
)
def update_task_publication_endpoint(
    publication_data: TaskPublishRequest,
    task_id: int = Path(
        ...,
        gt=0,
        description="Activity identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Task:
    try:
        return set_task_publication(
            db=db,
            task_id=task_id,
            instructor_id=current_instructor.user_id,
            is_published=publication_data.is_published,
        )
    except (
        TaskNotFoundError,
        TaskAccessDeniedError,
        TaskClassNotFoundError,
        TaskClassAccessDeniedError,
        TaskClassInactiveError,
        TaskPublicationError,
    ) as exc:
        raise_task_service_http_exception(exc)


@router.post(
    "/tasks/{task_id}/test-cases",
    response_model=InstructorTaskTestCaseResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_task_test_case",
    summary="Create an activity test case",
    description=(
        "Creates a public sample or hidden test case for an activity owned "
        "by the authenticated instructor. Hidden inputs and expected outputs "
        "remain instructor-only."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "The activity belongs to another instructor.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The activity does not exist.",
        },
    },
)
def create_task_test_case_endpoint(
    test_case_data: TaskTestCaseCreate,
    task_id: int = Path(
        ...,
        gt=0,
        description="Activity identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> TaskTestCase:
    try:
        return create_task_test_case(
            db=db,
            task_id=task_id,
            instructor_id=current_instructor.user_id,
            test_case_data=test_case_data,
        )
    except (
        TaskNotFoundError,
        TaskAccessDeniedError,
    ) as exc:
        raise_task_service_http_exception(exc)


@router.get(
    "/tasks/{task_id}/test-cases",
    response_model=list[InstructorTaskTestCaseResponse],
    status_code=status.HTTP_200_OK,
    operation_id="list_instructor_task_test_cases",
    summary="List all activity test cases",
    description=(
        "Returns public and hidden test cases for an activity owned by the "
        "authenticated instructor."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "The activity belongs to another instructor.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The activity does not exist.",
        },
    },
)
def list_task_test_cases_endpoint(
    task_id: int = Path(
        ...,
        gt=0,
        description="Activity identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> list[TaskTestCase]:
    try:
        return list_instructor_test_cases(
            db=db,
            task_id=task_id,
            instructor_id=current_instructor.user_id,
        )
    except (
        TaskNotFoundError,
        TaskAccessDeniedError,
    ) as exc:
        raise_task_service_http_exception(exc)


@router.get(
    "/test-cases/{test_case_id}",
    response_model=InstructorTaskTestCaseResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_instructor_task_test_case",
    summary="Get an activity test case",
    description=(
        "Returns a test case only when its activity belongs to the "
        "authenticated instructor."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "The test case belongs to another instructor.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The test case or activity does not exist.",
        },
    },
)
def get_task_test_case_endpoint(
    test_case_id: int = Path(
        ...,
        gt=0,
        description="Test-case identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> TaskTestCase:
    try:
        return get_instructor_test_case(
            db=db,
            test_case_id=test_case_id,
            instructor_id=current_instructor.user_id,
        )
    except (
        TaskTestCaseNotFoundError,
        TaskNotFoundError,
        TaskAccessDeniedError,
    ) as exc:
        raise_task_service_http_exception(exc)


@router.patch(
    "/test-cases/{test_case_id}",
    response_model=InstructorTaskTestCaseResponse,
    status_code=status.HTTP_200_OK,
    operation_id="update_task_test_case",
    summary="Update an activity test case",
    description=(
        "Updates a public or hidden test case belonging to an activity owned "
        "by the authenticated instructor."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "No test-case fields were supplied.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "The test case belongs to another instructor.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The test case or activity does not exist.",
        },
    },
)
def update_task_test_case_endpoint(
    test_case_data: TaskTestCaseUpdate,
    test_case_id: int = Path(
        ...,
        gt=0,
        description="Test-case identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> TaskTestCase:
    try:
        return update_task_test_case(
            db=db,
            test_case_id=test_case_id,
            instructor_id=current_instructor.user_id,
            test_case_data=test_case_data,
        )
    except (
        TaskTestCaseNotFoundError,
        TaskNotFoundError,
        TaskAccessDeniedError,
        TaskUpdateEmptyError,
    ) as exc:
        raise_task_service_http_exception(exc)


@router.delete(
    "/test-cases/{test_case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_task_test_case",
    summary="Delete an activity test case",
    description=(
        "Deletes a test case only when its activity belongs to the "
        "authenticated instructor."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "The test case belongs to another instructor.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The test case or activity does not exist.",
        },
    },
)
def delete_task_test_case_endpoint(
    test_case_id: int = Path(
        ...,
        gt=0,
        description="Test-case identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Response:
    try:
        delete_task_test_case(
            db=db,
            test_case_id=test_case_id,
            instructor_id=current_instructor.user_id,
        )
    except (
        TaskTestCaseNotFoundError,
        TaskNotFoundError,
        TaskAccessDeniedError,
    ) as exc:
        raise_task_service_http_exception(exc)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# SECURITY BOUNDARY:
# instructor_id always comes from the authenticated instructor.
# Clients cannot create or modify activities or test cases for another user.

# TEST-CASE PRIVACY BOUNDARY:
# This instructor router may expose public and hidden test cases only to the
# instructor who owns the associated activity. Student-facing routes must use
# a separate response that excludes all hidden records.

# PUBLICATION BOUNDARY:
# Publication state and published_at are controlled by the backend.
# Clients cannot directly assign publication timestamps.

# REVIEW BOUNDARY:
# Test cases and automated execution results support instructor review.
# They do not independently determine the official academic grade.
