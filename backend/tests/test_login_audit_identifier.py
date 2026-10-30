"""
Failed-login audit records never keep what was typed into the email field
unless it is a well-formed university email: anything else may be a
password entered in the wrong field.
"""

import json
import logging

import pytest
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.domain_models import AuditRecord, User
from app.routers import auth as auth_router
from app.routers.auth import (UNRECOGNIZED_LOGIN_IDENTIFIER,
                              recordable_login_identifier)

DOMAIN = "@pampangastateu.edu.ph"
TYPED_PASSWORD = "Hunter2-secret-pass"


def failed_login_records(db: Session) -> list[AuditRecord]:
    db.expire_all()
    return (
        db.query(AuditRecord)
        .filter(AuditRecord.action_type == "login_failed")
        .order_by(AuditRecord.audit_id)
        .all()
    )


def stored_text(record: AuditRecord) -> str:
    return " ".join(
        (record.audit_key, record.resource_id, json.dumps(record.audit_data))
    ).lower()


@pytest.mark.parametrize(
    "typed",
    [
        TYPED_PASSWORD,
        "   " + TYPED_PASSWORD + "   ",
        f"{TYPED_PASSWORD}@gmail.com",
        f"two words{DOMAIN}",
        f"a@b{DOMAIN}",
        f"{'x' * 100}{DOMAIN}",
        DOMAIN,
    ],
    ids=["password", "padded", "other-domain", "space", "extra-at", "too-long", "domain-only"],
)
def test_unrecognized_identifier_is_not_stored(client, db_session, typed):
    response = client.post("/login", data={"username": typed, "password": "x"})

    assert response.status_code == 401
    (record,) = failed_login_records(db_session)
    assert record.actor_user_id is None
    assert record.resource_id == UNRECOGNIZED_LOGIN_IDENTIFIER
    assert record.audit_data == {"identifier": UNRECOGNIZED_LOGIN_IDENTIFIER}

    typed_core = typed.strip().lower().removesuffix(DOMAIN)
    if typed_core:
        assert typed_core not in stored_text(record)


def test_unknown_university_email_is_still_recorded(client, db_session):
    email = f"no.such.student{DOMAIN}"

    response = client.post("/login", data={"username": f"  NO.SUCH.STUDENT{DOMAIN.upper()} ", "password": "x"})

    assert response.status_code == 401
    (record,) = failed_login_records(db_session)
    assert record.actor_user_id is None
    assert record.resource_id == email
    assert record.audit_data == {"email": email}


def test_wrong_password_for_existing_account_is_recorded_against_it(client, db_session):
    user = User(
        name="Stu Dent",
        email=f"stu.dent{DOMAIN}",
        role="student",
        school_id="2026000001",
        password_hash=get_password_hash("Correct#2026"),
        email_verified=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post("/login", data={"username": user.email, "password": TYPED_PASSWORD})

    assert response.status_code == 401
    (record,) = failed_login_records(db_session)
    assert record.actor_user_id == user.user_id
    assert record.resource_id == str(user.user_id)
    assert record.audit_data == {"email": user.email}
    assert TYPED_PASSWORD.lower() not in stored_text(record)


def test_audit_failure_logs_no_input(client, db_session, monkeypatch, caplog):
    def failing_create_audit_record(**kwargs):
        # Stands in for errors whose text echoes the payload, such as
        # pydantic's input_value or SQL parameters.
        raise ValueError(f"rejected {kwargs['payload']!r}")

    monkeypatch.setattr(auth_router, "create_audit_record", failing_create_audit_record)
    email = f"no.such.student{DOMAIN}"

    with caplog.at_level(logging.DEBUG):
        response = client.post("/login", data={"username": email, "password": TYPED_PASSWORD})

    assert response.status_code == 401
    logged = "\n".join(
        record.getMessage() + (logging.Formatter().formatException(record.exc_info) if record.exc_info else "")
        for record in caplog.records
    )
    assert "Could not record a failed login attempt (ValueError)." in logged
    assert email not in logged
    assert TYPED_PASSWORD not in logged


@pytest.mark.parametrize(
    ("normalized", "expected"),
    [
        (f"stu.dent{DOMAIN}", f"stu.dent{DOMAIN}"),
        (f"a{DOMAIN}", f"a{DOMAIN}"),
        (f"{'x' * (100 - len(DOMAIN))}{DOMAIN}", f"{'x' * (100 - len(DOMAIN))}{DOMAIN}"),
        (f"{'x' * (101 - len(DOMAIN))}{DOMAIN}", None),
        (DOMAIN, None),
        (f"a@b{DOMAIN}", None),
        (f"a\tb{DOMAIN}", None),
        ("stu.dent@gmail.com", None),
        ("hunter2", None),
        ("", None),
    ],
)
def test_recordable_login_identifier(normalized, expected):
    assert recordable_login_identifier(normalized) == expected
