from collections.abc import Generator
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import (
    get_current_instructor,
    get_current_student,
)
from app.routers import reporting as reporting_router
from app.services.reporting_service import (
    ReportingAccessDeniedError,
    ReportingClassroomNotFoundError,
    ReportingExportError,
    ReportingFilterConflictError,
    ReportingPaginationError,
    ReportingServiceError,
    ReportingTaskNotFoundError,
    ReportingTaskUnavailableError,
)


NOW = datetime.now(timezone.utc)


@pytest.fixture()
def fake_db() -> object:
    return object()


@pytest.fixture()
def instructor_user() -> SimpleNamespace:
    return SimpleNamespace(
        user_id=41,
        role="instructor",
    )


@pytest.fixture()
def student_user() -> SimpleNamespace:
    return SimpleNamespace(
        user_id=84,
        role="student",
    )


@pytest.fixture()
def app(
    fake_db: object,
    instructor_user: SimpleNamespace,
    student_user: SimpleNamespace,
) -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(
        reporting_router.router,
    )

    def override_db():
        yield fake_db

    def override_instructor():
        return instructor_user

    def override_student():
        return student_user

    test_app.dependency_overrides[get_db] = override_db

    test_app.dependency_overrides[get_current_instructor] = override_instructor

    test_app.dependency_overrides[get_current_student] = override_student

    return test_app


@pytest.fixture()
def client(
    app: FastAPI,
) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def _classroom_summary_result() -> dict[str, Any]:
    return {
        "classroom": {
            "class_id": 10,
            "name": "BSIT 3A",
            "subject_code": "IT-301",
            "section": "3A",
        },
        "active_student_count": 2,
        "published_graded_activity_count": 1,
        "completion": {
            "expected_count": 2,
            "submitted_count": 1,
            "missing_count": 1,
            "manually_graded_count": 1,
            "released_grade_count": 0,
            "completion_percentage": 50.0,
        },
        "activities": [
            {
                "activity": {
                    "task_id": 20,
                    "title": "Functions Laboratory",
                    "activity_type": "laboratory",
                    "class_id": 10,
                    "is_graded": True,
                    "is_published": True,
                    "due_at": None,
                },
                "completion": {
                    "expected_count": 2,
                    "submitted_count": 1,
                    "missing_count": 1,
                    "manually_graded_count": 1,
                    "released_grade_count": 0,
                    "completion_percentage": 50.0,
                },
            }
        ],
        "generated_at": NOW,
    }


def _activity_summary_result() -> dict[str, Any]:
    return {
        "activity": {
            "task_id": 20,
            "title": "Functions Laboratory",
            "activity_type": "laboratory",
            "class_id": 10,
            "is_graded": True,
            "is_published": True,
            "due_at": None,
        },
        "active_student_count": 2,
        "completion": {
            "expected_count": 2,
            "submitted_count": 1,
            "missing_count": 1,
            "manually_graded_count": 1,
            "released_grade_count": 0,
            "completion_percentage": 50.0,
        },
        "generated_at": NOW,
    }


def _grade_distribution_result() -> dict[str, Any]:
    return {
        "classroom": {
            "class_id": 10,
            "name": "BSIT 3A",
            "subject_code": "IT-301",
            "section": "3A",
        },
        "activity": None,
        "manually_graded_submission_count": 2,
        "released_grade_count": 1,
        "average_percentage": 85.0,
        "minimum_percentage": 80.0,
        "maximum_percentage": 90.0,
        "buckets": [
            {
                "band": "0-59.99",
                "minimum_percentage": 0.0,
                "maximum_percentage": 59.99,
                "count": 0,
                "percentage_of_graded": 0.0,
            },
            {
                "band": "60-69.99",
                "minimum_percentage": 60.0,
                "maximum_percentage": 69.99,
                "count": 0,
                "percentage_of_graded": 0.0,
            },
            {
                "band": "70-79.99",
                "minimum_percentage": 70.0,
                "maximum_percentage": 79.99,
                "count": 0,
                "percentage_of_graded": 0.0,
            },
            {
                "band": "80-89.99",
                "minimum_percentage": 80.0,
                "maximum_percentage": 89.99,
                "count": 1,
                "percentage_of_graded": 50.0,
            },
            {
                "band": "90-100",
                "minimum_percentage": 90.0,
                "maximum_percentage": 100.0,
                "count": 1,
                "percentage_of_graded": 50.0,
            },
        ],
        "generated_at": NOW,
    }


def _missing_submission_result() -> dict[str, Any]:
    return {
        "items": [
            {
                "student": {
                    "student_id": 84,
                    "name": "Student One",
                    "school_id": "2026000084",
                },
                "activity": {
                    "task_id": 20,
                    "title": "Functions Laboratory",
                    "activity_type": "laboratory",
                    "class_id": 10,
                    "is_graded": True,
                    "is_published": True,
                    "due_at": None,
                },
                "due_at": None,
                "enrollment_status": "active",
                "submission_state": "missing",
            }
        ],
        "page": 1,
        "page_size": 25,
        "total_items": 1,
        "total_pages": 1,
        "sort_by": "student_name",
        "sort_direction": "asc",
        "generated_at": NOW,
    }


def _student_progress_result() -> dict[str, Any]:
    return {
        "student_id": 84,
        "active_classroom_count": 1,
        "published_graded_activity_count": 2,
        "submitted_activity_count": 1,
        "missing_activity_count": 1,
        "released_grade_count": 1,
        "average_released_percentage": 90.0,
        "completion_percentage": 50.0,
        "classrooms": [
            {
                "classroom": {
                    "class_id": 10,
                    "name": "BSIT 3A",
                    "subject_code": "IT-301",
                    "section": "3A",
                },
                "published_graded_activity_count": 2,
                "submitted_activity_count": 1,
                "missing_activity_count": 1,
                "released_grade_count": 1,
                "average_released_percentage": 90.0,
                "completion_percentage": 50.0,
            }
        ],
        "generated_at": NOW,
    }


def test_classroom_completion_uses_authenticated_instructor_id(
    client: TestClient,
    fake_db: object,
    instructor_user: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
):
    service = Mock(
        return_value=_classroom_summary_result(),
    )

    monkeypatch.setattr(
        reporting_router,
        "get_classroom_completion_summary",
        service,
    )

    response = client.get(
        "/reports/classrooms/10/completion",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["classroom"]["class_id"] == 10
    assert response.json()["completion"]["missing_count"] == 1

    service.assert_called_once_with(
        fake_db,
        instructor_id=instructor_user.user_id,
        class_id=10,
    )


def test_activity_completion_uses_authenticated_instructor_id(
    client: TestClient,
    fake_db: object,
    instructor_user: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
):
    service = Mock(
        return_value=_activity_summary_result(),
    )

    monkeypatch.setattr(
        reporting_router,
        "get_activity_completion_summary",
        service,
    )

    response = client.get(
        "/reports/activities/20/completion",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["activity"]["task_id"] == 20

    service.assert_called_once_with(
        fake_db,
        instructor_id=instructor_user.user_id,
        task_id=20,
    )


def test_grade_distribution_passes_optional_task_filter(
    client: TestClient,
    fake_db: object,
    instructor_user: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
):
    result = _grade_distribution_result()
    result["activity"] = {
        "task_id": 20,
        "title": "Functions Laboratory",
        "activity_type": "laboratory",
        "class_id": 10,
        "is_graded": True,
        "is_published": True,
        "due_at": None,
    }

    service = Mock(
        return_value=result,
    )

    monkeypatch.setattr(
        reporting_router,
        "get_grade_distribution",
        service,
    )

    response = client.get(
        "/reports/classrooms/10/grade-distribution",
        params={
            "task_id": 20,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["activity"]["task_id"] == 20
    assert response.json()["released_grade_count"] == 1

    service.assert_called_once_with(
        fake_db,
        instructor_id=instructor_user.user_id,
        class_id=10,
        task_id=20,
    )


def test_missing_submissions_passes_bounded_filters_and_sorting(
    client: TestClient,
    fake_db: object,
    instructor_user: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
):
    service = Mock(
        return_value=_missing_submission_result(),
    )

    monkeypatch.setattr(
        reporting_router,
        "list_missing_submissions",
        service,
    )

    response = client.get(
        "/reports/missing-submissions",
        params={
            "page": 1,
            "page_size": 25,
            "class_id": 10,
            "task_id": 20,
            "sort_by": "student_name",
            "sort_direction": "asc",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total_items"] == 1
    assert response.json()["items"][0]["submission_state"] == "missing"

    service.assert_called_once_with(
        fake_db,
        instructor_id=instructor_user.user_id,
        page=1,
        page_size=25,
        class_id=10,
        task_id=20,
        sort_by="student_name",
        sort_direction="asc",
    )


@pytest.mark.parametrize(
    ("params", "expected_status"),
    [
        (
            {
                "page": 0,
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        ),
        (
            {
                "page_size": 101,
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        ),
        (
            {
                "sort_by": "risk_score",
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        ),
        (
            {
                "sort_direction": "sideways",
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        ),
    ],
)
def test_missing_submissions_rejects_invalid_query_contracts(
    client: TestClient,
    params: dict[str, Any],
    expected_status: int,
):
    response = client.get(
        "/reports/missing-submissions",
        params=params,
    )

    assert response.status_code == expected_status


def test_student_progress_uses_authenticated_student_id(
    client: TestClient,
    fake_db: object,
    student_user: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
):
    service = Mock(
        return_value=_student_progress_result(),
    )

    monkeypatch.setattr(
        reporting_router,
        "get_student_progress_summary",
        service,
    )

    response = client.get(
        "/reports/students/me/progress",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["student_id"] == student_user.user_id
    assert response.json()["released_grade_count"] == 1

    service.assert_called_once_with(
        fake_db,
        student_id=student_user.user_id,
    )


def test_gradebook_csv_returns_download_headers_and_privacy_marker(
    client: TestClient,
    fake_db: object,
    instructor_user: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
):
    service = Mock(
        return_value={
            "content": (
                "\ufeffstudent_name,school_id\r\nStudent One,2026000084\r\n"
            ).encode("utf-8"),
            "media_type": "text/csv; charset=utf-8",
            "filename": "classroom-10-gradebook.csv",
            "row_count": 1,
            "generated_at": NOW,
            "includes_raw_source": False,
        },
    )

    monkeypatch.setattr(
        reporting_router,
        "build_gradebook_csv_export",
        service,
    )

    response = client.get(
        "/reports/classrooms/10/gradebook.csv",
        params={
            "task_id": 20,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="classroom-10-gradebook.csv"'
    )
    assert response.headers["x-report-row-count"] == "1"
    assert response.headers["x-report-includes-raw-source"] == "false"
    assert "source_code" not in response.text
    assert "standard_input" not in response.text

    service.assert_called_once_with(
        fake_db,
        instructor_id=instructor_user.user_id,
        class_id=10,
        task_id=20,
    )


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (
            ReportingClassroomNotFoundError("Classroom not found."),
            status.HTTP_404_NOT_FOUND,
        ),
        (
            ReportingTaskNotFoundError("Activity not found."),
            status.HTTP_404_NOT_FOUND,
        ),
        (
            ReportingAccessDeniedError("Access denied."),
            status.HTTP_403_FORBIDDEN,
        ),
        (
            ReportingFilterConflictError("Filter conflict."),
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            ReportingPaginationError("Pagination invalid."),
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            ReportingTaskUnavailableError("Activity unavailable."),
            status.HTTP_409_CONFLICT,
        ),
        (
            ReportingExportError("Export failed."),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
        (
            ReportingServiceError("Unexpected reporting failure."),
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ),
    ],
)
def test_reporting_error_mapping(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    error: ReportingServiceError,
    expected_status: int,
):
    def fail_report(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(
        reporting_router,
        "get_classroom_completion_summary",
        fail_report,
    )

    response = client.get(
        "/reports/classrooms/10/completion",
    )

    assert response.status_code == expected_status

    if expected_status == status.HTTP_503_SERVICE_UNAVAILABLE:
        assert response.json()["detail"] == (
            "The reporting operation could not be completed."
        )
    else:
        assert response.json()["detail"] == str(error)


def test_instructor_endpoint_preserves_dependency_denial(
    app: FastAPI,
):
    def deny_instructor():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor access required.",
        )

    app.dependency_overrides[get_current_instructor] = deny_instructor

    with TestClient(app) as denied_client:
        response = denied_client.get(
            "/reports/classrooms/10/completion",
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Instructor access required."


def test_student_endpoint_preserves_dependency_denial(
    app: FastAPI,
):
    def deny_student():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required.",
        )

    app.dependency_overrides[get_current_student] = deny_student

    with TestClient(app) as denied_client:
        response = denied_client.get(
            "/reports/students/me/progress",
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Student access required."


def test_reporting_openapi_exposes_only_approved_routes(
    app: FastAPI,
):
    schema = app.openapi()

    expected_paths = {
        "/reports/classrooms/{class_id}/completion",
        "/reports/activities/{task_id}/completion",
        "/reports/classrooms/{class_id}/grade-distribution",
        "/reports/missing-submissions",
        "/reports/students/me/progress",
        "/reports/classrooms/{class_id}/gradebook.csv",
    }

    assert expected_paths.issubset(
        schema["paths"],
    )

    for path in expected_paths:
        assert set(schema["paths"][path]) == {
            "get",
        }


def test_reporting_responses_exclude_sensitive_contract_fields(
    app: FastAPI,
):
    schema_text = str(app.openapi()).lower()

    prohibited_contract_terms = {
        "source_code",
        "raw_code",
        "standard_input",
        "starter_code",
        "expected_output",
        "hidden_test",
        "ast_findings",
        "jaccard_score",
        "similarity_results",
        "stdout",
        "stderr",
        "worker_task_id",
        "clipboard_content",
        "pasted_text",
        "keystrokes",
        "screen_recording",
        "webcam",
        "microphone",
        "risk_score",
        "plagiarism_verdict",
        "cheating_verdict",
        "misconduct_verdict",
    }

    for prohibited_term in prohibited_contract_terms:
        assert prohibited_term not in schema_text
