import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.domain_models import User


load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256").strip()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

SUPPORTED_JWT_ALGORITHMS = {
    "HS256",
    "HS384",
    "HS512",
}

if len(SECRET_KEY) < 32:
    raise RuntimeError("JWT_SECRET_KEY must be configured with at least 32 characters.")

if ALGORITHM not in SUPPORTED_JWT_ALGORITHMS:
    raise RuntimeError("JWT_ALGORITHM must be one of: HS256, HS384, or HS512.")

if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero.")


password_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],
    deprecated=["bcrypt"],
)

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
        return password_context.verify(
            plain_password,
            password_hash,
        )
    except (UnknownHashError, ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("Password cannot be empty.")

    return password_context.hash(password)


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
        detail="Could not validate authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
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
            algorithms=[ALGORITHM],
        )

        if payload.get("type") != "access":
            raise authentication_error

        subject = payload.get("sub")

        if subject is None:
            raise authentication_error

        user_id = int(subject)

        if user_id <= 0:
            raise authentication_error

    except (JWTError, TypeError, ValueError) as exc:
        raise authentication_error from exc

    user = db.query(User).filter(User.user_id == user_id).first()

    if user is None:
        raise authentication_error

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


# SECURITY BOUNDARY:
# Authorization decisions use the current database record, not the role,
# name, email, or other claims supplied inside the token. This allows account
# deactivation and role corrections to take effect without trusting stale JWT
# claims.

# PARTNER INTEGRATION:
# Celery workers and sandbox services must not reuse browser access tokens as
# permission to execute arbitrary requests. FastAPI first validates the user,
# persists an authorized execution request, and sends only its execution ID
# through the trusted queue adapter.
