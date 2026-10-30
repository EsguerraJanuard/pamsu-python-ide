import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from typing import NoReturn

from app.integrations.otp_email import OTPEmailAdapter as OTPDeliveryAdapter
from app.integrations.otp_email import OTPEmailAdapterRejectedError

# Bounds every SMTP connect and command so a stalled relay cannot hold a
# worker thread indefinitely.
SMTP_TIMEOUT_SECONDS = 15
DEFAULT_SMTP_HOST = "smtp-relay.brevo.com"


class OTPDeliveryUnavailableError(RuntimeError):
    """Raised when no working OTP email adapter is configured."""


class SMTPEmailAdapter:
    """
    SMTP-based email delivery adapter.
    Reads SMTP configuration from environment variables.
    """

    def __init__(self):
        # Same defaults as the account-setup email (email_service): without
        # them, reset codes failed while welcome emails still went out.
        self.host = os.getenv("SMTP_HOST") or DEFAULT_SMTP_HOST
        self.port = int(os.getenv("SMTP_PORT") or "587")
        self.user = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASS", "")
        self.sender_name = os.getenv("SMTP_SENDER_NAME", "PSU Python IDE")
        # Same sender as the account-setup email (email_service). The SMTP
        # login is Brevo's relay account name, not a verified sender, so
        # Brevo refuses or drops mail sent from it.
        self.sender_email = os.getenv("SMTP_SENDER_EMAIL") or "noreply@pampangastateu.edu.ph"

    def send_otp(
        self,
        *,
        recipient_email: str,
        otp_code: str,
        purpose: str,
        expires_in_seconds: int,
    ) -> None:
        if not self.user or not self.password:
            raise OTPDeliveryUnavailableError("SMTP configuration is missing (SMTP_USER and SMTP_PASS).")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{self.sender_name} - Verification Code"
        msg["From"] = formataddr((self.sender_name, self.sender_email))
        msg["To"] = recipient_email
        # Gmail rejects or spam-files mail without these.
        msg["Date"] = formatdate(localtime=False)
        msg["Message-ID"] = make_msgid(domain=self.sender_email.partition("@")[2] or None)

        purpose_str = "verify your email address"
        if purpose == "registration":
            purpose_str = "complete your registration"
        elif purpose == "email_change":
            purpose_str = "verify your new email address"
        elif purpose == "password_reset":
            purpose_str = "reset your password"

        minutes = expires_in_seconds // 60

        text = f"""Hello,
Please use the following verification code to {purpose_str}:
{otp_code}

This code will expire in {minutes} minutes. If you did not request this code, you can safely ignore this email.
"""

        html = f"""
        <html>
          <body style="font-family: sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                <div style="background-color: #77250b; padding: 20px; text-align: center;">
                    <h2 style="color: #eaae19; margin: 0;">Pampanga State University Python IDE</h2>
                </div>
                <div style="padding: 30px; background-color: #ffffff;">
                    <p style="color: #374151; font-size: 16px; margin-top: 0;">Hello,</p>
                    <p style="color: #374151; font-size: 16px;">Please use the following verification code to {purpose_str}:</p>
                    
                    <div style="background-color: #f3f4f6; border-radius: 6px; padding: 16px; text-align: center; margin: 24px 0;">
                        <span style="font-family: monospace; font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #111827;">{otp_code}</span>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px;">This code will expire in {minutes} minutes.</p>
                    <p style="color: #6b7280; font-size: 14px;">If you did not request this code, you can safely ignore this email.</p>
                </div>
            </div>
          </body>
        </html>
        """

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        msg.attach(part1)
        msg.attach(part2)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=SMTP_TIMEOUT_SECONDS) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.sender_email, [recipient_email], msg.as_string())
        except Exception as e:
            # Class name and SMTP code only (535 = wrong key, SMTPSenderRefused =
            # sender not verified in Brevo); the error text can echo the address.
            summary = " ".join(str(part) for part in (type(e).__name__, getattr(e, "smtp_code", None)) if part)
            raise OTPEmailAdapterRejectedError(f"SMTP delivery failed ({summary}).") from None


class UnavailableOTPDeliveryAdapter:
    """
    Safe default adapter used until the partner connects email delivery.
    """

    def send_otp(
        self,
        *,
        recipient_email: str,
        otp_code: str,
        purpose: str,
        expires_in_seconds: int,
    ) -> NoReturn:
        del recipient_email
        del otp_code
        del purpose
        del expires_in_seconds

        raise OTPDeliveryUnavailableError("OTP email delivery is not configured.")


def get_otp_delivery_adapter() -> OTPDeliveryAdapter:
    """
    FastAPI dependency provider for OTP email delivery.
    """
    
    # SMTP_HOST is optional (Brevo's relay by default), as for welcome emails.
    if os.getenv("SMTP_USER") and os.getenv("SMTP_PASS"):
        return SMTPEmailAdapter()
    
    return UnavailableOTPDeliveryAdapter()


# PARTNER INTEGRATION:
# Replace UnavailableOTPDeliveryAdapter with the actual email implementation.
# (SMTPEmailAdapter added for quick integration!)
