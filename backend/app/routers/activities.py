from typing import NoReturn
from uuid import UUID

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
from app.models.domain_models import (
    Task,
    TaskTestCase,
    User,
)
from app.schemas.coding_session_schema import (
    CodingSessionActivityUpdate,
    CodingSessionStartRequest,
    StudentCodingSessionResponse,
)
from app.schemas.task_schema import (
    ActivityType,
    StudentTaskResponse,
)
from app.schemas.task_test_case_schema import (
    StudentSampleTestCaseResponse,
)
from app.services.coding_session_service import (
    CodingSessionAccessDeniedError,
    CodingSessionEndedError,
    CodingSessionNotFoundError,
    CodingSessionPersistenceConflictError,
    CodingSessionPersistenceError,
    CodingSessionServiceError,
    CodingSessionStateConflictError,
    CodingSessionTaskUnavailableError,
    end_student_coding_session as end_student_coding_session_service,
    get_student_coding_session as get_student_coding_session_service,
    list_student_coding_sessions as list_student_coding_sessions_service,
    start_or_resume_student_coding_session,
    update_student_coding_session_activity as update_student_coding_session_activity_service,
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
        # A generic response avoids revealing whether an activity exists
        # but is unavailable because of enrollment, publication, or class.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    raise exc


def raise_coding_session_http_exception(
    exc: CodingSessionServiceError,
) -> NoReturn:
    if isinstance(
        exc,
        (
            CodingSessionTaskUnavailableError,
            CodingSessionNotFoundError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        CodingSessionAccessDeniedError,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        (
            CodingSessionEndedError,
            CodingSessionStateConflictError,
            CodingSessionPersistenceConflictError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        CodingSessionPersistenceError,
    ):
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail=str(exc),
        ) from exc

    raise HTTPException(
        status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
        detail=("The coding-session operation could not be completed."),
    ) from exc


@router.get(
    "/",
    response_model=list[StudentTaskResponse],
    status_code=status.HTTP_200_OK,
    operation_id="list_student_activities",
    summary="List available student activities",
    description=(
        "Returns published laboratory and homework activities from "
        "active classrooms where the authenticated student has an "
        "active enrollment. Hidden test cases and instructor-only "
        "ownership details are excluded."
    ),
)
def list_student_activities_endpoint(
    class_id: int | None = Query(
        default=None,
        gt=0,
        description=("Optional classroom identifier filter."),
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


# ------------------------------------------------------------------
# Pillar 8 student coding-session routes
# ------------------------------------------------------------------


@router.post(
    "/coding-sessions/",
    response_model=StudentCodingSessionResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="start_or_resume_student_coding_session",
    summary="Start or resume a coding session",
    description=(
        "Starts a backend-owned coding session for an available "
        "activity. When an active session already exists for the "
        "same student and activity, that session is resumed instead "
        "of creating a duplicate. No source code, clipboard content, "
        "or surveillance information is collected."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The activity is unavailable to the authenticated student."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "Multiple active sessions or a concurrent "
                "database conflict was detected."
            ),
        },
    },
)
def start_or_resume_coding_session_endpoint(
    session_data: CodingSessionStartRequest,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> StudentCodingSessionResponse:
    try:
        coding_session = start_or_resume_student_coding_session(
            db,
            student_id=current_student.user_id,
            task_id=session_data.task_id,
        )
    except CodingSessionServiceError as exc:
        raise_coding_session_http_exception(exc)

    return StudentCodingSessionResponse.model_validate(coding_session)


@router.get(
    "/coding-sessions/",
    response_model=list[StudentCodingSessionResponse],
    status_code=status.HTTP_200_OK,
    operation_id="list_student_coding_sessions",
    summary="List my coding sessions",
    description=(
        "Returns only coding sessions belonging to the authenticated "
        "student. Historical ended sessions remain available for the "
        "student's own records."
    ),
)
def list_coding_sessions_endpoint(
    task_id: int | None = Query(
        default=None,
        gt=0,
        description="Optional activity identifier filter.",
    ),
    active_only: bool = Query(
        default=False,
        description=("Return only sessions that have not ended."),
    ),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> list[StudentCodingSessionResponse]:
    coding_sessions = list_student_coding_sessions_service(
        db,
        student_id=current_student.user_id,
        task_id=task_id,
        active_only=active_only,
    )

    return [
        StudentCodingSessionResponse.model_validate(coding_session)
        for coding_session in coding_sessions
    ]


@router.get(
    "/coding-sessions/{session_id}",
    response_model=StudentCodingSessionResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_student_coding_session",
    summary="Get one of my coding sessions",
    description=(
        "Returns a coding session only when it belongs to the authenticated student."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The coding session was not found for the authenticated student."
            ),
        },
    },
)
def get_coding_session_endpoint(
    session_id: UUID = Path(
        ...,
        description="Coding-session UUID.",
    ),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> StudentCodingSessionResponse:
    try:
        coding_session = get_student_coding_session_service(
            db,
            student_id=current_student.user_id,
            session_id=str(session_id),
        )
    except CodingSessionServiceError as exc:
        raise_coding_session_http_exception(exc)

    return StudentCodingSessionResponse.model_validate(coding_session)


@router.patch(
    "/coding-sessions/{session_id}/activity",
    response_model=StudentCodingSessionResponse,
    status_code=status.HTTP_200_OK,
    operation_id="update_student_coding_session_activity",
    summary="Record aggregate session activity",
    description=(
        "Adds privacy-safe aggregate tab-switch, blocked-paste, and "
        "idle-duration increments. Sending zero increments acts as a "
        "heartbeat. The endpoint cannot receive clipboard content, "
        "pasted text, browsing history, individual keystrokes, screen "
        "recordings, webcam data, microphone data, or run-attempt totals."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": ("The coding session or its activity is unavailable."),
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The session has ended, a counter would overflow, "
                "or a concurrent update conflict occurred."
            ),
        },
    },
)
def update_coding_session_activity_endpoint(
    activity_data: CodingSessionActivityUpdate,
    session_id: UUID = Path(
        ...,
        description="Coding-session UUID.",
    ),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> StudentCodingSessionResponse:
    try:
        coding_session = update_student_coding_session_activity_service(
            db,
            student_id=current_student.user_id,
            session_id=str(session_id),
            activity_data=activity_data,
        )
    except CodingSessionServiceError as exc:
        raise_coding_session_http_exception(exc)

    return StudentCodingSessionResponse.model_validate(coding_session)


@router.post(
    "/coding-sessions/{session_id}/end",
    response_model=StudentCodingSessionResponse,
    status_code=status.HTTP_200_OK,
    operation_id="end_student_coding_session",
    summary="End a coding session",
    description=(
        "Ends a coding session belonging to the authenticated student. "
        "The operation is idempotent and preserves the original end "
        "timestamp when called repeatedly."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The coding session was not found for the authenticated student."
            ),
        },
    },
)
def end_coding_session_endpoint(
    session_id: UUID = Path(
        ...,
        description="Coding-session UUID.",
    ),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> StudentCodingSessionResponse:
    try:
        coding_session = end_student_coding_session_service(
            db,
            student_id=current_student.user_id,
            session_id=str(session_id),
        )
    except CodingSessionServiceError as exc:
        raise_coding_session_http_exception(exc)

    return StudentCodingSessionResponse.model_validate(coding_session)


# ------------------------------------------------------------------
# Existing student-safe task and sample-test-case routes
# ------------------------------------------------------------------


@router.get(
    "/{task_id}/sample-test-cases",
    response_model=list[StudentSampleTestCaseResponse],
    status_code=status.HTTP_200_OK,
    operation_id="list_student_sample_test_cases",
    summary="List public sample test cases",
    description=(
        "Returns only non-hidden sample test cases for an available "
        "activity. Hidden test inputs, expected outputs, and hidden-test "
        "metadata are never included in student-facing responses."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The activity does not exist or is unavailable to "
                "the authenticated student."
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
        "Returns student-safe activity details only when the activity "
        "is published, its classroom is active, and the authenticated "
        "student has an active enrollment. Test cases are retrieved "
        "separately."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The activity does not exist or is unavailable to "
                "the authenticated student."
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
# Activities and coding sessions are available only through active
# classroom enrollments.

# STUDENT-SAFE BOUNDARY:
# Student activity responses exclude instructor ownership internals.
# Coding-session responses do not expose student_id because ownership
# comes from the authenticated access token.

# TEST-CASE PRIVACY BOUNDARY:
# Hidden test records, inputs, expected outputs, and metadata must never
# be returned by any route in this student-facing router.

# SESSION PRIVACY BOUNDARY:
# Coding-session activity routes accept aggregate count increments only.
# They never accept or store clipboard contents, pasted text, individual
# keystrokes, browsing history, screen recordings, webcam data, or
# microphone data.

# RUN-ATTEMPT BOUNDARY:
# The client cannot update run_attempt_count. It must be incremented by
# the execution-request service after a valid request is persisted.

# EXECUTION BOUNDARY:
# These routes never execute starter code, test cases, or student Python.
# Code execution remains exclusive to the isolated worker integration.

# REVIEW BOUNDARY:
# Session counters and timestamps are review indicators only. They do not
# assign grades, behavior scores, cheating findings, or misconduct verdicts.
