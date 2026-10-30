from app.core.database import get_db
from app.core.rate_limit import enforce_rate_limit, limit_per_ip
from app.core.security import (get_current_user, get_password_hash,
                               verify_password)
from app.integrations.otp_delivery import get_otp_delivery_adapter
from app.models.domain_models import User
from app.schemas.otp_schema import (OTPChallengeResponse, OTPResendRequest,
                                    PasswordResetCompleteRequest,
                                    PasswordResetStartRequest)
from app.schemas.user_schema import PasswordUpdate, UserResponse, UserUpdate
from app.services.otp_service import (OTPAttemptLimitError,
                                      OTPChallengeConsumedError,
                                      OTPChallengeExpiredError,
                                      OTPChallengeNotFoundError,
                                      OTPDeliveryAdapter,
                                      OTPInvalidCodeError, OTPResendLimitError,
                                      OTPResendTooSoonError,
                                      RegistrationConflictError,
                                      normalize_email,
                                      resend_password_reset_otp,
                                      start_password_reset,
                                      verify_and_complete_password_reset)
from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException,
                     status)
from sqlalchemy.orm import Session


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update my profile",
)
def update_profile(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    current_user.name = update_data.name
    if update_data.ast_strictness_level is not None:
        if current_user.role != "instructor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors are authorized to configure AST strictness.",
            )
        current_user.ast_strictness_level = update_data.ast_strictness_level
    db.commit()
    db.refresh(current_user)
    return current_user

@router.patch(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change my password",
)
def change_password(
    password_data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    enforce_rate_limit(
        scope="password_change",
        identifier=str(current_user.user_id),
        limit=5,
        window_seconds=300,
    )

    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The current password you entered is incorrect.",
        )

    current_user.password_hash = get_password_hash(password_data.new_password)
    # Increment password_version to invalidate existing tokens
    current_user.password_version += 1

    db.commit()


# PASSWORD RESET BOUNDARY:
# Start, resend and complete behave the same whether or not an account
# exists for the email (see start_password_reset).
# Codes are emailed after the response (background task), because the
# platform proxy drops requests that wait several seconds on SMTP. Starting
# a new reset expires the previous code for that email.


@router.post(
    "/password-reset/start",
    response_model=OTPChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a password reset flow",
    dependencies=[Depends(limit_per_ip("password_reset_start_ip", limit=30, window_seconds=600))],
)
def start_password_reset_endpoint(
    reset_data: PasswordResetStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    delivery_adapter: OTPDeliveryAdapter = Depends(get_otp_delivery_adapter),
) -> OTPChallengeResponse:
    try:
        normalized_email = normalize_email(reset_data.email)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Enter your official @pampangastateu.edu.ph email address.",
        ) from exc

    # Applies to every email, existing or not, so it reveals nothing.
    enforce_rate_limit(
        scope="password_reset_start_email",
        identifier=normalized_email,
        limit=3,
        window_seconds=900,
    )

    return start_password_reset(
        db=db,
        reset_data=reset_data,
        delivery_adapter=delivery_adapter,
        schedule_delivery=background_tasks.add_task,
    )


@router.post(
    "/password-reset/resend",
    response_model=OTPChallengeResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend password reset OTP",
    dependencies=[Depends(limit_per_ip("password_reset_resend_ip", limit=30, window_seconds=600))],
)
def resend_password_reset_endpoint(
    resend_data: OTPResendRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    delivery_adapter: OTPDeliveryAdapter = Depends(get_otp_delivery_adapter),
) -> OTPChallengeResponse:
    try:
        return resend_password_reset_otp(
            db=db,
            challenge_id=resend_data.challenge_id,
            delivery_adapter=delivery_adapter,
            schedule_delivery=background_tasks.add_task,
        )
    except OTPChallengeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OTPChallengeConsumedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except OTPResendTooSoonError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "OTP resend requested too soon.",
                "retry_after_seconds": exc.retry_after_seconds,
            },
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except OTPResendLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post(
    "/password-reset/complete",
    status_code=status.HTTP_200_OK,
    summary="Verify OTP and complete password reset",
    dependencies=[Depends(limit_per_ip("password_reset_complete_ip", limit=60, window_seconds=600))],
)
def complete_password_reset_endpoint(
    completion_data: PasswordResetCompleteRequest,
    db: Session = Depends(get_db),
) -> dict:
    try:
        return verify_and_complete_password_reset(
            db=db,
            completion_data=completion_data,
        )
    except OTPChallengeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OTPChallengeExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc
    except OTPChallengeConsumedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except OTPAttemptLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except OTPInvalidCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid OTP code.",
                "remaining_attempts": exc.remaining_attempts,
            },
        ) from exc
    except RegistrationConflictError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
