from datetime import datetime, timedelta, timezone
import os
from typing import Any, Optional

from jose import jwt
from passlib.context import CryptContext


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-key-before-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return password_context.verify(plain_password, password_hash)


def get_password_hash(password: str) -> str:
    return password_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    token_data = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    token_data.update({"exp": expire})

    encoded_jwt = jwt.encode(
        token_data,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return encoded_jwt
