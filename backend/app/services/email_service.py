import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

def get_smtp_config():
    return {
        "host": os.getenv("SMTP_HOST", "smtp-relay.brevo.com"),
        "port": int(os.getenv("SMTP_PORT", 587)),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASS", ""),
        "sender_name": os.getenv("SMTP_SENDER_NAME", "PAMSU Python IDE"),
        "sender_email": os.getenv("SMTP_SENDER_EMAIL", "noreply@pampangastateu.edu.ph")
    }

def send_provisioning_email(recipient_email: str, first_name: str, temp_password: str, role: str):
    config = get_smtp_config()
    
    # If no credentials, just log and return (for local dev)
    if not config["user"] or not config["password"]:
        logger.warning(f"SMTP credentials missing. Mock email to {recipient_email} (Pass: {temp_password})")
        return

    subject = f"Welcome to PAMSU Python IDE - Your {role} Account"
    
    frontend_url = os.getenv("FRONTEND_URL", "https://pamsu-python-ide.vercel.app")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Welcome to PAMSU Python IDE</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f4f5;
                margin: 0;
                padding: 0;
                color: #333333;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .header {{
                background-color: #800000; /* PSU Maroon */
                color: #ffffff;
                padding: 30px 20px;
                text-align: center;
                border-bottom: 4px solid #eeb319; /* PSU Gold */
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }}
            .content {{
                padding: 30px 40px;
                line-height: 1.6;
            }}
            .credentials-box {{
                background-color: #fcf8e3; /* Soft Gold Tint */
                border-left: 4px solid #eeb319;
                padding: 20px;
                margin: 25px 0;
                border-radius: 4px;
            }}
            .credentials-box p {{
                margin: 10px 0;
                font-size: 16px;
            }}
            .highlight {{
                font-weight: bold;
                color: #800000;
                font-family: monospace;
                font-size: 18px;
            }}
            .btn-container {{
                text-align: center;
                margin: 35px 0 20px;
            }}
            .btn {{
                background-color: #800000;
                color: #ffffff !important;
                text-decoration: none;
                padding: 14px 30px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
                display: inline-block;
                transition: background-color 0.3s ease;
            }}
            .btn:hover {{
                background-color: #5c0000;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                font-size: 12px;
                color: #777777;
                background-color: #f9fafb;
                border-top: 1px solid #eeeeee;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Pampanga State Agricultural University</h1>
                <p style="margin-top: 10px; opacity: 0.9;">College of Computing Studies</p>
            </div>
            <div class="content">
                <p>Hello <strong>{first_name}</strong>,</p>
                <p>Your official {role} account for the <strong>PAMSU Python IDE</strong> has been successfully provisioned by the MIS Administrator.</p>
                
                <div class="credentials-box">
                    <p style="margin-top: 0; font-weight: 600; color: #555;">Your Login Credentials:</p>
                    <p>School Email: <span class="highlight">{recipient_email}</span></p>
                    <p>Temporary Password: <span class="highlight">{temp_password}</span></p>
                </div>
                
                <p>For your security, please log in immediately and update your password in your Account Settings.</p>
                
                <div class="btn-container">
                    <a href="{frontend_url}" class="btn">Log In to Your Workspace</a>
                </div>
            </div>
            <div class="footer">
                <p>&copy; 2026 Pampanga State Agricultural University. All rights reserved.</p>
                <p>If you did not request this account or believe this is an error, please contact the MIS Department.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{config['sender_name']} <{config['sender_email']}>"
    msg["To"] = recipient_email
    
    msg.attach(MIMEText(html_content, "html"))
    
    try:
        with smtplib.SMTP(config["host"], config["port"]) as server:
            server.starttls()
            server.login(config["user"], config["password"])
            server.sendmail(config["sender_email"], recipient_email, msg.as_string())
            logger.info(f"Provisioning email successfully sent to {recipient_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {e}")
