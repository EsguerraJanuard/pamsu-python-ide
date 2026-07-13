from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    verify_password,
)
from app.models.domain_models import User
from app.schemas.user_schema import UNIVERSITY_EMAIL_DOMAIN


router = APIRouter(
    tags=["Authentication"],
)


class AuthenticatedUserResponse(BaseModel):
    user_id: int
    name: str
    school_id: str | None
    email: str
    role: Literal["student", "instructor"]
    email_verified: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthenticatedUserResponse


def invalid_credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    normalized_email = form_data.username.strip().lower()

    if not normalized_email.endswith(UNIVERSITY_EMAIL_DOMAIN):
        raise invalid_credentials_exception()

    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()

    if user is None:
        raise invalid_credentials_exception()

    if not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise invalid_credentials_exception()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="University email verification is required.",
        )

    if user.role not in {"student", "instructor"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account does not have a valid system role.",
        )

    access_token_expires = timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
            "role": user.role,
            "name": user.name,
            "email": user.email,
        },
        expires_delta=access_token_expires,
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=AuthenticatedUserResponse.model_validate(user),
    )


# SECURITY BOUNDARY:
# Login uses the verified university email as the account identifier.
# The client does not provide or select a role. The role included in the JWT
# comes exclusively from the persisted backend-controlled User record.
