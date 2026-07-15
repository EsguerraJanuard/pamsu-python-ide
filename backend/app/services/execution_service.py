from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.domain_models import (
    Classroom,
    CodingSession,
    Enrollment,
    ExecutionRequest,
    Submission,
    Task,
)
from app.schemas.execution_schema import (
    ExecutionRequestCreate,
    ExecutionRequestKind,
    ExecutionStatus,
    ExecutionWorkerUpdate,
    TERMINAL_EXECUTION_STATUSES,
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


class ExecutionPersistenceConflictError(
    ExecutionServiceError,
):
    """Raised when unique execution data conflicts."""


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
            "The execution request could not be saved because "
            "its identifier conflicts with an existing record."
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

    The generic unavailable response prevents students from discovering
    unpublished tasks or classrooms in which they are not enrolled.
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
    submission = (
        db.query(Submission)
        .filter(
            Submission.sub_id == submission_id,
            Submission.student_id == student_id,
            Submission.task_id == task_id,
        )
        .first()
    )

    if submission is None:
        raise ExecutionSubmissionUnavailableError(
            "The submission is unavailable for this activity."
        )

    return submission


def _get_student_coding_session(
    db: Session,
    *,
    student_id: int,
    task_id: int,
    coding_session_id: str,
) -> CodingSession:
    coding_session = (
        db.query(CodingSession)
        .filter(
            CodingSession.session_id == coding_session_id,
            CodingSession.student_id == student_id,
            CodingSession.task_id == task_id,
        )
        .first()
    )

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

    Run and check requests use the submitted request body. Submit
    requests use the source and standard input stored in the linked
    immutable submission attempt.
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
                coding_session_id=(payload.coding_session_id),
            )

        return (
            payload.source_code,
            payload.standard_input,
            None,
            payload.coding_session_id,
        )

    if payload.submission_id is None:
        raise ExecutionSubmissionUnavailableError(
            "Submit requests require a submission."
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
        and submission_session_id is not None
        and payload.coding_session_id != submission_session_id
    ):
        raise ExecutionCodingSessionUnavailableError(
            "The coding session does not match the submission."
        )

    effective_session_id = submission_session_id or payload.coding_session_id

    if effective_session_id is not None:
        _get_student_coding_session(
            db,
            student_id=student_id,
            task_id=task.task_id,
            coding_session_id=effective_session_id,
        )

    return (
        submission.raw_code,
        submission.standard_input,
        submission.sub_id,
        effective_session_id,
    )


def create_student_execution_request(
    db: Session,
    *,
    student_id: int,
    payload: ExecutionRequestCreate,
) -> ExecutionRequest:
    """
    Persist a queued execution request without executing Python code.

    The execution ID is the only value that should later be handed to
    the partner-owned Celery/Redis worker adapter.
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


def _validate_status_transition(
    *,
    current_status: str,
    target_status: str,
) -> None:
    if current_status == target_status:
        return

    if current_status in TERMINAL_EXECUTION_STATUSES:
        raise ExecutionStateConflictError(
            "A completed execution request cannot transition to another status."
        )

    if current_status == "queued":
        if target_status == "running" or target_status in TERMINAL_EXECUTION_STATUSES:
            return

    if current_status == "running" and target_status in TERMINAL_EXECUTION_STATUSES:
        return

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
    Apply a trusted worker lifecycle/result update.

    This function does not expose a public student or instructor write
    endpoint. The partner-owned adapter should call this boundary after
    authenticating through an internal integration mechanism.
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
    Attach the partner worker's task identifier without changing the
    execution request's ownership or source snapshot.
    """

    execution_request = get_internal_execution_request(
        db,
        execution_id=execution_id,
        lock_for_update=True,
    )

    normalized_worker_task_id = worker_task_id.strip()

    if not normalized_worker_task_id:
        raise ExecutionWorkerUpdateInvalidError("Worker task ID cannot be empty.")

    if len(normalized_worker_task_id) > 255:
        raise ExecutionWorkerUpdateInvalidError(
            "Worker task ID cannot exceed 255 characters."
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
