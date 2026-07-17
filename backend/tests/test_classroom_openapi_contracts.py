from typing import Any

from app.main import APP_VERSION, app


CLASSROOM_OPERATIONS = {
    ("post", "/classrooms/"),
    ("get", "/classrooms/"),
    ("post", "/classrooms/join"),
    ("get", "/classrooms/mine"),
    (
        "patch",
        "/classrooms/enrollments/{enrollment_id}/status",
    ),
    ("get", "/classrooms/{class_id}/members"),
    ("post", "/classrooms/{class_id}/regenerate-code"),
    ("get", "/classrooms/{class_id}"),
    ("patch", "/classrooms/{class_id}"),
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
    properties = dict(schema.get("properties", {}))

    for nested_schema in schema.get("allOf", []):
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


def get_request_schema(
    document: dict[str, Any],
    *,
    method: str,
    path: str,
) -> dict[str, Any]:
    operation = document["paths"][path][method]

    schema = operation["requestBody"]["content"]["application/json"]["schema"]

    return resolve_schema(
        document,
        schema,
    )


def test_classroom_api_version():
    document = get_openapi_document()

    assert document["info"]["version"] == APP_VERSION
    assert APP_VERSION == "0.11.0"


def test_classroom_routes_exist():
    document = get_openapi_document()

    for method, path in CLASSROOM_OPERATIONS:
        assert path in document["paths"]
        assert method in document["paths"][path]


def test_all_classroom_routes_require_authentication():
    document = get_openapi_document()

    for method, path in CLASSROOM_OPERATIONS:
        operation = document["paths"][path][method]

        assert operation.get("security"), (
            f"{method.upper()} {path} must require authentication."
        )


def test_classroom_create_excludes_backend_fields():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "ClassroomCreate",
    )

    assert {
        "name",
        "subject_code",
        "section",
    }.issubset(properties)

    prohibited_fields = {
        "class_id",
        "instructor_id",
        "class_code",
        "is_active",
        "created_at",
        "updated_at",
    }

    assert prohibited_fields.isdisjoint(properties)


def test_classroom_update_cannot_modify_owner_or_code():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "ClassroomUpdate",
    )

    assert {
        "name",
        "subject_code",
        "section",
        "is_active",
    }.issubset(properties)

    assert "instructor_id" not in properties
    assert "class_code" not in properties
    assert "class_id" not in properties


def test_join_request_accepts_only_class_code():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "EnrollmentJoinRequest",
    )

    assert set(properties) == {
        "class_code",
    }

    assert "student_id" not in properties
    assert "class_id" not in properties
    assert "status" not in properties


def test_enrollment_status_contract_matches_database():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "EnrollmentStatusUpdate",
    )

    status_schema = resolve_schema(
        document,
        properties["status"],
    )

    allowed_values = set(
        status_schema.get(
            "enum",
            [],
        )
    )

    assert allowed_values == {
        "active",
        "disabled",
        "removed",
    }


def test_classroom_response_exposes_generated_code():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "ClassroomResponse",
    )

    assert {
        "class_id",
        "instructor_id",
        "name",
        "subject_code",
        "section",
        "class_code",
        "is_active",
        "created_at",
        "updated_at",
    }.issubset(properties)


def test_enrollment_response_contains_backend_identity():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "EnrollmentResponse",
    )

    assert {
        "enrollment_id",
        "class_id",
        "student_id",
        "status",
    }.issubset(properties)


def test_class_member_response_excludes_sensitive_fields():
    document = get_openapi_document()

    properties = get_schema_properties(
        document,
        "ClassMemberResponse",
    )

    assert {
        "enrollment_id",
        "student_id",
        "school_id",
        "name",
        "email",
        "status",
    }.issubset(properties)

    prohibited_fields = {
        "password",
        "password_hash",
        "email_verified",
        "access_token",
    }

    assert prohibited_fields.isdisjoint(properties)


def test_classroom_operation_ids():
    document = get_openapi_document()

    expected_operation_ids = {
        "create_classroom",
        "list_instructor_classrooms",
        "join_classroom",
        "list_student_classrooms",
        "update_enrollment_status",
        "list_class_members",
        "regenerate_classroom_code",
        "get_instructor_classroom",
        "update_classroom",
    }

    actual_operation_ids = {
        document["paths"][path][method]["operationId"]
        for method, path in CLASSROOM_OPERATIONS
    }

    assert actual_operation_ids == expected_operation_ids
