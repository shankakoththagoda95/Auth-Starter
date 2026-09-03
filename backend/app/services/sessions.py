import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.models.user import Session


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(user_id) -> tuple[Session, str, str]:
    """Create high-entropy session and CSRF secrets, storing only their hashes."""

    settings = get_settings()
    raw_session_token = secrets.token_urlsafe(32)
    raw_csrf_token = secrets.token_urlsafe(32)
    session = Session(
        user_id=user_id,
        token_hash=hash_token(raw_session_token),
        csrf_token_hash=hash_token(raw_csrf_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.session_lifetime_days),
    )
    return session, raw_session_token, raw_csrf_token


def rotate_csrf_token(session: Session) -> str:
    """Issue a fresh CSRF token so a page refresh does not prevent logout."""
    raw_csrf_token = secrets.token_urlsafe(32)
    session.csrf_token_hash = hash_token(raw_csrf_token)
    return raw_csrf_token
