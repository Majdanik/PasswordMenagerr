import os
import smtplib
import logging
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("app.email")
logger.setLevel(logging.INFO)
if not logger.handlers:
    # Uvicorn only configures its own loggers by default, so without an
    # explicit handler here, INFO records from this logger are silently
    # dropped (root logger has none) instead of reaching the server console.
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(message)s"))
    logger.addHandler(_handler)
    logger.propagate = False

SMTP_HOST = os.getenv("SMTP_HOST") or None
SMTP_PORT = int(os.getenv("SMTP_PORT") or "587")
SMTP_USERNAME = os.getenv("SMTP_USERNAME") or None
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") or None
SMTP_FROM = os.getenv("SMTP_FROM") or "noreply@passwordmanager.local"
SMTP_TIMEOUT_SECONDS = 10


def _send_or_log(to_email: str, subject: str, body: str) -> None:
    """Send an email via SMTP if configured, otherwise log it (for testing without a mailbox)."""
    if not SMTP_HOST:
        logger.info("SMTP not configured; logging email instead of sending. To=%s Subject=%s Body=%s",
                     to_email, subject, body)
        return

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = SMTP_FROM
    message["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS) as server:
            server.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to_email], message.as_string())
    except (smtplib.SMTPException, OSError):
        # A misconfigured/unreachable SMTP server must not break the request
        # that triggered the email (registration, resend, forgot-password) -
        # the code is still valid and usable, just not delivered by mail.
        logger.exception("Failed to send email to %s (Subject=%s); code was still generated.", to_email, subject)


def send_verification_email(to_email: str, code: str) -> None:
    subject = "Verify your email — Password Manager"
    body = f"Your verification code is: {code}\n\nThis code expires in 24 hours."
    _send_or_log(to_email, subject, body)


def send_password_reset_email(to_email: str, code: str) -> None:
    subject = "Password reset code — Password Manager"
    body = f"Your password reset code is: {code}\n\nThis code expires in 1 hour."
    _send_or_log(to_email, subject, body)
