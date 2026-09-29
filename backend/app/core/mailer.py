"""Sends the 'here is your default password' emails. Meant to run as a FastAPI background task."""
import logging
import smtplib
import uuid
from datetime import datetime, timezone
from email.message import EmailMessage

from app.config import settings
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)


def _build_message(email: str, full_name: str, password: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = "Your ML Virtual Lab account"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = email
    msg.set_content(
        f"Hello {full_name},\n\n"
        f"An account has been created for you on the ML Virtual Lab.\n\n"
        f"Login page: {settings.FRONTEND_URL}/login\n"
        f"Email: {email}\n"
        f"Temporary password: {password}\n\n"
        f"You will be asked to change this password the first time you log in.\n"
        f"Do not share it with anyone.\n"
    )
    return msg


def _mark_sent(user_id: uuid.UUID) -> None:
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user:
            user.credentials_sent_at = datetime.now(timezone.utc)
            db.commit()


def send_credentials_emails(recipients: list[dict]) -> None:
    """recipients: [{"user_id": UUID, "email": str, "full_name": str, "password": str}]
    Uses one SMTP connection for the whole list. Failures are logged and leave
    credentials_sent_at NULL so the instructor can re-send."""
    if not recipients:
        return

    if not settings.EMAIL_ENABLED:  # dev mode: no SMTP, print instead
        for r in recipients:
            logger.warning("[DEV EMAIL - not sent] to=%s password=%s", r["email"], r["password"])
            _mark_sent(r["user_id"])
        return

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            for r in recipients:
                try:
                    smtp.send_message(_build_message(r["email"], r["full_name"], r["password"]))
                    _mark_sent(r["user_id"])
                except Exception:
                    logger.exception("Could not send credentials email to %s", r["email"])
    except Exception:
        logger.exception("Could not connect to the SMTP server")
