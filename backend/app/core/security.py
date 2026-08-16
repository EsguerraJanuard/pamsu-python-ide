from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.domain_models import User
from app.core.redis_client import redis_client

settings = get_settings()

SECRET_KEY = settings.jwt_secret_key.get_secret_value()
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

SUPPORTED_JWT_ALGORITHMS = {
    "HS256",
    "HS384",
    "HS512",
}


# Passlib removed in favor of raw bcrypt

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login",
)


def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    if not plain_password or not password_hash:
        return False

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (
        ValueError,
        TypeError,
    ):
        return False


def get_password_hash(
    password: str,
) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("Password cannot be empty.")

    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_bytes.decode("utf-8")


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    subject = data.get("sub")

    if subject is None or not str(subject).strip():
        raise ValueError("Access tokens require a non-empty subject claim.")

    current_time = datetime.now(timezone.utc)

    expiration_time = current_time + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    token_data = data.copy()

    token_data.update(
        {
            "sub": str(subject),
            "type": "access",
            "iat": current_time,
            "exp": expiration_time,
            "jti": str(uuid4()),
        }
    )

    return jwt.encode(
        token_data,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=("Could not validate authentication credentials."),
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    authentication_error = credentials_exception()

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[
                ALGORITHM,
            ],
        )

        if payload.get("type") != "access":
            raise authentication_error

        subject = payload.get("sub")

        if subject is None:
            raise authentication_error

        user_id = int(subject)

        if user_id <= 0:
            raise authentication_error

        jti = payload.get("jti")
        if jti and redis_client.get(f"blacklist:{jti}"):
            raise authentication_error
        
        pwd_ver = payload.get("pwd_ver", 1)

    except (
        JWTError,
        TypeError,
        ValueError,
    ) as error:
        raise authentication_error from error

    user = (
        db.query(User)
        .filter(
            User.user_id == user_id,
        )
        .first()
    )

    if user is None:
        raise authentication_error

    if pwd_ver != user.password_version:
        raise authentication_error

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

    return user


def get_current_instructor(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "instructor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor access required.",
        )

    return current_user


def get_current_student(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required.",
        )

    return current_user


# CONFIGURATION BOUNDARY:
# JWT signing configuration is loaded only through the validated immutable
# application settings object. This module does not independently parse
# process environment variables.

# SECRET HANDLING BOUNDARY:
# The JWT signing secret is unwrapped only for token signing and decoding.
# It must never be logged, returned, stored in database records, or exposed
# through health and readiness responses.

# SECURITY BOUNDARY:
# Authorization decisions use the current database record, not the role,
# name, email, or other claims supplied inside the token. Account
# deactivation and role corrections therefore take effect without trusting
# stale JWT claims.

# TOKEN BOUNDARY:
# Access tokens contain a string subject, access-token type, issued-at time,
# expiration time, and unique token identifier. Client-supplied expiration
# settings do not alter the configured default token lifetime.

# PARTNER INTEGRATION:
# Celery workers and sandbox services must not reuse browser access tokens as
# permission to execute arbitrary requests. FastAPI first validates the user,
# persists an authorized execution request, and sends only its execution ID
# through the trusted queue adapter.
