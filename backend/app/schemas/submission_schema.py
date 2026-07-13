from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SubmissionStatus = Literal[
    "submitted",
    "awaiting_review",
    "graded",
    "rejected",
]


class SubmissionBase(BaseModel):
    raw_code: str = Field(..., min_length=1)
    standard_input: str = Field(default="", max_length=10000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("raw_code")
    @classmethod
    def validate_raw_code(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Source code cannot be empty.")

        # Preserve the original indentation and whitespace of Python code.
        return value


class SubmissionCreate(SubmissionBase):
    task_id: int = Field(..., gt=0)
    coding_session_id: str | None = Field(
        default=None,
        min_length=36,
        max_length=36,
    )

    # SECURITY BOUNDARY:
    # student_id, attempt_number, status, and is_official are intentionally
    # excluded. The backend resolves the student from the authenticated JWT
    # and calculates the next attempt and official-attempt state.


class SubmissionResponse(SubmissionBase):
    sub_id: int
    student_id: int
    task_id: int
    coding_session_id: str | None
    attempt_number: int
    status: SubmissionStatus
    is_official: bool
    submitted_at: datetime
    accepted_at: datetime | None
    jaccard_score: float | None = None
    ast_pass_fail: bool | None = None

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    @field_validator("attempt_number")
    @classmethod
    def validate_attempt_number(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Attempt number must be greater than zero.")

        return value

    @field_validator("jaccard_score")
    @classmethod
    def validate_jaccard_score(
        cls,
        value: float | None,
    ) -> float | None:
        if value is not None and not 0 <= value <= 100:
            raise ValueError("Jaccard score must be between 0 and 100.")

        return value

    # REVIEW BOUNDARY:
    # jaccard_score and ast_pass_fail are automated review indicators only.
    # They must never automatically determine misconduct or the final grade.
