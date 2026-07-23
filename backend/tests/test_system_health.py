import os
from collections.abc import Generator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError


os.environ.setdefault(
    "DATABASE_URL",
    "sqlite:///./test_system_health_bootstrap.db",
)
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-jwt-secret-key-with-at-least-thirty-two-characters",
)
os.environ.setdefault(
    "OTP_SECRET_KEY",
    "test-otp-secret-key-with-at-least-thirty-two-characters",
)
os.environ.setdefault(
    "PAMSU_PARTNER_EXECUTION_TOKEN",
    ("test-partner-execution-token-0123456789abcdefghijklmnopqrstuvwxyz"),
)


from app.core.database import get_db
from app.integrations.partner_auth import (
    PARTNER_EXECUTION_TOKEN_ENV,
)
from app.main import (
    APP_TITLE,
    APP_VERSION,
    app,
)


VALID_PARTNER_TOKEN = (
    "test-partner-execution-token-0123456789abcdefghijklmnopqrstuvwxyz"
)


class ReadyDatabaseSession:
    def __init__(self) -> None:
        self.execute_calls = 0
        self.rollback_calls = 0

    def execute(self, _statement):
        self.execute_calls += 1
        return object()

    def rollback(self) -> None:
        self.rollback_calls += 1


class UnavailableDatabaseSession:
    def __init__(self) -> None:
        self.execute_calls = 0
        self.rollback_calls = 0

    def execute(self, _statement):
        self.execute_calls += 1
        raise SQLAlchemyError("Simulated database connection failure.")

    def rollback(self) -> None:
        self.rollback_calls += 1


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def override_database(
    database_session: object,
) -> None:
    def override_get_db() -> Generator[object, None, None]:
        yield database_session

    app.dependency_overrides[get_db] = override_get_db


def parse_response_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def component_map(
    response_body: dict[str, object],
) -> dict[str, dict[str, object]]:
    components = response_body["components"]

    assert isinstance(components, list)

    return {str(component["name"]): component for component in components}


def test_root_reports_pillar_15_service_links(
    client: TestClient,
):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": f"{APP_TITLE} is running.",
        "version": "1.0.0-rc1",
        "documentation": "/docs",
        "health": "/health",
        "readiness": "/ready",
    }
    assert APP_VERSION == "1.0.0-rc1"


def test_health_reports_process_liveness(
    client: TestClient,
):
    response = client.get("/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "healthy"
    assert body["service"] == APP_TITLE
    assert body["version"] == "1.0.0-rc1"

    checked_at = parse_response_datetime(body["checked_at"])

    assert checked_at.utcoffset() is not None


def test_health_does_not_require_database_or_partner_configuration(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        raising=False,
    )
    unavailable_database = UnavailableDatabaseSession()
    override_database(unavailable_database)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert unavailable_database.execute_calls == 0
    assert unavailable_database.rollback_calls == 0


def test_ready_returns_200_when_required_components_are_ready(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )
    ready_database = ReadyDatabaseSession()
    override_database(ready_database)

    response = client.get("/ready")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ready"
    assert body["service"] == APP_TITLE
    assert body["version"] == "1.0.0-rc1"

    checked_at = parse_response_datetime(body["checked_at"])
    assert checked_at.utcoffset() is not None

    components = component_map(body)

    assert components["database"] == {
        "name": "database",
        "status": "ready",
        "required": True,
        "detail": "The database connection is available.",
    }
    assert components["execution_partner_auth"] == {
        "name": "execution_partner_auth",
        "status": "ready",
        "required": True,
        "detail": ("The execution-partner authentication boundary is configured."),
    }
    assert components["otp_email_adapter"]["status"] == ("contract_only")
    assert components["otp_email_adapter"]["required"] is False
    assert components["local_llm_adapter"]["status"] == ("contract_only")
    assert components["local_llm_adapter"]["required"] is False

    assert ready_database.execute_calls == 1
    assert ready_database.rollback_calls == 0


def test_ready_returns_503_when_partner_auth_is_missing(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        raising=False,
    )
    ready_database = ReadyDatabaseSession()
    override_database(ready_database)

    response = client.get("/ready")

    assert response.status_code == 503

    body = response.json()
    components = component_map(body)

    assert body["status"] == "not_ready"
    assert components["database"]["status"] == "ready"
    assert components["execution_partner_auth"] == {
        "name": "execution_partner_auth",
        "status": "not_ready",
        "required": True,
        "detail": ("The execution-partner authentication boundary is not configured."),
    }


def test_ready_returns_503_when_partner_auth_is_too_short(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        "too-short",
    )
    ready_database = ReadyDatabaseSession()
    override_database(ready_database)

    response = client.get("/ready")

    assert response.status_code == 503

    components = component_map(response.json())

    assert components["execution_partner_auth"]["status"] == ("not_ready")


def test_ready_returns_503_when_database_is_unavailable(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )
    unavailable_database = UnavailableDatabaseSession()
    override_database(unavailable_database)

    response = client.get("/ready")

    assert response.status_code == 503

    body = response.json()
    components = component_map(body)

    assert body["status"] == "not_ready"
    assert components["database"] == {
        "name": "database",
        "status": "not_ready",
        "required": True,
        "detail": "The database connection is unavailable.",
    }
    assert components["execution_partner_auth"]["status"] == ("ready")
    assert unavailable_database.execute_calls == 1
    assert unavailable_database.rollback_calls == 1


def test_contract_only_components_do_not_block_readiness(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )
    override_database(ReadyDatabaseSession())

    response = client.get("/ready")

    assert response.status_code == 200

    components = component_map(response.json())

    assert components["otp_email_adapter"]["required"] is False
    assert components["otp_email_adapter"]["status"] == ("contract_only")
    assert components["local_llm_adapter"]["required"] is False
    assert components["local_llm_adapter"]["status"] == ("contract_only")


def test_health_and_readiness_responses_exclude_secrets(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )
    override_database(ReadyDatabaseSession())

    health_text = client.get("/health").text
    readiness_text = client.get("/ready").text

    prohibited_values = {
        VALID_PARTNER_TOKEN,
        PARTNER_EXECUTION_TOKEN_ENV,
        "DATABASE_URL",
        "JWT_SECRET_KEY",
        "OTP_SECRET_KEY",
        "sqlite:///./test_system_health_bootstrap.db",
    }

    for prohibited_value in prohibited_values:
        assert prohibited_value not in health_text
        assert prohibited_value not in readiness_text


def test_openapi_documents_health_and_readiness_contracts(
    client: TestClient,
):
    document = client.get("/openapi.json").json()

    assert document["info"]["version"] == "1.0.0-rc1"
    assert "/health" in document["paths"]
    assert "/ready" in document["paths"]

    health_operation = document["paths"]["/health"]["get"]
    readiness_operation = document["paths"]["/ready"]["get"]

    assert health_operation["summary"] == ("Check application liveness")
    assert readiness_operation["summary"] == ("Check required integration readiness")

    assert "200" in health_operation["responses"]
    assert "200" in readiness_operation["responses"]
    assert "503" in readiness_operation["responses"]


def test_openapi_excludes_secret_configuration_values(
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
    assert "JWT_SECRET_KEY" not in document_text
    assert "OTP_SECRET_KEY" not in document_text
    assert "DATABASE_URL" not in document_text
