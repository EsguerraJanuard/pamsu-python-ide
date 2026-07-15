from typing import Any

from app.main import app


STUDENT_EXECUTION_OPERATIONS = {
    ("post", "/execution/requests/"),
    ("get", "/execution/requests/"),
    (
        "get",
        "/execution/requests/{execution_id}",
    ),
}

INSTRUCTOR_EXECUTION_OPERATIONS = {
    (
        "get",
        "/instructors/tasks/{task_id}/execution-requests",
    ),
    (
        "get",
        "/instructors/execution-requests/{execution_id}",
    ),
}

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


def test_execution_request_routes_exist():
    document = get_openapi_document()

    expected_operations = STUDENT_EXECUTION_OPERATIONS | INSTRUCTOR_EXECUTION_OPERATIONS

    for method, path in expected_operations:
        assert path in document["paths"]
        assert method in document["paths"][path]


def test_execution_request_routes_use_read_only_public_contracts():
    document = get_openapi_document()

    expected_methods = {
        "/execution/requests/": {
            "get",
            "post",
        },
        "/execution/requests/{execution_id}": {
            "get",
        },
        ("/instructors/tasks/{task_id}/execution-requests"): {
            "get",
        },
        ("/instructors/execution-requests/{execution_id}"): {
            "get",
        },
    }

    for path, allowed_methods in expected_methods.items():
        actual_methods = {
            method for method in document["paths"][path] if method in HTTP_METHODS
        }

        assert actual_methods == allowed_methods

    # Public student and instructor APIs cannot update worker results.
    assert "patch" not in document["paths"]["/execution/requests/{execution_id}"]

    assert (
        "patch"
        not in document["paths"]["/instructors/execution-requests/{execution_id}"]
    )


def test_all_execution_request_routes_require_authentication():
    document = get_openapi_document()

    expected_operations = STUDENT_EXECUTION_OPERATIONS | INSTRUCTOR_EXECUTION_OPERATIONS

    for method, path in expected_operations:
        operation = get_operation(
            document,
            method=method,
            path=path,
        )

        assert operation.get("security"), (
            f"{method.upper()} {path} must require authentication."
        )


def test_execution_request_create_excludes_backend_fields():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "ExecutionRequestCreate",
    )

    assert set(properties) == {
        "request_kind",
        "task_id",
        "submission_id",
        "coding_session_id",
        "source_code",
        "standard_input",
    }

    prohibited_fields = {
        "execution_id",
        "student_id",
        "status",
        "stdout",
        "stderr",
        "exit_code",
        "execution_time_ms",
        "limit_reason",
        "worker_task_id",
        "queued_at",
        "started_at",
        "completed_at",
        "official_grade",
        "automatic_grade",
        "misconduct_verdict",
        "plagiarism_verdict",
    }

    assert prohibited_fields.isdisjoint(properties)


def test_execution_create_endpoint_uses_request_create_schema():
    document = get_openapi_document()

    request_schema = get_request_schema(
        document,
        method="post",
        path="/execution/requests/",
    )

    request_properties = request_schema.get(
        "properties",
        {},
    )

    assert set(request_properties) == {
        "request_kind",
        "task_id",
        "submission_id",
        "coding_session_id",
        "source_code",
        "standard_input",
    }

    assert "student_id" not in request_properties
    assert "execution_id" not in request_properties
    assert "worker_task_id" not in request_properties
    assert "status" not in request_properties


def test_student_execution_response_is_student_safe():
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


def test_instructor_execution_response_has_student_identity_only():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "InstructorExecutionResponse",
    )

    assert {
        "execution_id",
        "student_id",
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
        "worker_task_id",
        "official_grade",
        "automatic_grade",
        "misconduct_verdict",
        "plagiarism_verdict",
        "behavior_score",
    }

    assert prohibited_fields.isdisjoint(properties)


def test_public_execution_responses_never_use_internal_schema():
    document = get_openapi_document()

    expected_operations = STUDENT_EXECUTION_OPERATIONS | INSTRUCTOR_EXECUTION_OPERATIONS

    for method, path in expected_operations:
        status_code = (
            "201" if (method == "post" and path == "/execution/requests/") else "200"
        )

        schema = get_response_schema(
            document,
            method=method,
            path=path,
            status_code=status_code,
        )

        schema_text = str(schema)

        assert "InternalExecutionResponse" not in schema_text


def test_student_execution_endpoints_use_student_response_schema():
    document = get_openapi_document()

    create_schema = get_response_schema(
        document,
        method="post",
        path="/execution/requests/",
        status_code="201",
    )

    assert create_schema["$ref"].endswith("/StudentExecutionResponse")

    list_schema = get_response_schema(
        document,
        method="get",
        path="/execution/requests/",
        status_code="200",
    )

    assert list_schema["type"] == "array"

    assert list_schema["items"]["$ref"].endswith("/StudentExecutionResponse")

    detail_schema = get_response_schema(
        document,
        method="get",
        path=("/execution/requests/{execution_id}"),
        status_code="200",
    )

    assert detail_schema["$ref"].endswith("/StudentExecutionResponse")


def test_instructor_execution_endpoints_use_review_response_schema():
    document = get_openapi_document()

    list_schema = get_response_schema(
        document,
        method="get",
        path=("/instructors/tasks/{task_id}/execution-requests"),
        status_code="200",
    )

    assert list_schema["type"] == "array"

    assert list_schema["items"]["$ref"].endswith("/InstructorExecutionResponse")

    detail_schema = get_response_schema(
        document,
        method="get",
        path=("/instructors/execution-requests/{execution_id}"),
        status_code="200",
    )

    assert detail_schema["$ref"].endswith("/InstructorExecutionResponse")


def test_student_execution_list_documents_filters():
    document = get_openapi_document()

    query_parameters = get_parameter_names(
        document,
        method="get",
        path="/execution/requests/",
        parameter_location="query",
    )

    assert query_parameters == {
        "task_id",
        "request_kind",
        "status",
    }


def test_instructor_execution_list_documents_filters():
    document = get_openapi_document()

    path = "/instructors/tasks/{task_id}/execution-requests"

    query_parameters = get_parameter_names(
        document,
        method="get",
        path=path,
        parameter_location="query",
    )

    assert query_parameters == {
        "student_id",
        "request_kind",
        "status",
    }

    path_parameters = get_parameter_names(
        document,
        method="get",
        path=path,
        parameter_location="path",
    )

    assert path_parameters == {
        "task_id",
    }


def test_execution_uuid_path_parameters_are_documented():
    document = get_openapi_document()

    student_path = "/execution/requests/{execution_id}"

    student_operation = get_operation(
        document,
        method="get",
        path=student_path,
    )

    student_parameters = {
        parameter["name"]: parameter
        for parameter in student_operation.get(
            "parameters",
            [],
        )
        if parameter.get("in") == "path"
    }

    assert set(student_parameters) == {
        "execution_id",
    }

    assert student_parameters["execution_id"]["schema"]["type"] == "string"

    assert student_parameters["execution_id"]["schema"]["format"] == "uuid"

    instructor_path = "/instructors/execution-requests/{execution_id}"

    instructor_operation = get_operation(
        document,
        method="get",
        path=instructor_path,
    )

    instructor_parameters = {
        parameter["name"]: parameter
        for parameter in instructor_operation.get(
            "parameters",
            [],
        )
        if parameter.get("in") == "path"
    }

    assert set(instructor_parameters) == {
        "execution_id",
    }

    assert instructor_parameters["execution_id"]["schema"]["format"] == "uuid"


def test_execution_operation_ids_are_correct():
    document = get_openapi_document()

    expected_operation_ids = {
        (
            "post",
            "/execution/requests/",
        ): "create_student_execution_request",
        (
            "get",
            "/execution/requests/",
        ): "list_student_execution_requests",
        (
            "get",
            "/execution/requests/{execution_id}",
        ): "get_student_execution_request",
        (
            "get",
            "/instructors/tasks/{task_id}/execution-requests",
        ): "list_instructor_task_execution_requests",
        (
            "get",
            "/instructors/execution-requests/{execution_id}",
        ): "get_instructor_execution_request",
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


def test_execution_create_documents_expected_status_codes():
    document = get_openapi_document()

    operation = get_operation(
        document,
        method="post",
        path="/execution/requests/",
    )

    responses = operation["responses"]

    assert "201" in responses
    assert "404" in responses
    assert "409" in responses
    assert "422" in responses
