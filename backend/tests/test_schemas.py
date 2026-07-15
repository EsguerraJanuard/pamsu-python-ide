from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.log_schema import BehavioralLogCreate
from app.schemas.submission_schema import SubmissionResponse
from app.schemas.task_schema import TaskCreate, TaskResponse
from app.schemas.user_schema import UserCreate


VALID_USER_DATA = {
    "name": "Test Student",
    "school_id": "0000000001",
    "email": "student@pampangastateu.edu.ph",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "data_collection_acknowledged": True,
}


VALID_TASK_DATA = {
    "class_id": 1,
    "title": "Task Without AST Rules",
    "description": "Schema validation test.",
    "instructions": "Complete the programming task.",
    "activity_type": "laboratory",
    "required_ast_rules": {},
    "starter_code": "def solve():\n    pass\n",
    "paste_policy": "internal_only",
    "is_graded": True,
    "due_at": None,
}


def test_valid_user_registration_input():
    user = UserCreate(**VALID_USER_DATA)

    assert user.name == "Test Student"
    assert user.school_id == "0000000001"
    assert user.email == "student@pampangastateu.edu.ph"
    assert user.data_collection_acknowledged is True


def test_user_cannot_supply_role():
    with pytest.raises(ValidationError) as error:
        UserCreate(
            **VALID_USER_DATA,
            role="instructor",
        )

    error_locations = {item["loc"] for item in error.value.errors()}

    assert ("role",) in error_locations


def test_user_cannot_supply_password_hash():
    with pytest.raises(ValidationError) as error:
        UserCreate(
            **VALID_USER_DATA,
            password_hash="client-supplied-hash",
        )

    error_locations = {item["loc"] for item in error.value.errors()}

    assert ("password_hash",) in error_locations


@pytest.mark.parametrize(
    "school_id",
    [
        "123456789",
        "12345678901",
        "12345ABCDE",
        "12345-6789",
    ],
)
def test_school_id_must_be_exactly_ten_digits(
    school_id: str,
):
    with pytest.raises(ValidationError):
        UserCreate(
            **{
                **VALID_USER_DATA,
                "school_id": school_id,
            }
        )


@pytest.mark.parametrize(
    "email",
    [
        "student@gmail.com",
        "student@yahoo.com",
        "student@pampangastateu.edu.com",
        "invalid-email",
    ],
)
def test_user_requires_university_email(
    email: str,
):
    with pytest.raises(ValidationError):
        UserCreate(
            **{
                **VALID_USER_DATA,
                "email": email,
            }
        )


def test_password_confirmation_must_match():
    with pytest.raises(ValidationError):
        UserCreate(
            **{
                **VALID_USER_DATA,
                "confirm_password": "DifferentPass123!",
            }
        )


def test_data_collection_acknowledgment_is_required():
    with pytest.raises(ValidationError):
        UserCreate(
            **{
                **VALID_USER_DATA,
                "data_collection_acknowledged": False,
            }
        )


def test_task_allows_empty_ast_rules():
    task = TaskCreate(**VALID_TASK_DATA)

    assert task.required_ast_rules == {}


def test_task_preserves_starter_code_indentation():
    starter_code = "def solve():\n    for number in range(3):\n        print(number)\n"

    task = TaskCreate(
        **{
            **VALID_TASK_DATA,
            "starter_code": starter_code,
        }
    )

    assert task.starter_code == starter_code


def test_task_accepts_timezone_aware_due_date():
    philippine_timezone = timezone(timedelta(hours=8))

    task = TaskCreate(
        **{
            **VALID_TASK_DATA,
            "due_at": datetime(
                2026,
                7,
                22,
                10,
                0,
                tzinfo=philippine_timezone,
            ),
        }
    )

    assert task.due_at is not None
    assert task.due_at.utcoffset() == timedelta(0)
    assert task.due_at.hour == 2


def test_task_rejects_timezone_naive_due_date():
    with pytest.raises(ValidationError) as error:
        TaskCreate(
            **{
                **VALID_TASK_DATA,
                "due_at": datetime(
                    2026,
                    7,
                    22,
                    10,
                    0,
                ),
            }
        )

    error_locations = {item["loc"] for item in error.value.errors()}

    assert ("due_at",) in error_locations


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("instructor_id", 1),
        ("is_published", True),
        (
            "published_at",
            datetime.now(timezone.utc),
        ),
    ],
)
def test_task_create_rejects_backend_controlled_fields(
    field_name: str,
    field_value,
):
    with pytest.raises(ValidationError) as error:
        TaskCreate(
            **{
                **VALID_TASK_DATA,
                field_name: field_value,
            }
        )

    error_locations = {item["loc"] for item in error.value.errors()}

    assert (field_name,) in error_locations


def test_task_response_treats_naive_database_datetimes_as_utc():
    naive_due_at = datetime(
        2026,
        7,
        22,
        2,
        0,
    )
    naive_created_at = datetime(
        2026,
        7,
        15,
        1,
        0,
    )
    naive_updated_at = datetime(
        2026,
        7,
        15,
        2,
        0,
    )

    task = TaskResponse(
        task_id=1,
        class_id=1,
        instructor_id=1,
        title="Timezone Response Test",
        description="Database datetime normalization test.",
        instructions="Complete the task.",
        activity_type="homework",
        required_ast_rules={},
        starter_code="print('Hello')\n",
        paste_policy="internal_only",
        is_graded=True,
        due_at=naive_due_at,
        is_published=False,
        published_at=None,
        created_at=naive_created_at,
        updated_at=naive_updated_at,
    )

    assert task.due_at is not None
    assert task.due_at.utcoffset() == timedelta(0)
    assert task.created_at.utcoffset() == timedelta(0)
    assert task.updated_at.utcoffset() == timedelta(0)


def test_behavioral_log_rejects_negative_count():
    with pytest.raises(ValidationError) as error:
        BehavioralLogCreate(
            sub_id=1,
            tab_switches_count=-1,
        )

    error_locations = {item["loc"] for item in error.value.errors()}

    assert ("tab_switches_count",) in error_locations


def test_submission_response_rejects_out_of_range_jaccard():
    with pytest.raises(ValidationError) as error:
        SubmissionResponse(
            sub_id=1,
            student_id=1,
            task_id=1,
            raw_code="print('Hello')",
            jaccard_score=101.0,
            ast_pass_fail=True,
        )

    error_locations = {item["loc"] for item in error.value.errors()}

    assert ("jaccard_score",) in error_locations
