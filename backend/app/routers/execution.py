from typing import NoReturn
from uuid import UUID

from app.core.database import get_db
from app.core.rate_limit import limit_per_user
from app.core.security import get_current_student, get_current_user
from app.integrations.partner_auth import (PartnerExecutionIdentity,
                                           get_authenticated_execution_partner)
from app.models.domain_models import User
from app.schemas.execution_schema import (
    ExecutionRequestCreate, ExecutionRequestKind, ExecutionStatus,
    Judge0CallbackPayload, PartnerExecutionResultUpdate,
    PartnerExecutionUpdateAcceptedResponse, StudentExecutionResponse)
from app.services.execution_service import (
    ExecutionAccessDeniedError, ExecutionCodingSessionUnavailableError,
    ExecutionPartnerCorrelationError, ExecutionPartnerReplayConflictError,
    ExecutionPartnerSequenceConflictError, ExecutionPersistenceConflictError,
    ExecutionPersistenceError, ExecutionRequestIdempotencyConflictError,
    ExecutionRequestIdempotencyInvalidError, ExecutionRequestNotFoundError,
    ExecutionServiceError, ExecutionStateConflictError,
    ExecutionSubmissionUnavailableError, ExecutionTaskUnavailableError,
    ExecutionWorkerUpdateInvalidError, apply_partner_execution_result_update,
    create_student_execution_request, get_student_execution_request,
    list_student_execution_requests)
from fastapi import (APIRouter, Depends, Header, HTTPException, Path, Query,
                     status)
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/execution",
    tags=["Execution"],
)

SUBMIT_RUN_CREATED_BY_SERVER = (
    "Submit runs are created automatically when you submit an attempt "
    "(POST /submissions/)."
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
# Removed legacy submission routes
# ------------------------------------------------------------------
#
# POST /execution/submissions/ and GET /execution/submissions/{sub_id} were
# removed on 2026-10-22 (audit-status.md, "Still open" item 5). The frontend
# never called them; they duplicated POST /submissions/, GET
# /submissions/{submission_id} (students) and GET
# /instructors/submissions/{submission_id} (instructors), and the POST had
# already been the source of an audit/notification bypass (item 7). Both
# paths now answer 404.


# ------------------------------------------------------------------
# Pillar 7 and Pillar 15 student execution-request routes
# ------------------------------------------------------------------


@router.post(
    "/requests/",
    response_model=StudentExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_student_execution_request",
    summary="Queue an execution request",
    # Each request is a paid Judge0 run.
    dependencies=[Depends(limit_per_user("execution_request", limit=5, window_seconds=10))],
    description=(
        "Persists a queued run or check execution request. Submit runs are "
        "created by POST /submissions/ for every attempt; a submit request "
        "here is refused with 409. "
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
                "execution content, the request could not be persisted "
                "because of a conflicting record, or it asked for a submit "
                "run (those are created by POST /submissions/)."
            ),
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "More than 5 execution requests in 10 seconds.",
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
    if execution_data.request_kind == "submit":
        # POST /submissions/ queues the submit run of every attempt itself.
        # A second, client-made submit run would only repeat a paid Judge0
        # call for the same immutable code.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=SUBMIT_RUN_CREATED_BY_SERVER,
        )

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
# Judge0 Adapter Webhook (Standard PUT Callback)
# ------------------------------------------------------------------

@router.put(
    "/internal/judge0-callback",
    response_model=PartnerExecutionUpdateAcceptedResponse,
    status_code=status.HTTP_200_OK,
    operation_id="apply_judge0_callback",
    summary="Accept and map Judge0 callback payloads",
)
def apply_judge0_callback_endpoint(
    execution_id: str,
    correlation_id: str,
    payload: Judge0CallbackPayload,
    db: Session = Depends(get_db),
    # We do NOT require partner_identity here since Judge0 CE callbacks lack our custom auth header
    # unless we configure it in Judge0 config, but query params act as a signature.
) -> PartnerExecutionUpdateAcceptedResponse:
    import base64
    import uuid
    from datetime import datetime, timezone

    from app.schemas.execution_schema import MAX_EXECUTION_OUTPUT_LENGTH
    from app.models.domain_models import ExecutionRequest

    # Verify that execution exists, matches secret correlation_id, and is not already finalized
    req_record = (
        db.query(ExecutionRequest)
        .filter(
            ExecutionRequest.execution_id == execution_id,
            ExecutionRequest.correlation_id == correlation_id,
        )
        .first()
    )
    if not req_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution request not found or correlation token mismatch.",
        )
    if req_record.status in {"completed", "failed", "runtime_error", "timed_out"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Execution request is already in a terminal state.",
        )

    # Map Judge0 status IDs:
    # 3 = Accepted -> completed
    # 5 = Time Limit Exceeded -> timed_out
    # 6 = Compile Error, 7-12 = Runtime Errors -> runtime_error
    # Others -> failed
    raw_status_id = payload.status.get("id") if isinstance(payload.status, dict) else None
    # Only an explicit Accepted (3) counts as completed. A missing,
    # malformed or still-queued status (1, 2) is a failed callback.
    status_id = raw_status_id if isinstance(raw_status_id, int) else None

    limit_reason = None
    if status_id == 3:
        mapped_status = "completed"
    elif status_id == 5:
        mapped_status = "timed_out"
        limit_reason = "time_limit_exceeded"
    elif status_id in [6, 7, 8, 9, 10, 11, 12]:
        mapped_status = "runtime_error"
    else:
        mapped_status = "failed"

    def decode_b64(val: str | None) -> str:
        if not val:
            return ""
        try:
            return base64.b64decode(val).decode("utf-8")
        except Exception:
            return val
            
    stdout_decoded = decode_b64(payload.stdout)
    stderr_decoded = decode_b64(payload.stderr)
    
    # Include compilation errors in stderr if present
    if payload.compile_output:
        stderr_decoded += "\n" + decode_b64(payload.compile_output)
        
    exec_time_ms = 0
    if payload.time:
        try:
            exec_time_ms = int(float(payload.time) * 1000)
        except ValueError:
            pass

    now_ts = datetime.now(timezone.utc)
    update_data = PartnerExecutionResultUpdate(
        execution_id=execution_id,
        correlation_id=correlation_id,
        update_id=str(uuid.uuid4()),
        sequence_number=1,
        worker_task_id=payload.token or str(uuid.uuid4()),
        status=mapped_status,
        stdout=stdout_decoded[:MAX_EXECUTION_OUTPUT_LENGTH],
        stderr=stderr_decoded[:MAX_EXECUTION_OUTPUT_LENGTH],
        exit_code=0 if mapped_status == "completed" else 1,
        execution_time_ms=exec_time_ms,
        limit_reason=limit_reason,
        started_at=now_ts,
        completed_at=now_ts,
    )

    from app.services.execution_service import \
        apply_partner_execution_result_update
    try:
        return apply_partner_execution_result_update(
            db,
            update_data=update_data,
        )
    except ExecutionServiceError as exc:
        raise_execution_service_http_exception(exc)


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

from app.schemas.lint_schema import LintRequest, LintResult
from app.services.lint_service import lint_python_code


@router.post(
    "/lint",
    response_model=LintResult,
    dependencies=[Depends(limit_per_user("lint", limit=60, window_seconds=60))],
)
def lint_endpoint(
    request: LintRequest,
    _current_user: User = Depends(get_current_user),
) -> LintResult:
    # Static analysis only (pyflakes parses, never runs, the code). A plain
    # def runs in the threadpool so CPU-bound linting cannot stall the event
    # loop, and authentication keeps it from being an open compute endpoint.
    return lint_python_code(request.code)
