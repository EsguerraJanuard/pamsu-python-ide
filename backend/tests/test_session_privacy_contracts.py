from typing import Any

import pytest
from pydantic import ValidationError

from app.main import app
from app.models.domain_models import (
    BehavioralLog,
    CodingSession,
)
from app.schemas.coding_session_schema import (
    MAX_BLOCKED_PASTE_INCREMENT,
    MAX_IDLE_INCREMENT_SECONDS,
    MAX_TAB_SWITCH_INCREMENT,
    CodingSessionActivityUpdate,
    CodingSessionStartRequest,
    InstructorCodingSessionResponse,
    StudentCodingSessionResponse,
)


PROHIBITED_SURVEILLANCE_FIELDS = {
    "clipboard_content",
    "clipboard_text",
    "pasted_text",
    "paste_content",
    "keystrokes",
    "keystroke_data",
    "browsing_history",
    "visited_urls",
    "screen_recording",
    "screen_capture",
    "webcam",
    "microphone",
    "audio_recording",
}

PROHIBITED_AUTOMATIC_DECISION_FIELDS = {
    "behavior_score",
    "cheating_score",
    "cheating_verdict",
    "misconduct_verdict",
    "plagiarism_verdict",
    "automatic_grade",
    "official_grade",
}

ALL_PROHIBITED_FIELDS = (
    PROHIBITED_SURVEILLANCE_FIELDS | PROHIBITED_AUTOMATIC_DECISION_FIELDS
)


def get_openapi_document() -> dict[str, Any]:
    return app.openapi()


def get_schema_properties(
    document: dict[str, Any],
    schema_name: str,
) -> dict[str, Any]:
    schema = document["components"]["schemas"][schema_name]

    properties = dict(
        schema.get(
            "properties",
            {},
        )
    )

    for nested_schema in schema.get(
        "allOf",
        [],
    ):
        if "$ref" not in nested_schema:
            properties.update(
                nested_schema.get(
                    "properties",
                    {},
                )
            )
            continue

        nested_name = nested_schema["$ref"].split("/")[-1]

        nested_properties = get_schema_properties(
            document,
            nested_name,
        )

        properties.update(nested_properties)

    return properties


def get_response_schema(
    document: dict[str, Any],
    *,
    method: str,
    path: str,
    status_code: str,
) -> dict[str, Any]:
    return document["paths"][path][method]["responses"][status_code]["content"][
        "application/json"
    ]["schema"]


def test_coding_session_database_has_only_approved_fields():
    database_fields = set(CodingSession.__table__.columns.keys())

    assert database_fields == {
        "session_id",
        "student_id",
        "task_id",
        "started_at",
        "ended_at",
        "last_activity_at",
        "tab_switch_count",
        "blocked_paste_count",
        "run_attempt_count",
        "idle_duration_seconds",
        "last_blocked_paste_at",
    }

    assert ALL_PROHIBITED_FIELDS.isdisjoint(database_fields)


def test_behavioral_log_database_has_only_approved_fields():
    database_fields = set(BehavioralLog.__table__.columns.keys())

    assert database_fields == {
        "log_id",
        "sub_id",
        "tab_switches_count",
        "blocked_paste_count",
        "mouseleave_count",
        "run_attempt_count",
        "idle_duration_seconds",
        "last_blocked_paste_at",
        "created_at",
        "updated_at",
    }

    assert ALL_PROHIBITED_FIELDS.isdisjoint(database_fields)


def test_session_start_request_accepts_only_task_identity():
    assert set(CodingSessionStartRequest.model_fields) == {
        "task_id",
    }

    valid_request = CodingSessionStartRequest(
        task_id=1,
    )

    assert valid_request.task_id == 1

    with pytest.raises(ValidationError):
        CodingSessionStartRequest(
            task_id=1,
            student_id=50,
            session_id="forged-session",
            started_at="2026-07-15T00:00:00Z",
            run_attempt_count=999,
        )


def test_activity_update_accepts_only_aggregate_increments():
    assert set(CodingSessionActivityUpdate.model_fields) == {
        "tab_switch_increment",
        "blocked_paste_increment",
        "idle_duration_increment_seconds",
    }

    valid_update = CodingSessionActivityUpdate(
        tab_switch_increment=2,
        blocked_paste_increment=1,
        idle_duration_increment_seconds=30,
    )

    assert valid_update.model_dump() == {
        "tab_switch_increment": 2,
        "blocked_paste_increment": 1,
        "idle_duration_increment_seconds": 30,
    }

    with pytest.raises(ValidationError):
        CodingSessionActivityUpdate(
            tab_switch_increment=1,
            run_attempt_count=500,
            tab_switch_count=500,
            blocked_paste_count=500,
            student_id=20,
            clipboard_content="private clipboard text",
            pasted_text="private pasted source",
            keystrokes=["p", "r", "i", "n", "t"],
            browsing_history=[
                "https://example.invalid",
            ],
            screen_recording="forbidden",
            webcam="forbidden",
            microphone="forbidden",
            behavior_score=100,
            misconduct_verdict="automatic",
        )


def test_activity_increment_limits_are_enforced():
    heartbeat = CodingSessionActivityUpdate()

    assert heartbeat.model_dump() == {
        "tab_switch_increment": 0,
        "blocked_paste_increment": 0,
        "idle_duration_increment_seconds": 0,
    }

    CodingSessionActivityUpdate(
        tab_switch_increment=(MAX_TAB_SWITCH_INCREMENT),
        blocked_paste_increment=(MAX_BLOCKED_PASTE_INCREMENT),
        idle_duration_increment_seconds=(MAX_IDLE_INCREMENT_SECONDS),
    )

    invalid_payloads = [
        {
            "tab_switch_increment": -1,
        },
        {
            "tab_switch_increment": (MAX_TAB_SWITCH_INCREMENT + 1),
        },
        {
            "blocked_paste_increment": -1,
        },
        {
            "blocked_paste_increment": (MAX_BLOCKED_PASTE_INCREMENT + 1),
        },
        {
            "idle_duration_increment_seconds": -1,
        },
        {
            "idle_duration_increment_seconds": (MAX_IDLE_INCREMENT_SECONDS + 1),
        },
    ]

    for payload in invalid_payloads:
        with pytest.raises(ValidationError):
            CodingSessionActivityUpdate(**payload)


def test_session_response_models_are_review_only():
    student_fields = set(StudentCodingSessionResponse.model_fields)

    instructor_fields = set(InstructorCodingSessionResponse.model_fields)

    approved_student_fields = {
        "session_id",
        "task_id",
        "started_at",
        "ended_at",
        "last_activity_at",
        "tab_switch_count",
        "blocked_paste_count",
        "run_attempt_count",
        "idle_duration_seconds",
        "last_blocked_paste_at",
    }

    assert student_fields == (approved_student_fields)

    assert instructor_fields == (
        approved_student_fields
        | {
            "student_id",
        }
    )

    assert "student_id" not in student_fields

    assert ALL_PROHIBITED_FIELDS.isdisjoint(student_fields)

    assert ALL_PROHIBITED_FIELDS.isdisjoint(instructor_fields)


def test_openapi_session_requests_exclude_private_fields():
    document = get_openapi_document()

    start_properties = get_schema_properties(
        document,
        "CodingSessionStartRequest",
    )

    activity_properties = get_schema_properties(
        document,
        "CodingSessionActivityUpdate",
    )

    assert set(start_properties) == {
        "task_id",
    }

    assert set(activity_properties) == {
        "tab_switch_increment",
        "blocked_paste_increment",
        "idle_duration_increment_seconds",
    }

    server_controlled_fields = {
        "student_id",
        "session_id",
        "task_id",
        "started_at",
        "ended_at",
        "last_activity_at",
        "tab_switch_count",
        "blocked_paste_count",
        "run_attempt_count",
        "idle_duration_seconds",
        "last_blocked_paste_at",
    }

    assert server_controlled_fields.isdisjoint(activity_properties)

    assert ALL_PROHIBITED_FIELDS.isdisjoint(start_properties)

    assert ALL_PROHIBITED_FIELDS.isdisjoint(activity_properties)

    start_request_schema = document["paths"]["/activities/coding-sessions/"]["post"][
        "requestBody"
    ]["content"]["application/json"]["schema"]

    assert start_request_schema["$ref"].endswith("/CodingSessionStartRequest")

    activity_request_schema = document["paths"][
        "/activities/coding-sessions/{session_id}/activity"
    ]["patch"]["requestBody"]["content"]["application/json"]["schema"]

    assert activity_request_schema["$ref"].endswith("/CodingSessionActivityUpdate")


def test_session_routes_are_authenticated_and_role_safe():
    document = get_openapi_document()

    expected_methods = {
        "/activities/coding-sessions/": {
            "get",
            "post",
        },
        "/activities/coding-sessions/{session_id}": {
            "get",
        },
        ("/activities/coding-sessions/{session_id}/activity"): {
            "patch",
        },
        ("/activities/coding-sessions/{session_id}/end"): {
            "post",
        },
        ("/instructors/tasks/{task_id}/coding-sessions"): {
            "get",
        },
        ("/instructors/coding-sessions/{session_id}"): {
            "get",
        },
    }

    http_methods = {
        "get",
        "post",
        "put",
        "patch",
        "delete",
    }

    for path, allowed_methods in expected_methods.items():
        assert path in document["paths"]

        actual_methods = {
            method for method in document["paths"][path] if method in http_methods
        }

        assert actual_methods == allowed_methods

        for method in allowed_methods:
            operation = document["paths"][path][method]

            assert operation.get("security"), (
                f"{method.upper()} {path} must require authentication."
            )

    instructor_list_path = "/instructors/tasks/{task_id}/coding-sessions"

    instructor_detail_path = "/instructors/coding-sessions/{session_id}"

    assert "post" not in document["paths"][instructor_list_path]

    assert "patch" not in document["paths"][instructor_detail_path]

    assert "delete" not in document["paths"][instructor_detail_path]


def test_openapi_session_responses_exclude_surveillance_fields():
    document = get_openapi_document()

    student_properties = get_schema_properties(
        document,
        "StudentCodingSessionResponse",
    )

    instructor_properties = get_schema_properties(
        document,
        "InstructorCodingSessionResponse",
    )

    assert ALL_PROHIBITED_FIELDS.isdisjoint(student_properties)

    assert ALL_PROHIBITED_FIELDS.isdisjoint(instructor_properties)

    assert "student_id" not in student_properties
    assert "student_id" in instructor_properties

    student_create_schema = get_response_schema(
        document,
        method="post",
        path="/activities/coding-sessions/",
        status_code="201",
    )

    assert student_create_schema["$ref"].endswith("/StudentCodingSessionResponse")

    student_list_schema = get_response_schema(
        document,
        method="get",
        path="/activities/coding-sessions/",
        status_code="200",
    )

    assert student_list_schema["type"] == "array"

    assert student_list_schema["items"]["$ref"].endswith(
        "/StudentCodingSessionResponse"
    )

    instructor_list_schema = get_response_schema(
        document,
        method="get",
        path=("/instructors/tasks/{task_id}/coding-sessions"),
        status_code="200",
    )

    assert instructor_list_schema["type"] == "array"

    assert instructor_list_schema["items"]["$ref"].endswith(
        "/InstructorCodingSessionResponse"
    )

    instructor_detail_schema = get_response_schema(
        document,
        method="get",
        path=("/instructors/coding-sessions/{session_id}"),
        status_code="200",
    )

    assert instructor_detail_schema["$ref"].endswith("/InstructorCodingSessionResponse")
