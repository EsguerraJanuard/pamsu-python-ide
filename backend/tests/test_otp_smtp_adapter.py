"""The SMTP adapter that emails password-reset codes (QA STU-01)."""

import email

import pytest
from app.integrations import otp_delivery
from app.integrations.otp_delivery import SMTPEmailAdapter
from app.integrations.otp_email import OTPEmailAdapterRejectedError

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
    monkeypatch.setenv("SMTP_HOST", "smtp-relay.brevo.com")
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
