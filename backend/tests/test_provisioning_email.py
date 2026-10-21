"""Account-provisioning email (2026-10-21): wiring, content and delivery.

- POST /admin/students now queues the welcome email (it sent none before);
  POST /admin/instructors passes the last name and account ID.
- The email: PSU gold header with the logo as an inline (Content-ID) image,
  white body, gold footer; tables and inline styles only; a plain-text part.
"""

import logging
import re

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import User
from app.services import email_service
from app.services.email_service import (LOGO_CID, build_provisioning_message, greeting_name,
                                        send_provisioning_email)

DOMAIN = "@pampangastateu.edu.ph"
SENDER = {"sender_name": "PSU Python IDE", "sender_email": f"noreply{DOMAIN}"}


def build(**overrides):
    values = dict(
        recipient_email=f"juan.delacruz{DOMAIN}",
        first_name="Juan",
        last_name="Dela Cruz",
        school_id="2026000101",
        temp_password="R3Fce-aFFdr!",
        role="Student",
        **SENDER,
    )
    values.update(overrides)
    return build_provisioning_message(**values)


def parts(message):
    found = {}
    for part in message.walk():
        kind = part.get_content_type()
        if kind in ("text/plain", "text/html"):
            found[kind] = part.get_payload(decode=True).decode("utf-8")
        elif kind == "image/png":
            found[kind] = part
    return found


# ------------------------------------------------------------------ content


def test_message_structure_embeds_the_logo_inline():
    message = build()
    found = parts(message)

    assert message.get_content_type() == "multipart/related"
    assert [p.get_content_type() for p in message.walk()] == [
        "multipart/related", "multipart/alternative", "text/plain", "text/html", "image/png",
    ]
    logo = found["image/png"]
    assert logo["Content-ID"] == f"<{LOGO_CID}>"
    assert logo["Content-Disposition"].startswith("inline")
    assert logo.get_payload(decode=True).startswith(b"\x89PNG")
    assert f'src="cid:{LOGO_CID}"' in found["text/html"]
    assert message["Subject"] == "Your Pampanga State University Python IDE student account"
    assert message["To"] == f"juan.delacruz{DOMAIN}"
    assert message["Date"] and message["Message-ID"].endswith(f"@pampangastateu.edu.ph>")


def test_html_follows_the_university_layout():
    html = parts(build())["text/html"]

    assert "<style" not in html.lower()  # inline styles only
    header, body_and_footer = html.split("PAMPANGA STATE UNIVERSITY", 1)
    assert 'bgcolor="#eaae19"' in header and "background-color:#eaae19" in header
    assert "color:#77250b" in header[-200:]
    assert "Good day Dela Cruz, Juan," in body_and_footer
    assert (
        "Congratulations! Your account for the Pampanga State University Python IDE "
        "has been successfully provisioned by the MIS."
    ) in body_and_footer
    assert "Take note of your temporary account details:" in body_and_footer
    for label, value in (
        ("School ID Number", "2026000101"),
        ("Email / Username", f"juan.delacruz{DOMAIN}"),
        ("Temporary Password", "R3Fce-aFFdr!"),
    ):
        assert re.search(rf"<strong>{re.escape(label)}:</strong> (<span[^>]*>)?{re.escape(value)}", body_and_footer)
    assert re.search(r'please click <a href="https://pamsu-python-ide\.vercel\.app/login"[^>]*>here</a> to sign in and reset your password\.', body_and_footer)
    footer = body_and_footer.rsplit('bgcolor="#eaae19"', 1)[1]
    for line in ("Contact Details", "Pampanga State University, Cabambangan, Bacolor, Pampanga, 2001, Philippines",
                 "(045) 649 8050", "info@pampangastateu.edu.ph"):
        assert line in footer
    assert "text-align:center" in footer and "color:#ffffff" in footer
    assert "Agricultural" not in html


def test_plain_text_part_has_the_same_details():
    text = parts(build())["text/plain"]

    for line in ("PAMPANGA STATE UNIVERSITY", "Good day Dela Cruz, Juan,", "- School ID Number: 2026000101",
                 f"- Email / Username: juan.delacruz{DOMAIN}", "- Temporary Password: R3Fce-aFFdr!",
                 "https://pamsu-python-ide.vercel.app/login", "Contact Details", "(045) 649 8050"):
        assert line in text


def test_masterlist_email_has_no_password_and_links_to_password_setup():
    found = parts(build(temp_password=None, first_name="Student One", last_name=""))

    for content in found.values():
        if isinstance(content, str):
            assert "R3Fce" not in content
    html = found["text/html"]
    assert "Good day Student One," in html
    assert "<strong>Temporary Password:</strong> Not issued. You will set your own password." in html
    assert re.search(r'href="https://pamsu-python-ide\.vercel\.app/forgot-password"[^>]*>here</a> to set your password and sign in\.', html)
    assert "/login" not in html


def test_values_are_html_escaped_in_the_html_part_only():
    found = parts(build(first_name="<script>alert(1)</script>", last_name="O'Neil & Co", temp_password='a<b>"c&d'))

    html = found["text/html"]
    assert "<script>" not in html
    assert "Good day O&#x27;Neil &amp; Co, &lt;script&gt;alert(1)&lt;/script&gt;," in html
    assert "a&lt;b&gt;&quot;c&amp;d" in html
    assert 'Temporary Password: a<b>"c&d' in found["text/plain"]


def test_frontend_url_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "https://staging.example.edu/")

    html = parts(build())["text/html"]

    assert 'href="https://staging.example.edu/login"' in html


def test_without_the_logo_file_the_email_still_sends_without_an_image(monkeypatch):
    monkeypatch.setattr(email_service, "_logo_bytes", lambda: None)

    message = build()

    assert message.get_content_type() == "multipart/alternative"
    assert "cid:" not in parts(message)["text/html"]
    assert "PAMPANGA STATE UNIVERSITY" in parts(message)["text/html"]


@pytest.mark.parametrize(
    ("first", "last", "expected"),
    [("Juan", "Dela Cruz", "Dela Cruz, Juan"), ("  Maria  Lopez ", " Santos ", "Santos, Maria Lopez"),
     ("Juan Dela Cruz", "", "Juan Dela Cruz"), ("", "Reyes", "Reyes"), ("", "", "")],
)
def test_greeting_name(first, last, expected):
    assert greeting_name(first, last) == expected


# ------------------------------------------------------------------ sending


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
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(email_service, "get_smtp_config", lambda: {
        "host": "smtp-relay.brevo.com", "port": 2525, "user": "relay-user", "password": "relay-key",
        "sender_name": "PSU Python IDE", "sender_email": f"noreply{DOMAIN}",
    })
    return FakeSMTP


def test_send_uses_starttls_login_and_the_configured_port(smtp, caplog):
    with caplog.at_level(logging.INFO, logger="app.services.email_service"):
        send_provisioning_email(f"juan.delacruz{DOMAIN}", "Juan", "R3Fce-aFFdr!", "Student",
                                last_name="Dela Cruz", school_id="2026000101")

    (server,) = smtp.instances
    assert (server.host, server.port, server.timeout) == ("smtp-relay.brevo.com", 2525, 15)
    assert server.calls == ["starttls", ("login", "relay-user"), ("sendmail", f"noreply{DOMAIN}", [f"juan.delacruz{DOMAIN}"])]
    assert "Content-ID: <psu-logo>" in server.data
    assert f"j***{DOMAIN}" in caplog.text and "juan.delacruz" not in caplog.text


def test_failed_send_is_logged_without_the_address_or_error_text(smtp, monkeypatch, caplog):
    def refuse(self, sender, recipients, data):
        raise email_service.smtplib.SMTPSenderRefused(550, b"sender juan.delacruz not allowed", sender)

    monkeypatch.setattr(FakeSMTP, "sendmail", refuse)
    with caplog.at_level(logging.ERROR, logger="app.services.email_service"):
        send_provisioning_email(f"juan.delacruz{DOMAIN}", "Juan", "R3Fce-aFFdr!", "Student")

    assert "SMTPSenderRefused 550" in caplog.text
    assert "juan.delacruz" not in caplog.text and "not allowed" not in caplog.text


def test_nothing_is_sent_without_smtp_credentials(monkeypatch, caplog):
    FakeSMTP.instances = []
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)

    with caplog.at_level(logging.WARNING, logger="app.services.email_service"):
        send_provisioning_email(f"juan.delacruz{DOMAIN}", "Juan", "R3Fce-aFFdr!", "Student")

    assert FakeSMTP.instances == []
    assert "not sent" in caplog.text and "juan.delacruz" not in caplog.text


# ------------------------------------------------------------------ wiring


def make_admin(db: Session) -> User:
    admin = User(name="MIS Admin", email=f"mis{DOMAIN}", role="admin", school_id="9000000001",
                 password_hash=get_password_hash("Original#2026"), email_verified=True, is_active=True)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def queued(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.routers.admin.send_provisioning_email",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    return calls


def test_single_student_creation_emails_the_credentials(client, db_session, queued):
    admin = make_admin(db_session)
    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin.user_id)})}"}

    response = client.post("/admin/students", headers=headers, json={
        "email": f"Juan.DelaCruz{DOMAIN}", "first_name": "Juan", "middle_name": "P.", "last_name": "Dela Cruz",
        "school_id": "2026000101", "password": "R3Fce-aFFdr!",
    })

    assert response.status_code == 200, response.text
    assert queued == [(
        (f"juan.delacruz{DOMAIN}", "Juan", "R3Fce-aFFdr!", "Student"),
        {"last_name": "Dela Cruz", "school_id": "2026000101"},
    )]


def test_failed_student_creation_sends_nothing(client, db_session, queued):
    admin = make_admin(db_session)
    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin.user_id)})}"}
    body = {"email": f"juan{DOMAIN}", "first_name": "Juan", "last_name": "Cruz", "school_id": "2026000101", "password": "R3Fce-aFFdr!"}

    assert client.post("/admin/students", headers=headers, json=body).status_code == 200
    assert client.post("/admin/students", headers=headers, json=body).status_code == 400
    assert len(queued) == 1


def test_faculty_creation_emails_the_credentials_with_the_account_id(client, db_session, queued):
    admin = make_admin(db_session)
    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin.user_id)})}"}

    response = client.post("/admin/instructors", headers=headers, json={
        "email": f"maria.santos{DOMAIN}", "first_name": "Maria", "last_name": "Santos", "password": "Temp#2026pw",
    })

    assert response.status_code == 200, response.text
    ((args, kwargs),) = queued
    assert args == (f"maria.santos{DOMAIN}", "Maria", "Temp#2026pw", "Instructor")
    assert kwargs["last_name"] == "Santos"
    assert kwargs["school_id"] == response.json()["school_id"] and kwargs["school_id"].startswith("FAC")
