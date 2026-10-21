"""Account-provisioning email, sent through the SMTP relay (Brevo).

Routes queue send_provisioning_email() as a FastAPI background task after the
account is committed, so a slow or failing relay never delays or undoes the
account. A failed send is only logged.

The message is built by build_provisioning_message():
- multipart/related: the HTML refers to the PSU logo as an inline image
  (Content-ID), which Gmail, Outlook and Apple Mail show without remote-image
  prompts. Data: URIs are blocked by Gmail and Outlook, so they are not used.
- multipart/alternative inside it: a plain-text part and the HTML part.
- The HTML uses tables and inline styles only, because many clients drop
  <style> blocks.
"""

import html
import logging
import os
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

# Bounds every SMTP connect and command so a stalled relay cannot hold a
# worker thread indefinitely.
SMTP_TIMEOUT_SECONDS = 15

DEFAULT_FRONTEND_URL = "https://pamsu-python-ide.vercel.app"
LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "psu_logo_email.png"
LOGO_CID = "psu-logo"

PSU_GOLD = "#eaae19"
PSU_MAROON = "#77250b"
TEXT_COLOR = "#1f2937"
FONT_STACK = "Arial, Helvetica, sans-serif"

CONTACT_HEADING = "Contact Details"
CONTACT_ADDRESS = "Pampanga State University, Cabambangan, Bacolor, Pampanga, 2001, Philippines"
CONTACT_PHONE = "(045) 649 8050"
CONTACT_EMAIL = "info@pampangastateu.edu.ph"


def get_smtp_config():
    return {
        "host": os.getenv("SMTP_HOST", "smtp-relay.brevo.com"),
        "port": int(os.getenv("SMTP_PORT", 587)),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASS", ""),
        "sender_name": os.getenv("SMTP_SENDER_NAME", "PSU Python IDE"),
        "sender_email": os.getenv("SMTP_SENDER_EMAIL", "noreply@pampangastateu.edu.ph")
    }


def frontend_url() -> str:
    return (os.getenv("FRONTEND_URL") or DEFAULT_FRONTEND_URL).rstrip("/")


@lru_cache(maxsize=1)
def _logo_bytes() -> bytes | None:
    try:
        return LOGO_PATH.read_bytes()
    except OSError:
        logger.warning("Email logo %s not found; sending the email without it.", LOGO_PATH.name)
        return None


def _mask_email(email: str) -> str:
    """j***@pampangastateu.edu.ph: enough to trace a delivery, not to identify."""
    local, _, domain = (email or "").partition("@")
    return f"{local[:1]}***@{domain}" if domain else "***"


def greeting_name(first_name: str | None, last_name: str | None) -> str:
    """"Last, First" when both parts are known, else whichever name is known."""
    first = " ".join((first_name or "").split())
    last = " ".join((last_name or "").split())
    if first and last:
        return f"{last}, {first}"
    return first or last


def build_provisioning_message(
    *,
    recipient_email: str,
    first_name: str,
    last_name: str,
    school_id: str,
    temp_password: str | None,
    role: str,
    sender_name: str,
    sender_email: str,
) -> MIMEMultipart:
    """The full welcome email. temp_password=None means no password was issued
    (masterlist students): the link then leads to "Forgot password?" so the
    student sets their own."""

    has_password = temp_password is not None
    name = greeting_name(first_name, last_name)
    greeting = f"Good day {name}," if name else "Good day,"
    link = f"{frontend_url()}/login" if has_password else f"{frontend_url()}/forgot-password"
    password_value = temp_password if has_password else "Not issued. You will set your own password."
    cta_after_link = "to sign in and reset your password." if has_password else "to set your password and sign in."
    welcome = (
        "Congratulations! Your account for the Pampanga State University Python IDE "
        "has been successfully provisioned by the MIS."
    )
    details = [
        ("School ID Number", school_id or "Not assigned"),
        ("Email / Username", recipient_email),
        ("Temporary Password", password_value),
    ]
    subject = f"Your Pampanga State University Python IDE {role.lower()} account"

    # ---- plain text ------------------------------------------------------
    text_lines = [
        "PAMPANGA STATE UNIVERSITY",
        "",
        greeting,
        "",
        welcome,
        "",
        "Take note of your temporary account details:",
        *[f"- {label}: {value}" for label, value in details],
        "",
        f"To complete the process, please open this link {cta_after_link}",
        link,
        "",
        CONTACT_HEADING,
        CONTACT_ADDRESS,
        CONTACT_PHONE,
        CONTACT_EMAIL,
    ]
    text_body = "\n".join(text_lines) + "\n"

    # ---- HTML (tables and inline styles only) ------------------------------
    e = lambda value: html.escape(str(value), quote=True)  # noqa: E731
    logo = _logo_bytes()
    logo_cell = (
        f'<td valign="middle" style="padding:0 14px 0 0;">'
        f'<img src="cid:{LOGO_CID}" width="56" height="56" alt="Pampanga State University logo" '
        f'style="display:block;width:56px;height:56px;border:0;outline:none;text-decoration:none;"></td>'
        if logo
        else ""
    )
    # One "Label: value" line per detail, so a long email address simply wraps
    # to the next line on a phone instead of squeezing a second column.
    detail_rows = "".join(
        f'<tr><td style="padding:{"14px" if index == 0 else "4px"} 18px {"14px" if index == len(details) - 1 else "4px"};'
        f'font-family:{FONT_STACK};font-size:15px;line-height:24px;color:{TEXT_COLOR};'
        f'overflow-wrap:anywhere;word-break:break-word;">'
        f'<strong>{e(label)}:</strong> '
        + (
            f'<span style="font-family:Consolas,\'Courier New\',monospace;font-size:16px;font-weight:bold;'
            f'color:{PSU_MAROON};white-space:nowrap;">{e(value)}</span>'
            if label == "Temporary Password" and has_password
            else e(value)
        )
        + "</td></tr>"
        for index, (label, value) in enumerate(details)
    )
    paragraph = f"margin:0 0 18px;font-family:{FONT_STACK};font-size:15px;line-height:24px;color:{TEXT_COLOR};"
    footer_line = f"margin:0;font-family:{FONT_STACK};font-size:13px;line-height:20px;color:#ffffff;"

    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light only">
<title>{e(subject)}</title>
</head>
<body style="margin:0;padding:0;background-color:#f3f4f6;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">Your Pampanga State University Python IDE account is ready.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f3f4f6;">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;background-color:#ffffff;border-collapse:collapse;">
<tr><td bgcolor="{PSU_GOLD}" style="background-color:{PSU_GOLD};padding:18px 28px;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
{logo_cell}<td valign="middle" style="font-family:{FONT_STACK};font-size:20px;line-height:26px;font-weight:bold;letter-spacing:1px;color:{PSU_MAROON};">PAMPANGA STATE UNIVERSITY</td>
</tr></table>
</td></tr>
<tr><td bgcolor="#ffffff" style="background-color:#ffffff;padding:32px 28px 30px;">
<p style="{paragraph}">{e(greeting)}</p>
<p style="{paragraph}margin-bottom:22px;">{e(welcome)}</p>
<p style="{paragraph}margin-bottom:10px;">Take note of your temporary account details:</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;border:1px solid #e5e7eb;border-left:4px solid {PSU_MAROON};margin:0 0 24px;">
{detail_rows}
</table>
<p style="{paragraph}margin-bottom:0;">To complete the process, please click <a href="{e(link)}" style="color:{PSU_MAROON};font-weight:bold;text-decoration:underline;">here</a> {e(cta_after_link)}</p>
</td></tr>
<tr><td bgcolor="{PSU_GOLD}" align="center" style="background-color:{PSU_GOLD};padding:20px 28px;text-align:center;">
<p style="{footer_line}margin-bottom:6px;font-size:14px;font-weight:bold;">{e(CONTACT_HEADING)}</p>
<p style="{footer_line}">{e(CONTACT_ADDRESS)}</p>
<p style="{footer_line}">{e(CONTACT_PHONE)}</p>
<p style="{footer_line}"><a href="mailto:{e(CONTACT_EMAIL)}" style="color:#ffffff;text-decoration:underline;">{e(CONTACT_EMAIL)}</a></p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>
"""

    alternative = MIMEMultipart("alternative")
    alternative.attach(MIMEText(text_body, "plain", "utf-8"))
    alternative.attach(MIMEText(html_body, "html", "utf-8"))

    if logo:
        message = MIMEMultipart("related")
        message.attach(alternative)
        image = MIMEImage(logo, _subtype="png")
        image.add_header("Content-ID", f"<{LOGO_CID}>")
        image.add_header("Content-Disposition", "inline", filename="psu-logo.png")
        message.attach(image)
    else:
        message = alternative

    sender_domain = sender_email.partition("@")[2] or None
    message["Subject"] = subject
    message["From"] = formataddr((sender_name, sender_email))
    message["To"] = recipient_email
    message["Date"] = formatdate(localtime=False)
    message["Message-ID"] = make_msgid(domain=sender_domain)
    return message


def send_provisioning_email(
    recipient_email: str,
    first_name: str,
    temp_password: str | None,
    role: str,
    *,
    last_name: str = "",
    school_id: str = "",
):
    """Send the account-provisioned email (run as a background task).

    With temp_password=None no credential is sent: the recipient sets their
    own password through "Forgot password?" (the OTP reset flow).
    """
    config = get_smtp_config()

    # Without credentials (local development, tests) nothing is sent.
    if not config["user"] or not config["password"]:
        logger.warning("SMTP credentials missing; provisioning email to %s not sent.", _mask_email(recipient_email))
        return

    message = build_provisioning_message(
        recipient_email=recipient_email,
        first_name=first_name,
        last_name=last_name,
        school_id=school_id,
        temp_password=temp_password,
        role=role,
        sender_name=config["sender_name"],
        sender_email=config["sender_email"],
    )

    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=SMTP_TIMEOUT_SECONDS) as server:
            server.starttls()
            server.login(config["user"], config["password"])
            server.sendmail(config["sender_email"], [recipient_email], message.as_string())
        logger.info("Provisioning email sent to %s.", _mask_email(recipient_email))
    except Exception as error:
        # Class name and SMTP code only (e.g. SMTPAuthenticationError 535 = wrong
        # key, SMTPSenderRefused = sender not verified in Brevo); the error text
        # can echo the message or the address.
        logger.error(
            "Provisioning email to %s failed (%s %s).",
            _mask_email(recipient_email),
            type(error).__name__,
            getattr(error, "smtp_code", "") or "",
        )
