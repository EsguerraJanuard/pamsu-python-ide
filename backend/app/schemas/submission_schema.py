from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


SubmissionStatus = Literal[
    "submitted",
    "awaiting_review",
    "graded",
    "rejected",
]


MAX_SOURCE_CODE_LENGTH = 100_000
MAX_STANDARD_INPUT_LENGTH = 10_000


def validate_source_code(
    value: str,
) -> str:
    if not value.strip():
        raise ValueError("Source code cannot be empty.")

    if "\x00" in value:
        raise ValueError("Source code cannot contain null bytes.")

    # Preserve indentation, newlines, and all meaningful whitespace.
    return value


def validate_standard_input(
    value: str,
) -> str:
    if "\x00" in value:
        raise ValueError("Standard input cannot contain null bytes.")

    # Preserve input exactly as entered by the student.
    return value


def normalize_coding_session_id(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    try:
        parsed_value = UUID(value)
    except (TypeError, ValueError, AttributeError) as error:
        raise ValueError("Coding session ID must be a valid UUID.") from error

    return str(parsed_value)


def normalize_response_datetime(
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return None

    # SQLite may return timezone-aware SQLAlchemy columns as naive
    # datetime objects. Persisted backend timestamps are interpreted
    # as UTC.
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(
            tzinfo=timezone.utc,
        )

    return value.astimezone(
        timezone.utc,
    )


class SubmissionBase(BaseModel):
    raw_code: str = Field(
        ...,
        min_length=1,
        max_length=MAX_SOURCE_CODE_LENGTH,
        description=(
            "Exact Python source submitted by the student. "
            "Indentation and whitespace are preserved."
        ),
    )
    standard_input: str = Field(
        default="",
        max_length=MAX_STANDARD_INPUT_LENGTH,
        description=("Optional standard input associated with this attempt."),
    )

    model_config = ConfigDict(
        extra="forbid",
    )

    @field_validator("raw_code")
    @classmethod
    def validate_raw_code(
        cls,
        value: str,
    ) -> str:
        return validate_source_code(value)

    @field_validator("standard_input")
    @classmethod
    def validate_submission_standard_input(
        cls,
        value: str,
    ) -> str:
        return validate_standard_input(value)


class SubmissionCreate(SubmissionBase):
    task_id: int = Field(
        ...,
        gt=0,
        description=("Published activity receiving the immutable attempt."),
    )
    coding_session_id: str | None = Field(
        default=None,
        min_length=36,
        max_length=36,
        description=("Optional UUID of the student's coding session."),
    )

    @field_validator("coding_session_id")
    @classmethod
    def validate_coding_session_id(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_coding_session_id(value)

    # SECURITY BOUNDARY:
    # student_id, attempt_number, status, is_official,
    # submitted_at, accepted_at, automated indicators, and grades
    # are intentionally excluded. They are controlled by the backend.


class SubmissionResponseBase(SubmissionBase):
    sub_id: int = Field(
        ...,
        gt=0,
    )
    task_id: int = Field(
        ...,
        gt=0,
    )
    coding_session_id: str | None = Field(
        default=None,
        min_length=36,
        max_length=36,
    )
    attempt_number: int = Field(
        ...,
        gt=0,
        description=("Sequential attempt number calculated by the backend."),
    )
    status: SubmissionStatus
    is_official: bool = Field(
        ...,
        description=("Whether this attempt is currently the official attempt."),
    )
    submitted_at: datetime
    accepted_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    @field_validator("coding_session_id")
    @classmethod
    def validate_response_coding_session_id(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_coding_session_id(value)

    @field_validator(
        "submitted_at",
        "accepted_at",
        mode="after",
    )
    @classmethod
    def normalize_database_datetime(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return normalize_response_datetime(value)


class StudentSubmissionResponse(
    SubmissionResponseBase,
):
    # STUDENT-SAFE BOUNDARY:
    # This response represents only the authenticated student's own
    # attempt. It intentionally excludes student_id, similarity scores,
    # AST results, instructor grades, and internal review records.
    pass


class InstructorSubmissionResponse(
    SubmissionResponseBase,
):
    student_id: int = Field(
        ...,
        gt=0,
    )
    jaccard_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description=("Similarity indicator for instructor review only."),
    )
    ast_pass_fail: bool | None = Field(
        default=None,
        description=("Structural-analysis indicator for instructor review only."),
    )

    # REVIEW BOUNDARY:
    # jaccard_score and ast_pass_fail are review indicators only.
    # They must never automatically determine misconduct, rejection,
    # acceptance, official-attempt state, or the final grade.


class SubmissionResponse(
    InstructorSubmissionResponse,
):
    """
    Backward-compatible full submission response.

    Existing execution and evaluation endpoints may continue importing
    SubmissionResponse while Pillar 6 student endpoints use the safer
    StudentSubmissionResponse model.
    """

    pass
