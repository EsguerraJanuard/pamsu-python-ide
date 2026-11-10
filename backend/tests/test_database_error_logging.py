"""
Unhandled database errors are logged without their message.

hide_parameters (test_database_logging.py) removes the statement's bound
parameters, but PostgreSQL's own error text can still carry row values,
for example "DETAIL: Failing row contains (...)". These tests use a
psycopg-shaped error with a canary value in that text.
"""

import logging
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from app.core.database_errors import (database_error_summary,
                                      handle_unhandled_database_error)
from app.main import app

CANARY = "$2b$08$leak-canary-row-value"
TEST_PATH = "/__test__/database-error"


class FakeCheckViolation(Exception):
    """Shaped like psycopg2.errors.CheckViolation."""

    pgcode = "23514"

    def __init__(self, constraint_name: str = "ck_users_role"):
        super().__init__(
            'new row for relation "users" violates check constraint '
            f'"{constraint_name}"\nDETAIL:  Failing row contains (7, {CANARY}, student).'
        )
        self.diag = SimpleNamespace(constraint_name=constraint_name)


def canary_error() -> IntegrityError:
    return IntegrityError(
        "UPDATE users SET password_hash=%(password_hash)s",
        {"password_hash": CANARY},
        FakeCheckViolation(),
        hide_parameters=True,
    )


def logged_text(caplog) -> str:
    return "\n".join(
        record.getMessage()
        + (logging.Formatter().formatException(record.exc_info) if record.exc_info else "")
        for record in caplog.records
    )


@pytest.fixture
def failing_route():
    def raise_database_error():
        raise canary_error()

    app.add_api_route(TEST_PATH, raise_database_error, methods=["GET"])
    try:
        yield TEST_PATH
    finally:
        app.router.routes[:] = [
            route for route in app.router.routes if getattr(route, "path", None) != TEST_PATH
        ]


def test_canary_is_in_the_raw_error_text():
    # Control: proves the assertions below are meaningful.
    assert CANARY in str(canary_error())


def test_summary_keeps_only_classes_sqlstate_and_constraint():
    summary = database_error_summary(canary_error())

    assert summary == "IntegrityError FakeCheckViolation sqlstate=23514 constraint=ck_users_role"
    assert CANARY not in summary


def test_summary_drops_unsafe_constraint_names_and_handles_plain_errors():
    error = IntegrityError("stmt", None, FakeCheckViolation(constraint_name=f"x) ({CANARY}"))

    assert database_error_summary(error) == "IntegrityError FakeCheckViolation sqlstate=23514"
    assert database_error_summary(ValueError(CANARY)) == "ValueError"
    assert database_error_summary(OperationalError("stmt", None, Exception(CANARY))) == "OperationalError Exception"


def test_application_registers_the_handler():
    assert app.exception_handlers[SQLAlchemyError] is handle_unhandled_database_error


def test_unhandled_database_error_returns_500_and_logs_no_values(failing_route, caplog):
    # raise_server_exceptions=True: if the error escaped to the server's
    # default handler (which logs the full traceback), this call would raise.
    with TestClient(app, raise_server_exceptions=True) as client, caplog.at_level(logging.DEBUG):
        response = client.get(failing_route)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error."}
    assert CANARY not in response.text

    logged = logged_text(caplog)
    assert (
        f"Unhandled database error on GET {TEST_PATH} "
        "(IntegrityError FakeCheckViolation sqlstate=23514 constraint=ck_users_role; correlation_id="
    ) in logged
    assert CANARY not in logged
