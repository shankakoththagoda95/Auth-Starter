import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import delete, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.rate_limit import limiter
from app.models.user import EmailVerificationToken, PasswordResetToken, Session, User
from app.schemas.auth import (
    AcceptedResponse,
    CsrfTokenResponse,
    CurrentUserResponse,
    LoginRequest,
    LoginResponse,
    PasswordResetRequest,
    ResetPasswordRequest,
    RegistrationRequest,
    USERNAME_PATTERN,
    UsernameAvailabilityResponse,
    VerifyEmailRequest,
)
from app.services.email import send_password_reset_email, send_verification_email
from app.services.sessions import create_session, hash_token, rotate_csrf_token

router = APIRouter(prefix="/api/auth", tags=["authentication"])
password_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
GENERIC_REGISTRATION_MESSAGE = "If this email can be registered, a verification link has been sent."


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def normalize_username(username: str) -> str:
    return username.strip().casefold()


def create_verification_token(user_id) -> tuple[EmailVerificationToken, str]:
    settings = get_settings()
    raw_token = secrets.token_urlsafe(32)
    token = EmailVerificationToken(
        user_id=user_id,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=settings.verification_token_lifetime_hours),
    )
    return token, raw_token


def create_password_reset_token(user_id) -> tuple[PasswordResetToken, str]:
    settings = get_settings()
    raw_token = secrets.token_urlsafe(32)
    token = PasswordResetToken(
        user_id=user_id,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=settings.password_reset_token_lifetime_minutes),
    )
    return token, raw_token


def user_response(user: User) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        email_verified=user.email_verified_at is not None,
    )


async def get_current_session(request: Request, db: AsyncSession = Depends(get_db_session)) -> Session:
    raw_token = request.cookies.get(get_settings().session_cookie_name)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    session = await db.scalar(
        select(Session)
        .options(selectinload(Session.user))
        .where(Session.token_hash == hash_token(raw_token))
    )
    now = datetime.now(timezone.utc)
    if session is None or session.revoked_at is not None or session.expires_at < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return session


def require_csrf(request: Request, session: Session) -> None:
    supplied_token = request.headers.get("X-CSRF-Token")
    if supplied_token is None or not hmac.compare_digest(hash_token(supplied_token), session.csrf_token_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token.")


@router.get("/username-availability", response_model=UsernameAvailabilityResponse)
@limiter.limit("30/minute")
async def username_availability(
    request: Request,
    username: str = Query(min_length=3, max_length=30, pattern=USERNAME_PATTERN.pattern),
    db: AsyncSession = Depends(get_db_session),
) -> UsernameAvailabilityResponse:
    """Allows the frontend to check a username before registration."""

    normalized = normalize_username(username)
    result = await db.scalar(select(User.id).where(User.username_normalized == normalized))
    return UsernameAvailabilityResponse(username=username, available=result is None)


@router.post("/register", response_model=AcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/hour")
async def register(
    request: Request,
    payload: RegistrationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
) -> AcceptedResponse:
    """Create an unverified account and deliver a one-use verification link."""

    normalized_email = normalize_email(str(payload.email))
    normalized_username = normalize_username(payload.username)
    existing_user = await db.scalar(select(User).where(User.email_normalized == normalized_email))

    # Always use this generic response so this endpoint cannot confirm whether an email exists.
    if existing_user is not None:
        if existing_user.email_verified_at is None:
            await db.execute(
                delete(EmailVerificationToken).where(
                    EmailVerificationToken.user_id == existing_user.id,
                    EmailVerificationToken.used_at.is_(None),
                )
            )
            token, raw_token = create_verification_token(existing_user.id)
            db.add(token)
            await db.commit()
            background_tasks.add_task(send_verification_email, existing_user.email, raw_token)
        return AcceptedResponse(message=GENERIC_REGISTRATION_MESSAGE)

    username_in_use = await db.scalar(
        select(User.id).where(User.username_normalized == normalized_username)
    )
    if username_in_use is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username is unavailable.")

    user = User(
        email=str(payload.email),
        email_normalized=normalized_email,
        username=payload.username.strip(),
        username_normalized=normalized_username,
        password_hash=password_hasher.hash(payload.password),
    )
    db.add(user)
    await db.flush()
    token, raw_token = create_verification_token(user.id)
    db.add(token)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username is unavailable.")

    background_tasks.add_task(send_verification_email, user.email, raw_token)
    return AcceptedResponse(message=GENERIC_REGISTRATION_MESSAGE)


@router.post("/verify-email", response_model=AcceptedResponse)
@limiter.limit("10/hour")
async def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AcceptedResponse:
    """Consume an expiring verification token and mark its account as verified."""

    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    token = await db.scalar(
        select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
    )
    now = datetime.now(timezone.utc)
    if token is None or token.used_at is not None or token.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This verification link is invalid or expired.")

    user = await db.get(User, token.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This verification link is invalid.")

    token.used_at = now
    user.email_verified_at = now
    await db.commit()
    return AcceptedResponse(message="Email verified. You can now sign in.")


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> LoginResponse:
    """Authenticate a verified account and create a server-revocable browser session."""

    normalized_identifier = payload.identifier.casefold()
    user = await db.scalar(
        select(User).where(
            or_(
                User.email_normalized == normalized_identifier,
                User.username_normalized == normalized_identifier,
            )
        )
    )
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email, username, or password."
    )
    if user is None:
        raise invalid_credentials

    try:
        password_is_valid = password_hasher.verify(user.password_hash, payload.password)
    except (VerifyMismatchError, InvalidHashError):
        password_is_valid = False
    if not password_is_valid:
        raise invalid_credentials
    if user.email_verified_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verify your email address before signing in.",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is unavailable.")

    if password_hasher.check_needs_rehash(user.password_hash):
        user.password_hash = password_hasher.hash(payload.password)

    session, raw_session_token, raw_csrf_token = create_session(user.id)
    db.add(session)
    await db.commit()

    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_session_token,
        max_age=settings.session_lifetime_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return LoginResponse(user=user_response(user), csrf_token=raw_csrf_token)


@router.get("/me", response_model=CurrentUserResponse)
async def current_user(session: Session = Depends(get_current_session)) -> CurrentUserResponse:
    """Return the signed-in user without exposing password or internal session data."""

    return user_response(session.user)


@router.get("/csrf", response_model=CsrfTokenResponse)
async def csrf_token(
    session: Session = Depends(get_current_session),
    db: AsyncSession = Depends(get_db_session),
) -> CsrfTokenResponse:
    """Issue a new CSRF token for an authenticated browser session."""
    raw_csrf_token = rotate_csrf_token(session)
    await db.commit()
    return CsrfTokenResponse(csrf_token=raw_csrf_token)


@router.post("/logout", response_model=AcceptedResponse)
async def logout(
    request: Request,
    response: Response,
    session: Session = Depends(get_current_session),
    db: AsyncSession = Depends(get_db_session),
) -> AcceptedResponse:
    """Revoke the current server-side session and remove its browser cookie."""

    require_csrf(request, session)
    session.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    response.delete_cookie(key=get_settings().session_cookie_name, path="/")
    return AcceptedResponse(message="Signed out.")


@router.post("/password-reset/request", response_model=AcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/hour")
async def request_password_reset(
    request: Request,
    payload: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
) -> AcceptedResponse:
    """Send a generic reset response so email addresses cannot be enumerated."""
    user = await db.scalar(select(User).where(User.email_normalized == normalize_email(str(payload.email))))
    if user is not None and user.email_verified_at is not None and user.is_active:
        await db.execute(
            delete(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)
            )
        )
        token, raw_token = create_password_reset_token(user.id)
        db.add(token)
        await db.commit()
        background_tasks.add_task(send_password_reset_email, user.email, raw_token)
    return AcceptedResponse(message="If that account exists, a password-reset link has been sent.")


@router.post("/password-reset/confirm", response_model=AcceptedResponse)
@limiter.limit("10/hour")
async def confirm_password_reset(
    request: Request,
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AcceptedResponse:
    """Set a new password and revoke every existing session for that account."""
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    token = await db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
    now = datetime.now(timezone.utc)
    if token is None or token.used_at is not None or token.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This reset link is invalid or expired.")
    user = await db.get(User, token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This reset link is invalid.")
    user.password_hash = password_hasher.hash(payload.password)
    token.used_at = now
    await db.execute(
        update(Session)
        .where(Session.user_id == user.id, Session.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    await db.commit()
    return AcceptedResponse(message="Password updated. Please sign in with your new password.")
