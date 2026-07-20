from collections.abc import Generator

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.integrations.partner_auth import (
    MIN_PARTNER_EXECUTION_TOKEN_LENGTH,
    PARTNER_EXECUTION_TOKEN_ENV,
    PARTNER_EXECUTION_TOKEN_HEADER,
    get_authenticated_execution_partner,
)


VALID_PARTNER_TOKEN = "development-partner-token-0123456789abcdefghijklmnopqrstuvwxyz"


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app = FastAPI()

    @app.get(
        "/internal/partner-check",
        operation_id="check_execution_partner",
    )
    def partner_check(
        partner_identity: str = Depends(
            get_authenticated_execution_partner,
        ),
    ) -> dict[str, str]:
        return {
            "partner_identity": partner_identity,
        }

    with TestClient(app) as test_client:
        yield test_client


def test_valid_partner_token_is_authenticated(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )

    response = client.get(
        "/internal/partner-check",
        headers={
            PARTNER_EXECUTION_TOKEN_HEADER: VALID_PARTNER_TOKEN,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "partner_identity": "isolated_execution_worker",
    }


def test_partner_token_comparison_accepts_trimmed_header_value(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        f"  {VALID_PARTNER_TOKEN}  ",
    )

    response = client.get(
        "/internal/partner-check",
        headers={
            PARTNER_EXECUTION_TOKEN_HEADER: (f"  {VALID_PARTNER_TOKEN}  "),
        },
    )

    assert response.status_code == 200


def test_missing_partner_configuration_returns_service_unavailable(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        raising=False,
    )

    response = client.get(
        "/internal/partner-check",
        headers={
            PARTNER_EXECUTION_TOKEN_HEADER: VALID_PARTNER_TOKEN,
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": ("The execution-partner authentication boundary is not configured."),
    }


def test_short_partner_configuration_returns_service_unavailable(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        "too-short",
    )

    response = client.get(
        "/internal/partner-check",
        headers={
            PARTNER_EXECUTION_TOKEN_HEADER: "too-short",
        },
    )

    assert response.status_code == 503
    assert len("too-short") < MIN_PARTNER_EXECUTION_TOKEN_LENGTH


def test_missing_partner_header_returns_unauthorized(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )

    response = client.get(
        "/internal/partner-check",
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Execution-partner authentication is required.",
    }
    assert response.headers["www-authenticate"] == "PartnerExecutionToken"


def test_invalid_partner_token_returns_unauthorized(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )

    response = client.get(
        "/internal/partner-check",
        headers={
            PARTNER_EXECUTION_TOKEN_HEADER: (
                "different-partner-token-0123456789abcdefghijklmnopqrstuvwxyz"
            ),
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Execution-partner authentication failed.",
    }
    assert response.headers["www-authenticate"] == "PartnerExecutionToken"


def test_query_parameter_cannot_replace_partner_header(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )

    response = client.get(
        "/internal/partner-check",
        params={
            "partner_token": VALID_PARTNER_TOKEN,
        },
    )

    assert response.status_code == 401


def test_partner_secret_is_not_returned_in_error_response(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )

    response = client.get(
        "/internal/partner-check",
        headers={
            PARTNER_EXECUTION_TOKEN_HEADER: (
                "invalid-partner-token-0123456789abcdefghijklmnopqrstuvwxyz"
            ),
        },
    )

    response_text = response.text

    assert VALID_PARTNER_TOKEN not in response_text
    assert PARTNER_EXECUTION_TOKEN_ENV not in response_text


def test_openapi_declares_partner_api_key_header(
    client: TestClient,
):
    document = client.get("/openapi.json").json()

    security_scheme = document["components"]["securitySchemes"]["PartnerExecutionToken"]

    assert security_scheme["type"] == "apiKey"
    assert security_scheme["in"] == "header"
    assert security_scheme["name"] == PARTNER_EXECUTION_TOKEN_HEADER

    operation = document["paths"]["/internal/partner-check"]["get"]

    assert {
        "PartnerExecutionToken": [],
    } in operation["security"]


def test_openapi_does_not_expose_configured_partner_secret(
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
