import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_-]+")


class UserRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("This field is required.")
        if len(v) > 50:
            raise ValueError("Must be at most 50 characters.")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Username is required.")
        if not (3 <= len(v) <= 50):
            raise ValueError("Username must be between 3 and 50 characters.")
        if not USERNAME_PATTERN.fullmatch(v):
            raise ValueError("Username may only contain letters, numbers, underscores and hyphens.")
        return v.lower()

    @field_validator("email", mode="before")
    @classmethod
    def strip_email(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        v = str(v)
        if not (1 <= len(v) <= 255):
            raise ValueError("Email must be between 1 and 255 characters.")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not (8 <= len(v) <= 255):
            raise ValueError("Password must be between 8 and 255 characters.")
        if not v.strip():
            raise ValueError("Password cannot be whitespace only.")
        return v


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    username: str
    email: str
    created_at: datetime


class UserRegisterResponse(BaseModel):
    user: UserResponse
