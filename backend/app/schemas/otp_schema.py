from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.schemas.user_schema import UserCreate, UserResponse


OTPPurpose = Literal["registration", "email_change", "password_reset"]

class PasswordResetStartRequest(BaseModel):
    email: str

    model_config = ConfigDict(extra="forbid")

class PasswordResetCompleteRequest(BaseModel):
    challenge_id: str = Field(..., min_length=36, max_length=36)
    otp_code: str = Field(..., pattern=r"^\d{6}$")
    new_password: str

    model_config = ConfigDict(extra="forbid")

class RegistrationStartRequest(UserCreate):
    """
    Start a registration flow and request an OTP challenge.

    The account must not be created until the OTP challenge is verified.
    """


class OTPChallengeResponse(BaseModel):
    challenge_id: str = Field(..., min_length=36, max_length=36)
    email: str
    purpose: OTPPurpose
    expires_in_seconds: int = Field(..., gt=0)
    resend_after_seconds: int = Field(..., ge=0)
    message: str

    model_config = ConfigDict(extra="forbid")


class OTPVerificationRequest(BaseModel):
    challenge_id: str = Field(..., min_length=36, max_length=36)
    otp_code: str = Field(..., pattern=r"^\d{6}$")

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator("otp_code")
    @classmethod
    def validate_otp_code(cls, value: str) -> str:
        if len(value) != 6 or not value.isdigit():
            raise ValueError("OTP code must contain exactly 6 digits.")

        return value


class OTPResendRequest(BaseModel):
    challenge_id: str = Field(..., min_length=36, max_length=36)

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class OTPVerificationResponse(BaseModel):
    challenge_id: str
    verified: bool
    message: str

    model_config = ConfigDict(extra="forbid")


class RegistrationCompleteResponse(BaseModel):
    user: UserResponse
    message: str

    model_config = ConfigDict(extra="forbid")


# SECURITY BOUNDARY:
# OTP plaintext codes must never be returned by these response schemas.
# Only the OTP hash, attempt count, expiration, and consumed state belong
# in backend persistence.

# PARTNER INTEGRATION:
# The partner-owned email adapter receives the temporary plaintext OTP for
# delivery only. It must not create users, verify challenges, assign roles,
# or decide whether registration is valid.
