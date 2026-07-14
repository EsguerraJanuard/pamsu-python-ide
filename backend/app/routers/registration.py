from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.integrations.otp_delivery import get_otp_delivery_adapter
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


@router.post(
    "/start",
    response_model=OTPChallengeResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_registration_endpoint(
    registration_data: RegistrationStartRequest,
    db: Session = Depends(get_db),
    delivery_adapter: OTPDeliveryAdapter = Depends(get_otp_delivery_adapter),
):
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
            detail=("Verification email delivery is temporarily unavailable."),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/verify",
    response_model=RegistrationCompleteResponse,
)
def verify_registration_endpoint(
    verification_data: OTPVerificationRequest,
    db: Session = Depends(get_db),
):
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
)
def resend_registration_endpoint(
    resend_data: OTPResendRequest,
    db: Session = Depends(get_db),
    delivery_adapter: OTPDeliveryAdapter = Depends(get_otp_delivery_adapter),
):
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
            detail=("Verification email delivery is temporarily unavailable."),
        ) from exc


# SECURITY BOUNDARY:
# Registration clients cannot supply a role, password hash, verified state,
# or account status. These values are controlled by backend services.

# OTP BOUNDARY:
# Plaintext OTP codes must never appear in API responses, logs, exceptions,
# or database records.

# PARTNER INTEGRATION:
# The email adapter is injected through get_otp_delivery_adapter().
# The partner replaces only the delivery implementation while keeping the
# registration, verification, expiration, attempt, and role rules here.
