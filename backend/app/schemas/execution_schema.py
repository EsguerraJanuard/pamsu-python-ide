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

MAX_SOURCE_CODE_LENGTH = 100_000
MAX_STANDARD_INPUT_LENGTH = 10_000
MAX_EXECUTION_OUTPUT_LENGTH = 100_000
MAX_LIMIT_REASON_LENGTH = 100
MAX_WORKER_TASK_ID_LENGTH = 255


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
    def validate_update_has_fields(
        self,
    ) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one execution update field is required.")

        return self

    # WORKER BOUNDARY:
    # The worker adapter may update lifecycle and result fields only.
    # It cannot replace student ownership, task ownership, submission
    # ownership, coding-session ownership, request kind, or source code.


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
