from jose import jwt

from app.core.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing_and_verification():
    plain_password = "test12345"
    password_hash = get_password_hash(plain_password)

    assert password_hash != plain_password
    assert verify_password(plain_password, password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_access_token_contains_user_claims():
    token = create_access_token(
        {
            "sub": "1",
            "role": "instructor",
            "name": "Test Instructor",
        }
    )

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )

    assert payload["sub"] == "1"
    assert payload["role"] == "instructor"
    assert payload["name"] == "Test Instructor"
    assert "exp" in payload
