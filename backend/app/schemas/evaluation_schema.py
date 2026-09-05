from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


EvaluationStatus = Literal[
    "awaiting_review",
    "graded",
    "rejected",
]

MAX_GRADE_FEEDBACK_LENGTH = 5000


def normalize_utc_datetime(
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


class ASTFindingResponse(BaseModel):
    """
    Instructor-only structural-analysis finding.

    Findings are review indicators and do not independently determine
    an academic grade or misconduct decision.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    finding_id: int = Field(
        ...,
        gt=0,
    )

    rule_key: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    label: str = Field(
        ...,
        min_length=1,
        max_length=150,
    )

    passed: bool | None = None

    line_number: int | None = Field(
        default=None,
        gt=0,
    )

    message: str | None = None

    details: dict[str, Any] = Field(
        default_factory=dict,
    )


class ASTAnalysisResponse(BaseModel):
    """
    Instructor-only static AST analysis record.

    Student Python is parsed statically and must never be executed by
    the FastAPI process.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    analysis_id: int = Field(
        ...,
        gt=0,
    )

    submission_id: int | None = Field(
        default=None,
        gt=0,
    )

    execution_id: UUID | None = None

    overall_pass: bool | None = None

    syntax_error: dict[str, Any] | None = None

    details: dict[str, Any] = Field(
        default_factory=dict,
    )

    created_at: datetime

    findings: list[ASTFindingResponse] = Field(
        default_factory=list,
    )

    @field_validator(
        "created_at",
        mode="after",
    )
    @classmethod
    def normalize_created_at(
        cls,
        value: datetime,
    ) -> datetime:
        normalized = normalize_utc_datetime(value)

        assert normalized is not None

        return normalized


class SimilarityResultResponse(BaseModel):
    """
    Instructor-only source-similarity comparison record.

    A similarity score is not a plagiarism or misconduct verdict.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    result_id: int = Field(
        ...,
        gt=0,
    )

    source_submission_id: int = Field(
        ...,
        gt=0,
    )

    compared_submission_id: int = Field(
        ...,
        gt=0,
    )

    score: float = Field(
        ...,
        ge=0,
        le=100,
    )

    algorithm: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    created_at: datetime

    @field_validator(
        "created_at",
        mode="after",
    )
    @classmethod
    def normalize_created_at(
        cls,
        value: datetime,
    ) -> datetime:
        normalized = normalize_utc_datetime(value)

        assert normalized is not None

        return normalized


class InstructorGradeBase(BaseModel):
    """
    Fields explicitly assigned by an authorized instructor.

    AST, similarity, execution, and session indicators must never
    populate these fields automatically.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    score: float = Field(
        ...,
        ge=0,
        description="Score manually assigned by the instructor.",
    )

    max_score: float = Field(
        ...,
        gt=0,
        description="Maximum possible score.",
    )

    feedback: str | None = Field(
        default=None,
        max_length=MAX_GRADE_FEEDBACK_LENGTH,
        description="Optional manual instructor feedback.",
    )

    is_released: bool = Field(
        default=False,
        description=("Whether the manual grade is visible to the student."),
    )

    @model_validator(
        mode="after",
    )
    def validate_score_bounds(
        self,
    ) -> "InstructorGradeBase":
        if self.score > self.max_score:
            raise ValueError("score cannot be greater than max_score")

        return self


class InstructorGradeCreate(InstructorGradeBase):
    """Create or fully replace a manual instructor grade."""


class InstructorGradeUpdate(BaseModel):
    """
    Partially update a manual instructor grade.

    At least one field must be supplied. Final score validation against
    existing database values is also performed by the service.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    score: float | None = Field(
        default=None,
        ge=0,
    )

    max_score: float | None = Field(
        default=None,
        gt=0,
    )

    feedback: str | None = Field(
        default=None,
        max_length=MAX_GRADE_FEEDBACK_LENGTH,
    )

    is_released: bool | None = None

    @model_validator(
        mode="after",
    )
    def validate_update(
        self,
    ) -> "InstructorGradeUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one grade field must be supplied.")

        if (
            self.score is not None
            and self.max_score is not None
            and self.score > self.max_score
        ):
            raise ValueError("score cannot be greater than max_score")

        return self


class InstructorGradeResponse(InstructorGradeBase):
    """
    Full instructor-facing manual-grade response.

    This response may include unreleased grades because it is restricted
    to the instructor who owns the activity.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    grade_id: int = Field(
        ...,
        gt=0,
    )

    submission_id: int = Field(
        ...,
        gt=0,
    )

    instructor_id: int = Field(
        ...,
        gt=0,
    )

    created_at: datetime

    updated_at: datetime

    @field_validator(
        "created_at",
        "updated_at",
        mode="after",
    )
    @classmethod
    def normalize_grade_datetime(
        cls,
        value: datetime,
    ) -> datetime:
        normalized = normalize_utc_datetime(value)

        assert normalized is not None

        return normalized


class ReleasedInstructorGradeResponse(BaseModel):
    """
    Student-safe released manual grade.

    instructor_id is intentionally excluded. This response must be
    returned only when is_released is true.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    score: float = Field(
        ...,
        ge=0,
    )

    max_score: float = Field(
        ...,
        gt=0,
    )

    feedback: str | None = Field(
        default=None,
        max_length=MAX_GRADE_FEEDBACK_LENGTH,
    )

    is_released: Literal[True] = True

    released_at: datetime | None = Field(
        default=None,
        description=(
            "Current grade-update timestamp used as the release display timestamp."
        ),
    )

    @field_validator(
        "released_at",
        mode="after",
    )
    @classmethod
    def normalize_release_datetime(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return normalize_utc_datetime(value)


class EvaluationStatusUpdate(BaseModel):
    """
    Explicit instructor-controlled submission-review status update.

    Manual grade creation does not silently modify this status.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    status: EvaluationStatus


class StudentSubmissionEvaluationResponse(BaseModel):
    """
    Student-safe evaluation view.

    Full AST findings, source-similarity records, comparison submission
    identifiers, unreleased grades, and instructor identity are excluded.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    sub_id: int = Field(
        ...,
        gt=0,
    )

    task_id: int = Field(
        ...,
        gt=0,
    )

    status: str

    is_official: bool

    submitted_at: datetime

    accepted_at: datetime | None = None

    instructor_grade: ReleasedInstructorGradeResponse | None = None

    @field_validator(
        "submitted_at",
        "accepted_at",
        mode="after",
    )
    @classmethod
    def normalize_submission_datetime(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return normalize_utc_datetime(value)


class InstructorSubmissionEvaluationResponse(BaseModel):
    """
    Instructor review view for a submission belonging to an owned task.

    Automated indicators remain review-only and do not independently
    assign the official grade or determine academic misconduct.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    sub_id: int = Field(
        ...,
        gt=0,
    )

    student_id: int = Field(
        ...,
        gt=0,
    )

    task_id: int = Field(
        ...,
        gt=0,
    )

    status: str

    is_official: bool

    submitted_at: datetime

    accepted_at: datetime | None = None

    jaccard_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    ast_pass_fail: bool | None = None

    ast_analyses: list[ASTAnalysisResponse] = Field(
        default_factory=list,
    )

    similarity_results_as_source: list[SimilarityResultResponse] = Field(
        default_factory=list,
    )

    instructor_grade: InstructorGradeResponse | None = None

    @field_validator(
        "submitted_at",
        "accepted_at",
        mode="after",
    )
    @classmethod
    def normalize_submission_datetime(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return normalize_utc_datetime(value)


# Compatibility alias for older instructor-facing imports.
# Student routes must use StudentSubmissionEvaluationResponse directly.
SubmissionEvaluationResponse = InstructorSubmissionEvaluationResponse
