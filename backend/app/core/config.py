from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings are loaded from backend/.env, never committed to source control."""

    database_url: str
    frontend_origin: str = "http://localhost:5173"
    environment: str = "development"
    session_secret: str
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    email_from: str = "Auth Starter <no-reply@auth-starter.local>"
    verification_token_lifetime_hours: int = 24
    password_reset_token_lifetime_minutes: int = 30
    session_cookie_name: str = "auth_session"
    session_lifetime_days: int = 7
    cookie_secure: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
