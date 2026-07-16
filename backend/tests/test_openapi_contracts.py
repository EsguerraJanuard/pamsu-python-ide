from typing import Any

from app.main import APP_TITLE, APP_VERSION, app


HTTP_METHODS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head",
    "trace",
}

PUBLIC_OPERATIONS = {
    ("get", "/"),
    ("get", "/health"),
    ("post", "/login"),
    ("post", "/registration/start"),
    ("post", "/registration/verify"),
    ("post", "/registration/resend"),
}


def get_openapi_document() -> dict[str, Any]:
    return app.openapi()


def iter_operations(
    document: dict[str, Any],
):
    for path, path_item in document["paths"].items():
        for method, operation in path_item.items():
            if method.lower() in HTTP_METHODS:
                yield method.lower(), path, operation


def resolve_schema(
    document: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    if "$ref" in schema:
        schema_name = schema["$ref"].split("/")[-1]

        return document["components"]["schemas"][schema_name]

    return schema


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
        resolved_schema = resolve_schema(
            document,
            nested_schema,
        )

        properties.update(
            resolved_schema.get(
                "properties",
                {},
            )
        )

    return properties


def test_openapi_metadata_and_tags():
    document = get_openapi_document()

    assert APP_VERSION == "0.10.0"
    assert document["info"]["title"] == APP_TITLE
    assert document["info"]["version"] == APP_VERSION

    declared_tags = {
        tag["name"]
        for tag in document.get(
            "tags",
            [],
        )
    }

    assert declared_tags == {
        "System",
        "Authentication",
        "Registration",
        "Classrooms",
        "Instructor",
        "Activities",
        "Submissions",
        "Execution",
        "Behavioral Logs",
        "Evaluation",
        "Notifications",
    }


def test_required_api_paths_and_status_codes():
    document = get_openapi_document()
    paths = document["paths"]

    required_paths = {
        "/",
        "/health",
        "/login",
        "/registration/start",
        "/registration/verify",
        "/registration/resend",
        "/classrooms/",
        "/classrooms/join",
        "/classrooms/mine",
        "/instructors/tasks/",
        "/instructors/tasks/{task_id}",
        "/instructors/tasks/{task_id}/publication",
        "/instructors/tasks/{task_id}/submissions",
        "/instructors/submissions/{submission_id}",
        "/instructors/tasks/{task_id}/execution-requests",
        "/instructors/execution-requests/{execution_id}",
        "/instructors/tasks/{task_id}/coding-sessions",
        "/instructors/coding-sessions/{session_id}",
        "/activities/",
        "/activities/{task_id}",
        "/activities/{task_id}/sample-test-cases",
        "/activities/coding-sessions/",
        "/activities/coding-sessions/{session_id}",
        "/activities/coding-sessions/{session_id}/activity",
        "/activities/coding-sessions/{session_id}/end",
        "/submissions/",
        "/submissions/official/{task_id}",
        "/submissions/{submission_id}",
        "/execution/submissions/",
        "/execution/submissions/{sub_id}",
        "/execution/requests/",
        "/execution/requests/{execution_id}",
        "/evaluation/submissions/{sub_id}",
        "/logs/behavioral/",
        "/logs/behavioral/{log_id}",
        "/logs/behavioral/submission/{sub_id}",
    }

    assert required_paths.issubset(paths.keys())

    assert "201" in paths["/registration/start"]["post"]["responses"]

    assert "200" in paths["/registration/verify"]["post"]["responses"]

    assert "201" in paths["/instructors/tasks/"]["post"]["responses"]

    assert "201" in paths["/submissions/"]["post"]["responses"]

    assert "201" in paths["/execution/requests/"]["post"]["responses"]

    assert "200" in paths["/execution/requests/"]["get"]["responses"]

    assert "201" in paths["/activities/coding-sessions/"]["post"]["responses"]

    assert "200" in paths["/activities/coding-sessions/"]["get"]["responses"]

    assert (
        "200"
        in paths["/activities/coding-sessions/{session_id}/activity"]["patch"][
            "responses"
        ]
    )

    assert (
        "200"
        in paths["/activities/coding-sessions/{session_id}/end"]["post"]["responses"]
    )

    assert (
        "200"
        in paths["/instructors/tasks/{task_id}/coding-sessions"]["get"]["responses"]
    )

    assert (
        "200"
        in paths["/instructors/tasks/{task_id}/execution-requests"]["get"]["responses"]
    )

    assert "201" in paths["/execution/submissions/"]["post"]["responses"]

    assert "200" in paths["/evaluation/submissions/{sub_id}"]["post"]["responses"]


def test_all_operation_ids_are_unique():
    document = get_openapi_document()

    operation_ids = [
        operation["operationId"] for _, _, operation in iter_operations(document)
    ]

    assert len(operation_ids) == len(set(operation_ids))


def test_oauth2_password_flow_uses_login_endpoint():
    document = get_openapi_document()

    security_schemes = document["components"]["securitySchemes"]

    oauth2_schemes = [
        scheme for scheme in security_schemes.values() if scheme.get("type") == "oauth2"
    ]

    assert oauth2_schemes

    password_flows = [
        scheme["flows"]["password"]
        for scheme in oauth2_schemes
        if "password"
        in scheme.get(
            "flows",
            {},
        )
    ]

    assert password_flows

    assert any(flow["tokenUrl"] == "/login" for flow in password_flows)


def test_public_and_protected_route_boundaries():
    document = get_openapi_document()

    for method, path, operation in iter_operations(document):
        route_key = (
            method,
            path,
        )

        security = operation.get(
            "security",
            [],
        )

        if route_key in PUBLIC_OPERATIONS:
            assert security == [], f"{method.upper()} {path} should be public."
        else:
            assert security, f"{method.upper()} {path} must require authentication."


def test_login_uses_oauth2_form_contract():
    document = get_openapi_document()

    request_body = document["paths"]["/login"]["post"]["requestBody"]

    content_types = set(request_body["content"].keys())

    assert "application/x-www-form-urlencoded" in content_types


def test_registration_contract_excludes_backend_fields():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "RegistrationStartRequest",
    )

    assert {
        "name",
        "school_id",
        "email",
        "password",
        "confirm_password",
        "data_collection_acknowledged",
    }.issubset(properties)

    assert "role" not in properties
    assert "password_hash" not in properties
    assert "email_verified" not in properties
    assert "is_active" not in properties


def test_otp_challenge_response_never_exposes_plaintext_code():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "OTPChallengeResponse",
    )

    assert "challenge_id" in properties
    assert "email" in properties
    assert "expires_in_seconds" in properties

    assert "otp_code" not in properties
    assert "otp_hash" not in properties
    assert "password" not in properties
    assert "password_hash" not in properties


def test_identity_and_server_controlled_fields_come_from_token():
    document = get_openapi_document()

    task_properties = get_schema_properties(
        document,
        "TaskCreate",
    )

    submission_properties = get_schema_properties(
        document,
        "SubmissionCreate",
    )

    execution_properties = get_schema_properties(
        document,
        "ExecutionRequestCreate",
    )

    session_start_properties = get_schema_properties(
        document,
        "CodingSessionStartRequest",
    )

    session_activity_properties = get_schema_properties(
        document,
        "CodingSessionActivityUpdate",
    )

    assert "instructor_id" not in task_properties

    assert "student_id" not in submission_properties
    assert "attempt_number" not in submission_properties
    assert "status" not in submission_properties
    assert "is_official" not in submission_properties
    assert "submitted_at" not in submission_properties
    assert "accepted_at" not in submission_properties

    assert "student_id" not in execution_properties
    assert "execution_id" not in execution_properties
    assert "status" not in execution_properties
    assert "stdout" not in execution_properties
    assert "stderr" not in execution_properties
    assert "exit_code" not in execution_properties
    assert "execution_time_ms" not in execution_properties
    assert "limit_reason" not in execution_properties
    assert "worker_task_id" not in execution_properties
    assert "queued_at" not in execution_properties
    assert "started_at" not in execution_properties
    assert "completed_at" not in execution_properties

    assert set(session_start_properties) == {
        "task_id",
    }

    assert set(session_activity_properties) == {
        "tab_switch_increment",
        "blocked_paste_increment",
        "idle_duration_increment_seconds",
    }

    session_backend_fields = {
        "student_id",
        "session_id",
        "task_id",
        "run_attempt_count",
        "tab_switch_count",
        "blocked_paste_count",
        "idle_duration_seconds",
        "started_at",
        "ended_at",
        "last_activity_at",
        "last_blocked_paste_at",
    }

    assert session_backend_fields.isdisjoint(session_activity_properties)

    assert "class_id" in task_properties

    assert "task_id" in submission_properties
    assert "raw_code" in submission_properties

    assert "request_kind" in execution_properties
    assert "task_id" in execution_properties
    assert "source_code" in execution_properties
    assert "standard_input" in execution_properties


def test_student_submission_response_respects_review_boundary():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "StudentSubmissionResponse",
    )

    assert {
        "sub_id",
        "task_id",
        "coding_session_id",
        "attempt_number",
        "raw_code",
        "standard_input",
        "status",
        "is_official",
        "submitted_at",
        "accepted_at",
    }.issubset(properties)

    prohibited_fields = {
        "student_id",
        "jaccard_score",
        "ast_pass_fail",
        "official_grade",
        "automatic_grade",
        "misconduct_verdict",
        "plagiarism_verdict",
        "behavior_score",
    }

    assert prohibited_fields.isdisjoint(properties)


def test_student_execution_response_hides_internal_worker_identity():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "StudentExecutionResponse",
    )

    assert {
        "execution_id",
        "task_id",
        "submission_id",
        "coding_session_id",
        "request_kind",
        "status",
        "source_code",
        "standard_input",
        "stdout",
        "stderr",
        "exit_code",
        "execution_time_ms",
        "limit_reason",
        "queued_at",
        "started_at",
        "completed_at",
    }.issubset(properties)

    prohibited_fields = {
        "student_id",
        "worker_task_id",
        "official_grade",
        "automatic_grade",
        "misconduct_verdict",
        "plagiarism_verdict",
        "behavior_score",
    }

    assert prohibited_fields.isdisjoint(properties)


def test_student_coding_session_response_respects_privacy_boundary():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "StudentCodingSessionResponse",
    )

    assert {
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
    }.issubset(properties)

    prohibited_fields = {
        "student_id",
        "clipboard_content",
        "pasted_text",
        "paste_content",
        "keystrokes",
        "browsing_history",
        "screen_recording",
        "webcam",
        "microphone",
        "behavior_score",
        "automatic_grade",
        "misconduct_verdict",
    }

    assert prohibited_fields.isdisjoint(properties)


def test_instructor_coding_session_response_is_review_only():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "InstructorCodingSessionResponse",
    )

    assert {
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
    }.issubset(properties)

    prohibited_fields = {
        "clipboard_content",
        "pasted_text",
        "paste_content",
        "keystrokes",
        "browsing_history",
        "screen_recording",
        "webcam",
        "microphone",
        "behavior_score",
        "automatic_grade",
        "official_grade",
        "cheating_verdict",
        "misconduct_verdict",
    }

    assert prohibited_fields.isdisjoint(properties)


def test_behavioral_log_contract_respects_privacy_boundary():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "BehavioralLogCreate",
    )

    assert {
        "sub_id",
        "tab_switches_count",
        "blocked_paste_count",
        "run_attempt_count",
        "idle_duration_seconds",
        "last_blocked_paste_at",
    }.issubset(properties)

    prohibited_fields = {
        "clipboard_content",
        "pasted_text",
        "paste_content",
        "keystrokes",
        "browsing_history",
        "screen_recording",
        "webcam",
        "microphone",
    }

    assert prohibited_fields.isdisjoint(properties)


def test_evaluation_contract_has_no_automatic_grade_verdict():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "EvaluationResponse",
    )

    assert "ast_pass_fail" in properties
    assert "jaccard_score" in properties
    assert "review_notice" in properties

    prohibited_fields = {
        "official_grade",
        "automatic_grade",
        "plagiarism_verdict",
        "misconduct_verdict",
        "behavior_score",
    }

    assert prohibited_fields.isdisjoint(properties)
