import smtplib
from email.message import EmailMessage

from app.core.config import get_settings


def send_verification_email(recipient: str, verification_token: str) -> None:
    """Send a verification link. Mailpit receives it locally during development."""

    settings = get_settings()
    verification_url = f"{settings.frontend_origin}/verify-email?token={verification_token}"

    message = EmailMessage()
    message["Subject"] = "Verify your email address"
    message["From"] = settings.email_from
    message["To"] = recipient
    message.set_content(
        "Welcome! Verify your email address by opening this link:\n\n"
        f"{verification_url}\n\n"
        f"This link expires in {settings.verification_token_lifetime_hours} hours."
    )
    message.add_alternative(
        f"""\
<html><body>
  <h1>Verify your email</h1>
  <p>Welcome! Confirm your account by opening this link:</p>
  <p><a href=\"{verification_url}\">Verify my email</a></p>
  <p>This link expires in {settings.verification_token_lifetime_hours} hours.</p>
</body></html>
""",
        subtype="html",
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        smtp.send_message(message)


def send_password_reset_email(recipient: str, reset_token: str) -> None:
    """Send a password-reset link. Mailpit receives it locally during development."""
    settings = get_settings()
    reset_url = f"{settings.frontend_origin}/reset-password?token={reset_token}"
    message = EmailMessage()
    message["Subject"] = "Reset your password"
    message["From"] = settings.email_from
    message["To"] = recipient
    message.set_content(
        "We received a request to reset your password. Open this link to choose a new password:\n\n"
        f"{reset_url}\n\n"
        f"This link expires in {settings.password_reset_token_lifetime_minutes} minutes. "
        "If you did not request this, you can ignore this email."
    )
    message.add_alternative(
        f"""\
<html><body>
  <h1>Reset your password</h1>
  <p>Open this link to choose a new password:</p>
  <p><a href=\"{reset_url}\">Reset my password</a></p>
  <p>This link expires in {settings.password_reset_token_lifetime_minutes} minutes.</p>
  <p>If you did not request this, you can ignore this email.</p>
</body></html>
""",
        subtype="html",
    )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        smtp.send_message(message)
