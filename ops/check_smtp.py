#!/usr/bin/env python3
"""
Check SMTP (Brevo) credentials before they go on Render.

    python ops/check_smtp.py                    # log in only (sends nothing)
    python ops/check_smtp.py --send-test you@pampangastateu.edu.ph

Reads the same variables as the backend: SMTP_HOST, SMTP_PORT, SMTP_USER,
SMTP_PASS, SMTP_SENDER_EMAIL, SMTP_SENDER_NAME. When SMTP_PASS is not set
(the safer way: keeps the key out of shell history), it asks for it without
echoing. The key is never printed; failures show the SMTP code only:
535 = wrong key; "sender refused" = the sender address is not verified in
Brevo. Step-by-step rotation: docs/operations/smtp-key-rotation.md.
"""

from __future__ import annotations

import argparse
import getpass
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

TIMEOUT_SECONDS = 15


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check SMTP credentials (sends nothing unless asked).")
    parser.add_argument("--send-test", metavar="ADDRESS", help="also send one short test email to this address")
    args = parser.parse_args(argv)

    host = os.getenv("SMTP_HOST", "smtp-relay.brevo.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    sender = os.getenv("SMTP_SENDER_EMAIL", "noreply@pampangastateu.edu.ph")
    sender_name = os.getenv("SMTP_SENDER_NAME", "PSU Python IDE")
    if not user:
        print("Set SMTP_USER (the Brevo SMTP login, shown on Brevo's SMTP & API page).", file=sys.stderr)
        return 2
    password = os.getenv("SMTP_PASS") or getpass.getpass("SMTP key (input hidden): ")

    try:
        with smtplib.SMTP(host, port, timeout=TIMEOUT_SECONDS) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(user, password)
            print(f"OK: logged in to {host}:{port} with STARTTLS.")
            if args.send_test:
                message = EmailMessage()
                message["Subject"] = "PSU Python IDE: SMTP key check"
                message["From"] = formataddr((sender_name, sender))
                message["To"] = args.send_test
                message["Date"] = formatdate(localtime=False)
                message["Message-ID"] = make_msgid(domain=sender.partition("@")[2] or None)
                message.set_content("This is a test from ops/check_smtp.py. The new SMTP key works.\n")
                server.send_message(message)
                print(f"OK: test email accepted for delivery from {sender}.")
    except smtplib.SMTPAuthenticationError as error:
        print(f"FAILED: login refused ({error.smtp_code}). The key or SMTP_USER is wrong.", file=sys.stderr)
        return 1
    except smtplib.SMTPSenderRefused as error:
        print(f"FAILED: sender refused ({error.smtp_code}). Verify {sender} in Brevo (Senders).", file=sys.stderr)
        return 1
    except (smtplib.SMTPException, OSError) as error:
        code = getattr(error, "smtp_code", "")
        print(f"FAILED: {type(error).__name__} {code}".rstrip() + ".", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
