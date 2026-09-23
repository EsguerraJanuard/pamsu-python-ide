from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.execution_schema import (
    MAX_COMBINED_EXECUTION_OUTPUT_BYTES,
    MAX_MEMORY_LIMIT_BYTES,
    MAX_OUTPUT_LIMIT_BYTES,
    MAX_PROCESS_LIMIT,
    MAX_TIME_LIMIT_MS,
    ExecutionWorkerUpdate,
    PartnerExecutionDispatchRequest,
    PartnerExecutionLimits,
    PartnerExecutionResultUpdate,
    PartnerExecutionUpdateAcceptedResponse,
    is_execution_status_transition_allowed,
)
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
    "class_ids": [1],
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


def _valid_dispatch_data(
    *,
    request_kind: str = "run",
) -> dict[str, object]:
    data: dict[str, object] = {
        "execution_id": str(uuid4()),
        "correlation_id": str(uuid4()),
        "idempotency_key": str(uuid4()),
        "request_kind": request_kind,
        "task_id": 1,
        "submission_id": None,
        "coding_session_id": str(uuid4()),
        "source_code": "print('hello')\n",
        "standard_input": "",
        "queued_at": datetime.now(timezone.utc),
    }

    if request_kind == "submit":
        data["submission_id"] = 10

    return data


def _valid_result_update_data(
    *,
    status: str = "completed",
) -> dict[str, object]:
    now = datetime.now(timezone.utc)

    return {
        "execution_id": str(uuid4()),
        "correlation_id": str(uuid4()),
        "update_id": str(uuid4()),
        "sequence_number": 1,
        "worker_task_id": "worker-task-1",
        "status": status,
        "stdout": "hello\n",
        "stderr": "",
        "exit_code": 0 if status == "completed" else None,
        "execution_time_ms": 15,
        "limit_reason": None,
        "error_code": None,
        "error_message": None,
        "started_at": now,
        "completed_at": (
            None if status == "running" else now + timedelta(milliseconds=15)
        ),
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
            mouseleave_count=-1,
        )

    error_locations = {item["loc"] for item in error.value.errors()}

    assert ("tab_switches_count",) in error_locations
    assert ("mouseleave_count",) in error_locations


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


def test_partner_dispatch_accepts_valid_run_contract():
    dispatch = PartnerExecutionDispatchRequest(**_valid_dispatch_data())

    assert dispatch.request_kind == "run"
    assert dispatch.submission_id is None
    assert dispatch.source_code == "print('hello')\n"
    assert dispatch.queued_at.utcoffset() == timedelta(0)


def test_partner_dispatch_accepts_valid_submit_contract():
    dispatch = PartnerExecutionDispatchRequest(
        **_valid_dispatch_data(
            request_kind="submit",
        )
    )

    assert dispatch.request_kind == "submit"
    assert dispatch.submission_id == 10


def test_partner_dispatch_normalizes_uuid_strings():
    execution_id = uuid4()
    correlation_id = uuid4()
    idempotency_key = uuid4()

    dispatch = PartnerExecutionDispatchRequest(
        **{
            **_valid_dispatch_data(),
            "execution_id": str(execution_id).upper(),
            "correlation_id": str(correlation_id).upper(),
            "idempotency_key": str(idempotency_key).upper(),
        }
    )

    assert dispatch.execution_id == str(execution_id)
    assert dispatch.correlation_id == str(correlation_id)
    assert dispatch.idempotency_key == str(idempotency_key)


def test_partner_dispatch_rejects_timezone_naive_queued_at():
    with pytest.raises(
        ValidationError,
        match="timestamps must include a timezone",
    ):
        PartnerExecutionDispatchRequest(
            **{
                **_valid_dispatch_data(),
                "queued_at": datetime.now(),
            }
        )


@pytest.mark.parametrize(
    (
        "request_kind",
        "submission_id",
        "expected_message",
    ),
    [
        (
            "submit",
            None,
            "require a submission ID",
        ),
        (
            "run",
            10,
            "cannot reference a submission",
        ),
        (
            "check",
            10,
            "cannot reference a submission",
        ),
    ],
)
def test_partner_dispatch_enforces_submission_contract(
    request_kind: str,
    submission_id: int | None,
    expected_message: str,
):
    with pytest.raises(
        ValidationError,
        match=expected_message,
    ):
        PartnerExecutionDispatchRequest(
            **{
                **_valid_dispatch_data(
                    request_kind=request_kind,
                ),
                "submission_id": submission_id,
            }
        )


def test_partner_dispatch_forbids_extra_sensitive_fields():
    with pytest.raises(ValidationError) as error:
        PartnerExecutionDispatchRequest(
            **{
                **_valid_dispatch_data(),
                "jwt": "forbidden",
                "password": "forbidden",
                "official_grade": 99,
            }
        )

    error_locations = {item["loc"] for item in error.value.errors()}

    assert ("jwt",) in error_locations
    assert ("password",) in error_locations
    assert ("official_grade",) in error_locations


@pytest.mark.parametrize(
    (
        "field_name",
        "field_value",
    ),
    [
        (
            "time_limit_ms",
            MAX_TIME_LIMIT_MS + 1,
        ),
        (
            "memory_limit_bytes",
            MAX_MEMORY_LIMIT_BYTES + 1,
        ),
        (
            "output_limit_bytes",
            MAX_OUTPUT_LIMIT_BYTES + 1,
        ),
        (
            "process_limit",
            MAX_PROCESS_LIMIT + 1,
        ),
    ],
)
def test_partner_execution_limits_are_bounded(
    field_name: str,
    field_value: int,
):
    with pytest.raises(ValidationError):
        PartnerExecutionLimits(
            **{
                field_name: field_value,
            }
        )


def test_partner_result_accepts_running_update():
    result = PartnerExecutionResultUpdate(
        **_valid_result_update_data(
            status="running",
        )
    )

    assert result.status == "running"
    assert result.completed_at is None
    assert result.sequence_number == 1


def test_partner_result_requires_completed_at_for_terminal_status():
    with pytest.raises(
        ValidationError,
        match="Terminal worker updates require completed_at",
    ):
        PartnerExecutionResultUpdate(
            **{
                **_valid_result_update_data(),
                "completed_at": None,
            }
        )


def test_partner_result_rejects_terminal_fields_while_running():
    with pytest.raises(
        ValidationError,
        match="Running updates cannot include terminal result fields",
    ):
        PartnerExecutionResultUpdate(
            **{
                **_valid_result_update_data(
                    status="running",
                ),
                "exit_code": 1,
            }
        )


def test_partner_result_completed_status_rejects_nonzero_exit_code():
    with pytest.raises(
        ValidationError,
        match="cannot report a non-zero exit code",
    ):
        PartnerExecutionResultUpdate(
            **{
                **_valid_result_update_data(),
                "exit_code": 1,
            }
        )


@pytest.mark.parametrize(
    "status_value",
    [
        "timed_out",
        "memory_limit",
        "output_limit",
        "process_limit",
    ],
)
def test_partner_result_resource_limit_requires_reason(
    status_value: str,
):
    with pytest.raises(
        ValidationError,
        match="require limit_reason",
    ):
        PartnerExecutionResultUpdate(
            **{
                **_valid_result_update_data(
                    status=status_value,
                ),
                "limit_reason": None,
            }
        )


def test_partner_result_rejects_completed_at_before_started_at():
    now = datetime.now(timezone.utc)

    with pytest.raises(
        ValidationError,
        match="completed_at cannot be earlier than started_at",
    ):
        PartnerExecutionResultUpdate(
            **{
                **_valid_result_update_data(),
                "started_at": now,
                "completed_at": now - timedelta(seconds=1),
            }
        )


def test_partner_result_rejects_combined_utf8_output_above_limit():
    oversized_multibyte_output = "🙂" * (MAX_COMBINED_EXECUTION_OUTPUT_BYTES // 4 + 1)

    with pytest.raises(
        ValidationError,
        match="Combined stdout and stderr",
    ):
        PartnerExecutionResultUpdate(
            **{
                **_valid_result_update_data(),
                "stdout": oversized_multibyte_output,
                "stderr": "",
            }
        )


def test_legacy_worker_update_also_enforces_combined_output_limit():
    oversized_multibyte_output = "🙂" * (MAX_COMBINED_EXECUTION_OUTPUT_BYTES // 4 + 1)

    with pytest.raises(
        ValidationError,
        match="Combined stdout and stderr",
    ):
        ExecutionWorkerUpdate(
            status="completed",
            stdout=oversized_multibyte_output,
        )


@pytest.mark.parametrize(
    (
        "current_status",
        "next_status",
        "expected",
    ),
    [
        (
            "queued",
            "running",
            True,
        ),
        (
            "queued",
            "completed",
            True,
        ),
        (
            "running",
            "runtime_error",
            True,
        ),
        (
            "completed",
            "running",
            False,
        ),
        (
            "failed",
            "completed",
            False,
        ),
        (
            "running",
            "queued",
            False,
        ),
    ],
)
def test_execution_status_transition_contract(
    current_status: str,
    next_status: str,
    expected: bool,
):
    assert (
        is_execution_status_transition_allowed(
            current_status=current_status,
            next_status=next_status,
        )
        is expected
    )


def test_partner_update_acknowledgment_contract():
    execution_id = str(uuid4())
    correlation_id = str(uuid4())
    update_id = str(uuid4())

    response = PartnerExecutionUpdateAcceptedResponse(
        execution_id=execution_id,
        correlation_id=correlation_id,
        update_id=update_id,
        status="completed",
        sequence_number=2,
        replayed=False,
        accepted_at=datetime.now(timezone.utc),
    )

    assert response.accepted is True
    assert response.replayed is False
    assert response.sequence_number == 2


def test_partner_update_acknowledgment_rejects_naive_timestamp():
    with pytest.raises(
        ValidationError,
        match="timestamps must include a timezone",
    ):
        PartnerExecutionUpdateAcceptedResponse(
            execution_id=str(uuid4()),
            correlation_id=str(uuid4()),
            update_id=str(uuid4()),
            status="running",
            sequence_number=1,
            replayed=False,
            accepted_at=datetime.now(),
        )


def test_partner_contracts_exclude_credentials_grades_and_verdicts():
    prohibited_fields = {
        "password",
        "password_hash",
        "otp",
        "otp_code",
        "jwt",
        "access_token",
        "refresh_token",
        "api_key",
        "shared_secret",
        "official_grade",
        "automatic_grade",
        "plagiarism_verdict",
        "cheating_verdict",
        "misconduct_verdict",
        "risk_score",
        "clipboard_content",
        "pasted_text",
        "browsing_history",
        "keystrokes",
        "screen_recording",
        "webcam",
        "microphone",
    }

    for schema in (
        PartnerExecutionDispatchRequest,
        PartnerExecutionResultUpdate,
        PartnerExecutionUpdateAcceptedResponse,
    ):
        assert prohibited_fields.isdisjoint(
            schema.model_fields,
        )
