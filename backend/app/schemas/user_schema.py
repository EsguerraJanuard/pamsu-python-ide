from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

UNIVERSITY_EMAIL_DOMAIN = "@pampangastateu.edu.ph"


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    school_id: str = Field(..., pattern=r"^(\d{10}|\d{4}-\d{5})$")
    email: str = Field(..., min_length=1, max_length=255)

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized_name = " ".join(value.split())

        if not normalized_name:
            raise ValueError("Name is required.")

        return normalized_name

    @field_validator("school_id")
    @classmethod
    def validate_school_id(cls, value: str) -> str:
        if len(value) != 10:
            raise ValueError("School ID must contain exactly 10 characters.")

        # Keep this value as a string to preserve possible leading zeroes.
        return value

    @field_validator("email")
    @classmethod
    def validate_university_email(cls, value: str) -> str:
        normalized_email = value.strip().lower()

        if not normalized_email.endswith(UNIVERSITY_EMAIL_DOMAIN):
            raise ValueError(
                "Email must use the official @pampangastateu.edu.ph domain."
            )

        local_part = normalized_email.removesuffix(UNIVERSITY_EMAIL_DOMAIN)

        if not local_part or "@" in local_part:
            raise ValueError("Enter a valid university email address.")

        return normalized_email


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    data_collection_acknowledged: Literal[True]

    @model_validator(mode="after")
    def validate_password_confirmation(self) -> "UserCreate":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")

        return self

    # SECURITY BOUNDARY:
    # This public registration schema intentionally excludes role,
    # password_hash, email_verified, and is_active. Those values are
    # assigned exclusively by trusted backend services.


class UserResponse(UserBase):
    user_id: int
    role: Literal["student", "instructor"]
    email_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

class UserUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized_name = " ".join(value.split())

        if not normalized_name:
            raise ValueError("Name is required.")

        return normalized_name

class PasswordUpdate(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    model_config = ConfigDict(
        extra="forbid",
    )

    @model_validator(mode="after")
    def validate_new_passwords_match(self) -> "PasswordUpdate":
        if self.new_password != self.confirm_password:
            raise ValueError("New passwords do not match.")
        
        if self.current_password == self.new_password:
            raise ValueError("The new password must be different from the current password.")

        return self

