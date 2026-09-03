import re
import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

USERNAME_PATTERN = re.compile(r"^[a-z0-9_]{3,30}$")


class RegistrationRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("username")
    @classmethod
    def username_is_allowed(cls, value: str) -> str:
        normalized = value.casefold()
        if not USERNAME_PATTERN.fullmatch(normalized):
            raise ValueError("Username must use 3–30 letters, numbers, or underscores.")
        return value

    @field_validator("password")
    @classmethod
    def password_is_strong(cls, value: str) -> str:
        requirements = (
            any(character.islower() for character in value),
            any(character.isupper() for character in value),
            any(character.isdigit() for character in value),
            any(not character.isalnum() for character in value),
        )
        if not all(requirements):
            raise ValueError(
                "Password must include uppercase, lowercase, a number, and a special character."
            )
        return value


class UsernameAvailabilityResponse(BaseModel):
    username: str
    available: bool


class AcceptedResponse(BaseModel):
    message: str


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=32, max_length=512)


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("identifier")
    @classmethod
    def identifier_is_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Email or username is required.")
        return value


class CurrentUserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    email_verified: bool


class LoginResponse(BaseModel):
    user: CurrentUserResponse
    csrf_token: str


class CsrfTokenResponse(BaseModel):
    csrf_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=32, max_length=512)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def password_is_strong(cls, value: str) -> str:
        requirements = (
            any(character.islower() for character in value),
            any(character.isupper() for character in value),
            any(character.isdigit() for character in value),
            any(not character.isalnum() for character in value),
        )
        if not all(requirements):
            raise ValueError(
                "Password must include uppercase, lowercase, a number, and a special character."
            )
        return value
