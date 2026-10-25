"""The SMTP adapter that emails password-reset codes (QA STU-01)."""

import email
import logging
import re

import pytest
from app.core.security import get_password_hash
from app.integrations import otp_delivery
from app.integrations.otp_delivery import (SMTPEmailAdapter,
                                           UnavailableOTPDeliveryAdapter,
                                           get_otp_delivery_adapter)
from app.integrations.otp_email import OTPEmailAdapterRejectedError
from app.models.domain_models import User

DOMAIN = "@pampangastateu.edu.ph"


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout):
        self.host, self.port, self.timeout = host, port, timeout
        self.calls = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.calls.append("starttls")

    def login(self, user, password):
        self.calls.append(("login", user))

    def sendmail(self, sender, recipients, data):
        self.calls.append(("sendmail", sender, recipients))
        self.data = data


@pytest.fixture
def smtp(monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr(otp_delivery.smtplib, "SMTP", FakeSMTP)
    # Not set on purpose: the host defaults to Brevo's relay, as for the
    # account-setup email.
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_USER", "relay-user@smtp-brevo.com")
    monkeypatch.setenv("SMTP_PASS", "relay-key")
    monkeypatch.delenv("SMTP_SENDER_EMAIL", raising=False)
    monkeypatch.delenv("SMTP_SENDER_NAME", raising=False)
    return FakeSMTP


def send(adapter):
    adapter.send_otp(
        recipient_email=f"2023304134{DOMAIN}",
        otp_code="123456",
        purpose="password_reset",
        expires_in_seconds=600,
    )


def test_code_is_sent_from_the_university_sender_not_the_relay_login(smtp):
    send(SMTPEmailAdapter())

    (server,) = smtp.instances
    assert (server.host, server.port, server.timeout) == ("smtp-relay.brevo.com", 2525, 15)
    assert server.calls == [
        "starttls",
        ("login", "relay-user@smtp-brevo.com"),
        ("sendmail", f"noreply{DOMAIN}", [f"2023304134{DOMAIN}"]),
    ]
    message = email.message_from_string(server.data)
    assert message["From"] == f"PSU Python IDE <noreply{DOMAIN}>"
    assert message["Date"]
    assert message["Message-ID"].endswith("@pampangastateu.edu.ph>")


def test_configured_sender_is_used(smtp, monkeypatch):
    monkeypatch.setenv("SMTP_SENDER_EMAIL", f"mis{DOMAIN}")
    send(SMTPEmailAdapter())

    (server,) = smtp.instances
    assert server.calls[-1] == ("sendmail", f"mis{DOMAIN}", [f"2023304134{DOMAIN}"])


def test_failure_names_the_smtp_error_without_its_text(smtp, monkeypatch):
    def refuse(self, sender, recipients, data):
        raise otp_delivery.smtplib.SMTPSenderRefused(550, b"2023304134 not allowed", sender)

    monkeypatch.setattr(FakeSMTP, "sendmail", refuse)
    with pytest.raises(OTPEmailAdapterRejectedError) as raised:
        send(SMTPEmailAdapter())

    assert str(raised.value) == "SMTP delivery failed (SMTPSenderRefused 550)."
    assert raised.value.__cause__ is None


def test_login_and_key_are_enough_to_send(smtp, monkeypatch):
    assert isinstance(get_otp_delivery_adapter(), SMTPEmailAdapter)

    monkeypatch.setenv("SMTP_PASS", "")
    assert isinstance(get_otp_delivery_adapter(), UnavailableOTPDeliveryAdapter)


# ------------------------------------------------------- through the API


@pytest.fixture
def student(db_session):
    user = User(
        name="Reset Student",
        email=f"2023304134{DOMAIN}",
        role="student",
        school_id="2023304134",
        password_hash=get_password_hash("Original#2026"),
        email_verified=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_reset_code_is_emailed_and_completes_the_reset(client, smtp, student, caplog):
    with caplog.at_level(logging.INFO, logger="app.services.otp_service"):
        started = client.post("/users/password-reset/start", json={"email": f"2023304134{DOMAIN}"})

    assert started.status_code == 201
    (server,) = smtp.instances
    assert server.host == "smtp-relay.brevo.com"
    assert server.calls[-1] == ("sendmail", f"noreply{DOMAIN}", [f"2023304134{DOMAIN}"])
    assert f"Password reset code to 2***{DOMAIN} accepted by the mail relay." in caplog.text

    text_part = email.message_from_string(server.data).get_payload()[0].get_payload()
    code = re.search(r"\b\d{6}\b", text_part).group(0)
    assert code not in caplog.text

    completed = client.post(
        "/users/password-reset/complete",
        json={"challenge_id": started.json()["challenge_id"], "otp_code": code, "new_password": "Changed#2026"},
    )
    assert completed.status_code == 200


def test_reset_for_an_unknown_email_sends_nothing_and_says_so_in_the_log(client, smtp, caplog):
    with caplog.at_level(logging.INFO, logger="app.services.otp_service"):
        started = client.post("/users/password-reset/start", json={"email": f"nobody.here{DOMAIN}"})

    assert started.status_code == 201
    assert smtp.instances == []
    assert f"Password reset requested for n***{DOMAIN}, which no account uses; no code sent." in caplog.text


def test_refused_reset_email_is_logged_with_the_smtp_code(client, smtp, student, monkeypatch, caplog):
    def refuse(self, sender, recipients, data):
        raise otp_delivery.smtplib.SMTPSenderRefused(550, b"sender not valid", sender)

    monkeypatch.setattr(FakeSMTP, "sendmail", refuse)
    with caplog.at_level(logging.INFO, logger="app.services.otp_service"):
        started = client.post("/users/password-reset/start", json={"email": f"2023304134{DOMAIN}"})

    assert started.status_code == 201
    assert "SMTP delivery failed (SMTPSenderRefused 550)." in caplog.text
    assert f"Password reset code to 2***{DOMAIN} was not sent." in caplog.text
    assert "2023304134" not in caplog.text and "not valid" not in caplog.text


def test_app_info_logs_have_a_handler():
    import app.main  # noqa: F401  (configures logging)
    from app.core.config import get_settings

    app_logger = logging.getLogger("app")
    assert app_logger.level == logging.getLevelName(get_settings().log_level)
    assert any(getattr(handler, "_pamsu_app_handler", False) for handler in app_logger.handlers)
