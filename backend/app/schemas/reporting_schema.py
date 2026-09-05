from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ActivityType = Literal["laboratory", "homework"]
ReportingSortDirection = Literal["asc", "desc"]
MissingSubmissionSortField = Literal[
    "student_name",
    "school_id",
    "activity_title",
    "due_at",
]
GradeDistributionBand = Literal[
    "0-59.99",
    "60-69.99",
    "70-79.99",
    "80-89.99",
    "90-100",
]


class ReportingSchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReportingStudentSummary(ReportingSchemaBase):
    student_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=150)
    school_id: str = Field(..., pattern=r"^\d{10}$")


class ReportingClassroomSummary(ReportingSchemaBase):
    class_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=150)
    subject_code: str | None = Field(default=None, max_length=50)
    section: str | None = Field(default=None, max_length=100)


class ReportingActivitySummary(ReportingSchemaBase):
    task_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    activity_type: ActivityType
    class_id: int = Field(..., gt=0)
    is_graded: bool
    is_published: bool
    due_at: datetime | None = None


class CompletionCounts(ReportingSchemaBase):
    expected_count: int = Field(..., ge=0)
    submitted_count: int = Field(..., ge=0)
    missing_count: int = Field(..., ge=0)
    manually_graded_count: int = Field(..., ge=0)
    released_grade_count: int = Field(..., ge=0)
    completion_percentage: float = Field(..., ge=0, le=100)

    @model_validator(mode="after")
    def validate_counts(self) -> "CompletionCounts":
        if self.submitted_count + self.missing_count != self.expected_count:
            raise ValueError(
                "submitted_count plus missing_count must equal expected_count."
            )

        if self.manually_graded_count > self.submitted_count:
            raise ValueError("manually_graded_count cannot exceed submitted_count.")

        if self.released_grade_count > self.manually_graded_count:
            raise ValueError(
                "released_grade_count cannot exceed manually_graded_count."
            )

        return self


class ActivityCompletionSummaryResponse(ReportingSchemaBase):
    activity: ReportingActivitySummary
    active_student_count: int = Field(..., ge=0)
    completion: CompletionCounts
    generated_at: datetime


class ClassroomActivityCompletionItem(ReportingSchemaBase):
    activity: ReportingActivitySummary
    completion: CompletionCounts


class ClassroomCompletionSummaryResponse(ReportingSchemaBase):
    classroom: ReportingClassroomSummary
    active_student_count: int = Field(..., ge=0)
    published_graded_activity_count: int = Field(..., ge=0)
    completion: CompletionCounts
    activities: list[ClassroomActivityCompletionItem] = Field(default_factory=list)
    generated_at: datetime


class GradeDistributionBucket(ReportingSchemaBase):
    band: GradeDistributionBand
    minimum_percentage: float = Field(..., ge=0, le=100)
    maximum_percentage: float = Field(..., ge=0, le=100)
    count: int = Field(..., ge=0)
    percentage_of_graded: float = Field(..., ge=0, le=100)

    @model_validator(mode="after")
    def validate_range(self) -> "GradeDistributionBucket":
        if self.minimum_percentage > self.maximum_percentage:
            raise ValueError("minimum_percentage cannot exceed maximum_percentage.")

        return self


class GradeDistributionResponse(ReportingSchemaBase):
    classroom: ReportingClassroomSummary
    activity: ReportingActivitySummary | None = None
    manually_graded_submission_count: int = Field(..., ge=0)
    released_grade_count: int = Field(..., ge=0)
    average_percentage: float | None = Field(default=None, ge=0, le=100)
    minimum_percentage: float | None = Field(default=None, ge=0, le=100)
    maximum_percentage: float | None = Field(default=None, ge=0, le=100)
    buckets: list[GradeDistributionBucket] = Field(default_factory=list)
    generated_at: datetime

    @model_validator(mode="after")
    def validate_distribution(self) -> "GradeDistributionResponse":
        if self.released_grade_count > self.manually_graded_submission_count:
            raise ValueError(
                "released_grade_count cannot exceed manually_graded_submission_count."
            )

        if sum(bucket.count for bucket in self.buckets) != (
            self.manually_graded_submission_count
        ):
            raise ValueError(
                "Bucket counts must equal manually_graded_submission_count."
            )

        return self


class MissingSubmissionItem(ReportingSchemaBase):
    student: ReportingStudentSummary
    activity: ReportingActivitySummary
    due_at: datetime | None = None
    enrollment_status: Literal["active"] = "active"
    submission_state: Literal["missing"] = "missing"


class MissingSubmissionListResponse(ReportingSchemaBase):
    items: list[MissingSubmissionItem] = Field(default_factory=list)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_items: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)
    sort_by: MissingSubmissionSortField
    sort_direction: ReportingSortDirection
    generated_at: datetime


class StudentClassProgressItem(ReportingSchemaBase):
    classroom: ReportingClassroomSummary
    published_graded_activity_count: int = Field(..., ge=0)
    submitted_activity_count: int = Field(..., ge=0)
    missing_activity_count: int = Field(..., ge=0)
    released_grade_count: int = Field(..., ge=0)
    average_released_percentage: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    completion_percentage: float = Field(..., ge=0, le=100)

    @model_validator(mode="after")
    def validate_progress(self) -> "StudentClassProgressItem":
        if self.submitted_activity_count + self.missing_activity_count != (
            self.published_graded_activity_count
        ):
            raise ValueError(
                "submitted_activity_count plus missing_activity_count "
                "must equal published_graded_activity_count."
            )

        return self


class StudentProgressSummaryResponse(ReportingSchemaBase):
    student_id: int = Field(..., gt=0)
    active_classroom_count: int = Field(..., ge=0)
    published_graded_activity_count: int = Field(..., ge=0)
    submitted_activity_count: int = Field(..., ge=0)
    missing_activity_count: int = Field(..., ge=0)
    released_grade_count: int = Field(..., ge=0)
    average_released_percentage: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    completion_percentage: float = Field(..., ge=0, le=100)
    classrooms: list[StudentClassProgressItem] = Field(default_factory=list)
    generated_at: datetime

    @model_validator(mode="after")
    def validate_progress(self) -> "StudentProgressSummaryResponse":
        if self.submitted_activity_count + self.missing_activity_count != (
            self.published_graded_activity_count
        ):
            raise ValueError(
                "submitted_activity_count plus missing_activity_count "
                "must equal published_graded_activity_count."
            )

        if self.released_grade_count > self.submitted_activity_count:
            raise ValueError(
                "released_grade_count cannot exceed submitted_activity_count."
            )

        return self


class GradebookCSVExportMetadata(ReportingSchemaBase):
    filename: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=r"^[A-Za-z0-9._-]+\.csv$",
    )
    row_count: int = Field(..., ge=0)
    generated_at: datetime
    includes_raw_source: Literal[False] = False
    includes_unreleased_student_data: Literal[False] = False


# AUTHORIZATION BOUNDARY:
# Instructor reports and exports must be scoped to classrooms and
# activities owned by the authenticated instructor. Student progress
# must use only the authenticated student's identity.

# PRIVACY BOUNDARY:
# Reporting contracts exclude source code, standard input, starter code,
# hidden tests, AST findings, similarity records, execution output,
# coding-session telemetry, clipboard or pasted text, browsing history,
# surveillance data, credentials, OTPs, JWTs, and misconduct verdicts.

# GRADING BOUNDARY:
# Grade distributions and gradebook exports use only manually created
# InstructorGrade records. Automated indicators never populate grades,
# rankings, completion results, or misconduct conclusions.

# EXPORT BOUNDARY:
# CSV exports are gradebook summaries only. Raw source export is not
# enabled by default or through any client-selectable option.
