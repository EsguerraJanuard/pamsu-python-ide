import pytest
from pydantic import ValidationError

from app.schemas.log_schema import BehavioralLogCreate
from app.schemas.submission_schema import SubmissionResponse
from app.schemas.task_schema import TaskCreate
from app.schemas.user_schema import UserCreate


def test_user_role_validation():
    valid_user = UserCreate(
        name="Test Student",
        role="student",
        password_hash="hashed-password",
    )

    assert valid_user.role == "student"

    with pytest.raises(ValidationError):
        UserCreate(
            name="Invalid User",
            role="admin",
            password_hash="hashed-password",
        )


def test_task_requires_non_empty_ast_rules():
    with pytest.raises(ValidationError):
        TaskCreate(
            instructor_id=1,
            title="Empty Rules Task",
            required_ast_rules={},
        )


def test_behavioral_log_rejects_negative_count():
    with pytest.raises(ValidationError):
        BehavioralLogCreate(
            sub_id=1,
            tab_switches_count=-1,
        )


def test_submission_response_rejects_out_of_range_jaccard():
    with pytest.raises(ValidationError):
        SubmissionResponse(
            sub_id=1,
            student_id=1,
            task_id=1,
            raw_code="print('Hello')",
            jaccard_score=101.0,
            ast_pass_fail=True,
        )
