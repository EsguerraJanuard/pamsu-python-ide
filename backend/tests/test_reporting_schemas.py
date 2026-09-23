from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.reporting_schema import (
    ActivityCompletionSummaryResponse,
    ClassroomActivityCompletionItem,
    ClassroomCompletionSummaryResponse,
    CompletionCounts,
    GradeDistributionBucket,
    GradeDistributionResponse,
    GradebookCSVExportMetadata,
    MissingSubmissionItem,
    MissingSubmissionListResponse,
    ReportingActivitySummary,
    ReportingClassroomSummary,
    ReportingStudentSummary,
    StudentClassProgressItem,
    StudentProgressSummaryResponse,
)


NOW = datetime.now(timezone.utc)


def _classroom_summary() -> ReportingClassroomSummary:
    return ReportingClassroomSummary(
        class_id=1,
        name="BSIT 3A",
        subject_code="IT-301",
        section="3A",
    )


def _activity_summary() -> ReportingActivitySummary:
    return ReportingActivitySummary(
        task_id=10,
        title="Functions Laboratory",
        activity_type="laboratory",
        class_id=1,
        is_graded=True,
        is_published=True,
        due_at=None,
    )


def _completion_counts() -> CompletionCounts:
    return CompletionCounts(
        expected_count=4,
        submitted_count=3,
        missing_count=1,
        manually_graded_count=2,
        released_grade_count=1,
        completion_percentage=75.0,
    )


def test_reporting_schemas_forbid_extra_fields():
    with pytest.raises(
        ValidationError,
        match="Extra inputs are not permitted",
    ):
        ReportingClassroomSummary(
            class_id=1,
            name="BSIT 3A",
            subject_code="IT-301",
            section="3A",
            raw_code="print('forbidden')",
        )


@pytest.mark.parametrize(
    ("school_id", "expected_message"),
    [
        (
            "123456789",
            "String should match pattern",
        ),
        (
            "12345678901",
            "String should match pattern",
        ),
        (
            "ABCDEFGHIJ",
            "String should match pattern",
        ),
    ],
)
def test_reporting_student_summary_requires_ten_digit_school_id(
    school_id: str,
    expected_message: str,
):
    with pytest.raises(
        ValidationError,
        match=expected_message,
    ):
        ReportingStudentSummary(
            student_id=1,
            name="Student One",
            school_id=school_id,
        )


def test_completion_counts_accept_valid_invariants():
    counts = _completion_counts()

    assert counts.expected_count == 4
    assert counts.submitted_count == 3
    assert counts.missing_count == 1
    assert counts.manually_graded_count == 2
    assert counts.released_grade_count == 1
    assert counts.completion_percentage == 75.0


def test_completion_counts_reject_inconsistent_expected_total():
    with pytest.raises(
        ValidationError,
        match=("submitted_count plus missing_count must equal expected_count"),
    ):
        CompletionCounts(
            expected_count=5,
            submitted_count=3,
            missing_count=1,
            manually_graded_count=2,
            released_grade_count=1,
            completion_percentage=60.0,
        )


def test_completion_counts_reject_more_manual_grades_than_submissions():
    with pytest.raises(
        ValidationError,
        match="manually_graded_count cannot exceed submitted_count",
    ):
        CompletionCounts(
            expected_count=4,
            submitted_count=2,
            missing_count=2,
            manually_graded_count=3,
            released_grade_count=1,
            completion_percentage=50.0,
        )


def test_completion_counts_reject_more_released_than_manual_grades():
    with pytest.raises(
        ValidationError,
        match=("released_grade_count cannot exceed manually_graded_count"),
    ):
        CompletionCounts(
            expected_count=4,
            submitted_count=3,
            missing_count=1,
            manually_graded_count=1,
            released_grade_count=2,
            completion_percentage=75.0,
        )


def test_activity_completion_summary_contract():
    response = ActivityCompletionSummaryResponse(
        activity=_activity_summary(),
        active_student_count=4,
        completion=_completion_counts(),
        generated_at=NOW,
    )

    assert response.activity.task_id == 10
    assert response.active_student_count == 4
    assert response.completion.missing_count == 1
    assert response.generated_at == NOW


def test_classroom_completion_summary_contract():
    response = ClassroomCompletionSummaryResponse(
        classroom=_classroom_summary(),
        active_student_count=4,
        published_graded_activity_count=1,
        completion=_completion_counts(),
        activities=[
            ClassroomActivityCompletionItem(
                activity=_activity_summary(),
                completion=_completion_counts(),
            )
        ],
        generated_at=NOW,
    )

    assert response.classroom.class_id == 1
    assert response.published_graded_activity_count == 1
    assert len(response.activities) == 1
    assert response.activities[0].activity.task_id == 10


def test_grade_distribution_bucket_rejects_reversed_range():
    with pytest.raises(
        ValidationError,
        match=("minimum_percentage cannot exceed maximum_percentage"),
    ):
        GradeDistributionBucket(
            band="80-89.99",
            minimum_percentage=89.99,
            maximum_percentage=80.0,
            count=1,
            percentage_of_graded=100.0,
        )


def test_grade_distribution_requires_bucket_total_to_match():
    with pytest.raises(
        ValidationError,
        match=("Bucket counts must equal manually_graded_submission_count"),
    ):
        GradeDistributionResponse(
            classroom=_classroom_summary(),
            activity=_activity_summary(),
            manually_graded_submission_count=2,
            released_grade_count=1,
            average_percentage=85.0,
            minimum_percentage=80.0,
            maximum_percentage=90.0,
            buckets=[
                GradeDistributionBucket(
                    band="80-89.99",
                    minimum_percentage=80.0,
                    maximum_percentage=89.99,
                    count=1,
                    percentage_of_graded=50.0,
                )
            ],
            generated_at=NOW,
        )


def test_grade_distribution_accepts_manual_grade_only_summary():
    response = GradeDistributionResponse(
        classroom=_classroom_summary(),
        activity=None,
        manually_graded_submission_count=2,
        released_grade_count=1,
        average_percentage=85.0,
        minimum_percentage=80.0,
        maximum_percentage=90.0,
        buckets=[
            GradeDistributionBucket(
                band="80-89.99",
                minimum_percentage=80.0,
                maximum_percentage=89.99,
                count=1,
                percentage_of_graded=50.0,
            ),
            GradeDistributionBucket(
                band="90-100",
                minimum_percentage=90.0,
                maximum_percentage=100.0,
                count=1,
                percentage_of_graded=50.0,
            ),
        ],
        generated_at=NOW,
    )

    assert response.manually_graded_submission_count == 2
    assert response.released_grade_count == 1
    assert sum(bucket.count for bucket in response.buckets) == 2


def test_missing_submission_report_contract():
    response = MissingSubmissionListResponse(
        items=[
            MissingSubmissionItem(
                student=ReportingStudentSummary(
                    student_id=2,
                    name="Student Two",
                    school_id="2026000002",
                ),
                activity=_activity_summary(),
                due_at=None,
            )
        ],
        page=1,
        page_size=25,
        total_items=1,
        total_pages=1,
        sort_by="student_name",
        sort_direction="asc",
        generated_at=NOW,
    )

    assert response.items[0].submission_state == "missing"
    assert response.items[0].enrollment_status == "active"
    assert response.total_items == 1


def test_student_class_progress_rejects_inconsistent_counts():
    with pytest.raises(
        ValidationError,
        match=(
            "submitted_activity_count plus missing_activity_count "
            "must equal published_graded_activity_count"
        ),
    ):
        StudentClassProgressItem(
            classroom=_classroom_summary(),
            published_graded_activity_count=5,
            submitted_activity_count=2,
            missing_activity_count=1,
            released_grade_count=1,
            average_released_percentage=88.0,
            completion_percentage=40.0,
        )


def test_student_progress_summary_contract():
    class_progress = StudentClassProgressItem(
        classroom=_classroom_summary(),
        published_graded_activity_count=4,
        submitted_activity_count=3,
        missing_activity_count=1,
        released_grade_count=2,
        average_released_percentage=87.5,
        completion_percentage=75.0,
    )

    response = StudentProgressSummaryResponse(
        student_id=2,
        active_classroom_count=1,
        published_graded_activity_count=4,
        submitted_activity_count=3,
        missing_activity_count=1,
        released_grade_count=2,
        average_released_percentage=87.5,
        completion_percentage=75.0,
        classrooms=[
            class_progress,
        ],
        generated_at=NOW,
    )

    assert response.student_id == 2
    assert response.active_classroom_count == 1
    assert len(response.classrooms) == 1
    assert response.classrooms[0].completion_percentage == 75.0


def test_student_progress_rejects_released_count_above_submitted_count():
    with pytest.raises(
        ValidationError,
        match=("released_grade_count cannot exceed submitted_activity_count"),
    ):
        StudentProgressSummaryResponse(
            student_id=2,
            active_classroom_count=1,
            published_graded_activity_count=2,
            submitted_activity_count=1,
            missing_activity_count=1,
            released_grade_count=2,
            average_released_percentage=90.0,
            completion_percentage=50.0,
            classrooms=[],
            generated_at=NOW,
        )


@pytest.mark.parametrize(
    "filename",
    [
        "../gradebook.csv",
        "gradebook.xlsx",
        "grade book.csv",
        "gradebook;rm.csv",
    ],
)
def test_csv_export_metadata_rejects_unsafe_filename(
    filename: str,
):
    with pytest.raises(ValidationError):
        GradebookCSVExportMetadata(
            filename=filename,
            row_count=10,
            generated_at=NOW,
        )


def test_csv_export_metadata_enforces_privacy_flags():
    metadata = GradebookCSVExportMetadata(
        filename="classroom-1-gradebook.csv",
        row_count=10,
        generated_at=NOW,
    )

    assert metadata.includes_raw_source is False
    assert metadata.includes_unreleased_student_data is False

    with pytest.raises(ValidationError):
        GradebookCSVExportMetadata(
            filename="classroom-1-gradebook.csv",
            row_count=10,
            generated_at=NOW,
            includes_raw_source=True,
        )


def test_reporting_contracts_exclude_sensitive_fields():
    reporting_models = [
        ReportingStudentSummary,
        ReportingClassroomSummary,
        ReportingActivitySummary,
        ActivityCompletionSummaryResponse,
        ClassroomCompletionSummaryResponse,
        GradeDistributionResponse,
        MissingSubmissionListResponse,
        StudentProgressSummaryResponse,
        GradebookCSVExportMetadata,
    ]

    prohibited_fields = {
        "raw_code",
        "source_code",
        "starter_code",
        "standard_input",
        "expected_output",
        "hidden_test_cases",
        "required_ast_rules",
        "ast_details",
        "ast_findings",
        "jaccard_score",
        "similarity_results",
        "stdout",
        "stderr",
        "worker_task_id",
        "coding_session_telemetry",
        "clipboard_content",
        "pasted_text",
        "keystrokes",
        "browsing_history",
        "screen_recording",
        "webcam",
        "microphone",
        "automatic_grade",
        "risk_score",
        "plagiarism_verdict",
        "cheating_verdict",
        "misconduct_verdict",
    }

    for model in reporting_models:
        assert prohibited_fields.isdisjoint(
            model.model_fields,
        )
