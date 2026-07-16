from datetime import datetime, timezone
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.submission_schema import (
    SubmissionStatus,
)


ReviewQueueSortField = Literal[
    "submitted_at",
    "accepted_at",
    "student_name",
    "attempt_number",
]

SortDirection = Literal[
    "asc",
    "desc",
]

MIN_PAGE_SIZE = 1
MAX_PAGE_SIZE = 100


def normalize_review_datetime(
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


class ReviewQueueStudentSummary(BaseModel):
    """
    Minimal instructor-facing student identity.

    Authentication data, password information, and unrelated profile
    fields are intentionally excluded.
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


class ReviewQueueActivitySummary(BaseModel):
    """
    Minimal activity and classroom information needed by the queue.
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


class InstructorReviewQueueItem(BaseModel):
    """
    Instructor-owned review-queue summary.

    Raw source code, standard input, AST details, similarity details,
    execution output, and behavioral telemetry are intentionally
    excluded. Those records require separate authorized detail routes.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    sub_id: int = Field(
        ...,
        gt=0,
    )

    student: ReviewQueueStudentSummary

    activity: ReviewQueueActivitySummary

    attempt_number: int = Field(
        ...,
        gt=0,
    )

    status: SubmissionStatus

    is_official: bool

    submitted_at: datetime

    accepted_at: datetime | None = None

    has_manual_grade: bool

    grade_is_released: bool

    @field_validator(
        "submitted_at",
        "accepted_at",
        mode="after",
    )
    @classmethod
    def normalize_datetime_fields(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return normalize_review_datetime(value)

    @model_validator(
        mode="after",
    )
    def validate_grade_state(
        self,
    ) -> "InstructorReviewQueueItem":
        if self.grade_is_released and not self.has_manual_grade:
            raise ValueError("A released grade requires an existing manual grade.")

        return self


class ReviewQueueCounts(BaseModel):
    """
    Counts calculated from the instructor-authorized filtered result set.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    total: int = Field(
        ...,
        ge=0,
    )

    submitted: int = Field(
        ...,
        ge=0,
    )

    awaiting_review: int = Field(
        ...,
        ge=0,
    )

    graded: int = Field(
        ...,
        ge=0,
    )

    rejected: int = Field(
        ...,
        ge=0,
    )

    official: int = Field(
        ...,
        ge=0,
    )

    unofficial: int = Field(
        ...,
        ge=0,
    )

    unreleased_grades: int = Field(
        ...,
        ge=0,
    )

    @model_validator(
        mode="after",
    )
    def validate_counts(
        self,
    ) -> "ReviewQueueCounts":
        status_total = (
            self.submitted + self.awaiting_review + self.graded + self.rejected
        )

        official_total = self.official + self.unofficial

        if status_total != self.total:
            raise ValueError("Submission-status counts must equal the total.")

        if official_total != self.total:
            raise ValueError("Official-attempt counts must equal the total.")

        if self.unreleased_grades > self.total:
            raise ValueError("Unreleased-grade count cannot exceed the total.")

        return self


class InstructorReviewQueueResponse(BaseModel):
    """
    Paginated instructor review queue.

    Pagination is bounded, and the service must use deterministic
    sorting with submission ID as the final tie-breaker.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[InstructorReviewQueueItem] = Field(
        default_factory=list,
    )

    page: int = Field(
        ...,
        ge=1,
    )

    page_size: int = Field(
        ...,
        ge=MIN_PAGE_SIZE,
        le=MAX_PAGE_SIZE,
    )

    total_items: int = Field(
        ...,
        ge=0,
    )

    total_pages: int = Field(
        ...,
        ge=0,
    )

    sort_by: ReviewQueueSortField

    sort_direction: SortDirection

    counts: ReviewQueueCounts

    @model_validator(
        mode="after",
    )
    def validate_pagination(
        self,
    ) -> "InstructorReviewQueueResponse":
        expected_total_pages = (
            0
            if self.total_items == 0
            else (self.total_items + self.page_size - 1) // self.page_size
        )

        if self.total_pages != expected_total_pages:
            raise ValueError("total_pages does not match total_items and page_size.")

        if len(self.items) > self.page_size:
            raise ValueError("Queue items cannot exceed page_size.")

        if self.counts.total != self.total_items:
            raise ValueError("Queue counts total must equal total_items.")

        return self


# PRIVACY BOUNDARY:
# Review-queue summaries never expose raw source code, standard input,
# hidden test cases, AST findings, similarity comparison details,
# execution output, clipboard contents, pasted text, or surveillance data.

# REVIEW BOUNDARY:
# Queue membership and ordering must not be determined by an automatic
# misconduct, plagiarism, cheating, copying, or risk score.
