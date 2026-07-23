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
    ("get", "/ready"),
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

    # Pillar 14 partner integrations and health/readiness contracts.
    assert APP_VERSION == "1.0.0-rc1"
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
        "Audit Trail",
        "Reporting",
    }


def test_required_api_paths_and_status_codes():
    document = get_openapi_document()
    paths = document["paths"]

    required_paths = {
        "/",
        "/health",
        "/ready",
        "/login",
        "/registration/start",
        "/registration/verify",
        "/registration/resend",
        "/classrooms/",
        "/classrooms/join",
        "/classrooms/mine",
        "/classrooms/enrollments/{enrollment_id}/status",
        "/classrooms/{class_id}/regenerate-code",
        "/classrooms/{class_id}",
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
        "/execution/internal/partner-results",
        "/evaluation/submissions/{sub_id}",
        "/evaluation/submissions/{sub_id}/status",
        "/evaluation/submissions/{sub_id}/grade",
        "/logs/behavioral/",
        "/logs/behavioral/{log_id}",
        "/logs/behavioral/submission/{sub_id}",
        "/notifications/",
        "/notifications/unread-count",
        "/notifications/read-all",
        "/notifications/{notification_id}",
        "/notifications/{notification_id}/read",
        "/audit-records/",
        "/audit-records/{audit_id}",
        "/reports/classrooms/{class_id}/completion",
        "/reports/activities/{task_id}/completion",
        "/reports/classrooms/{class_id}/grade-distribution",
        "/reports/missing-submissions",
        "/reports/students/me/progress",
        "/reports/classrooms/{class_id}/gradebook.csv",
    }

    assert required_paths.issubset(paths.keys())

    assert "200" in paths["/health"]["get"]["responses"]

    assert "200" in paths["/ready"]["get"]["responses"]

    assert "503" in paths["/ready"]["get"]["responses"]

    assert "201" in paths["/registration/start"]["post"]["responses"]

    assert "200" in paths["/registration/verify"]["post"]["responses"]

    assert "201" in paths["/instructors/tasks/"]["post"]["responses"]

    assert (
        "200" in paths["/instructors/tasks/{task_id}/publication"]["patch"]["responses"]
    )

    assert (
        "503" in paths["/instructors/tasks/{task_id}/publication"]["patch"]["responses"]
    )

    assert "201" in paths["/submissions/"]["post"]["responses"]

    assert "503" in paths["/submissions/"]["post"]["responses"]

    assert "201" in paths["/execution/requests/"]["post"]["responses"]

    assert "200" in paths["/execution/requests/"]["get"]["responses"]

    partner_result_responses = paths["/execution/internal/partner-results"]["post"][
        "responses"
    ]

    assert {
        "200",
        "400",
        "401",
        "404",
        "409",
        "422",
        "500",
        "503",
    }.issubset(partner_result_responses)

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

    assert "503" in paths["/evaluation/submissions/{sub_id}/grade"]["put"]["responses"]

    assert (
        "503" in paths["/evaluation/submissions/{sub_id}/grade"]["patch"]["responses"]
    )

    assert "503" in paths["/classrooms/{class_id}"]["patch"]["responses"]

    assert "200" in paths["/notifications/"]["get"]["responses"]

    assert "200" in paths["/notifications/unread-count"]["get"]["responses"]

    assert "200" in paths["/notifications/{notification_id}"]["get"]["responses"]

    assert "200" in paths["/notifications/{notification_id}/read"]["patch"]["responses"]

    assert "200" in paths["/notifications/read-all"]["patch"]["responses"]

    assert "200" in paths["/audit-records/"]["get"]["responses"]

    assert "200" in paths["/audit-records/{audit_id}"]["get"]["responses"]

    assert "404" in paths["/audit-records/{audit_id}"]["get"]["responses"]

    assert (
        "200" in paths["/reports/classrooms/{class_id}/completion"]["get"]["responses"]
    )

    assert (
        "200" in paths["/reports/activities/{task_id}/completion"]["get"]["responses"]
    )

    assert (
        "409" in paths["/reports/activities/{task_id}/completion"]["get"]["responses"]
    )

    assert (
        "200"
        in paths["/reports/classrooms/{class_id}/grade-distribution"]["get"][
            "responses"
        ]
    )

    assert "200" in paths["/reports/missing-submissions"]["get"]["responses"]

    assert "200" in paths["/reports/students/me/progress"]["get"]["responses"]

    assert (
        "200"
        in paths["/reports/classrooms/{class_id}/gradebook.csv"]["get"]["responses"]
    )


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


def test_audit_routes_are_read_only_and_actor_scoped():
    document = get_openapi_document()
    paths = document["paths"]

    assert set(
        method for method in paths["/audit-records/"] if method.lower() in HTTP_METHODS
    ) == {
        "get",
    }

    assert set(
        method
        for method in paths["/audit-records/{audit_id}"]
        if method.lower() in HTTP_METHODS
    ) == {
        "get",
    }

    audit_operations = [
        operation
        for _, path, operation in iter_operations(document)
        if path.startswith("/audit-records")
    ]

    assert all(operation.get("requestBody") is None for operation in audit_operations)

    list_parameter_names = {
        parameter["name"]
        for parameter in paths["/audit-records/"]["get"].get(
            "parameters",
            [],
        )
    }

    assert {
        "page",
        "page_size",
        "action_type",
        "resource_type",
        "resource_id",
        "outcome",
    }.issubset(list_parameter_names)

    assert {
        "actor_user_id",
        "user_id",
        "school_id",
        "email",
        "audit_key",
    }.isdisjoint(list_parameter_names)


def test_audit_record_response_respects_privacy_boundary():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "AuditRecordResponse",
    )

    assert {
        "audit_id",
        "actor_user_id",
        "action_type",
        "resource_type",
        "resource_id",
        "outcome",
        "audit_data",
        "occurred_at",
        "created_at",
    }.issubset(properties)

    prohibited_fields = {
        "audit_key",
        "password",
        "password_hash",
        "otp",
        "otp_code",
        "raw_code",
        "source_code",
        "starter_code",
        "standard_input",
        "expected_output",
        "hidden_test_cases",
        "required_ast_rules",
        "ast_details",
        "ast_findings",
        "similarity_score",
        "similarity_details",
        "stdout",
        "stderr",
        "execution_output",
        "worker_task_id",
        "clipboard_content",
        "paste_content",
        "pasted_text",
        "keystrokes",
        "browsing_history",
        "screen_recording",
        "webcam",
        "microphone",
        "score",
        "max_score",
        "feedback",
        "automatic_grade",
        "risk_score",
        "plagiarism_verdict",
        "cheating_verdict",
        "misconduct_verdict",
    }

    assert prohibited_fields.isdisjoint(properties)


def test_audit_list_contract_is_actor_safe():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "AuditRecordListResponse",
    )

    assert {
        "items",
        "page",
        "page_size",
        "total",
        "total_pages",
    }.issubset(properties)

    prohibited_fields = {
        "actor_filter",
        "actor_user_id",
        "user_id",
        "school_id",
        "email",
        "audit_key",
        "system_wide_records",
    }

    assert prohibited_fields.isdisjoint(properties)


def test_notification_routes_are_read_state_only():
    document = get_openapi_document()
    paths = document["paths"]

    assert set(
        method for method in paths["/notifications/"] if method.lower() in HTTP_METHODS
    ) == {
        "get",
    }

    assert set(
        method
        for method in paths["/notifications/unread-count"]
        if method.lower() in HTTP_METHODS
    ) == {
        "get",
    }

    assert set(
        method
        for method in paths["/notifications/read-all"]
        if method.lower() in HTTP_METHODS
    ) == {
        "patch",
    }

    assert set(
        method
        for method in paths["/notifications/{notification_id}"]
        if method.lower() in HTTP_METHODS
    ) == {
        "get",
    }

    assert set(
        method
        for method in paths["/notifications/{notification_id}/read"]
        if method.lower() in HTTP_METHODS
    ) == {
        "patch",
    }


def test_notification_response_respects_privacy_boundary():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "NotificationResponse",
    )

    assert {
        "notification_id",
        "event_id",
        "event_type",
        "resource_type",
        "resource_id",
        "title",
        "message",
        "is_read",
        "read_at",
        "created_at",
        "occurred_at",
    }.issubset(properties)

    prohibited_fields = {
        "recipient_id",
        "actor_user_id",
        "event_key",
        "event_data",
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
        "exit_code",
        "worker_task_id",
        "coding_session",
        "clipboard_content",
        "pasted_text",
        "keystrokes",
        "browsing_history",
        "screen_recording",
        "webcam",
        "microphone",
        "score",
        "max_score",
        "feedback",
        "unreleased_score",
        "unreleased_feedback",
        "automatic_grade",
        "risk_score",
        "plagiarism_verdict",
        "cheating_verdict",
        "misconduct_verdict",
    }

    assert prohibited_fields.isdisjoint(properties)


def test_notification_list_contract_is_recipient_safe():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "NotificationListResponse",
    )

    assert {
        "items",
        "total_items",
        "total_pages",
        "page",
        "page_size",
        "recipient_unread_count",
        "read_filter",
        "sort_direction",
    }.issubset(properties)

    prohibited_fields = {
        "recipient_id",
        "recipient_email",
        "recipient_school_id",
        "actor_user_id",
        "event_key",
        "event_data",
        "source_code",
        "standard_input",
        "score",
        "feedback",
    }

    assert prohibited_fields.isdisjoint(properties)


def test_notification_counter_and_read_all_contracts():
    document = get_openapi_document()

    unread_properties = get_schema_properties(
        document,
        "NotificationUnreadCountResponse",
    )

    mark_all_properties = get_schema_properties(
        document,
        "MarkAllNotificationsReadResponse",
    )

    assert set(unread_properties) == {
        "unread_count",
    }

    assert {
        "marked_read_count",
        "remaining_unread_count",
        "marked_at",
    }.issubset(mark_all_properties)

    assert {
        "recipient_id",
        "notification_ids",
        "event_ids",
        "event_data",
    }.isdisjoint(mark_all_properties)


def test_notification_create_contract_is_not_exposed_by_routes():
    document = get_openapi_document()

    notification_operations = [
        operation
        for method, path, operation in iter_operations(document)
        if path.startswith("/notifications")
    ]

    request_bodies = [
        operation.get("requestBody")
        for operation in notification_operations
        if operation.get("requestBody") is not None
    ]

    assert request_bodies == []


def test_accountability_workflow_failure_responses_are_documented():
    document = get_openapi_document()
    paths = document["paths"]

    protected_operations = {
        (
            "post",
            "/classrooms/",
        ),
        (
            "post",
            "/classrooms/join",
        ),
        (
            "patch",
            "/classrooms/enrollments/{enrollment_id}/status",
        ),
        (
            "post",
            "/classrooms/{class_id}/regenerate-code",
        ),
        (
            "patch",
            "/classrooms/{class_id}",
        ),
        (
            "post",
            "/instructors/tasks/",
        ),
        (
            "patch",
            "/instructors/tasks/{task_id}",
        ),
        (
            "patch",
            "/instructors/tasks/{task_id}/publication",
        ),
        (
            "post",
            "/submissions/",
        ),
        (
            "put",
            "/evaluation/submissions/{sub_id}/grade",
        ),
        (
            "patch",
            "/evaluation/submissions/{sub_id}/grade",
        ),
    }

    for method, path in protected_operations:
        assert "503" in paths[path][method]["responses"]


def test_reporting_routes_are_get_only():
    document = get_openapi_document()
    paths = document["paths"]

    reporting_paths = {
        "/reports/classrooms/{class_id}/completion",
        "/reports/activities/{task_id}/completion",
        "/reports/classrooms/{class_id}/grade-distribution",
        "/reports/missing-submissions",
        "/reports/students/me/progress",
        "/reports/classrooms/{class_id}/gradebook.csv",
    }

    for path in reporting_paths:
        methods = {
            method.lower() for method in paths[path] if method.lower() in HTTP_METHODS
        }

        assert methods == {
            "get",
        }


def test_reporting_query_contracts_are_owner_safe():
    document = get_openapi_document()
    paths = document["paths"]

    instructor_reporting_paths = {
        "/reports/classrooms/{class_id}/completion",
        "/reports/activities/{task_id}/completion",
        "/reports/classrooms/{class_id}/grade-distribution",
        "/reports/missing-submissions",
        "/reports/classrooms/{class_id}/gradebook.csv",
    }

    prohibited_parameter_names = {
        "instructor_id",
        "student_id",
        "user_id",
        "actor_user_id",
        "school_id",
        "email",
        "include_raw_source",
        "include_source_code",
        "include_unreleased_grades",
        "risk_score",
        "misconduct_rank",
    }

    for path in instructor_reporting_paths:
        parameter_names = {
            parameter["name"]
            for parameter in paths[path]["get"].get(
                "parameters",
                [],
            )
        }

        assert prohibited_parameter_names.isdisjoint(parameter_names)

    student_progress_parameters = {
        parameter["name"]
        for parameter in paths["/reports/students/me/progress"]["get"].get(
            "parameters",
            [],
        )
    }

    assert prohibited_parameter_names.isdisjoint(student_progress_parameters)


def test_reporting_missing_submission_filters_are_bounded():
    document = get_openapi_document()

    operation = document["paths"]["/reports/missing-submissions"]["get"]

    parameters = {
        parameter["name"]: parameter
        for parameter in operation.get(
            "parameters",
            [],
        )
    }

    assert {
        "page",
        "page_size",
        "class_id",
        "task_id",
        "sort_by",
        "sort_direction",
    }.issubset(parameters)

    page_schema = resolve_schema(
        document,
        parameters["page"]["schema"],
    )

    page_size_schema = resolve_schema(
        document,
        parameters["page_size"]["schema"],
    )

    assert page_schema["minimum"] == 1
    assert page_size_schema["minimum"] == 1
    assert page_size_schema["maximum"] == 100

    sort_by_schema = resolve_schema(
        document,
        parameters["sort_by"]["schema"],
    )

    sort_direction_schema = resolve_schema(
        document,
        parameters["sort_direction"]["schema"],
    )

    assert set(sort_by_schema["enum"]) == {
        "student_name",
        "school_id",
        "activity_title",
        "due_at",
    }

    assert set(sort_direction_schema["enum"]) == {
        "asc",
        "desc",
    }


def test_reporting_completion_contracts_are_privacy_safe():
    document = get_openapi_document()

    completion_properties = get_schema_properties(
        document,
        "CompletionCounts",
    )

    classroom_properties = get_schema_properties(
        document,
        "ClassroomCompletionSummaryResponse",
    )

    activity_properties = get_schema_properties(
        document,
        "ActivityCompletionSummaryResponse",
    )

    assert {
        "expected_count",
        "submitted_count",
        "missing_count",
        "manually_graded_count",
        "released_grade_count",
        "completion_percentage",
    }.issubset(completion_properties)

    assert {
        "classroom",
        "active_student_count",
        "published_graded_activity_count",
        "completion",
        "activities",
        "generated_at",
    }.issubset(classroom_properties)

    assert {
        "activity",
        "active_student_count",
        "completion",
        "generated_at",
    }.issubset(activity_properties)

    prohibited_fields = {
        "raw_code",
        "source_code",
        "starter_code",
        "standard_input",
        "expected_output",
        "hidden_test_cases",
        "required_ast_rules",
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

    for properties in (
        completion_properties,
        classroom_properties,
        activity_properties,
    ):
        assert prohibited_fields.isdisjoint(properties)


def test_grade_distribution_contract_uses_manual_grade_summary_only():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "GradeDistributionResponse",
    )

    bucket_properties = get_schema_properties(
        document,
        "GradeDistributionBucket",
    )

    assert {
        "classroom",
        "activity",
        "manually_graded_submission_count",
        "released_grade_count",
        "average_percentage",
        "minimum_percentage",
        "maximum_percentage",
        "buckets",
        "generated_at",
    }.issubset(properties)

    assert {
        "band",
        "minimum_percentage",
        "maximum_percentage",
        "count",
        "percentage_of_graded",
    }.issubset(bucket_properties)

    prohibited_fields = {
        "raw_code",
        "source_code",
        "standard_input",
        "feedback",
        "automatic_grade",
        "risk_score",
        "plagiarism_verdict",
        "cheating_verdict",
        "misconduct_verdict",
        "student_rank",
        "misconduct_rank",
    }

    assert prohibited_fields.isdisjoint(properties)

    assert prohibited_fields.isdisjoint(bucket_properties)


def test_missing_submission_contract_has_no_source_or_risk_data():
    document = get_openapi_document()

    list_properties = get_schema_properties(
        document,
        "MissingSubmissionListResponse",
    )

    item_properties = get_schema_properties(
        document,
        "MissingSubmissionItem",
    )

    assert {
        "items",
        "page",
        "page_size",
        "total_items",
        "total_pages",
        "sort_by",
        "sort_direction",
        "generated_at",
    }.issubset(list_properties)

    assert {
        "student",
        "activity",
        "due_at",
        "enrollment_status",
        "submission_state",
    }.issubset(item_properties)

    prohibited_fields = {
        "raw_code",
        "source_code",
        "standard_input",
        "feedback",
        "ast_findings",
        "jaccard_score",
        "similarity_results",
        "execution_output",
        "session_telemetry",
        "risk_score",
        "misconduct_rank",
        "plagiarism_verdict",
        "cheating_verdict",
        "misconduct_verdict",
    }

    assert prohibited_fields.isdisjoint(list_properties)

    assert prohibited_fields.isdisjoint(item_properties)


def test_student_progress_contract_is_personal_and_release_safe():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "StudentProgressSummaryResponse",
    )

    classroom_properties = get_schema_properties(
        document,
        "StudentClassProgressItem",
    )

    assert {
        "student_id",
        "active_classroom_count",
        "published_graded_activity_count",
        "submitted_activity_count",
        "missing_activity_count",
        "released_grade_count",
        "average_released_percentage",
        "completion_percentage",
        "classrooms",
        "generated_at",
    }.issubset(properties)

    assert {
        "classroom",
        "published_graded_activity_count",
        "submitted_activity_count",
        "missing_activity_count",
        "released_grade_count",
        "average_released_percentage",
        "completion_percentage",
    }.issubset(classroom_properties)

    prohibited_fields = {
        "instructor_id",
        "another_student_id",
        "unreleased_score",
        "unreleased_feedback",
        "raw_code",
        "source_code",
        "standard_input",
        "automatic_grade",
        "risk_score",
        "misconduct_rank",
        "plagiarism_verdict",
        "cheating_verdict",
        "misconduct_verdict",
    }

    assert prohibited_fields.isdisjoint(properties)

    assert prohibited_fields.isdisjoint(classroom_properties)


def test_gradebook_csv_openapi_contract_is_privacy_safe():
    document = get_openapi_document()

    operation = document["paths"]["/reports/classrooms/{class_id}/gradebook.csv"]["get"]

    responses = operation["responses"]

    assert {
        "200",
        "400",
        "403",
        "404",
        "500",
        "503",
    }.issubset(responses)

    success_content = responses["200"].get(
        "content",
        {},
    )

    assert "text/csv" in success_content

    csv_schema = success_content["text/csv"]["schema"]

    assert csv_schema["type"] == "string"
    assert csv_schema["format"] == "binary"

    assert operation.get("requestBody") is None

    parameter_names = {
        parameter["name"]
        for parameter in operation.get(
            "parameters",
            [],
        )
    }

    assert {
        "class_id",
        "task_id",
    }.issubset(parameter_names)

    assert {
        "student_id",
        "instructor_id",
        "include_raw_source",
        "include_source_code",
        "include_feedback",
        "include_unreleased_grades",
        "include_ast_findings",
        "include_similarity_details",
        "include_session_telemetry",
        "risk_score",
        "misconduct_rank",
    }.isdisjoint(parameter_names)
