from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.main import app
from app.schemas.gradebook_schema import (
    InstructorGradebookItem,
    StudentReleasedGradeItem,
)
from app.schemas.review_queue_schema import (
    InstructorReviewQueueItem,
    InstructorReviewQueueResponse,
    ReviewQueueCounts,
)


def build_activity_payload() -> dict[str, object]:
    return {
        "task_id": 10,
        "title": "Privacy Contract Activity",
        "activity_type": "laboratory",
        "class_ids": [5],
        "class_name": "Programming Class",
        "subject_code": "CS101",
        "section": "A",
    }


def build_student_payload() -> dict[str, object]:
    return {
        "student_id": 20,
        "name": "Privacy Contract Student",
        "school_id": "7200000001",
    }


def test_review_queue_item_rejects_source_and_analytics():
    payload = {
        "sub_id": 1,
        "student": build_student_payload(),
        "activity": build_activity_payload(),
        "attempt_number": 1,
        "status": "awaiting_review",
        "is_official": True,
        "submitted_at": datetime.now(timezone.utc),
        "accepted_at": datetime.now(timezone.utc),
        "has_manual_grade": False,
        "grade_is_released": False,
        "raw_code": "print('private')",
        "standard_input": "private input",
        "jaccard_score": 90,
        "ast_pass_fail": True,
    }

    with pytest.raises(ValidationError):
        InstructorReviewQueueItem.model_validate(payload)


def test_gradebook_item_rejects_review_analytics():
    payload = {
        "sub_id": 1,
        "student": build_student_payload(),
        "activity": build_activity_payload(),
        "attempt_number": 1,
        "submission_status": "graded",
        "is_official": True,
        "submitted_at": datetime.now(timezone.utc),
        "accepted_at": datetime.now(timezone.utc),
        "has_manual_grade": True,
        "score": 90,
        "max_score": 100,
        "percentage": 90,
        "grade_is_released": True,
        "grade_updated_at": datetime.now(timezone.utc),
        "jaccard_score": 95,
        "ast_analyses": [],
        "similarity_results": [],
        "risk_score": 99,
        "plagiarism_verdict": "confirmed",
    }

    with pytest.raises(ValidationError):
        InstructorGradebookItem.model_validate(payload)


def test_student_released_grade_rejects_internal_identity_fields():
    payload = {
        "sub_id": 1,
        "activity": build_activity_payload(),
        "attempt_number": 1,
        "submission_status": "graded",
        "score": 90,
        "max_score": 100,
        "percentage": 90,
        "feedback": "Released feedback.",
        "is_released": True,
        "released_at": datetime.now(timezone.utc),
        "grade_id": 55,
        "student_id": 20,
        "instructor_id": 30,
    }

    with pytest.raises(ValidationError):
        StudentReleasedGradeItem.model_validate(payload)


def test_student_grade_schema_requires_released_state():
    payload = {
        "sub_id": 1,
        "activity": build_activity_payload(),
        "attempt_number": 1,
        "submission_status": "graded",
        "score": 90,
        "max_score": 100,
        "percentage": 90,
        "feedback": "Draft feedback.",
        "is_released": False,
        "released_at": datetime.now(timezone.utc),
    }

    with pytest.raises(ValidationError):
        StudentReleasedGradeItem.model_validate(payload)


def test_student_grade_percentage_must_match_manual_score():
    payload = {
        "sub_id": 1,
        "activity": build_activity_payload(),
        "attempt_number": 1,
        "submission_status": "graded",
        "score": 90,
        "max_score": 100,
        "percentage": 75,
        "feedback": "Released feedback.",
        "is_released": True,
        "released_at": datetime.now(timezone.utc),
    }

    with pytest.raises(ValidationError):
        StudentReleasedGradeItem.model_validate(payload)


def test_review_queue_counts_must_match_total():
    with pytest.raises(ValidationError):
        ReviewQueueCounts(
            total=2,
            submitted=0,
            awaiting_review=1,
            graded=0,
            rejected=0,
            official=1,
            unofficial=0,
            unreleased_grades=0,
        )


def test_review_queue_page_size_is_bounded():
    with pytest.raises(ValidationError):
        InstructorReviewQueueResponse(
            items=[],
            page=1,
            page_size=101,
            total_items=0,
            total_pages=0,
            sort_by="submitted_at",
            sort_direction="desc",
            counts={
                "total": 0,
                "submitted": 0,
                "awaiting_review": 0,
                "graded": 0,
                "rejected": 0,
                "official": 0,
                "unofficial": 0,
                "unreleased_grades": 0,
            },
        )


def test_pillar10_endpoints_are_registered_in_openapi():
    document = app.openapi()

    assert "/instructors/review-queue" in document["paths"]

    assert "/instructors/gradebook" in document["paths"]

    assert "/activities/released-grades" in document["paths"]

    assert "get" in document["paths"]["/instructors/review-queue"]

    assert "get" in document["paths"]["/instructors/gradebook"]

    assert "get" in document["paths"]["/activities/released-grades"]


def test_openapi_summary_schemas_exclude_sensitive_fields():
    document = app.openapi()

    schemas = document["components"]["schemas"]

    review_queue_properties = schemas["InstructorReviewQueueItem"]["properties"]

    gradebook_properties = schemas["InstructorGradebookItem"]["properties"]

    student_grade_properties = schemas["StudentReleasedGradeItem"]["properties"]

    prohibited_summary_fields = {
        "raw_code",
        "standard_input",
        "ast_analyses",
        "ast_details",
        "jaccard_score",
        "similarity_results",
        "execution_requests",
        "coding_session",
        "risk_score",
        "behavior_score",
        "plagiarism_verdict",
        "misconduct_verdict",
    }

    assert prohibited_summary_fields.isdisjoint(review_queue_properties)

    assert prohibited_summary_fields.isdisjoint(gradebook_properties)

    assert prohibited_summary_fields.isdisjoint(student_grade_properties)

    prohibited_student_fields = {
        "grade_id",
        "student_id",
        "instructor_id",
        "submission_id",
    }

    assert prohibited_student_fields.isdisjoint(student_grade_properties)
