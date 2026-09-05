from typing import Any

from app.main import app


STUDENT_SUBMISSION_OPERATIONS = {
    ("post", "/submissions/"),
    ("get", "/submissions/"),
    ("get", "/submissions/official/{task_id}"),
    ("get", "/submissions/{submission_id}"),
}

INSTRUCTOR_SUBMISSION_OPERATIONS = {
    (
        "get",
        "/instructors/tasks/{task_id}/submissions",
    ),
    (
        "get",
        "/instructors/submissions/{submission_id}",
    ),
}


def get_openapi_document() -> dict[str, Any]:
    return app.openapi()


def resolve_schema(
    document: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    if "$ref" not in schema:
        return schema

    schema_name = schema["$ref"].split("/")[-1]

    return document["components"]["schemas"][schema_name]


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


def get_operation(
    document: dict[str, Any],
    *,
    method: str,
    path: str,
) -> dict[str, Any]:
    assert path in document["paths"]
    assert method in document["paths"][path]

    return document["paths"][path][method]


def get_request_schema(
    document: dict[str, Any],
    *,
    method: str,
    path: str,
) -> dict[str, Any]:
    operation = get_operation(
        document,
        method=method,
        path=path,
    )

    request_body = operation["requestBody"]

    assert request_body.get("required") is True

    schema = request_body["content"]["application/json"]["schema"]

    return resolve_schema(
        document,
        schema,
    )


def get_response_schema(
    document: dict[str, Any],
    *,
    method: str,
    path: str,
    status_code: str,
) -> dict[str, Any]:
    operation = get_operation(
        document,
        method=method,
        path=path,
    )

    responses = operation["responses"]

    assert status_code in responses

    content = responses[status_code].get(
        "content",
        {},
    )

    assert "application/json" in content

    return content["application/json"]["schema"]


def get_parameter_names(
    document: dict[str, Any],
    *,
    method: str,
    path: str,
    parameter_location: str,
) -> set[str]:
    operation = get_operation(
        document,
        method=method,
        path=path,
    )

    return {
        parameter["name"]
        for parameter in operation.get(
            "parameters",
            [],
        )
        if parameter.get("in") == parameter_location
    }


def test_submission_routes_exist():
    document = get_openapi_document()

    expected_operations = (
        STUDENT_SUBMISSION_OPERATIONS | INSTRUCTOR_SUBMISSION_OPERATIONS
    )

    for method, path in expected_operations:
        assert path in document["paths"]
        assert method in document["paths"][path]


def test_all_submission_routes_require_authentication():
    document = get_openapi_document()

    expected_operations = (
        STUDENT_SUBMISSION_OPERATIONS | INSTRUCTOR_SUBMISSION_OPERATIONS
    )

    for method, path in expected_operations:
        operation = get_operation(
            document,
            method=method,
            path=path,
        )

        assert operation.get("security"), (
            f"{method.upper()} {path} must require authentication."
        )


def test_submission_create_excludes_backend_controlled_fields():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "SubmissionCreate",
    )

    assert {
        "task_id",
        "raw_code",
        "standard_input",
        "coding_session_id",
    }.issubset(properties)

    prohibited_fields = {
        "sub_id",
        "student_id",
        "attempt_number",
        "status",
        "is_official",
        "submitted_at",
        "accepted_at",
        "jaccard_score",
        "ast_pass_fail",
        "official_grade",
        "automatic_grade",
    }

    assert prohibited_fields.isdisjoint(properties)


def test_create_submission_endpoint_uses_submission_create():
    document = get_openapi_document()

    request_schema = get_request_schema(
        document,
        method="post",
        path="/submissions/",
    )

    request_properties = request_schema.get(
        "properties",
        {},
    )

    assert {
        "task_id",
        "raw_code",
        "standard_input",
        "coding_session_id",
    }.issubset(request_properties)

    assert "student_id" not in request_properties
    assert "attempt_number" not in request_properties
    assert "is_official" not in request_properties


def test_student_submission_response_is_student_safe():
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

    instructor_only_fields = {
        "student_id",
        "jaccard_score",
        "ast_pass_fail",
        "official_grade",
        "automatic_grade",
        "instructor_grade",
        "plagiarism_verdict",
        "misconduct_verdict",
        "behavior_score",
    }

    assert instructor_only_fields.isdisjoint(properties)


def test_instructor_submission_response_has_review_indicators():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "InstructorSubmissionResponse",
    )

    assert {
        "sub_id",
        "student_id",
        "task_id",
        "attempt_number",
        "raw_code",
        "standard_input",
        "status",
        "is_official",
        "submitted_at",
        "accepted_at",
        "jaccard_score",
        "ast_pass_fail",
    }.issubset(properties)

    prohibited_automatic_verdicts = {
        "automatic_grade",
        "official_grade",
        "plagiarism_verdict",
        "misconduct_verdict",
        "behavior_score",
    }

    assert prohibited_automatic_verdicts.isdisjoint(properties)


def test_student_submission_endpoints_use_student_response_schema():
    document = get_openapi_document()

    create_schema = get_response_schema(
        document,
        method="post",
        path="/submissions/",
        status_code="201",
    )

    assert create_schema["$ref"].endswith("/StudentSubmissionResponse")

    list_schema = get_response_schema(
        document,
        method="get",
        path="/submissions/",
        status_code="200",
    )

    assert list_schema["type"] == "array"
    assert list_schema["items"]["$ref"].endswith("/StudentSubmissionResponse")

    official_schema = get_response_schema(
        document,
        method="get",
        path="/submissions/official/{task_id}",
        status_code="200",
    )

    assert official_schema["$ref"].endswith("/StudentSubmissionResponse")

    detail_schema = get_response_schema(
        document,
        method="get",
        path="/submissions/{submission_id}",
        status_code="200",
    )

    assert detail_schema["$ref"].endswith("/StudentSubmissionResponse")


def test_instructor_submission_endpoints_use_review_response_schema():
    document = get_openapi_document()

    list_schema = get_response_schema(
        document,
        method="get",
        path=("/instructors/tasks/{task_id}/submissions"),
        status_code="200",
    )

    assert list_schema["type"] == "array"
    assert list_schema["items"]["$ref"].endswith("/InstructorSubmissionResponse")

    detail_schema = get_response_schema(
        document,
        method="get",
        path=("/instructors/submissions/{submission_id}"),
        status_code="200",
    )

    assert detail_schema["$ref"].endswith("/InstructorSubmissionResponse")


def test_student_submission_list_documents_filters():
    document = get_openapi_document()

    query_parameters = get_parameter_names(
        document,
        method="get",
        path="/submissions/",
        parameter_location="query",
    )

    assert query_parameters == {
        "task_id",
        "status",
        "official_only",
    }


def test_instructor_submission_list_documents_filters():
    document = get_openapi_document()

    query_parameters = get_parameter_names(
        document,
        method="get",
        path=("/instructors/tasks/{task_id}/submissions"),
        parameter_location="query",
    )

    assert query_parameters == {
        "student_id",
        "status",
        "official_only",
    }

    path_parameters = get_parameter_names(
        document,
        method="get",
        path=("/instructors/tasks/{task_id}/submissions"),
        parameter_location="path",
    )

    assert path_parameters == {
        "task_id",
    }


def test_submission_path_parameters_are_documented():
    document = get_openapi_document()

    official_path_parameters = get_parameter_names(
        document,
        method="get",
        path="/submissions/official/{task_id}",
        parameter_location="path",
    )

    assert official_path_parameters == {
        "task_id",
    }

    student_detail_parameters = get_parameter_names(
        document,
        method="get",
        path="/submissions/{submission_id}",
        parameter_location="path",
    )

    assert student_detail_parameters == {
        "submission_id",
    }

    instructor_detail_parameters = get_parameter_names(
        document,
        method="get",
        path=("/instructors/submissions/{submission_id}"),
        parameter_location="path",
    )

    assert instructor_detail_parameters == {
        "submission_id",
    }


def test_submission_operation_ids_are_correct():
    document = get_openapi_document()

    expected_operation_ids = {
        (
            "post",
            "/submissions/",
        ): "create_student_submission_attempt",
        (
            "get",
            "/submissions/",
        ): "list_my_submission_attempts",
        (
            "get",
            "/submissions/official/{task_id}",
        ): "read_my_official_submission_attempt",
        (
            "get",
            "/submissions/{submission_id}",
        ): "read_my_submission_attempt",
        (
            "get",
            "/instructors/tasks/{task_id}/submissions",
        ): "list_instructor_task_submissions",
        (
            "get",
            "/instructors/submissions/{submission_id}",
        ): "get_instructor_submission",
    }

    actual_operation_ids = {
        (
            method,
            path,
        ): get_operation(
            document,
            method=method,
            path=path,
        )["operationId"]
        for method, path in expected_operation_ids
    }

    assert actual_operation_ids == expected_operation_ids


def test_submission_create_documents_expected_status_codes():
    document = get_openapi_document()

    operation = get_operation(
        document,
        method="post",
        path="/submissions/",
    )

    responses = operation["responses"]

    assert "201" in responses
    assert "404" in responses
    assert "409" in responses
    assert "422" in responses
