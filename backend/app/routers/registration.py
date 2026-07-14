from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.integrations.otp_delivery import (
    get_otp_delivery_adapter,
)
from app.schemas.otp_schema import (
    OTPChallengeResponse,
    OTPResendRequest,
    OTPVerificationRequest,
    RegistrationCompleteResponse,
    RegistrationStartRequest,
)
from app.services.otp_service import (
    OTPAttemptLimitError,
    OTPChallengeConsumedError,
    OTPChallengeExpiredError,
    OTPChallengeNotFoundError,
    OTPDeliveryAdapter,
    OTPDeliveryError,
    OTPInvalidCodeError,
    OTPResendLimitError,
    OTPResendTooSoonError,
    RegistrationConflictError,
    resend_registration_otp,
    start_registration,
    verify_registration_otp,
)


router = APIRouter(
    prefix="/registration",
    tags=["Registration"],
)


DELIVERY_UNAVAILABLE_MESSAGE = "Verification email delivery is temporarily unavailable."


@router.post(
    "/start",
    response_model=OTPChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="start_registration",
    summary="Start university account registration",
    description=(
        "Validates registration details, stores a pending registration, "
        "creates an OTP challenge, and requests delivery of the OTP to the "
        "provided PAMSU university email. The response never contains the "
        "plaintext OTP."
    ),
    responses={
        status.HTTP_409_CONFLICT: {
            "description": (
                "The email address or school ID is already registered, "
                "or conflicts with another pending registration."
            ),
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "The registration data is invalid.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": ("The OTP email delivery service is unavailable."),
        },
    },
)
def start_registration_endpoint(
    registration_data: RegistrationStartRequest,
    db: Session = Depends(get_db),
    delivery_adapter: OTPDeliveryAdapter = Depends(get_otp_delivery_adapter),
) -> OTPChallengeResponse:
    try:
        return start_registration(
            db=db,
            registration_data=registration_data,
            delivery_adapter=delivery_adapter,
        )
    except RegistrationConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except OTPDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=DELIVERY_UNAVAILABLE_MESSAGE,
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post(
    "/verify",
    response_model=RegistrationCompleteResponse,
    status_code=status.HTTP_200_OK,
    operation_id="verify_registration_otp",
    summary="Verify a registration OTP",
    description=(
        "Verifies the submitted OTP challenge. A user account is created "
        "only after successful OTP verification. The backend assigns the "
        "account role using the instructor allowlist; clients cannot select "
        "their own role."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": (
                "The OTP is invalid. The response includes the remaining "
                "verification attempts."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The OTP challenge does not exist.",
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The challenge was already consumed or the registration "
                "now conflicts with an existing account."
            ),
        },
        status.HTTP_410_GONE: {
            "description": "The OTP challenge has expired.",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": ("The maximum OTP verification attempts were reached."),
        },
    },
)
def verify_registration_endpoint(
    verification_data: OTPVerificationRequest,
    db: Session = Depends(get_db),
) -> RegistrationCompleteResponse:
    try:
        return verify_registration_otp(
            db=db,
            verification_data=verification_data,
        )
    except OTPChallengeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except OTPChallengeExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=str(exc),
        ) from exc
    except OTPChallengeConsumedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except OTPAttemptLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except OTPInvalidCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid OTP code.",
                "remaining_attempts": exc.remaining_attempts,
            },
        ) from exc
    except RegistrationConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/resend",
    response_model=OTPChallengeResponse,
    status_code=status.HTTP_200_OK,
    operation_id="resend_registration_otp",
    summary="Resend a registration OTP",
    description=(
        "Replaces the active OTP for an existing pending registration and "
        "requests delivery of a new code. Resend cooldown and maximum resend "
        "limits are enforced by the backend."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "The OTP challenge does not exist.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "The OTP challenge was already consumed.",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": (
                "The resend request was made too soon or the resend limit was reached."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": ("The OTP email delivery service is unavailable."),
        },
    },
)
def resend_registration_endpoint(
    resend_data: OTPResendRequest,
    db: Session = Depends(get_db),
    delivery_adapter: OTPDeliveryAdapter = Depends(get_otp_delivery_adapter),
) -> OTPChallengeResponse:
    try:
        return resend_registration_otp(
            db=db,
            challenge_id=resend_data.challenge_id,
            delivery_adapter=delivery_adapter,
        )
    except OTPChallengeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except OTPChallengeConsumedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except OTPResendTooSoonError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "OTP resend requested too soon.",
                "retry_after_seconds": exc.retry_after_seconds,
            },
            headers={
                "Retry-After": str(exc.retry_after_seconds),
            },
        ) from exc
    except OTPResendLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except OTPDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=DELIVERY_UNAVAILABLE_MESSAGE,
        ) from exc


# SECURITY BOUNDARY:
# Registration clients cannot supply a role, password hash, verified state,
# or account status. These values are controlled by backend services.

# OTP BOUNDARY:
# Plaintext OTP codes must never appear in API responses, logs, exceptions,
# or database records.

# PARTNER INTEGRATION:
# The partner replaces only the injected OTP delivery adapter. Registration,
# verification, expiration, resend, attempt, and role-assignment rules remain
# controlled by the backend service layer.
