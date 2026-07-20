from datetime import datetime, timezone
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


ExecutionRequestKind = Literal[
    "run",
    "check",
    "submit",
]

ExecutionStatus = Literal[
    "queued",
    "running",
    "completed",
    "syntax_error",
    "runtime_error",
    "timed_out",
    "memory_limit",
    "output_limit",
    "process_limit",
    "cancelled",
    "failed",
]

WorkerReportableExecutionStatus = Literal[
    "running",
    "completed",
    "syntax_error",
    "runtime_error",
    "timed_out",
    "memory_limit",
    "output_limit",
    "process_limit",
    "cancelled",
    "failed",
]


TERMINAL_EXECUTION_STATUSES = frozenset(
    {
        "completed",
        "syntax_error",
        "runtime_error",
        "timed_out",
        "memory_limit",
        "output_limit",
        "process_limit",
        "cancelled",
        "failed",
    }
)

ALLOWED_EXECUTION_STATUS_TRANSITIONS = {
    "queued": frozenset(
        {
            "running",
            "completed",
            "syntax_error",
            "runtime_error",
            "timed_out",
            "memory_limit",
            "output_limit",
            "process_limit",
            "cancelled",
            "failed",
        }
    ),
    "running": TERMINAL_EXECUTION_STATUSES,
    "completed": frozenset(),
    "syntax_error": frozenset(),
    "runtime_error": frozenset(),
    "timed_out": frozenset(),
    "memory_limit": frozenset(),
    "output_limit": frozenset(),
    "process_limit": frozenset(),
    "cancelled": frozenset(),
    "failed": frozenset(),
}

MAX_SOURCE_CODE_LENGTH = 100_000
MAX_STANDARD_INPUT_LENGTH = 10_000
MAX_EXECUTION_OUTPUT_LENGTH = 100_000
MAX_COMBINED_EXECUTION_OUTPUT_BYTES = 200_000
MAX_LIMIT_REASON_LENGTH = 100
MAX_WORKER_TASK_ID_LENGTH = 255
MAX_PARTNER_ERROR_CODE_LENGTH = 100
MAX_PARTNER_ERROR_MESSAGE_LENGTH = 500

DEFAULT_TIME_LIMIT_MS = 10_000
MAX_TIME_LIMIT_MS = 60_000
DEFAULT_MEMORY_LIMIT_BYTES = 268_435_456
MAX_MEMORY_LIMIT_BYTES = 1_073_741_824
DEFAULT_OUTPUT_LIMIT_BYTES = 100_000
MAX_OUTPUT_LIMIT_BYTES = 1_000_000
DEFAULT_PROCESS_LIMIT = 8
MAX_PROCESS_LIMIT = 64


def validate_source_code(
    value: str,
) -> str:
    if not value.strip():
        raise ValueError("Source code cannot be empty.")

    if "\x00" in value:
        raise ValueError("Source code cannot contain null bytes.")

    # Preserve Python indentation, newlines, and whitespace.
    return value


def validate_optional_source_code(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return validate_source_code(value)


def validate_standard_input(
    value: str,
) -> str:
    if "\x00" in value:
        raise ValueError("Standard input cannot contain null bytes.")

    # Preserve standard input exactly as received.
    return value


def validate_execution_output(
    value: str,
) -> str:
    if "\x00" in value:
        raise ValueError("Execution output cannot contain null bytes.")

    return value


def normalize_uuid_string(
    value: str | None,
    *,
    field_label: str,
) -> str | None:
    if value is None:
        return None

    try:
        parsed_value = UUID(value)
    except (
        TypeError,
        ValueError,
        AttributeError,
    ) as error:
        raise ValueError(f"{field_label} must be a valid UUID.") from error

    return str(parsed_value)


def normalize_required_uuid_string(
    value: str,
    *,
    field_label: str,
) -> str:
    normalized_value = normalize_uuid_string(
        value,
        field_label=field_label,
    )

    if normalized_value is None:
        raise ValueError(f"{field_label} is required.")

    return normalized_value


def normalize_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized_value = value.strip()

    return normalized_value or None


def normalize_request_datetime(
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Execution timestamps must include a timezone.")

    return value.astimezone(timezone.utc)


def normalize_required_request_datetime(
    value: datetime,
) -> datetime:
    normalized_value = normalize_request_datetime(
        value,
    )

    if normalized_value is None:
        raise ValueError("Execution timestamp is required.")

    return normalized_value


def normalize_response_datetime(
    value: Any,
) -> Any:
    if value is None:
        return None

    if not isinstance(
        value,
        datetime,
    ):
        return value

    # SQLite may return DateTime(timezone=True) values without tzinfo.
    # Persisted backend timestamps are interpreted as UTC.
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def validate_combined_output_size(
    *,
    stdout: str | None,
    stderr: str | None,
) -> None:
    total_bytes = len((stdout or "").encode("utf-8")) + len(
        (stderr or "").encode("utf-8")
    )

    if total_bytes > MAX_COMBINED_EXECUTION_OUTPUT_BYTES:
        raise ValueError(
            "Combined stdout and stderr must not exceed "
            f"{MAX_COMBINED_EXECUTION_OUTPUT_BYTES} UTF-8 bytes."
        )


def is_execution_status_transition_allowed(
    *,
    current_status: ExecutionStatus,
    next_status: ExecutionStatus,
) -> bool:
    return next_status in ALLOWED_EXECUTION_STATUS_TRANSITIONS[current_status]


class ExecutionRequestCreate(BaseModel):
    request_kind: ExecutionRequestKind = Field(
        ...,
        description=("Requested execution operation: run, check, or submit."),
        examples=["run"],
    )
    task_id: int = Field(
        ...,
        gt=0,
        description=("Published activity associated with the execution request."),
    )
    submission_id: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Required only for submit requests. The submission must "
            "belong to the authenticated student and task."
        ),
    )
    coding_session_id: str | None = Field(
        default=None,
        min_length=36,
        max_length=36,
        description=(
            "Optional coding-session UUID belonging to the student and activity."
        ),
    )
    source_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_SOURCE_CODE_LENGTH,
        description=(
            "Required for run and check requests. Submit requests use "
            "the immutable source snapshot from the linked submission."
        ),
    )
    standard_input: str = Field(
        default="",
        max_length=MAX_STANDARD_INPUT_LENGTH,
        description=(
            "Standard input used for run and check requests. Submit "
            "requests use the linked submission input snapshot."
        ),
    )

    model_config = ConfigDict(
        extra="forbid",
    )

    @field_validator("coding_session_id")
    @classmethod
    def validate_coding_session_id(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_uuid_string(
            value,
            field_label="Coding session ID",
        )

    @field_validator("source_code")
    @classmethod
    def validate_request_source_code(
        cls,
        value: str | None,
    ) -> str | None:
        return validate_optional_source_code(value)

    @field_validator("standard_input")
    @classmethod
    def validate_request_standard_input(
        cls,
        value: str,
    ) -> str:
        return validate_standard_input(value)

    @model_validator(mode="after")
    def validate_request_kind_contract(
        self,
    ) -> Self:
        if self.request_kind == "submit":
            if self.submission_id is None:
                raise ValueError("Submit requests require a submission ID.")

            if self.source_code is not None:
                raise ValueError(
                    "Submit request source code must come from "
                    "the linked immutable submission."
                )

            return self

        if self.submission_id is not None:
            raise ValueError("Run and check requests cannot reference a submission.")

        if self.source_code is None:
            raise ValueError("Run and check requests require source code.")

        return self

    # SECURITY BOUNDARY:
    # student_id, execution_id, status, lifecycle timestamps, output,
    # exit code, limit reason, execution time, and worker task ID are
    # intentionally excluded and controlled by the backend or worker.


class ExecutionWorkerUpdate(BaseModel):
    status: ExecutionStatus | None = Field(
        default=None,
        description=("Lifecycle status reported by the isolated worker adapter."),
    )
    stdout: str | None = Field(
        default=None,
        max_length=MAX_EXECUTION_OUTPUT_LENGTH,
    )
    stderr: str | None = Field(
        default=None,
        max_length=MAX_EXECUTION_OUTPUT_LENGTH,
    )
    exit_code: int | None = None
    execution_time_ms: int | None = Field(
        default=None,
        ge=0,
    )
    limit_reason: str | None = Field(
        default=None,
        max_length=MAX_LIMIT_REASON_LENGTH,
    )
    worker_task_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_WORKER_TASK_ID_LENGTH,
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(
        extra="forbid",
    )

    @field_validator(
        "stdout",
        "stderr",
    )
    @classmethod
    def validate_worker_output(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return validate_execution_output(value)

    @field_validator("limit_reason")
    @classmethod
    def validate_limit_reason(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_optional_text(value)

    @field_validator("worker_task_id")
    @classmethod
    def validate_worker_task_id(
        cls,
        value: str | None,
    ) -> str | None:
        normalized_value = normalize_optional_text(value)

        if value is not None and normalized_value is None:
            raise ValueError("Worker task ID cannot be empty.")

        return normalized_value

    @field_validator(
        "started_at",
        "completed_at",
    )
    @classmethod
    def validate_worker_timestamp(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return normalize_request_datetime(value)

    @model_validator(mode="after")
    def validate_update_contract(
        self,
    ) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one execution update field is required.")

        validate_combined_output_size(
            stdout=self.stdout,
            stderr=self.stderr,
        )

        if (
            self.started_at is not None
            and self.completed_at is not None
            and self.completed_at < self.started_at
        ):
            raise ValueError("completed_at cannot be earlier than started_at.")

        return self

    # WORKER BOUNDARY:
    # The worker adapter may update lifecycle and result fields only.
    # It cannot replace student ownership, task ownership, submission
    # ownership, coding-session ownership, request kind, or source code.


class PartnerExecutionLimits(BaseModel):
    time_limit_ms: int = Field(
        default=DEFAULT_TIME_LIMIT_MS,
        gt=0,
        le=MAX_TIME_LIMIT_MS,
    )
    memory_limit_bytes: int = Field(
        default=DEFAULT_MEMORY_LIMIT_BYTES,
        gt=0,
        le=MAX_MEMORY_LIMIT_BYTES,
    )
    output_limit_bytes: int = Field(
        default=DEFAULT_OUTPUT_LIMIT_BYTES,
        gt=0,
        le=MAX_OUTPUT_LIMIT_BYTES,
    )
    process_limit: int = Field(
        default=DEFAULT_PROCESS_LIMIT,
        gt=0,
        le=MAX_PROCESS_LIMIT,
    )

    model_config = ConfigDict(
        extra="forbid",
    )

    # CONTRACT BOUNDARY:
    # These values describe requested sandbox limits. Pillar 14 defines
    # contracts only and does not implement the sandbox runtime or
    # resource-limit enforcement.


class PartnerExecutionDispatchRequest(BaseModel):
    execution_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
    )
    correlation_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
    )
    idempotency_key: str = Field(
        ...,
        min_length=36,
        max_length=36,
    )
    request_kind: ExecutionRequestKind
    task_id: int = Field(
        ...,
        gt=0,
    )
    submission_id: int | None = Field(
        default=None,
        gt=0,
    )
    coding_session_id: str | None = Field(
        default=None,
        min_length=36,
        max_length=36,
    )
    source_code: str = Field(
        ...,
        min_length=1,
        max_length=MAX_SOURCE_CODE_LENGTH,
    )
    standard_input: str = Field(
        default="",
        max_length=MAX_STANDARD_INPUT_LENGTH,
    )
    limits: PartnerExecutionLimits = Field(
        default_factory=PartnerExecutionLimits,
    )
    queued_at: datetime

    model_config = ConfigDict(
        extra="forbid",
    )

    @field_validator(
        "execution_id",
        "correlation_id",
        "idempotency_key",
    )
    @classmethod
    def validate_required_partner_uuid(
        cls,
        value: str,
        info: Any,
    ) -> str:
        field_labels = {
            "execution_id": "Execution ID",
            "correlation_id": "Correlation ID",
            "idempotency_key": "Idempotency key",
        }

        return normalize_required_uuid_string(
            value,
            field_label=field_labels[info.field_name],
        )

    @field_validator("coding_session_id")
    @classmethod
    def validate_partner_coding_session_id(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_uuid_string(
            value,
            field_label="Coding session ID",
        )

    @field_validator("source_code")
    @classmethod
    def validate_partner_source_code(
        cls,
        value: str,
    ) -> str:
        return validate_source_code(value)

    @field_validator("standard_input")
    @classmethod
    def validate_partner_standard_input(
        cls,
        value: str,
    ) -> str:
        return validate_standard_input(value)

    @field_validator("queued_at")
    @classmethod
    def validate_partner_queued_at(
        cls,
        value: datetime,
    ) -> datetime:
        return normalize_required_request_datetime(value)

    @model_validator(mode="after")
    def validate_partner_request_kind(
        self,
    ) -> Self:
        if self.request_kind == "submit":
            if self.submission_id is None:
                raise ValueError("Submit dispatch requests require a submission ID.")

            return self

        if self.submission_id is not None:
            raise ValueError(
                "Run and check dispatch requests cannot reference a submission."
            )

        return self

    # PARTNER DISPATCH BOUNDARY:
    # This internal contract contains the immutable execution snapshot
    # required by the isolated worker. It excludes passwords, OTPs, JWTs,
    # grade fields, misconduct verdicts, clipboard contents, browsing
    # history, screen, webcam, microphone, and individual-keystroke data.


class PartnerExecutionResultUpdate(BaseModel):
    execution_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
    )
    correlation_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
    )
    update_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
    )
    sequence_number: int = Field(
        ...,
        ge=1,
    )
    worker_task_id: str = Field(
        ...,
        min_length=1,
        max_length=MAX_WORKER_TASK_ID_LENGTH,
    )
    status: WorkerReportableExecutionStatus
    stdout: str = Field(
        default="",
        max_length=MAX_EXECUTION_OUTPUT_LENGTH,
    )
    stderr: str = Field(
        default="",
        max_length=MAX_EXECUTION_OUTPUT_LENGTH,
    )
    exit_code: int | None = None
    execution_time_ms: int | None = Field(
        default=None,
        ge=0,
    )
    limit_reason: str | None = Field(
        default=None,
        max_length=MAX_LIMIT_REASON_LENGTH,
    )
    error_code: str | None = Field(
        default=None,
        max_length=MAX_PARTNER_ERROR_CODE_LENGTH,
    )
    error_message: str | None = Field(
        default=None,
        max_length=MAX_PARTNER_ERROR_MESSAGE_LENGTH,
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(
        extra="forbid",
    )

    @field_validator(
        "execution_id",
        "correlation_id",
        "update_id",
    )
    @classmethod
    def validate_required_result_uuid(
        cls,
        value: str,
        info: Any,
    ) -> str:
        field_labels = {
            "execution_id": "Execution ID",
            "correlation_id": "Correlation ID",
            "update_id": "Update ID",
        }

        return normalize_required_uuid_string(
            value,
            field_label=field_labels[info.field_name],
        )

    @field_validator("worker_task_id")
    @classmethod
    def validate_result_worker_task_id(
        cls,
        value: str,
    ) -> str:
        normalized_value = normalize_optional_text(value)

        if normalized_value is None:
            raise ValueError("Worker task ID cannot be empty.")

        return normalized_value

    @field_validator(
        "stdout",
        "stderr",
    )
    @classmethod
    def validate_partner_result_output(
        cls,
        value: str,
    ) -> str:
        return validate_execution_output(value)

    @field_validator(
        "limit_reason",
        "error_code",
        "error_message",
    )
    @classmethod
    def normalize_partner_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_optional_text(value)

    @field_validator(
        "started_at",
        "completed_at",
    )
    @classmethod
    def validate_partner_result_timestamp(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return normalize_request_datetime(value)

    @model_validator(mode="after")
    def validate_partner_result_contract(
        self,
    ) -> Self:
        validate_combined_output_size(
            stdout=self.stdout,
            stderr=self.stderr,
        )

        if (
            self.started_at is not None
            and self.completed_at is not None
            and self.completed_at < self.started_at
        ):
            raise ValueError("completed_at cannot be earlier than started_at.")

        if self.status == "running":
            terminal_fields = {
                "completed_at": self.completed_at,
                "exit_code": self.exit_code,
                "limit_reason": self.limit_reason,
            }

            if any(value is not None for value in terminal_fields.values()):
                raise ValueError(
                    "Running updates cannot include terminal result fields."
                )

            return self

        if self.completed_at is None:
            raise ValueError("Terminal worker updates require completed_at.")

        if self.status == "completed" and self.exit_code not in (
            None,
            0,
        ):
            raise ValueError(
                "Completed execution updates cannot report a non-zero exit code."
            )

        if (
            self.status
            in {
                "timed_out",
                "memory_limit",
                "output_limit",
                "process_limit",
            }
            and self.limit_reason is None
        ):
            raise ValueError("Resource-limit execution updates require limit_reason.")

        return self

    # AUTHENTICATED WORKER BOUNDARY:
    # Authentication belongs to the transport dependency or partner
    # adapter and is intentionally excluded from the body. JWTs, API
    # keys, and shared secrets must never be persisted in this schema.

    # REPLAY BOUNDARY:
    # update_id is the idempotency identity. sequence_number provides
    # deterministic ordering. Service logic must reject correlation
    # mismatches, stale sequences, and updates after terminal status.


class PartnerExecutionUpdateAcceptedResponse(BaseModel):
    execution_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
    )
    correlation_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
    )
    update_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
    )
    status: ExecutionStatus
    sequence_number: int = Field(
        ...,
        ge=1,
    )
    accepted: Literal[True] = True
    replayed: bool
    accepted_at: datetime

    model_config = ConfigDict(
        extra="forbid",
    )

    @field_validator(
        "execution_id",
        "correlation_id",
        "update_id",
    )
    @classmethod
    def validate_required_ack_uuid(
        cls,
        value: str,
        info: Any,
    ) -> str:
        field_labels = {
            "execution_id": "Execution ID",
            "correlation_id": "Correlation ID",
            "update_id": "Update ID",
        }

        return normalize_required_uuid_string(
            value,
            field_label=field_labels[info.field_name],
        )

    @field_validator("accepted_at")
    @classmethod
    def validate_accepted_at(
        cls,
        value: datetime,
    ) -> datetime:
        return normalize_required_request_datetime(value)


class ExecutionResponseBase(BaseModel):
    execution_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
    )
    task_id: int | None = Field(
        default=None,
        gt=0,
    )
    submission_id: int | None = Field(
        default=None,
        gt=0,
    )
    coding_session_id: str | None = Field(
        default=None,
        min_length=36,
        max_length=36,
    )
    request_kind: ExecutionRequestKind
    status: ExecutionStatus
    source_code: str = Field(
        ...,
        min_length=1,
        max_length=MAX_SOURCE_CODE_LENGTH,
    )
    standard_input: str = Field(
        default="",
        max_length=MAX_STANDARD_INPUT_LENGTH,
    )
    stdout: str = Field(
        default="",
        max_length=MAX_EXECUTION_OUTPUT_LENGTH,
    )
    stderr: str = Field(
        default="",
        max_length=MAX_EXECUTION_OUTPUT_LENGTH,
    )
    exit_code: int | None = None
    execution_time_ms: int | None = Field(
        default=None,
        ge=0,
    )
    limit_reason: str | None = Field(
        default=None,
        max_length=MAX_LIMIT_REASON_LENGTH,
    )
    queued_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    @field_validator("execution_id")
    @classmethod
    def validate_execution_id(
        cls,
        value: str,
    ) -> str:
        normalized_value = normalize_uuid_string(
            value,
            field_label="Execution ID",
        )

        if normalized_value is None:
            raise ValueError("Execution ID is required.")

        return normalized_value

    @field_validator("coding_session_id")
    @classmethod
    def validate_response_coding_session_id(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_uuid_string(
            value,
            field_label="Coding session ID",
        )

    @field_validator("source_code")
    @classmethod
    def validate_response_source_code(
        cls,
        value: str,
    ) -> str:
        return validate_source_code(value)

    @field_validator("standard_input")
    @classmethod
    def validate_response_standard_input(
        cls,
        value: str,
    ) -> str:
        return validate_standard_input(value)

    @field_validator(
        "stdout",
        "stderr",
    )
    @classmethod
    def validate_response_output(
        cls,
        value: str,
    ) -> str:
        return validate_execution_output(value)

    @model_validator(mode="after")
    def validate_response_output_size(
        self,
    ) -> Self:
        validate_combined_output_size(
            stdout=self.stdout,
            stderr=self.stderr,
        )

        return self

    @field_validator(
        "queued_at",
        "started_at",
        "completed_at",
        mode="before",
    )
    @classmethod
    def normalize_database_datetime(
        cls,
        value: Any,
    ) -> Any:
        return normalize_response_datetime(value)


class StudentExecutionResponse(
    ExecutionResponseBase,
):
    # STUDENT-SAFE BOUNDARY:
    # A student receives only execution requests they own.
    # Internal worker task identifiers are excluded.
    pass


class InstructorExecutionResponse(
    ExecutionResponseBase,
):
    student_id: int = Field(
        ...,
        gt=0,
    )

    # REVIEW BOUNDARY:
    # Execution output and resource-limit results support instructor
    # review only. They do not assign a grade or misconduct verdict.


class InternalExecutionResponse(
    InstructorExecutionResponse,
):
    worker_task_id: str | None = Field(
        default=None,
        max_length=MAX_WORKER_TASK_ID_LENGTH,
    )

    # INTERNAL BOUNDARY:
    # This schema is reserved for trusted backend-worker integration.
    # It must not be used as a student-facing API response.


# Backward-compatible names for modules that may use shorter names.
ExecutionCreate = ExecutionRequestCreate
ExecutionResponse = InstructorExecutionResponse
