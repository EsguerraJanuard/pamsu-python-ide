from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    verify_password,
    oauth2_scheme,
    SECRET_KEY,
    ALGORITHM,
)
from app.core.redis_client import redis_client
from jose import jwt
from datetime import datetime, timezone
from app.models.domain_models import User
from app.schemas.user_schema import UNIVERSITY_EMAIL_DOMAIN


router = APIRouter(
    tags=["Authentication"],
)


class AuthenticatedUserResponse(BaseModel):
    user_id: int
    name: str
    school_id: str
    email: str
    role: Literal["student", "instructor"]
    email_verified: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str = Field(
        description="JWT bearer access token.",
    )
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(
        gt=0,
        description="Token lifetime in seconds.",
    )
    user: AuthenticatedUserResponse


def invalid_credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    return db.query(User).filter(func.lower(User.email) == email).first()


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in using a verified university email",
    description=(
        "The OAuth2 `username` form field must contain the user's "
        "PAMSU university email address. Account roles are read only "
        "from the backend-controlled user record."
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid email or password.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "The account is inactive, unverified, or has an invalid backend role."
            ),
        },
    },
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    normalized_email = form_data.username.strip().lower()

    if not normalized_email.endswith(UNIVERSITY_EMAIL_DOMAIN):
        raise invalid_credentials_exception()

    user = get_user_by_email(
        db=db,
        email=normalized_email,
    )

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
            detail=("University email verification is required."),
        )

    if user.role not in {
        "student",
        "instructor",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=("This account does not have a valid system role."),
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
# The OAuth2 username field contains the verified university email.
# The client cannot select or modify its account role.
# JWT identity and role claims come only from the persisted User record.

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the current access token",
)
def logout(
    token: str = Depends(oauth2_scheme)
) -> None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        exp = payload.get("exp")
        
        if jti and exp:
            now = datetime.now(timezone.utc).timestamp()
            ttl = int(exp - now)
            if ttl > 0:
                redis_client.setex(f"blacklist:{jti}", ttl, "revoked")
    except Exception:
        pass
