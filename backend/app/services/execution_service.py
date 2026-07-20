import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.domain_models import (
    Classroom,
    CodingSession,
    Enrollment,
    ExecutionRequest,
    PartnerExecutionUpdateRecord,
    Submission,
    Task,
)
from app.schemas.execution_schema import (
    MAX_WORKER_TASK_ID_LENGTH,
    ExecutionRequestCreate,
    ExecutionRequestKind,
    ExecutionStatus,
    ExecutionWorkerUpdate,
    PartnerExecutionDispatchRequest,
    PartnerExecutionLimits,
    PartnerExecutionResultUpdate,
    PartnerExecutionUpdateAcceptedResponse,
    TERMINAL_EXECUTION_STATUSES,
    is_execution_status_transition_allowed,
)
from app.services.coding_session_service import (
    CodingSessionCounterOverflowError,
    CodingSessionEndedError,
    CodingSessionNotFoundError,
    CodingSessionServiceError,
    increment_coding_session_run_attempt,
)


class ExecutionServiceError(Exception):
    """Base exception for execution-request workflow errors."""


class ExecutionTaskUnavailableError(
    ExecutionServiceError,
):
    """Raised when a student cannot execute code for an activity."""


class ExecutionSubmissionUnavailableError(
    ExecutionServiceError,
):
    """Raised when a linked submission is invalid or inaccessible."""


class ExecutionCodingSessionUnavailableError(
    ExecutionServiceError,
):
    """Raised when a coding session is invalid or inaccessible."""


class ExecutionRequestNotFoundError(
    ExecutionServiceError,
):
    """Raised when an execution request cannot be found."""


class ExecutionAccessDeniedError(
    ExecutionServiceError,
):
    """Raised when an instructor cannot access an execution request."""


class ExecutionStateConflictError(
    ExecutionServiceError,
):
    """Raised when an invalid lifecycle transition is requested."""


class ExecutionWorkerUpdateInvalidError(
    ExecutionServiceError,
):
    """Raised when worker lifecycle data is inconsistent."""


class ExecutionPartnerCorrelationError(
    ExecutionServiceError,
):
    """Raised when a partner result uses the wrong correlation ID."""


class ExecutionPartnerReplayConflictError(
    ExecutionServiceError,
):
    """Raised when an update ID is replayed with different content."""


class ExecutionPartnerSequenceConflictError(
    ExecutionServiceError,
):
    """Raised when a partner update sequence is stale or out of order."""


class ExecutionPersistenceConflictError(
    ExecutionServiceError,
):
    """Raised when execution data conflicts."""


class ExecutionPersistenceError(
    ExecutionServiceError,
):
    """Raised when an unexpected database error occurs."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_database_datetime(
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(
            tzinfo=timezone.utc,
        )

    return value.astimezone(
        timezone.utc,
    )


def _commit_execution_transaction(
    db: Session,
) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()

        raise ExecutionPersistenceConflictError(
            "The execution-request operation conflicted "
            "with another database operation."
        ) from error
    except SQLAlchemyError as error:
        db.rollback()

        raise ExecutionPersistenceError(
            "The execution request could not be saved."
        ) from error


def _get_student_execution_task(
    db: Session,
    *,
    student_id: int,
    task_id: int,
) -> Task:
    """
    Resolve a published task accessible through an active enrollment.

    A generic unavailable response prevents students from discovering
    unpublished activities or classrooms they cannot access.
    """

    task = (
        db.query(Task)
        .join(
            Classroom,
            Task.class_id == Classroom.class_id,
        )
        .join(
            Enrollment,
            Enrollment.class_id == Classroom.class_id,
        )
        .filter(
            Task.task_id == task_id,
            Task.class_id.is_not(None),
            Task.is_published.is_(True),
            Classroom.is_active.is_(True),
            Enrollment.student_id == student_id,
            Enrollment.status == "active",
        )
        .first()
    )

    if task is None:
        raise ExecutionTaskUnavailableError(
            "The activity is unavailable for execution."
        )

    return task


def _get_student_submission(
    db: Session,
    *,
    student_id: int,
    task_id: int,
    submission_id: int,
) -> Submission:
    """
    Resolve the student's latest accepted official submission.

    A submit execution request cannot reference an obsolete,
    unofficial, rejected, or unaccepted attempt.
    """

    submission = (
        db.query(Submission)
        .filter(
            Submission.sub_id == submission_id,
            Submission.student_id == student_id,
            Submission.task_id == task_id,
            Submission.is_official.is_(True),
            Submission.accepted_at.is_not(None),
        )
        .first()
    )

    if submission is None:
        raise ExecutionSubmissionUnavailableError(
            "The official submission is unavailable for this activity."
        )

    return submission


def _get_student_coding_session(
    db: Session,
    *,
    student_id: int,
    task_id: int,
    coding_session_id: str,
    require_active: bool,
) -> CodingSession:
    query = db.query(CodingSession).filter(
        CodingSession.session_id == coding_session_id,
        CodingSession.student_id == student_id,
        CodingSession.task_id == task_id,
    )

    if require_active:
        query = query.filter(
            CodingSession.ended_at.is_(None),
        )

    coding_session = query.first()

    if coding_session is None:
        raise ExecutionCodingSessionUnavailableError(
            "The coding session is unavailable for this activity."
        )

    return coding_session


def _resolve_execution_snapshot(
    db: Session,
    *,
    student_id: int,
    task: Task,
    payload: ExecutionRequestCreate,
) -> tuple[
    str,
    str,
    int | None,
    str | None,
]:
    """
    Resolve the immutable source and input snapshot.

    Run and check requests use the source supplied in the request.
    Submit requests use the immutable source and standard input stored
    in the latest accepted official submission attempt.
    """

    if payload.request_kind in {
        "run",
        "check",
    }:
        if payload.source_code is None:
            raise ExecutionWorkerUpdateInvalidError(
                "Run and check requests require source code."
            )

        if payload.coding_session_id is not None:
            _get_student_coding_session(
                db,
                student_id=student_id,
                task_id=task.task_id,
                coding_session_id=payload.coding_session_id,
                require_active=True,
            )

        return (
            payload.source_code,
            payload.standard_input,
            None,
            payload.coding_session_id,
        )

    if payload.submission_id is None:
        raise ExecutionSubmissionUnavailableError(
            "Submit requests require an official submission."
        )

    submission = _get_student_submission(
        db,
        student_id=student_id,
        task_id=task.task_id,
        submission_id=payload.submission_id,
    )

    submission_session_id = submission.coding_session_id

    if (
        payload.coding_session_id is not None
        and payload.coding_session_id != submission_session_id
    ):
        raise ExecutionCodingSessionUnavailableError(
            "The coding session does not match the official submission."
        )

    if submission_session_id is not None:
        _get_student_coding_session(
            db,
            student_id=student_id,
            task_id=task.task_id,
            coding_session_id=submission_session_id,
            require_active=False,
        )

    return (
        submission.raw_code,
        submission.standard_input,
        submission.sub_id,
        submission_session_id,
    )


def _increment_linked_session_attempt(
    db: Session,
    *,
    student_id: int,
    task_id: int,
    coding_session_id: str | None,
    request_kind: ExecutionRequestKind,
) -> None:
    """
    Increment the server-controlled run-attempt counter.

    The update participates in the execution-request transaction.
    A failed execution-request insert therefore does not leave behind
    an incorrect counter increment.
    """

    if coding_session_id is None:
        return

    try:
        increment_coding_session_run_attempt(
            db,
            student_id=student_id,
            task_id=task_id,
            session_id=coding_session_id,
            require_active=(request_kind != "submit"),
            commit=False,
        )
    except (
        CodingSessionNotFoundError,
        CodingSessionEndedError,
    ) as error:
        db.rollback()

        raise ExecutionCodingSessionUnavailableError(
            "The coding session is unavailable for this execution request."
        ) from error
    except CodingSessionCounterOverflowError as error:
        db.rollback()

        raise ExecutionPersistenceConflictError(
            "The coding session run-attempt counter cannot accept another increment."
        ) from error
    except CodingSessionServiceError as error:
        db.rollback()

        raise ExecutionPersistenceError(
            "The coding-session attempt counter could not be updated."
        ) from error


def create_student_execution_request(
    db: Session,
    *,
    student_id: int,
    payload: ExecutionRequestCreate,
) -> ExecutionRequest:
    """
    Persist a queued execution request without executing Python code.

    Partner correlation and dispatch-idempotency identifiers are generated
    by the database model defaults and are never accepted from the student.

    When the request references a coding session, its server-controlled
    run-attempt counter is incremented in the same transaction.
    """

    task = _get_student_execution_task(
        db,
        student_id=student_id,
        task_id=payload.task_id,
    )

    (
        source_code,
        standard_input,
        submission_id,
        coding_session_id,
    ) = _resolve_execution_snapshot(
        db,
        student_id=student_id,
        task=task,
        payload=payload,
    )

    _increment_linked_session_attempt(
        db,
        student_id=student_id,
        task_id=task.task_id,
        coding_session_id=coding_session_id,
        request_kind=payload.request_kind,
    )

    execution_request = ExecutionRequest(
        student_id=student_id,
        task_id=task.task_id,
        submission_id=submission_id,
        coding_session_id=coding_session_id,
        request_kind=payload.request_kind,
        status="queued",
        source_code=source_code,
        standard_input=standard_input,
        stdout="",
        stderr="",
        exit_code=None,
        execution_time_ms=None,
        limit_reason=None,
        worker_task_id=None,
        started_at=None,
        completed_at=None,
        last_partner_sequence=0,
    )

    db.add(execution_request)

    _commit_execution_transaction(db)

    db.refresh(execution_request)

    return execution_request


def list_student_execution_requests(
    db: Session,
    *,
    student_id: int,
    task_id: int | None = None,
    request_kind: ExecutionRequestKind | None = None,
    status: ExecutionStatus | None = None,
) -> list[ExecutionRequest]:
    query = db.query(ExecutionRequest).filter(
        ExecutionRequest.student_id == student_id,
    )

    if task_id is not None:
        query = query.filter(
            ExecutionRequest.task_id == task_id,
        )

    if request_kind is not None:
        query = query.filter(
            ExecutionRequest.request_kind == request_kind,
        )

    if status is not None:
        query = query.filter(
            ExecutionRequest.status == status,
        )

    return query.order_by(
        ExecutionRequest.queued_at.desc(),
        ExecutionRequest.execution_id.desc(),
    ).all()


def get_student_execution_request(
    db: Session,
    *,
    student_id: int,
    execution_id: str,
) -> ExecutionRequest:
    execution_request = (
        db.query(ExecutionRequest)
        .filter(
            ExecutionRequest.execution_id == execution_id,
            ExecutionRequest.student_id == student_id,
        )
        .first()
    )

    if execution_request is None:
        raise ExecutionRequestNotFoundError("Execution request not found.")

    return execution_request


def _get_instructor_owned_task(
    db: Session,
    *,
    instructor_id: int,
    task_id: int,
) -> Task:
    task = (
        db.query(Task)
        .join(
            Classroom,
            Task.class_id == Classroom.class_id,
        )
        .filter(
            Task.task_id == task_id,
            Classroom.instructor_id == instructor_id,
        )
        .first()
    )

    if task is None:
        raise ExecutionAccessDeniedError(
            "You can only review execution requests from your own classrooms."
        )

    return task


def list_instructor_task_execution_requests(
    db: Session,
    *,
    instructor_id: int,
    task_id: int,
    student_id: int | None = None,
    request_kind: ExecutionRequestKind | None = None,
    status: ExecutionStatus | None = None,
) -> list[ExecutionRequest]:
    task = _get_instructor_owned_task(
        db,
        instructor_id=instructor_id,
        task_id=task_id,
    )

    query = db.query(ExecutionRequest).filter(
        ExecutionRequest.task_id == task.task_id,
    )

    if student_id is not None:
        query = query.filter(
            ExecutionRequest.student_id == student_id,
        )

    if request_kind is not None:
        query = query.filter(
            ExecutionRequest.request_kind == request_kind,
        )

    if status is not None:
        query = query.filter(
            ExecutionRequest.status == status,
        )

    return query.order_by(
        ExecutionRequest.queued_at.desc(),
        ExecutionRequest.execution_id.desc(),
    ).all()


def get_instructor_execution_request(
    db: Session,
    *,
    instructor_id: int,
    execution_id: str,
) -> ExecutionRequest:
    execution_request = (
        db.query(ExecutionRequest)
        .join(
            Task,
            ExecutionRequest.task_id == Task.task_id,
        )
        .join(
            Classroom,
            Task.class_id == Classroom.class_id,
        )
        .filter(
            ExecutionRequest.execution_id == execution_id,
            Classroom.instructor_id == instructor_id,
        )
        .first()
    )

    if execution_request is None:
        raise ExecutionAccessDeniedError(
            "You can only review execution requests from your own classrooms."
        )

    return execution_request


def get_internal_execution_request(
    db: Session,
    *,
    execution_id: str,
    lock_for_update: bool = False,
) -> ExecutionRequest:
    query = db.query(ExecutionRequest).filter(
        ExecutionRequest.execution_id == execution_id,
    )

    if lock_for_update:
        query = query.with_for_update()

    execution_request = query.first()

    if execution_request is None:
        raise ExecutionRequestNotFoundError("Execution request not found.")

    return execution_request


def build_partner_execution_dispatch(
    execution_request: ExecutionRequest,
    *,
    limits: PartnerExecutionLimits | None = None,
) -> PartnerExecutionDispatchRequest:
    """
    Build the internal immutable request handed to the isolated worker.

    This function performs no dispatch and executes no student code.
    """

    if execution_request.task_id is None:
        raise ExecutionWorkerUpdateInvalidError(
            "The execution request has no activity identifier."
        )

    queued_at = _normalize_database_datetime(
        execution_request.queued_at,
    )

    if queued_at is None:
        raise ExecutionWorkerUpdateInvalidError(
            "The execution request has no queue timestamp."
        )

    return PartnerExecutionDispatchRequest(
        execution_id=execution_request.execution_id,
        correlation_id=execution_request.correlation_id,
        idempotency_key=execution_request.dispatch_idempotency_key,
        request_kind=execution_request.request_kind,
        task_id=execution_request.task_id,
        submission_id=execution_request.submission_id,
        coding_session_id=execution_request.coding_session_id,
        source_code=execution_request.source_code,
        standard_input=execution_request.standard_input,
        limits=limits or PartnerExecutionLimits(),
        queued_at=queued_at,
    )


def _validate_status_transition(
    *,
    current_status: str,
    target_status: str,
) -> None:
    if current_status == target_status:
        if current_status in TERMINAL_EXECUTION_STATUSES:
            raise ExecutionStateConflictError(
                "A terminal execution request cannot accept another update."
            )

        return

    if is_execution_status_transition_allowed(
        current_status=current_status,
        next_status=target_status,
    ):
        return

    if current_status in TERMINAL_EXECUTION_STATUSES:
        raise ExecutionStateConflictError(
            "A terminal execution request cannot transition to another status."
        )

    raise ExecutionStateConflictError(
        f"Execution status cannot transition from {current_status} to {target_status}."
    )


def _validate_worker_timestamps(
    *,
    execution_request: ExecutionRequest,
    values: dict,
    target_status: str,
) -> None:
    started_at = values.get(
        "started_at",
        execution_request.started_at,
    )

    completed_at = values.get(
        "completed_at",
        execution_request.completed_at,
    )

    started_at = _normalize_database_datetime(started_at)
    completed_at = _normalize_database_datetime(completed_at)

    if completed_at is not None and target_status not in TERMINAL_EXECUTION_STATUSES:
        raise ExecutionWorkerUpdateInvalidError(
            "Only terminal execution requests may have a completion timestamp."
        )

    if (
        started_at is not None
        and completed_at is not None
        and completed_at < started_at
    ):
        raise ExecutionWorkerUpdateInvalidError(
            "Execution completion time cannot be earlier than its start time."
        )


def update_execution_from_worker(
    db: Session,
    *,
    execution_id: str,
    update_data: ExecutionWorkerUpdate,
) -> ExecutionRequest:
    """
    Apply the legacy trusted worker lifecycle/result update.

    New partner integrations should use apply_partner_execution_result_update,
    which adds correlation, idempotency, and sequence enforcement.
    """

    execution_request = get_internal_execution_request(
        db,
        execution_id=execution_id,
        lock_for_update=True,
    )

    values = update_data.model_dump(
        exclude_unset=True,
    )

    target_status = values.get(
        "status",
        execution_request.status,
    )

    _validate_status_transition(
        current_status=execution_request.status,
        target_status=target_status,
    )

    if target_status == "running":
        values.setdefault(
            "started_at",
            execution_request.started_at or _utc_now(),
        )

        if values.get("completed_at") is not None:
            raise ExecutionWorkerUpdateInvalidError(
                "A running execution request cannot have a completion timestamp."
            )

    if target_status in TERMINAL_EXECUTION_STATUSES:
        values.setdefault(
            "started_at",
            execution_request.started_at or _utc_now(),
        )

        values.setdefault(
            "completed_at",
            execution_request.completed_at or _utc_now(),
        )

    _validate_worker_timestamps(
        execution_request=execution_request,
        values=values,
        target_status=target_status,
    )

    for field_name, value in values.items():
        setattr(
            execution_request,
            field_name,
            value,
        )

    _commit_execution_transaction(db)

    db.refresh(execution_request)

    return execution_request


def assign_worker_task_id(
    db: Session,
    *,
    execution_id: str,
    worker_task_id: str,
) -> ExecutionRequest:
    """
    Attach the partner worker's identifier without changing ownership,
    source snapshots, results, or academic review fields.
    """

    execution_request = get_internal_execution_request(
        db,
        execution_id=execution_id,
        lock_for_update=True,
    )

    normalized_worker_task_id = worker_task_id.strip()

    if not normalized_worker_task_id:
        raise ExecutionWorkerUpdateInvalidError("Worker task ID cannot be empty.")

    if len(normalized_worker_task_id) > MAX_WORKER_TASK_ID_LENGTH:
        raise ExecutionWorkerUpdateInvalidError(
            f"Worker task ID cannot exceed {MAX_WORKER_TASK_ID_LENGTH} characters."
        )

    if (
        execution_request.worker_task_id is not None
        and execution_request.worker_task_id != normalized_worker_task_id
    ):
        raise ExecutionStateConflictError(
            "The execution request already has a different worker task ID."
        )

    execution_request.worker_task_id = normalized_worker_task_id

    _commit_execution_transaction(db)

    db.refresh(execution_request)

    return execution_request


def _partner_update_payload_digest(
    update_data: PartnerExecutionResultUpdate,
) -> str:
    canonical_payload = json.dumps(
        update_data.model_dump(
            mode="json",
        ),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _find_partner_update_record(
    db: Session,
    *,
    update_id: str,
) -> PartnerExecutionUpdateRecord | None:
    return (
        db.query(PartnerExecutionUpdateRecord)
        .filter(
            PartnerExecutionUpdateRecord.update_id == update_id,
        )
        .first()
    )


def _build_partner_update_acknowledgment(
    *,
    record: PartnerExecutionUpdateRecord,
    replayed: bool,
) -> PartnerExecutionUpdateAcceptedResponse:
    accepted_at = _normalize_database_datetime(
        record.accepted_at,
    )

    if accepted_at is None:
        raise ExecutionPersistenceError(
            "The accepted partner update has no acceptance timestamp."
        )

    return PartnerExecutionUpdateAcceptedResponse(
        execution_id=record.execution_id,
        correlation_id=record.correlation_id,
        update_id=record.update_id,
        status=record.status,
        sequence_number=record.sequence_number,
        replayed=replayed,
        accepted_at=accepted_at,
    )


def _resolve_existing_partner_replay(
    *,
    existing_record: PartnerExecutionUpdateRecord,
    payload_digest: str,
) -> PartnerExecutionUpdateAcceptedResponse:
    if existing_record.payload_digest != payload_digest:
        raise ExecutionPartnerReplayConflictError(
            "The partner update ID was already used for different content."
        )

    return _build_partner_update_acknowledgment(
        record=existing_record,
        replayed=True,
    )


def _validate_partner_sequence(
    *,
    execution_request: ExecutionRequest,
    sequence_number: int,
) -> None:
    expected_sequence = execution_request.last_partner_sequence + 1

    if sequence_number != expected_sequence:
        raise ExecutionPartnerSequenceConflictError(
            "Partner result updates must use the next sequence number. "
            f"Expected {expected_sequence}, received {sequence_number}."
        )


def _validate_partner_worker_identity(
    *,
    execution_request: ExecutionRequest,
    worker_task_id: str,
) -> None:
    if (
        execution_request.worker_task_id is not None
        and execution_request.worker_task_id != worker_task_id
    ):
        raise ExecutionStateConflictError(
            "The execution request is assigned to a different worker task."
        )


def _partner_execution_update_values(
    *,
    execution_request: ExecutionRequest,
    update_data: PartnerExecutionResultUpdate,
) -> dict:
    values = update_data.model_dump(
        exclude={
            "execution_id",
            "correlation_id",
            "update_id",
            "sequence_number",
            "error_code",
            "error_message",
        },
        exclude_unset=True,
    )

    target_status = update_data.status

    _validate_status_transition(
        current_status=execution_request.status,
        target_status=target_status,
    )

    if target_status == "running":
        values.setdefault(
            "started_at",
            execution_request.started_at or _utc_now(),
        )
        values.pop(
            "completed_at",
            None,
        )

    if target_status in TERMINAL_EXECUTION_STATUSES:
        values.setdefault(
            "started_at",
            execution_request.started_at or _utc_now(),
        )
        values["completed_at"] = update_data.completed_at

    _validate_worker_timestamps(
        execution_request=execution_request,
        values=values,
        target_status=target_status,
    )

    return values


def apply_partner_execution_result_update(
    db: Session,
    *,
    update_data: PartnerExecutionResultUpdate,
) -> PartnerExecutionUpdateAcceptedResponse:
    """
    Atomically apply an authenticated partner result update.

    Authentication is enforced by the calling router or integration adapter.
    This service validates execution identity, correlation, worker identity,
    lifecycle transition, strict sequence ordering, and idempotent replay.

    A repeated update_id with identical canonical content returns a replay
    acknowledgment without mutating the execution a second time.
    """

    payload_digest = _partner_update_payload_digest(
        update_data,
    )

    existing_record = _find_partner_update_record(
        db,
        update_id=update_data.update_id,
    )

    if existing_record is not None:
        return _resolve_existing_partner_replay(
            existing_record=existing_record,
            payload_digest=payload_digest,
        )

    execution_request = get_internal_execution_request(
        db,
        execution_id=update_data.execution_id,
        lock_for_update=True,
    )

    if execution_request.correlation_id != update_data.correlation_id:
        raise ExecutionPartnerCorrelationError(
            "The partner correlation ID does not match the execution request."
        )

    _validate_partner_sequence(
        execution_request=execution_request,
        sequence_number=update_data.sequence_number,
    )

    _validate_partner_worker_identity(
        execution_request=execution_request,
        worker_task_id=update_data.worker_task_id,
    )

    values = _partner_execution_update_values(
        execution_request=execution_request,
        update_data=update_data,
    )

    if execution_request.worker_task_id is None:
        execution_request.worker_task_id = update_data.worker_task_id

    for field_name, value in values.items():
        setattr(
            execution_request,
            field_name,
            value,
        )

    execution_request.last_partner_sequence = update_data.sequence_number

    update_record = PartnerExecutionUpdateRecord(
        update_id=update_data.update_id,
        execution_id=execution_request.execution_id,
        correlation_id=execution_request.correlation_id,
        sequence_number=update_data.sequence_number,
        status=update_data.status,
        payload_digest=payload_digest,
    )

    db.add(update_record)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()

        concurrent_record = _find_partner_update_record(
            db,
            update_id=update_data.update_id,
        )

        if concurrent_record is not None:
            return _resolve_existing_partner_replay(
                existing_record=concurrent_record,
                payload_digest=payload_digest,
            )

        raise ExecutionPersistenceConflictError(
            "The partner result update conflicted with another database operation."
        ) from error
    except SQLAlchemyError as error:
        db.rollback()

        raise ExecutionPersistenceError(
            "The partner result update could not be saved."
        ) from error

    db.refresh(execution_request)
    db.refresh(update_record)

    return _build_partner_update_acknowledgment(
        record=update_record,
        replayed=False,
    )


# EXECUTION BOUNDARY:
# This service persists and authorizes execution requests only. It never
# executes student Python inside FastAPI or the host operating system.

# PARTNER AUTHENTICATION BOUNDARY:
# Authentication belongs to the internal router or integration adapter.
# Credentials, JWTs, API keys, and shared secrets are never accepted inside
# partner result bodies and are never persisted as update metadata.

# TELEMETRY BOUNDARY:
# run_attempt_count is incremented only after backend validation and in
# the same transaction as the execution request. The client cannot submit
# or overwrite the counter directly.

# IMMUTABILITY BOUNDARY:
# Execution source, standard input, ownership, task, submission, and
# coding-session references are immutable after request creation.

# REPLAY BOUNDARY:
# Accepted partner update IDs and canonical payload digests provide
# idempotent replay handling. Sequence numbers are strictly monotonic per
# execution. Terminal executions cannot accept later lifecycle mutations.

# REVIEW BOUNDARY:
# Worker output and resource-limit results support instructor review only.
# They never automatically assign grades or misconduct verdicts.
