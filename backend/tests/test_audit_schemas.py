from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.audit_schema import (
    AuditRecordCreateInternal,
    AuditRecordListResponse,
    AuditRecordResponse,
    validate_audit_data,
)


def valid_create_payload() -> dict:
    return {
        "audit_key": "audit:activity-published:task:101",
        "actor_user_id": 12,
        "action_type": "activity_published",
        "resource_type": "task",
        "resource_id": "101",
        "outcome": "succeeded",
        "audit_data": {
            "class_id": 5,
            "previous_state": "draft",
            "new_state": "published",
        },
    }


def valid_response_payload() -> dict:
    timestamp = datetime.now(timezone.utc)

    return {
        "audit_id": "8be43a61-6ec2-48db-a6e1-a93d814b5d95",
        "actor_user_id": 12,
        "action_type": "activity_published",
        "resource_type": "task",
        "resource_id": "101",
        "outcome": "succeeded",
        "audit_data": {
            "class_id": 5,
            "previous_state": "draft",
            "new_state": "published",
        },
        "occurred_at": timestamp,
        "created_at": timestamp,
    }


def test_internal_create_schema_accepts_valid_privacy_safe_payload():
    schema = AuditRecordCreateInternal(
        **valid_create_payload(),
    )

    assert schema.audit_key == "audit:activity-published:task:101"
    assert schema.actor_user_id == 12
    assert schema.action_type == "activity_published"
    assert schema.resource_type == "task"
    assert schema.resource_id == "101"
    assert schema.outcome == "succeeded"
    assert schema.audit_data["class_id"] == 5


def test_internal_create_schema_strips_identifier_whitespace():
    payload = valid_create_payload()
    payload["audit_key"] = "  audit:classroom-created:1  "
    payload["resource_id"] = "  1  "

    schema = AuditRecordCreateInternal(**payload)

    assert schema.audit_key == "audit:classroom-created:1"
    assert schema.resource_id == "1"


def test_internal_create_schema_defaults_outcome_and_audit_data():
    schema = AuditRecordCreateInternal(
        audit_key="audit:user-registered:user:10",
        actor_user_id=10,
        action_type="user_registered",
        resource_type="user",
        resource_id="10",
    )

    assert schema.outcome == "succeeded"
    assert schema.audit_data == {}


def test_internal_create_schema_allows_null_actor():
    payload = valid_create_payload()
    payload["actor_user_id"] = None
    payload["action_type"] = "login_failed"
    payload["resource_type"] = "user"
    payload["resource_id"] = "unknown"
    payload["outcome"] = "denied"

    schema = AuditRecordCreateInternal(**payload)

    assert schema.actor_user_id is None
    assert schema.action_type == "login_failed"
    assert schema.outcome == "denied"


def test_internal_create_schema_rejects_extra_fields():
    payload = valid_create_payload()
    payload["client_selected_actor"] = 999

    with pytest.raises(ValidationError):
        AuditRecordCreateInternal(**payload)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("audit_key", ""),
        ("audit_key", "   "),
        ("resource_id", ""),
        ("resource_id", "   "),
    ],
)
def test_internal_create_schema_rejects_blank_identifiers(
    field_name: str,
    invalid_value: str,
):
    payload = valid_create_payload()
    payload[field_name] = invalid_value

    with pytest.raises(ValidationError):
        AuditRecordCreateInternal(**payload)


@pytest.mark.parametrize(
    "invalid_action_type",
    [
        "password_viewed",
        "source_code_exported",
        "automatic_misconduct_decision",
    ],
)
def test_internal_create_schema_rejects_unapproved_action_types(
    invalid_action_type: str,
):
    payload = valid_create_payload()
    payload["action_type"] = invalid_action_type

    with pytest.raises(ValidationError):
        AuditRecordCreateInternal(**payload)


@pytest.mark.parametrize(
    "invalid_resource_type",
    [
        "password",
        "otp",
        "source_code",
    ],
)
def test_internal_create_schema_rejects_unapproved_resource_types(
    invalid_resource_type: str,
):
    payload = valid_create_payload()
    payload["resource_type"] = invalid_resource_type

    with pytest.raises(ValidationError):
        AuditRecordCreateInternal(**payload)


@pytest.mark.parametrize(
    "invalid_outcome",
    [
        "unknown",
        "automatic_verdict",
        "completed",
    ],
)
def test_internal_create_schema_rejects_unapproved_outcomes(
    invalid_outcome: str,
):
    payload = valid_create_payload()
    payload["outcome"] = invalid_outcome

    with pytest.raises(ValidationError):
        AuditRecordCreateInternal(**payload)


@pytest.mark.parametrize(
    "invalid_actor_user_id",
    [
        0,
        -1,
    ],
)
def test_internal_create_schema_rejects_nonpositive_actor_ids(
    invalid_actor_user_id: int,
):
    payload = valid_create_payload()
    payload["actor_user_id"] = invalid_actor_user_id

    with pytest.raises(ValidationError):
        AuditRecordCreateInternal(**payload)


def test_internal_create_schema_uses_strict_actor_type():
    payload = valid_create_payload()
    payload["actor_user_id"] = "12"

    with pytest.raises(ValidationError):
        AuditRecordCreateInternal(**payload)


@pytest.mark.parametrize(
    "invalid_audit_data",
    [
        [],
        "metadata",
        100,
        True,
    ],
)
def test_audit_data_must_be_a_json_object(
    invalid_audit_data,
):
    payload = valid_create_payload()
    payload["audit_data"] = invalid_audit_data

    with pytest.raises(ValidationError):
        AuditRecordCreateInternal(**payload)


@pytest.mark.parametrize(
    "prohibited_audit_data",
    [
        {"password": "secret"},
        {"account": {"otp_code": "123456"}},
        {"submission": {"raw-code": "print('secret')"}},
        {"execution": {"standard input": "classified"}},
        {"test": {"expected_output": "private"}},
        {"analysis": {"ast_details": {"rule": "loop"}}},
        {"analysis": {"similarity_score": 91.5}},
        {"session": {"clipboard_content": "copied text"}},
        {"session": {"pasted_text": "pasted text"}},
        {"session": {"browsing_history": ["example.test"]}},
        {"session": {"keystrokes": ["a", "b"]}},
        {"media": {"webcam_data": "binary"}},
        {"media": {"microphone": "binary"}},
        {"decision": {"misconduct_verdict": "guilty"}},
        {"grade": {"score": 95}},
        {"grade": {"feedback": "unreleased feedback"}},
    ],
)
def test_internal_create_schema_rejects_nested_prohibited_fields(
    prohibited_audit_data: dict,
):
    payload = valid_create_payload()
    payload["audit_data"] = prohibited_audit_data

    with pytest.raises(
        ValidationError,
        match="prohibited field",
    ):
        AuditRecordCreateInternal(**payload)


def test_prohibited_key_matching_is_case_and_separator_insensitive():
    payload = valid_create_payload()
    payload["audit_data"] = {
        "private": {
            "Source Code": "print('secret')",
        },
    }

    with pytest.raises(
        ValidationError,
        match="prohibited field",
    ):
        AuditRecordCreateInternal(**payload)


def test_audit_data_rejects_non_string_dictionary_keys():
    payload = valid_create_payload()
    payload["audit_data"] = {
        "approved": {
            1: "invalid key",
        },
    }

    with pytest.raises(
        ValidationError,
        match="keys must be strings",
    ):
        AuditRecordCreateInternal(**payload)


@pytest.mark.parametrize(
    "non_json_value",
    [
        {"invalid": {1, 2, 3}},
        {"invalid": ("tuple", "value")},
        {"invalid": datetime.now(timezone.utc)},
        {"invalid": object()},
    ],
)
def test_audit_data_rejects_non_json_values(
    non_json_value: dict,
):
    payload = valid_create_payload()
    payload["audit_data"] = non_json_value

    with pytest.raises(
        ValidationError,
        match="JSON-compatible",
    ):
        AuditRecordCreateInternal(**payload)


def test_audit_data_accepts_nested_json_safe_values():
    approved_data = {
        "class_id": 10,
        "state_transition": {
            "from": "active",
            "to": "disabled",
        },
        "changed_fields": [
            "status",
            "deactivated_at",
        ],
        "flags": {
            "actor_authenticated": True,
            "system_generated": False,
        },
        "optional_reason": None,
        "attempt_number": 2,
        "duration_seconds": 12.5,
    }

    validated = validate_audit_data(approved_data)

    assert validated == approved_data


def test_response_schema_validates_orm_attributes():
    payload = valid_response_payload()
    orm_record = SimpleNamespace(**payload)

    response = AuditRecordResponse.model_validate(
        orm_record,
    )

    assert response.audit_id == payload["audit_id"]
    assert response.actor_user_id == 12
    assert response.action_type == "activity_published"
    assert response.audit_data == payload["audit_data"]


def test_response_schema_rejects_prohibited_audit_data():
    payload = valid_response_payload()
    payload["audit_data"] = {
        "nested": {
            "source_code": "print('private')",
        },
    }

    with pytest.raises(
        ValidationError,
        match="prohibited field",
    ):
        AuditRecordResponse(**payload)


def test_response_schema_excludes_internal_audit_key():
    response = AuditRecordResponse(
        **valid_response_payload(),
    )

    assert "audit_key" not in response.model_dump()


def test_list_response_accepts_valid_pagination():
    response = AuditRecordListResponse(
        items=[
            AuditRecordResponse(
                **valid_response_payload(),
            ),
        ],
        page=1,
        page_size=20,
        total=1,
        total_pages=1,
    )

    assert len(response.items) == 1
    assert response.page == 1
    assert response.page_size == 20
    assert response.total == 1
    assert response.total_pages == 1


@pytest.mark.parametrize(
    "invalid_values",
    [
        {
            "page": 0,
            "page_size": 20,
            "total": 0,
            "total_pages": 0,
        },
        {
            "page": 1,
            "page_size": 0,
            "total": 0,
            "total_pages": 0,
        },
        {
            "page": 1,
            "page_size": 101,
            "total": 0,
            "total_pages": 0,
        },
        {
            "page": 1,
            "page_size": 20,
            "total": -1,
            "total_pages": 0,
        },
        {
            "page": 1,
            "page_size": 20,
            "total": 0,
            "total_pages": -1,
        },
    ],
)
def test_list_response_rejects_invalid_pagination(
    invalid_values: dict,
):
    with pytest.raises(ValidationError):
        AuditRecordListResponse(
            items=[],
            **invalid_values,
        )
