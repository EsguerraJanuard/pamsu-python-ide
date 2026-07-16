from datetime import datetime, timezone
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.submission_schema import SubmissionStatus


GradebookSortField = Literal[
    "student_name",
    "school_id",
    "submitted_at",
    "score",
    "percentage",
]

GradebookSortDirection = Literal[
    "asc",
    "desc",
]

MIN_GRADEBOOK_PAGE_SIZE = 1
MAX_GRADEBOOK_PAGE_SIZE = 100


def normalize_gradebook_datetime(
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


class GradebookStudentSummary(BaseModel):
    """
    Minimal instructor-facing student identity for gradebook rows.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    student_id: int = Field(
        ...,
        gt=0,
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
    )

    school_id: str = Field(
        ...,
        pattern=r"^\d{10}$",
    )


class GradebookActivitySummary(BaseModel):
    """
    Minimal activity and classroom context for gradebook responses.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    task_id: int = Field(
        ...,
        gt=0,
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    activity_type: Literal[
        "laboratory",
        "homework",
    ]

    class_id: int | None = Field(
        default=None,
        gt=0,
    )

    class_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    subject_code: str | None = Field(
        default=None,
        max_length=50,
    )

    section: str | None = Field(
        default=None,
        max_length=100,
    )


class InstructorGradebookItem(BaseModel):
    """
    Instructor-owned gradebook row.

    Raw source code, standard input, AST details, similarity records,
    execution output, and session telemetry are intentionally excluded.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    sub_id: int = Field(
        ...,
        gt=0,
    )

    student: GradebookStudentSummary

    activity: GradebookActivitySummary

    attempt_number: int = Field(
        ...,
        gt=0,
    )

    submission_status: SubmissionStatus

    is_official: bool

    submitted_at: datetime

    accepted_at: datetime | None = None

    has_manual_grade: bool

    score: float | None = Field(
        default=None,
        ge=0,
    )

    max_score: float | None = Field(
        default=None,
        gt=0,
    )

    percentage: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    grade_is_released: bool

    grade_updated_at: datetime | None = None

    @field_validator(
        "submitted_at",
        "accepted_at",
        "grade_updated_at",
        mode="after",
    )
    @classmethod
    def normalize_datetime_fields(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return normalize_gradebook_datetime(value)

    @model_validator(
        mode="after",
    )
    def validate_grade_state(
        self,
    ) -> "InstructorGradebookItem":
        grade_values = (
            self.score,
            self.max_score,
            self.percentage,
            self.grade_updated_at,
        )

        if not self.has_manual_grade:
            if any(value is not None for value in grade_values):
                raise ValueError(
                    "Grade values must be absent when no manual grade exists."
                )

            if self.grade_is_released:
                raise ValueError("A released grade requires an existing manual grade.")

            return self

        if (
            self.score is None
            or self.max_score is None
            or self.percentage is None
            or self.grade_updated_at is None
        ):
            raise ValueError(
                "Complete grade values are required when a manual grade exists."
            )

        if self.score > self.max_score:
            raise ValueError("score cannot be greater than max_score")

        expected_percentage = self.score / self.max_score * 100

        if abs(self.percentage - expected_percentage) > 0.01:
            raise ValueError("percentage does not match score and max_score.")

        return self


class InstructorGradebookCounts(BaseModel):
    """
    Counts calculated from the instructor-authorized filtered dataset.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    total: int = Field(
        ...,
        ge=0,
    )

    with_manual_grade: int = Field(
        ...,
        ge=0,
    )

    without_manual_grade: int = Field(
        ...,
        ge=0,
    )

    released: int = Field(
        ...,
        ge=0,
    )

    unreleased: int = Field(
        ...,
        ge=0,
    )

    graded_status: int = Field(
        ...,
        ge=0,
    )

    awaiting_review_status: int = Field(
        ...,
        ge=0,
    )

    @model_validator(
        mode="after",
    )
    def validate_counts(
        self,
    ) -> "InstructorGradebookCounts":
        if self.with_manual_grade + self.without_manual_grade != self.total:
            raise ValueError("Manual-grade counts must equal the total.")

        if self.released + self.unreleased != self.with_manual_grade:
            raise ValueError("Released and unreleased counts must equal graded rows.")

        if self.graded_status > self.total:
            raise ValueError("graded_status cannot exceed the total.")

        if self.awaiting_review_status > self.total:
            raise ValueError("awaiting_review_status cannot exceed the total.")

        return self


class InstructorGradebookResponse(BaseModel):
    """
    Paginated instructor gradebook.

    The service must use deterministic ordering and submission ID as
    the final tie-breaker.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[InstructorGradebookItem] = Field(
        default_factory=list,
    )

    page: int = Field(
        ...,
        ge=1,
    )

    page_size: int = Field(
        ...,
        ge=MIN_GRADEBOOK_PAGE_SIZE,
        le=MAX_GRADEBOOK_PAGE_SIZE,
    )

    total_items: int = Field(
        ...,
        ge=0,
    )

    total_pages: int = Field(
        ...,
        ge=0,
    )

    sort_by: GradebookSortField

    sort_direction: GradebookSortDirection

    counts: InstructorGradebookCounts

    @model_validator(
        mode="after",
    )
    def validate_pagination(
        self,
    ) -> "InstructorGradebookResponse":
        expected_total_pages = (
            0
            if self.total_items == 0
            else (self.total_items + self.page_size - 1) // self.page_size
        )

        if self.total_pages != expected_total_pages:
            raise ValueError("total_pages does not match total_items and page_size.")

        if len(self.items) > self.page_size:
            raise ValueError("Gradebook items cannot exceed page_size.")

        if self.counts.total != self.total_items:
            raise ValueError("Gradebook counts total must equal total_items.")

        return self


class StudentReleasedGradeItem(BaseModel):
    """
    Student-safe released grade.

    Internal grade identifiers, instructor identity, unreleased grades,
    and instructor-only analytics are intentionally excluded.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    sub_id: int = Field(
        ...,
        gt=0,
    )

    activity: GradebookActivitySummary

    attempt_number: int = Field(
        ...,
        gt=0,
    )

    submission_status: SubmissionStatus

    score: float = Field(
        ...,
        ge=0,
    )

    max_score: float = Field(
        ...,
        gt=0,
    )

    percentage: float = Field(
        ...,
        ge=0,
        le=100,
    )

    feedback: str | None = Field(
        default=None,
        max_length=5000,
    )

    is_released: Literal[True] = True

    released_at: datetime

    @field_validator(
        "released_at",
        mode="after",
    )
    @classmethod
    def normalize_released_at(
        cls,
        value: datetime,
    ) -> datetime:
        normalized = normalize_gradebook_datetime(value)

        assert normalized is not None

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_grade_values(
        self,
    ) -> "StudentReleasedGradeItem":
        if self.score > self.max_score:
            raise ValueError("score cannot be greater than max_score")

        expected_percentage = self.score / self.max_score * 100

        if abs(self.percentage - expected_percentage) > 0.01:
            raise ValueError("percentage does not match score and max_score.")

        return self


class StudentReleasedGradeListResponse(BaseModel):
    """
    Paginated list containing only the authenticated student's
    released manual grades.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[StudentReleasedGradeItem] = Field(
        default_factory=list,
    )

    page: int = Field(
        ...,
        ge=1,
    )

    page_size: int = Field(
        ...,
        ge=MIN_GRADEBOOK_PAGE_SIZE,
        le=MAX_GRADEBOOK_PAGE_SIZE,
    )

    total_items: int = Field(
        ...,
        ge=0,
    )

    total_pages: int = Field(
        ...,
        ge=0,
    )

    @model_validator(
        mode="after",
    )
    def validate_pagination(
        self,
    ) -> "StudentReleasedGradeListResponse":
        expected_total_pages = (
            0
            if self.total_items == 0
            else (self.total_items + self.page_size - 1) // self.page_size
        )

        if self.total_pages != expected_total_pages:
            raise ValueError("total_pages does not match total_items and page_size.")

        if len(self.items) > self.page_size:
            raise ValueError("Released-grade items cannot exceed page_size.")

        return self


# PRIVACY BOUNDARY:
# Gradebook summary responses never expose source code, standard input,
# hidden test cases, AST details, similarity comparison records,
# execution output, session telemetry, or surveillance data.

# GRADING BOUNDARY:
# Gradebook values come only from an authorized instructor-created
# InstructorGrade record. Automated indicators never populate score,
# maximum score, percentage, release state, or feedback.

# STUDENT VISIBILITY BOUNDARY:
# StudentReleasedGradeListResponse contains only grades whose
# is_released value is true and which belong to the authenticated student.
