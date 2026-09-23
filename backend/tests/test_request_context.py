import io
import json
import logging
from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.request_context import (
    REQUEST_LOGGER_NAME,
    PrivacySafeJsonFormatter,
    RequestContextMiddleware,
    configure_request_logging,
    get_current_correlation_id,
)


CORRELATION_ID_HEADER = "X-Correlation-ID"


def _build_test_logger(
    output: io.StringIO,
) -> logging.Logger:
    logger = logging.getLogger("pamsu.test.request_context")

    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(output)
    handler.setLevel(logging.INFO)
    handler.setFormatter(PrivacySafeJsonFormatter())

    logger.addHandler(handler)

    return logger


def _build_test_app(
    *,
    logger: logging.Logger,
) -> FastAPI:
    application = FastAPI()

    application.add_middleware(
        RequestContextMiddleware,
        correlation_id_header=(CORRELATION_ID_HEADER),
        logger=logger,
    )

    @application.get(
        "/context",
    )
    def read_context(
        request: Request,
    ) -> dict[str, str | None]:
        return {
            "request_state_correlation_id": (request.state.correlation_id),
            "context_variable_correlation_id": (get_current_correlation_id()),
        }

    @application.post(
        "/privacy-check",
    )
    def privacy_check() -> dict[str, str]:
        return {
            "status": "accepted",
        }

    @application.get(
        "/failure",
    )
    def failure() -> None:
        raise RuntimeError("private-internal-exception-message")

    return application


@pytest.fixture()
def log_output() -> io.StringIO:
    return io.StringIO()


@pytest.fixture()
def test_logger(
    log_output: io.StringIO,
) -> Generator[logging.Logger, None, None]:
    logger = _build_test_logger(log_output)

    yield logger

    logger.handlers.clear()


@pytest.fixture()
def app(
    test_logger: logging.Logger,
) -> FastAPI:
    return _build_test_app(logger=test_logger)


@pytest.fixture()
def client(
    app: FastAPI,
) -> Generator[TestClient, None, None]:
    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as test_client:
        yield test_client


def _read_log_events(
    output: io.StringIO,
) -> list[dict[str, object]]:
    lines = [line.strip() for line in output.getvalue().splitlines() if line.strip()]

    events = []

    for line in lines:
        parsed = json.loads(line)

        assert isinstance(
            parsed,
            dict,
        )

        events.append(parsed)

    return events


def test_valid_client_correlation_id_is_preserved(
    client: TestClient,
    log_output: io.StringIO,
) -> None:
    supplied_correlation_id = str(uuid4())

    response = client.get(
        "/context",
        headers={
            CORRELATION_ID_HEADER: (supplied_correlation_id),
        },
    )

    assert response.status_code == 200

    assert response.headers[CORRELATION_ID_HEADER] == supplied_correlation_id

    assert response.json() == {
        "request_state_correlation_id": (supplied_correlation_id),
        "context_variable_correlation_id": (supplied_correlation_id),
    }

    events = _read_log_events(log_output)

    assert len(events) == 1
    assert events[0]["event"] == ("http_request_completed")
    assert events[0]["correlation_id"] == (supplied_correlation_id)
    assert events[0]["method"] == "GET"
    assert events[0]["path"] == "/context"
    assert events[0]["status_code"] == 200


@pytest.mark.parametrize(
    "invalid_value",
    [
        "",
        "not-a-uuid",
        "12345",
        "private-client-value",
    ],
)
def test_invalid_client_correlation_id_is_replaced(
    client: TestClient,
    invalid_value: str,
) -> None:
    response = client.get(
        "/context",
        headers={
            CORRELATION_ID_HEADER: invalid_value,
        },
    )

    assert response.status_code == 200

    generated_correlation_id = response.headers[CORRELATION_ID_HEADER]

    parsed_correlation_id = UUID(generated_correlation_id)

    assert str(parsed_correlation_id) == generated_correlation_id

    assert generated_correlation_id != (invalid_value)

    assert response.json() == {
        "request_state_correlation_id": (generated_correlation_id),
        "context_variable_correlation_id": (generated_correlation_id),
    }


def test_missing_correlation_id_generates_unique_request_values(
    client: TestClient,
) -> None:
    first_response = client.get("/context")
    second_response = client.get("/context")

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_correlation_id = first_response.headers[CORRELATION_ID_HEADER]
    second_correlation_id = second_response.headers[CORRELATION_ID_HEADER]

    UUID(first_correlation_id)
    UUID(second_correlation_id)

    assert first_correlation_id != (second_correlation_id)

    assert get_current_correlation_id() is None


def test_completed_request_log_excludes_sensitive_request_data(
    client: TestClient,
    log_output: io.StringIO,
) -> None:
    supplied_correlation_id = str(uuid4())

    secret_query_value = "private-query-secret"
    authorization_value = "Bearer private-jwt-value"
    partner_token_value = "private-partner-token"
    request_body_value = "private-source-code-value"

    response = client.post(
        (f"/privacy-check?token={secret_query_value}"),
        headers={
            CORRELATION_ID_HEADER: (supplied_correlation_id),
            "Authorization": (authorization_value),
            "X-Partner-Token": (partner_token_value),
        },
        json={
            "source_code": (request_body_value),
        },
    )

    assert response.status_code == 200

    events = _read_log_events(log_output)

    assert len(events) == 1

    event = events[0]

    assert set(event) == {
        "timestamp",
        "level",
        "event",
        "correlation_id",
        "method",
        "path",
        "status_code",
        "duration_ms",
    }

    assert event["event"] == ("http_request_completed")
    assert event["correlation_id"] == (supplied_correlation_id)
    assert event["method"] == "POST"
    assert event["path"] == ("/privacy-check")
    assert event["status_code"] == 200

    serialized_logs = log_output.getvalue()

    prohibited_values = {
        secret_query_value,
        authorization_value,
        partner_token_value,
        request_body_value,
        "source_code",
        "Authorization",
        "X-Partner-Token",
    }

    for prohibited_value in prohibited_values:
        assert prohibited_value not in (serialized_logs)


def test_failed_request_log_excludes_exception_details(
    client: TestClient,
    log_output: io.StringIO,
) -> None:
    response = client.get("/failure")

    assert response.status_code == 500

    events = _read_log_events(log_output)

    assert len(events) == 1

    event = events[0]

    assert event["event"] == ("http_request_failed")
    assert event["method"] == "GET"
    assert event["path"] == "/failure"
    assert event["status_code"] == 500

    UUID(str(event["correlation_id"]))

    serialized_logs = log_output.getvalue()

    assert "private-internal-exception-message" not in serialized_logs
    assert "RuntimeError" not in serialized_logs
    assert "traceback" not in serialized_logs.lower()


def test_custom_correlation_header_is_supported(
    log_output: io.StringIO,
) -> None:
    custom_header = "X-PAMSU-Request-ID"
    supplied_correlation_id = str(uuid4())

    logger = _build_test_logger(log_output)

    application = FastAPI()

    application.add_middleware(
        RequestContextMiddleware,
        correlation_id_header=custom_header,
        logger=logger,
    )

    @application.get(
        "/custom",
    )
    def custom_context(
        request: Request,
    ) -> dict[str, str]:
        return {
            "correlation_id": (request.state.correlation_id),
        }

    with TestClient(application) as custom_client:
        response = custom_client.get(
            "/custom",
            headers={
                custom_header: (supplied_correlation_id),
            },
        )

    assert response.status_code == 200
    assert response.headers[custom_header] == supplied_correlation_id
    assert response.json() == {
        "correlation_id": (supplied_correlation_id),
    }


def test_configure_request_logging_does_not_duplicate_handlers() -> None:
    logger = logging.getLogger(REQUEST_LOGGER_NAME)

    original_handlers = list(logger.handlers)
    original_level = logger.level
    original_propagate = logger.propagate

    try:
        logger.handlers.clear()

        first_logger = configure_request_logging(log_level="INFO")
        second_logger = configure_request_logging(log_level="DEBUG")

        privacy_safe_handlers = [
            handler
            for handler in logger.handlers
            if getattr(
                handler,
                "_pamsu_privacy_safe_handler",
                False,
            )
        ]

        assert first_logger is logger
        assert second_logger is logger
        assert len(privacy_safe_handlers) == 1
        assert logger.level == logging.DEBUG
        assert privacy_safe_handlers[0].level == logging.DEBUG
        assert isinstance(
            privacy_safe_handlers[0].formatter,
            PrivacySafeJsonFormatter,
        )

    finally:
        logger.handlers.clear()

        for handler in original_handlers:
            logger.addHandler(handler)

        logger.setLevel(original_level)
        logger.propagate = original_propagate
