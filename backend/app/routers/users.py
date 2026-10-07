from app.core.database import get_db
from app.core.security import (get_current_user, get_password_hash,
                               verify_password)
from app.models.domain_models import User
from app.schemas.user_schema import PasswordUpdate, UserResponse, UserUpdate
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session


router = APIRouter()`n`nclass IntegrityUpdate(BaseModel):
    is_graded: bool
    tab_switch_increment: int
    blocked_paste_increment: int
    mouseleave_increment: int

@router.patch(
    "/me/integrity",
    status_code=status.HTTP_200_OK,
    summary="Deduct points from academic integrity score",
)
def update_integrity_score(
    payload: IntegrityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Weight factors
    paste_weight = 2.0 if payload.is_graded else 0.5
    tab_weight = 1.0 if payload.is_graded else 0.2
    mouse_weight = 0.5 if payload.is_graded else 0.1
    
    deduction = (
        (payload.blocked_paste_increment * paste_weight) +
        (payload.tab_switch_increment * tab_weight) +
        (payload.mouseleave_increment * mouse_weight)
    )
    
    if deduction > 0:
        current_user.academic_integrity_score = max(0.0, current_user.academic_integrity_score - deduction)
        db.commit()
        db.refresh(current_user)
        
    return {"academic_integrity_score": current_user.academic_integrity_score}

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
    current_user.first_name = update_data.first_name
    current_user.middle_name = update_data.middle_name
    current_user.last_name = update_data.last_name
    if update_data.ast_strictness_level is not None:
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
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The current password you entered is incorrect.",
        )
    
    current_user.password_hash = get_password_hash(password_data.new_password)
    # Increment password_version to invalidate existing tokens
    current_user.password_version += 1
    
    db.commit()


from app.integrations.otp_delivery import get_otp_delivery_adapter
from app.schemas.otp_schema import (OTPChallengeResponse, OTPResendRequest,
                                    PasswordResetCompleteRequest,
                                    PasswordResetStartRequest)
from app.services.otp_service import (OTPAttemptLimitError,
                                      OTPChallengeConsumedError,
                                      OTPChallengeExpiredError,
                                      OTPChallengeNotFoundError,
                                      OTPDeliveryAdapter, OTPDeliveryError,
                                      OTPInvalidCodeError, OTPResendLimitError,
                                      OTPResendTooSoonError,
                                      RegistrationConflictError,
                                      resend_password_reset_otp,
                                      start_password_reset,
                                      verify_and_complete_password_reset)


@router.post(
    "/password-reset/start",
    response_model=OTPChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a password reset flow",
)
def start_password_reset_endpoint(
    reset_data: PasswordResetStartRequest,
    db: Session = Depends(get_db),
    delivery_adapter: OTPDeliveryAdapter = Depends(get_otp_delivery_adapter),
) -> OTPChallengeResponse:
    try:
        return start_password_reset(
            db=db,
            reset_data=reset_data,
            delivery_adapter=delivery_adapter,
        )
    except RegistrationConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except OTPDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.post(
    "/password-reset/resend",
    response_model=OTPChallengeResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend password reset OTP",
)
def resend_password_reset_endpoint(
    resend_data: OTPResendRequest,
    db: Session = Depends(get_db),
    delivery_adapter: OTPDeliveryAdapter = Depends(get_otp_delivery_adapter),
) -> OTPChallengeResponse:
    try:
        return resend_password_reset_otp(
            db=db,
            challenge_id=resend_data.challenge_id,
            delivery_adapter=delivery_adapter,
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
        ) from exc
    except OTPResendLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except OTPDeliveryError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post(
    "/password-reset/complete",
    status_code=status.HTTP_200_OK,
    summary="Verify OTP and complete password reset",
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
