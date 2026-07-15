from typing import Any

from app.main import app


INSTRUCTOR_TASK_PATHS = {
    "/instructors/tasks/": {
        "get",
        "post",
    },
    "/instructors/tasks/{task_id}": {
        "get",
        "patch",
    },
    "/instructors/tasks/{task_id}/publication": {
        "patch",
    },
    "/instructors/tasks/{task_id}/test-cases": {
        "get",
        "post",
    },
    "/instructors/test-cases/{test_case_id}": {
        "get",
        "patch",
        "delete",
    },
}

STUDENT_ACTIVITY_PATHS = {
    "/activities/": {
        "get",
    },
    "/activities/{task_id}": {
        "get",
    },
    "/activities/{task_id}/sample-test-cases": {
        "get",
    },
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


def get_openapi_schema() -> dict[str, Any]:
    return app.openapi()


def get_schema_properties(
    schema_name: str,
) -> dict[str, Any]:
    openapi_schema = get_openapi_schema()

    schemas = openapi_schema["components"]["schemas"]

    assert schema_name in schemas

    return schemas[schema_name].get(
        "properties",
        {},
    )


def get_operation(
    path: str,
    method: str,
) -> dict[str, Any]:
    openapi_schema = get_openapi_schema()

    assert path in openapi_schema["paths"]
    assert method in openapi_schema["paths"][path]

    return openapi_schema["paths"][path][method]


def get_json_response_schema(
    path: str,
    method: str,
    status_code: str,
) -> dict[str, Any]:
    operation = get_operation(
        path,
        method,
    )

    responses = operation["responses"]

    assert status_code in responses

    response = responses[status_code]
    content = response.get("content", {})

    assert "application/json" in content

    return content["application/json"]["schema"]


def get_request_schema_reference(
    path: str,
    method: str,
) -> str:
    operation = get_operation(
        path,
        method,
    )

    request_body = operation["requestBody"]

    assert request_body.get("required") is True

    schema = request_body["content"]["application/json"]["schema"]

    assert "$ref" in schema

    return schema["$ref"]


def assert_operation_requires_authentication(
    path: str,
    method: str,
) -> None:
    operation = get_operation(
        path,
        method,
    )

    assert "security" in operation
    assert operation["security"]
    assert isinstance(
        operation["security"],
        list,
    )


def test_task_management_paths_and_methods_are_registered():
    openapi_schema = get_openapi_schema()
    paths = openapi_schema["paths"]

    expected_paths = {
        **INSTRUCTOR_TASK_PATHS,
        **STUDENT_ACTIVITY_PATHS,
    }

    for path, expected_methods in expected_paths.items():
        assert path in paths

        actual_methods = {method for method in paths[path] if method in HTTP_METHODS}

        assert actual_methods == expected_methods


def test_task_management_operations_require_authentication():
    expected_paths = {
        **INSTRUCTOR_TASK_PATHS,
        **STUDENT_ACTIVITY_PATHS,
    }

    for path, methods in expected_paths.items():
        for method in methods:
            assert_operation_requires_authentication(
                path,
                method,
            )


def test_task_create_schema_excludes_backend_controlled_fields():
    properties = get_schema_properties(
        "TaskCreate",
    )

    assert "class_id" in properties
    assert "title" in properties
    assert "activity_type" in properties
    assert "required_ast_rules" in properties
    assert "starter_code" in properties
    assert "paste_policy" in properties
    assert "is_graded" in properties
    assert "due_at" in properties

    assert "task_id" not in properties
    assert "instructor_id" not in properties
    assert "is_published" not in properties
    assert "published_at" not in properties
    assert "created_at" not in properties
    assert "updated_at" not in properties


def test_task_update_schema_excludes_publication_and_ownership_fields():
    properties = get_schema_properties(
        "TaskUpdate",
    )

    expected_editable_fields = {
        "class_id",
        "title",
        "description",
        "instructions",
        "activity_type",
        "required_ast_rules",
        "starter_code",
        "paste_policy",
        "is_graded",
        "due_at",
    }

    assert set(properties) == expected_editable_fields

    assert "task_id" not in properties
    assert "instructor_id" not in properties
    assert "is_published" not in properties
    assert "published_at" not in properties


def test_task_publication_uses_dedicated_request_schema():
    schema_reference = get_request_schema_reference(
        "/instructors/tasks/{task_id}/publication",
        "patch",
    )

    assert schema_reference.endswith("/TaskPublishRequest")

    properties = get_schema_properties(
        "TaskPublishRequest",
    )

    assert set(properties) == {
        "is_published",
    }


def test_test_case_create_schema_excludes_parent_task_id():
    properties = get_schema_properties(
        "TaskTestCaseCreate",
    )

    assert "name" in properties
    assert "standard_input" in properties
    assert "expected_output" in properties
    assert "is_hidden" in properties
    assert "display_order" in properties

    assert "test_case_id" not in properties
    assert "task_id" not in properties
    assert "created_at" not in properties
    assert "updated_at" not in properties


def test_instructor_test_case_response_contains_management_fields():
    properties = get_schema_properties(
        "InstructorTaskTestCaseResponse",
    )

    assert "test_case_id" in properties
    assert "task_id" in properties
    assert "name" in properties
    assert "standard_input" in properties
    assert "expected_output" in properties
    assert "is_hidden" in properties
    assert "display_order" in properties
    assert "created_at" in properties

    # TaskTestCase currently has no updated_at column.
    assert "updated_at" not in properties


def test_student_task_response_excludes_instructor_ownership():
    properties = get_schema_properties(
        "StudentTaskResponse",
    )

    assert "task_id" in properties
    assert "class_id" in properties
    assert "title" in properties
    assert "activity_type" in properties
    assert "starter_code" in properties
    assert "paste_policy" in properties
    assert "is_published" in properties
    assert "published_at" in properties

    assert "instructor_id" not in properties
    assert "test_cases" not in properties


def test_student_sample_response_excludes_hidden_case_metadata():
    properties = get_schema_properties(
        "StudentSampleTestCaseResponse",
    )

    assert "test_case_id" in properties
    assert "name" in properties
    assert "standard_input" in properties
    assert "expected_output" in properties
    assert "display_order" in properties

    assert "task_id" not in properties
    assert "is_hidden" not in properties


def test_instructor_task_endpoints_use_expected_response_schemas():
    create_response = get_json_response_schema(
        "/instructors/tasks/",
        "post",
        "201",
    )

    assert create_response["$ref"].endswith("/TaskResponse")

    detail_response = get_json_response_schema(
        "/instructors/tasks/{task_id}",
        "get",
        "200",
    )

    assert detail_response["$ref"].endswith("/TaskResponse")

    update_response = get_json_response_schema(
        "/instructors/tasks/{task_id}",
        "patch",
        "200",
    )

    assert update_response["$ref"].endswith("/TaskResponse")

    publication_response = get_json_response_schema(
        "/instructors/tasks/{task_id}/publication",
        "patch",
        "200",
    )

    assert publication_response["$ref"].endswith("/TaskResponse")


def test_student_activity_endpoints_use_student_safe_schemas():
    list_response = get_json_response_schema(
        "/activities/",
        "get",
        "200",
    )

    assert list_response["type"] == "array"
    assert list_response["items"]["$ref"].endswith("/StudentTaskResponse")

    detail_response = get_json_response_schema(
        "/activities/{task_id}",
        "get",
        "200",
    )

    assert detail_response["$ref"].endswith("/StudentTaskResponse")

    sample_response = get_json_response_schema(
        "/activities/{task_id}/sample-test-cases",
        "get",
        "200",
    )

    assert sample_response["type"] == "array"
    assert sample_response["items"]["$ref"].endswith("/StudentSampleTestCaseResponse")


def test_delete_test_case_documents_empty_success_response():
    operation = get_operation(
        "/instructors/test-cases/{test_case_id}",
        "delete",
    )

    assert "204" in operation["responses"]

    response = operation["responses"]["204"]

    assert "content" not in response
