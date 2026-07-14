import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from math import ceil
from typing import Protocol

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.domain_models import (
    InstructorAllowlist,
    OTPChallenge,
    PendingRegistration,
    User,
)
from app.schemas.otp_schema import (
    OTPChallengeResponse,
    OTPVerificationRequest,
    RegistrationCompleteResponse,
    RegistrationStartRequest,
)
from app.schemas.user_schema import (
    UNIVERSITY_EMAIL_DOMAIN,
    UserResponse,
)


OTP_CODE_LENGTH = 6

OTP_EXPIRE_SECONDS = int(os.getenv("OTP_EXPIRE_SECONDS", "600"))
OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", "60"))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
OTP_MAX_RESENDS = int(os.getenv("OTP_MAX_RESENDS", "3"))

# A separate OTP secret is preferred in production. JWT_SECRET_KEY is used
# only as a development fallback so the project remains easy to configure.
OTP_SECRET_KEY = (
    os.getenv("OTP_SECRET_KEY") or os.getenv("JWT_SECRET_KEY") or ""
).strip()

if len(OTP_SECRET_KEY) < 32:
    raise RuntimeError(
        "OTP_SECRET_KEY or JWT_SECRET_KEY must contain at least 32 characters."
    )

if OTP_EXPIRE_SECONDS <= 0:
    raise RuntimeError("OTP_EXPIRE_SECONDS must be greater than zero.")

if OTP_RESEND_COOLDOWN_SECONDS < 0:
    raise RuntimeError("OTP_RESEND_COOLDOWN_SECONDS cannot be negative.")

if OTP_MAX_ATTEMPTS <= 0:
    raise RuntimeError("OTP_MAX_ATTEMPTS must be greater than zero.")

if OTP_MAX_RESENDS < 0:
    raise RuntimeError("OTP_MAX_RESENDS cannot be negative.")


class OTPServiceError(Exception):
    """Base exception for expected OTP service failures."""


class RegistrationConflictError(OTPServiceError):
    """Raised when an email or school ID is already registered."""


class OTPChallengeNotFoundError(OTPServiceError):
    """Raised when an OTP challenge cannot be found."""


class OTPChallengeExpiredError(OTPServiceError):
    """Raised when an OTP challenge has expired."""


class OTPChallengeConsumedError(OTPServiceError):
    """Raised when an OTP challenge was already completed."""


class OTPAttemptLimitError(OTPServiceError):
    """Raised when the maximum verification attempts were reached."""


class OTPInvalidCodeError(OTPServiceError):
    def __init__(self, remaining_attempts: int):
        self.remaining_attempts = remaining_attempts
        super().__init__(
            f"Invalid OTP code. {remaining_attempts} attempt(s) remaining."
        )


class OTPResendTooSoonError(OTPServiceError):
    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            "OTP resend requested too soon. "
            f"Retry after {retry_after_seconds} second(s)."
        )


class OTPResendLimitError(OTPServiceError):
    """Raised when the maximum resend count has been reached."""


class OTPDeliveryError(OTPServiceError):
    """Raised when the partner-owned email adapter cannot deliver OTP."""


class OTPDeliveryAdapter(Protocol):
    def send_otp(
        self,
        *,
        recipient_email: str,
        otp_code: str,
        purpose: str,
        expires_in_seconds: int,
    ) -> None:
        """
        Deliver an OTP without returning or persisting its plaintext value.
        """


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_email(email: str) -> str:
    normalized_email = email.strip().lower()

    if not normalized_email.endswith(UNIVERSITY_EMAIL_DOMAIN):
        raise ValueError("Email must use the official university domain.")

    return normalized_email


def generate_otp_code() -> str:
    upper_limit = 10**OTP_CODE_LENGTH
    random_number = secrets.randbelow(upper_limit)

    return f"{random_number:0{OTP_CODE_LENGTH}d}"


def hash_otp_code(
    *,
    challenge_id: str,
    otp_code: str,
) -> str:
    message = f"{challenge_id}:{otp_code}".encode("utf-8")
    secret = OTP_SECRET_KEY.encode("utf-8")

    return hmac.new(
        secret,
        message,
        hashlib.sha256,
    ).hexdigest()


def verify_otp_hash(
    *,
    challenge_id: str,
    otp_code: str,
    stored_hash: str,
) -> bool:
    candidate_hash = hash_otp_code(
        challenge_id=challenge_id,
        otp_code=otp_code,
    )

    return hmac.compare_digest(
        candidate_hash,
        stored_hash,
    )


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def get_challenge_or_raise(
    *,
    db: Session,
    challenge_id: str,
) -> OTPChallenge:
    challenge = (
        db.query(OTPChallenge).filter(OTPChallenge.challenge_id == challenge_id).first()
    )

    if challenge is None:
        raise OTPChallengeNotFoundError("OTP challenge not found.")

    return challenge


def validate_active_challenge(
    challenge: OTPChallenge,
) -> None:
    if challenge.consumed_at is not None:
        raise OTPChallengeConsumedError(
            "This OTP challenge has already been completed."
        )

    if utc_now() >= normalize_datetime(challenge.expires_at):
        raise OTPChallengeExpiredError("The OTP code has expired.")

    if challenge.attempt_count >= challenge.max_attempts:
        raise OTPAttemptLimitError("The maximum number of OTP attempts was reached.")


def determine_user_role(
    *,
    db: Session,
    email: str,
) -> str:
    allowlist_entry = (
        db.query(InstructorAllowlist)
        .filter(
            func.lower(InstructorAllowlist.email) == email,
            InstructorAllowlist.is_active.is_(True),
        )
        .first()
    )

    return "instructor" if allowlist_entry is not None else "student"


def ensure_registration_is_available(
    *,
    db: Session,
    email: str,
    school_id: str,
) -> None:
    existing_user = (
        db.query(User)
        .filter(
            or_(
                func.lower(User.email) == email,
                User.school_id == school_id,
            )
        )
        .first()
    )

    if existing_user is not None:
        if existing_user.email.lower() == email:
            raise RegistrationConflictError(
                "An account already uses this university email."
            )

        raise RegistrationConflictError("An account already uses this school ID.")


def remove_previous_pending_registration(
    *,
    db: Session,
    email: str,
    school_id: str,
) -> None:
    previous_registrations = (
        db.query(PendingRegistration)
        .filter(
            or_(
                func.lower(PendingRegistration.email) == email,
                PendingRegistration.school_id == school_id,
            )
        )
        .all()
    )

    for pending_registration in previous_registrations:
        challenge = pending_registration.challenge

        db.delete(pending_registration)

        if challenge is not None:
            db.delete(challenge)

    if previous_registrations:
        db.flush()


def deliver_otp(
    *,
    delivery_adapter: OTPDeliveryAdapter,
    email: str,
    otp_code: str,
    purpose: str,
) -> None:
    try:
        delivery_adapter.send_otp(
            recipient_email=email,
            otp_code=otp_code,
            purpose=purpose,
            expires_in_seconds=OTP_EXPIRE_SECONDS,
        )
    except Exception as exc:
        raise OTPDeliveryError(
            "The verification email could not be delivered."
        ) from exc


def start_registration(
    *,
    db: Session,
    registration_data: RegistrationStartRequest,
    delivery_adapter: OTPDeliveryAdapter,
) -> OTPChallengeResponse:
    normalized_email = normalize_email(registration_data.email)

    ensure_registration_is_available(
        db=db,
        email=normalized_email,
        school_id=registration_data.school_id,
    )

    password_hash = get_password_hash(registration_data.password)

    current_time = utc_now()
    challenge_id = str(secrets.token_hex(16))
    otp_code = generate_otp_code()

    challenge = OTPChallenge(
        challenge_id=challenge_id,
        email=normalized_email,
        purpose="registration",
        otp_hash=hash_otp_code(
            challenge_id=challenge_id,
            otp_code=otp_code,
        ),
        attempt_count=0,
        max_attempts=OTP_MAX_ATTEMPTS,
        resend_count=0,
        expires_at=current_time + timedelta(seconds=OTP_EXPIRE_SECONDS),
        last_sent_at=current_time,
    )

    pending_registration = PendingRegistration(
        challenge_id=challenge_id,
        name=registration_data.name,
        school_id=registration_data.school_id,
        email=normalized_email,
        password_hash=password_hash,
        data_collection_acknowledged=(registration_data.data_collection_acknowledged),
    )

    try:
        remove_previous_pending_registration(
            db=db,
            email=normalized_email,
            school_id=registration_data.school_id,
        )

        db.add(challenge)
        db.add(pending_registration)
        db.flush()

        deliver_otp(
            delivery_adapter=delivery_adapter,
            email=normalized_email,
            otp_code=otp_code,
            purpose="registration",
        )

        db.commit()

    except IntegrityError as exc:
        db.rollback()

        raise RegistrationConflictError(
            "The email or school ID already has a pending registration."
        ) from exc

    except Exception:
        db.rollback()
        raise

    return OTPChallengeResponse(
        challenge_id=challenge.challenge_id,
        email=normalized_email,
        purpose="registration",
        expires_in_seconds=OTP_EXPIRE_SECONDS,
        resend_after_seconds=(OTP_RESEND_COOLDOWN_SECONDS),
        message=("A verification code was sent to the university email address."),
    )


def resend_registration_otp(
    *,
    db: Session,
    challenge_id: str,
    delivery_adapter: OTPDeliveryAdapter,
) -> OTPChallengeResponse:
    challenge = get_challenge_or_raise(
        db=db,
        challenge_id=challenge_id,
    )

    if challenge.purpose != "registration":
        raise OTPChallengeNotFoundError("Registration OTP challenge not found.")

    if challenge.consumed_at is not None:
        raise OTPChallengeConsumedError(
            "This OTP challenge has already been completed."
        )

    pending_registration = challenge.pending_registration

    if pending_registration is None:
        raise OTPChallengeNotFoundError("Pending registration not found.")

    if challenge.resend_count >= OTP_MAX_RESENDS:
        raise OTPResendLimitError("The maximum number of OTP resends was reached.")

    current_time = utc_now()
    last_sent_at = normalize_datetime(challenge.last_sent_at)

    elapsed_seconds = (current_time - last_sent_at).total_seconds()

    if elapsed_seconds < OTP_RESEND_COOLDOWN_SECONDS:
        retry_after = ceil(OTP_RESEND_COOLDOWN_SECONDS - elapsed_seconds)

        raise OTPResendTooSoonError(retry_after)

    otp_code = generate_otp_code()

    challenge.otp_hash = hash_otp_code(
        challenge_id=challenge.challenge_id,
        otp_code=otp_code,
    )
    challenge.attempt_count = 0
    challenge.resend_count += 1
    challenge.expires_at = current_time + timedelta(seconds=OTP_EXPIRE_SECONDS)
    challenge.last_sent_at = current_time

    try:
        db.flush()

        deliver_otp(
            delivery_adapter=delivery_adapter,
            email=challenge.email,
            otp_code=otp_code,
            purpose="registration",
        )

        db.commit()
        db.refresh(challenge)

    except Exception:
        db.rollback()
        raise

    return OTPChallengeResponse(
        challenge_id=challenge.challenge_id,
        email=challenge.email,
        purpose="registration",
        expires_in_seconds=OTP_EXPIRE_SECONDS,
        resend_after_seconds=(OTP_RESEND_COOLDOWN_SECONDS),
        message=("A new verification code was sent to the university email address."),
    )


def verify_registration_otp(
    *,
    db: Session,
    verification_data: OTPVerificationRequest,
) -> RegistrationCompleteResponse:
    challenge = get_challenge_or_raise(
        db=db,
        challenge_id=verification_data.challenge_id,
    )

    if challenge.purpose != "registration":
        raise OTPChallengeNotFoundError("Registration OTP challenge not found.")

    validate_active_challenge(challenge)

    pending_registration = challenge.pending_registration

    if pending_registration is None:
        raise OTPChallengeNotFoundError("Pending registration not found.")

    otp_is_valid = verify_otp_hash(
        challenge_id=challenge.challenge_id,
        otp_code=verification_data.otp_code,
        stored_hash=challenge.otp_hash,
    )

    if not otp_is_valid:
        challenge.attempt_count += 1
        remaining_attempts = max(
            challenge.max_attempts - challenge.attempt_count,
            0,
        )

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        if remaining_attempts == 0:
            raise OTPAttemptLimitError(
                "The maximum number of OTP attempts was reached."
            )

        raise OTPInvalidCodeError(remaining_attempts)

    ensure_registration_is_available(
        db=db,
        email=pending_registration.email,
        school_id=pending_registration.school_id,
    )

    assigned_role = determine_user_role(
        db=db,
        email=pending_registration.email,
    )

    new_user = User(
        name=pending_registration.name,
        school_id=pending_registration.school_id,
        email=pending_registration.email,
        role=assigned_role,
        password_hash=(pending_registration.password_hash),
        email_verified=True,
        is_active=True,
    )

    challenge.consumed_at = utc_now()

    try:
        db.add(new_user)
        db.flush()

        db.delete(pending_registration)

        db.commit()
        db.refresh(new_user)

    except IntegrityError as exc:
        db.rollback()

        raise RegistrationConflictError(
            "The email or school ID was registered while verification was in progress."
        ) from exc

    except Exception:
        db.rollback()
        raise

    return RegistrationCompleteResponse(
        user=UserResponse.model_validate(new_user),
        message=("University email verified and account created successfully."),
    )


# SECURITY BOUNDARY:
# Plaintext OTP codes exist only long enough to be passed to the delivery
# adapter. They must never be stored, logged, or returned through the API.

# ROLE BOUNDARY:
# The client never chooses a role. Instructor status is assigned only when
# the verified email exists in the active backend instructor allowlist.

# PARTNER INTEGRATION:
# The partner implements OTPDeliveryAdapter.send_otp(). The adapter delivers
# email only; it must not validate OTPs, create users, assign roles, or update
# challenge state.
