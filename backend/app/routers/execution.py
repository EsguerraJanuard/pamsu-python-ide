from datetime import datetime, timezone
from typing import NoReturn
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Path,
    Query,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.integrations.partner_auth import (
    PartnerExecutionIdentity,
    get_authenticated_execution_partner,
)
from app.core.security import (
    get_current_student,
    get_current_user,
)
from app.models.domain_models import (
    CodingSession,
    Enrollment,
    Submission,
    Task,
    User,
)
from app.schemas.execution_schema import (
    ExecutionRequestCreate,
    ExecutionRequestKind,
    ExecutionStatus,
    PartnerExecutionResultUpdate,
    PartnerExecutionUpdateAcceptedResponse,
    StudentExecutionResponse,
)
from app.schemas.submission_schema import (
    SubmissionCreate,
    SubmissionResponse,
)
from app.services.execution_service import (
    ExecutionAccessDeniedError,
    ExecutionCodingSessionUnavailableError,
    ExecutionPartnerCorrelationError,
    ExecutionPartnerReplayConflictError,
    ExecutionPartnerSequenceConflictError,
    ExecutionPersistenceConflictError,
    ExecutionPersistenceError,
    ExecutionRequestIdempotencyConflictError,
    ExecutionRequestIdempotencyInvalidError,
    ExecutionRequestNotFoundError,
    ExecutionServiceError,
    ExecutionStateConflictError,
    ExecutionSubmissionUnavailableError,
    ExecutionTaskUnavailableError,
    ExecutionWorkerUpdateInvalidError,
    apply_partner_execution_result_update,
    create_student_execution_request,
    get_student_execution_request,
    list_student_execution_requests,
)


router = APIRouter(
    prefix="/execution",
    tags=["Execution"],
)


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_utc_datetime(
    value: datetime,
) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(
            tzinfo=timezone.utc,
        )

    return value.astimezone(
        timezone.utc,
    )


def is_past_due(
    due_at: datetime | None,
) -> bool:
    if due_at is None:
        return False

    return get_utc_now() >= normalize_utc_datetime(due_at)


def get_task_or_404(
    *,
    db: Session,
    task_id: int,
) -> Task:
    task = (
        db.query(Task)
        .filter(
            Task.task_id == task_id,
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    return task


def get_submission_or_404(
    *,
    db: Session,
    sub_id: int,
) -> Submission:
    submission = (
        db.query(Submission)
        .filter(
            Submission.sub_id == sub_id,
        )
        .first()
    )

    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )

    return submission


def verify_student_task_access(
    *,
    db: Session,
    task: Task,
    student_id: int,
) -> None:
    if not task.is_published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This activity is not available for submission.",
        )

    if not task.is_graded:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Practice activities do not accept graded submissions.",
        )

    if is_past_due(task.due_at):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The submission period for this activity has ended.",
        )

    # Transitional compatibility for records created before classroom
    # ownership was introduced. New tasks must belong to a classroom.
    if task.class_id is None:
        return

    if task.classroom is None or not task.classroom.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The class for this activity is no longer active.",
        )

    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.class_id == task.class_id,
            Enrollment.student_id == student_id,
            Enrollment.status == "active",
        )
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be actively enrolled in the class.",
        )


def verify_coding_session(
    *,
    db: Session,
    coding_session_id: str | None,
    student_id: int,
    task_id: int,
) -> CodingSession | None:
    if coding_session_id is None:
        return None

    coding_session = (
        db.query(CodingSession)
        .filter(
            CodingSession.session_id == coding_session_id,
        )
        .first()
    )

    if coding_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coding session not found.",
        )

    if coding_session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot use another student's coding session.",
        )

    if coding_session.task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The coding session does not belong to this activity.",
        )

    return coding_session


def verify_submission_access(
    *,
    db: Session,
    submission: Submission,
    current_user: User,
) -> None:
    if current_user.role == "student":
        if submission.student_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own submissions.",
            )

        return

    if current_user.role == "instructor":
        task = get_task_or_404(
            db=db,
            task_id=submission.task_id,
        )

        if task.instructor_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=("You can only access submissions for activities that you own."),
            )

        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied.",
    )


def raise_execution_service_http_exception(
    exc: ExecutionServiceError,
) -> NoReturn:
    if isinstance(
        exc,
        (
            ExecutionTaskUnavailableError,
            ExecutionSubmissionUnavailableError,
            ExecutionCodingSessionUnavailableError,
            ExecutionRequestNotFoundError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        ExecutionAccessDeniedError,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        (
            ExecutionWorkerUpdateInvalidError,
            ExecutionRequestIdempotencyInvalidError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        (
            ExecutionRequestIdempotencyConflictError,
            ExecutionPartnerCorrelationError,
            ExecutionPartnerReplayConflictError,
            ExecutionPartnerSequenceConflictError,
            ExecutionStateConflictError,
            ExecutionPersistenceConflictError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        ExecutionPersistenceError,
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="The execution request operation could not be completed.",
    ) from exc


# ------------------------------------------------------------------
# Legacy submission routes
# ------------------------------------------------------------------
#
# These endpoints are retained for backward compatibility with the
# existing API and test suite. New client integrations should use the
# dedicated /submissions router introduced in Pillar 6.


@router.post(
    "/submissions/",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_student_submission",
    summary="Create a legacy submission attempt",
    description=(
        "Creates a new immutable code-submission attempt for the "
        "authenticated student. Previous attempts remain stored, "
        "while the newest accepted attempt becomes official. "
        "This endpoint does not execute student code."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "The activity is unpublished, the class is inactive, "
                "the student is not enrolled, or the coding session "
                "belongs to another student."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The task or supplied coding session does not exist."),
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The activity does not accept graded submissions, "
                "the deadline has passed, the coding session belongs "
                "to another activity, or a concurrent attempt conflict "
                "occurred."
            ),
        },
    },
)
def create_submission(
    submission_data: SubmissionCreate,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> Submission:
    task = get_task_or_404(
        db=db,
        task_id=submission_data.task_id,
    )

    verify_student_task_access(
        db=db,
        task=task,
        student_id=current_student.user_id,
    )

    verify_coding_session(
        db=db,
        coding_session_id=submission_data.coding_session_id,
        student_id=current_student.user_id,
        task_id=task.task_id,
    )

    try:
        previous_attempts = (
            db.query(Submission)
            .filter(
                Submission.student_id == current_student.user_id,
                Submission.task_id == task.task_id,
            )
            .order_by(Submission.attempt_number.desc())
            .with_for_update()
            .all()
        )

        next_attempt_number = (
            previous_attempts[0].attempt_number + 1 if previous_attempts else 1
        )

        for previous_attempt in previous_attempts:
            if previous_attempt.is_official:
                previous_attempt.is_official = False

        new_submission = Submission(
            student_id=current_student.user_id,
            task_id=task.task_id,
            coding_session_id=submission_data.coding_session_id,
            attempt_number=next_attempt_number,
            raw_code=submission_data.raw_code,
            standard_input=submission_data.standard_input,
            status="awaiting_review",
            is_official=True,
            accepted_at=get_utc_now(),
            jaccard_score=None,
            ast_pass_fail=None,
        )

        db.add(new_submission)
        db.commit()
        db.refresh(new_submission)

        return new_submission

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A submission attempt was created "
                "at the same time. Please retry "
                "the submission."
            ),
        ) from exc

    except Exception:
        db.rollback()
        raise


@router.get(
    "/submissions/{sub_id}",
    response_model=SubmissionResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_submission",
    summary="Get an authorized legacy submission",
    description=(
        "Students may retrieve only their own submissions. "
        "Instructors may retrieve submissions only for tasks "
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
            "description": ("The submission or its associated task does not exist."),
        },
    },
)
def get_submission(
    sub_id: int = Path(
        ...,
        gt=0,
        description="Submission identifier.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Submission:
    submission = get_submission_or_404(
        db=db,
        sub_id=sub_id,
    )

    verify_submission_access(
        db=db,
        submission=submission,
        current_user=current_user,
    )

    return submission


# ------------------------------------------------------------------
# Pillar 7 and Pillar 15 student execution-request routes
# ------------------------------------------------------------------


@router.post(
    "/requests/",
    response_model=StudentExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_student_execution_request",
    summary="Queue an execution request",
    description=(
        "Persists a queued run, check, or submit execution request. "
        "The endpoint does not execute Python code and does not call "
        "the host operating system. The optional Idempotency-Key "
        "header prevents duplicate execution requests when a client "
        "safely retries the same logical operation."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": ("The supplied Idempotency-Key header is not a valid UUID."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The activity, submission, or coding session "
                "is unavailable to the authenticated student."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The Idempotency-Key was already used for different "
                "execution content, or the request could not be persisted "
                "because of a conflicting record."
            ),
        },
    },
)
def create_execution_request_endpoint(
    execution_data: ExecutionRequestCreate,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        min_length=1,
        max_length=100,
        description=(
            "Optional UUID that identifies one logical student "
            "execution request across safe client retries."
        ),
    ),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> StudentExecutionResponse:
    try:
        execution_request = create_student_execution_request(
            db,
            student_id=current_student.user_id,
            payload=execution_data,
            request_idempotency_key=idempotency_key,
        )
    except ExecutionServiceError as exc:
        raise_execution_service_http_exception(exc)

    return StudentExecutionResponse.model_validate(
        execution_request,
    )


@router.get(
    "/requests/",
    response_model=list[StudentExecutionResponse],
    status_code=status.HTTP_200_OK,
    operation_id="list_student_execution_requests",
    summary="List my execution requests",
    description=(
        "Returns only execution requests belonging to the "
        "authenticated student. Results may be filtered by activity, "
        "request kind, or lifecycle status."
    ),
)
def list_execution_requests_endpoint(
    task_id: int | None = Query(
        default=None,
        gt=0,
        description="Optional activity filter.",
    ),
    request_kind: ExecutionRequestKind | None = Query(
        default=None,
        description="Optional run, check, or submit filter.",
    ),
    execution_status: ExecutionStatus | None = Query(
        default=None,
        alias="status",
        description="Optional execution lifecycle-status filter.",
    ),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> list[StudentExecutionResponse]:
    execution_requests = list_student_execution_requests(
        db,
        student_id=current_student.user_id,
        task_id=task_id,
        request_kind=request_kind,
        status=execution_status,
    )

    return [
        StudentExecutionResponse.model_validate(
            execution_request,
        )
        for execution_request in execution_requests
    ]


@router.get(
    "/requests/{execution_id}",
    response_model=StudentExecutionResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_student_execution_request",
    summary="Get one of my execution requests",
    description=(
        "Returns an execution request only when it belongs "
        "to the authenticated student. Internal worker task "
        "identifiers and idempotency metadata are not exposed."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The execution request was not found for the authenticated student."
            ),
        },
    },
)
def get_execution_request_endpoint(
    execution_id: UUID = Path(
        ...,
        description="Execution-request UUID.",
    ),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> StudentExecutionResponse:
    try:
        execution_request = get_student_execution_request(
            db,
            student_id=current_student.user_id,
            execution_id=str(execution_id),
        )
    except ExecutionServiceError as exc:
        raise_execution_service_http_exception(exc)

    return StudentExecutionResponse.model_validate(
        execution_request,
    )


# ------------------------------------------------------------------
# Pillar 14 authenticated partner-result route
# ------------------------------------------------------------------


@router.post(
    "/internal/partner-results",
    response_model=PartnerExecutionUpdateAcceptedResponse,
    status_code=status.HTTP_200_OK,
    operation_id="apply_partner_execution_result_update",
    summary="Apply an authenticated isolated-worker result update",
    description=(
        "Accepts a lifecycle or execution-result update only from the "
        "trusted isolated-execution partner. The route validates partner "
        "authentication, execution identity, correlation ID, update ID, "
        "strict sequence ordering, worker-task identity, lifecycle "
        "transitions, and replay safety. It never executes Python code."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": (
                "The authenticated partner supplied lifecycle data that "
                "cannot be applied to the execution request."
            ),
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": ("The execution-partner token is missing or invalid."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The referenced execution request does not exist."),
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The correlation ID, replay payload, sequence number, "
                "worker identity, lifecycle transition, or persistence "
                "state conflicts with the stored execution."
            ),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": ("The authenticated partner update could not be persisted."),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": (
                "The execution-partner authentication boundary is not configured."
            ),
        },
    },
)
def apply_partner_execution_result_endpoint(
    update_data: PartnerExecutionResultUpdate,
    db: Session = Depends(get_db),
    _partner_identity: PartnerExecutionIdentity = Depends(
        get_authenticated_execution_partner,
    ),
) -> PartnerExecutionUpdateAcceptedResponse:
    try:
        return apply_partner_execution_result_update(
            db,
            update_data=update_data,
        )
    except ExecutionServiceError as exc:
        raise_execution_service_http_exception(exc)


# SECURITY BOUNDARY:
# student_id always comes from the authenticated student. Clients cannot
# create a submission or execution request for another student.

# EXECUTION BOUNDARY:
# This router validates authorization and stores source snapshots and
# execution-request metadata only. It must never execute student Python
# inside FastAPI, React, or the host operating system.

# REQUEST IDEMPOTENCY BOUNDARY:
# Idempotency-Key is optional, UUID-based, and scoped to the authenticated
# student. The service persists only the normalized key and a SHA-256 digest
# of the resolved immutable request snapshot. It never exposes those fields
# in student responses.

# WORKER BOUNDARY:
# No student or instructor route may assign worker_task_id or update
# lifecycle/result fields. Only the authenticated internal partner route
# may apply isolated-worker updates.

# IMMUTABILITY BOUNDARY:
# Every execution request stores its own source and standard-input
# snapshot. Submit requests use the immutable linked submission snapshot.

# REVIEW BOUNDARY:
# Execution output, errors, and resource-limit results support instructor
# review. They do not automatically assign a grade or misconduct verdict.
