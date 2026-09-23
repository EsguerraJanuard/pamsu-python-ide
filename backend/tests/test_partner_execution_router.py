from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.integrations.partner_auth import (
    PARTNER_EXECUTION_TOKEN_ENV,
    PARTNER_EXECUTION_TOKEN_HEADER,
)
from app.models.domain_models import (
    ExecutionRequest,
    PartnerExecutionUpdateRecord,
    Task,
    User,
)
from app.routers.execution import router


VALID_PARTNER_TOKEN = "development-partner-token-0123456789abcdefghijklmnopqrstuvwxyz"


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(
        dbapi_connection,
        _connection_record,
    ) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    session = testing_session_local()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(
    db_session: Session,
) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(router)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def create_user(
    db: Session,
    *,
    name: str,
    school_id: str,
    email: str,
    role: str,
) -> User:
    user = User(
        name=name,
        school_id=school_id,
        email=email,
        role=role,
        password_hash="hashed-password",
        email_verified=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_task(
    db: Session,
    *,
    instructor_id: int,
) -> Task:
    task = Task(
        class_id=None,
        instructor_id=instructor_id,
        title="Partner Router Activity",
        description="Partner execution router test.",
        instructions="Run the Python program.",
        activity_type="laboratory",
        required_ast_rules={},
        starter_code="print('starter')\n",
        paste_policy="internal_only",
        is_graded=True,
        is_published=True,
        published_at=datetime.now(timezone.utc),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def create_execution_request(
    db: Session,
) -> ExecutionRequest:
    instructor = create_user(
        db,
        name="Router Instructor",
        school_id="3000000001",
        email="router.instructor@pampangastateu.edu.ph",
        role="instructor",
    )
    student = create_user(
        db,
        name="Router Student",
        school_id="3000000002",
        email="router.student@pampangastateu.edu.ph",
        role="student",
    )
    task = create_task(
        db,
        instructor_id=instructor.user_id,
    )

    execution = ExecutionRequest(
        student_id=student.user_id,
        task_id=task.task_id,
        submission_id=None,
        coding_session_id=None,
        request_kind="run",
        status="queued",
        source_code="print('hello')\n",
        standard_input="",
        stdout="",
        stderr="",
        exit_code=None,
        execution_time_ms=None,
        limit_reason=None,
        worker_task_id=None,
        started_at=None,
        completed_at=None,
        last_partner_sequence=0,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


def partner_headers(
    token: str = VALID_PARTNER_TOKEN,
) -> dict[str, str]:
    return {PARTNER_EXECUTION_TOKEN_HEADER: token}


def build_update_payload(
    execution: ExecutionRequest,
    *,
    status_value: str,
    sequence_number: int,
    update_id: str | None = None,
    correlation_id: str | None = None,
    worker_task_id: str = "router-worker-task-1",
    stdout: str = "",
    stderr: str = "",
    exit_code: int | None = None,
    limit_reason: str | None = None,
) -> dict[str, object]:
    started_at = datetime.now(timezone.utc)

    if status_value == "completed" and exit_code is None:
        exit_code = 0

    return {
        "execution_id": execution.execution_id,
        "correlation_id": correlation_id or execution.correlation_id,
        "update_id": update_id or str(uuid4()),
        "sequence_number": sequence_number,
        "worker_task_id": worker_task_id,
        "status": status_value,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "execution_time_ms": 20,
        "limit_reason": limit_reason,
        "error_code": None,
        "error_message": None,
        "started_at": started_at.isoformat(),
        "completed_at": (
            None
            if status_value == "running"
            else (started_at + timedelta(milliseconds=20)).isoformat()
        ),
    }


def test_authenticated_partner_can_apply_running_update(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )
    execution = create_execution_request(db_session)

    response = client.post(
        "/execution/internal/partner-results",
        headers=partner_headers(),
        json=build_update_payload(
            execution,
            status_value="running",
            sequence_number=1,
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["execution_id"] == execution.execution_id
    assert body["correlation_id"] == execution.correlation_id
    assert body["status"] == "running"
    assert body["sequence_number"] == 1
    assert body["accepted"] is True
    assert body["replayed"] is False

    db_session.refresh(execution)
    assert execution.status == "running"
    assert execution.last_partner_sequence == 1
    assert execution.worker_task_id == "router-worker-task-1"


def test_identical_partner_update_returns_replay_acknowledgment(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )
    execution = create_execution_request(db_session)
    update_id = str(uuid4())
    payload = build_update_payload(
        execution,
        status_value="running",
        sequence_number=1,
        update_id=update_id,
    )

    first = client.post(
        "/execution/internal/partner-results",
        headers=partner_headers(),
        json=payload,
    )
    second = client.post(
        "/execution/internal/partner-results",
        headers=partner_headers(),
        json=payload,
    )

    assert first.status_code == 200
    assert first.json()["replayed"] is False
    assert second.status_code == 200
    assert second.json()["replayed"] is True
    assert (
        db_session.query(PartnerExecutionUpdateRecord)
        .filter(
            PartnerExecutionUpdateRecord.update_id == update_id,
        )
        .count()
        == 1
    )


def test_missing_partner_token_returns_unauthorized(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )
    execution = create_execution_request(db_session)

    response = client.post(
        "/execution/internal/partner-results",
        json=build_update_payload(
            execution,
            status_value="running",
            sequence_number=1,
        ),
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Execution-partner authentication is required.",
    }


def test_invalid_partner_token_returns_unauthorized(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )
    execution = create_execution_request(db_session)

    response = client.post(
        "/execution/internal/partner-results",
        headers=partner_headers(
            "different-partner-token-0123456789abcdefghijklmnopqrstuvwxyz"
        ),
        json=build_update_payload(
            execution,
            status_value="running",
            sequence_number=1,
        ),
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Execution-partner authentication failed.",
    }


def test_unconfigured_partner_auth_returns_service_unavailable(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        raising=False,
    )
    execution = create_execution_request(db_session)

    response = client.post(
        "/execution/internal/partner-results",
        headers=partner_headers(),
        json=build_update_payload(
            execution,
            status_value="running",
            sequence_number=1,
        ),
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": ("The execution-partner authentication boundary is not configured."),
    }


def test_partner_result_body_validation_returns_422(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )
    execution = create_execution_request(db_session)
    payload = build_update_payload(
        execution,
        status_value="completed",
        sequence_number=1,
    )
    payload["completed_at"] = None

    response = client.post(
        "/execution/internal/partner-results",
        headers=partner_headers(),
        json=payload,
    )

    assert response.status_code == 422
    assert any(
        "Terminal worker updates require completed_at" in error["msg"]
        for error in response.json()["detail"]
    )


def test_correlation_conflict_maps_to_409(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )
    execution = create_execution_request(db_session)

    response = client.post(
        "/execution/internal/partner-results",
        headers=partner_headers(),
        json=build_update_payload(
            execution,
            status_value="running",
            sequence_number=1,
            correlation_id=str(uuid4()),
        ),
    )

    assert response.status_code == 409
    assert "correlation ID does not match" in response.json()["detail"]


def test_sequence_conflict_maps_to_409(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )
    execution = create_execution_request(db_session)

    response = client.post(
        "/execution/internal/partner-results",
        headers=partner_headers(),
        json=build_update_payload(
            execution,
            status_value="running",
            sequence_number=2,
        ),
    )

    assert response.status_code == 409
    assert "Expected 1, received 2" in response.json()["detail"]


def test_conflicting_replay_maps_to_409(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )
    execution = create_execution_request(db_session)
    update_id = str(uuid4())
    first_payload = build_update_payload(
        execution,
        status_value="running",
        sequence_number=1,
        update_id=update_id,
    )
    second_payload = {
        **first_payload,
        "stdout": "different replay content",
    }

    first = client.post(
        "/execution/internal/partner-results",
        headers=partner_headers(),
        json=first_payload,
    )
    second = client.post(
        "/execution/internal/partner-results",
        headers=partner_headers(),
        json=second_payload,
    )

    assert first.status_code == 200
    assert second.status_code == 409
    assert "already used for different content" in second.json()["detail"]


def test_terminal_execution_rejects_later_update(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )
    execution = create_execution_request(db_session)

    completed = client.post(
        "/execution/internal/partner-results",
        headers=partner_headers(),
        json=build_update_payload(
            execution,
            status_value="completed",
            sequence_number=1,
        ),
    )
    later_update = client.post(
        "/execution/internal/partner-results",
        headers=partner_headers(),
        json=build_update_payload(
            execution,
            status_value="failed",
            sequence_number=2,
        ),
    )

    assert completed.status_code == 200
    assert later_update.status_code == 409
    assert "terminal execution request" in later_update.json()["detail"]


def test_unknown_execution_maps_to_404(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )

    response = client.post(
        "/execution/internal/partner-results",
        headers=partner_headers(),
        json={
            "execution_id": str(uuid4()),
            "correlation_id": str(uuid4()),
            "update_id": str(uuid4()),
            "sequence_number": 1,
            "worker_task_id": "missing-worker-task",
            "status": "running",
            "stdout": "",
            "stderr": "",
            "exit_code": None,
            "execution_time_ms": 1,
            "limit_reason": None,
            "error_code": None,
            "error_message": None,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Execution request not found.",
    }


def test_partner_endpoint_openapi_requires_partner_security(
    client: TestClient,
):
    document = client.get("/openapi.json").json()
    operation = document["paths"]["/execution/internal/partner-results"]["post"]

    assert {
        "PartnerExecutionToken": [],
    } in operation["security"]
    assert operation["operationId"] == ("apply_partner_execution_result_update")

    for expected_status in (
        "200",
        "400",
        "401",
        "404",
        "409",
        "422",
        "500",
        "503",
    ):
        assert expected_status in operation["responses"]


def test_partner_endpoint_is_post_only(
    client: TestClient,
):
    document = client.get("/openapi.json").json()
    path_item = document["paths"]["/execution/internal/partner-results"]

    assert set(path_item).intersection({"get", "post", "put", "patch", "delete"}) == {
        "post"
    }


def test_partner_secret_is_not_exposed_by_route_or_openapi(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )

    document_text = client.get("/openapi.json").text
    assert VALID_PARTNER_TOKEN not in document_text
    assert PARTNER_EXECUTION_TOKEN_ENV not in document_text

    document = client.get("/openapi.json").json()
    request_schema = document["paths"]["/execution/internal/partner-results"]["post"][
        "requestBody"
    ]["content"]["application/json"]["schema"]
    schema_name = request_schema["$ref"].split("/")[-1]
    properties = document["components"]["schemas"][schema_name]["properties"]

    assert {
        "token",
        "partner_token",
        "api_key",
        "shared_secret",
        "jwt",
        "access_token",
    }.isdisjoint(properties)
