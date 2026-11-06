import pytest
from jose import jwt

from app.core.security import (
    ALGORITHM,
    ROLE_CLAIM,
    SECRET_KEY,
    create_access_token,
    create_user_access_token,
    get_password_hash,
    verify_password,
)
from app.models.domain_models import User


def test_password_hashing_and_verification():
    plain_password = "test12345"
    password_hash = get_password_hash(plain_password)

    assert password_hash != plain_password
    assert verify_password(plain_password, password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_access_token_keeps_the_claims_it_is_given():
    token = create_access_token(
        {
            "sub": "1",
            ROLE_CLAIM: "instructor",
        }
    )

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )

    assert payload["sub"] == "1"
    assert payload[ROLE_CLAIM] == "instructor"
    assert payload["type"] == "access"
    assert "exp" in payload


# Sign-in tokens carry only these. Name, email and the rest of the profile
# come back in the response body (`user`), not inside the token.
MINIMAL_CLAIMS = {"sub", ROLE_CLAIM, "pwd_ver", "type", "iat", "exp", "jti"}


@pytest.mark.parametrize("role", ["student", "instructor", "admin"])
def test_login_token_has_only_the_minimal_claims(client, db_session, role):
    user = User(
        name="Maria Clara Dela Cruz",
        email=f"mcdc.{role}@pampangastateu.edu.ph",
        role=role,
        school_id={"student": "2026000001", "instructor": "FAC0000001", "admin": "ADM0000001"}[role],
        password_hash=get_password_hash("Correct#2026"),
        email_verified=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/login",
        data={"username": user.email, "password": "Correct#2026"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    payload = jwt.decode(body["access_token"], SECRET_KEY, algorithms=[ALGORITHM])

    assert set(payload) == MINIMAL_CLAIMS
    assert payload["sub"] == str(user.user_id)
    assert payload[ROLE_CLAIM] == role
    assert payload["pwd_ver"] == user.password_version
    # The profile is in the response body, never in the token.
    assert body["user"]["name"] == "Maria Clara Dela Cruz"
    assert body["user"]["email"] == user.email
    assert body["user"]["role"] == role
    assert body["user"]["is_guest"] is False
    assert user.email not in body["access_token"]

    # The token still works for an authenticated request.
    me = client.get(
        "/notifications/",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code != 401


def test_guest_token_has_only_the_minimal_claims(client):
    response = client.post("/guest")

    assert response.status_code == 200, response.text
    body = response.json()
    payload = jwt.decode(body["access_token"], SECRET_KEY, algorithms=[ALGORITHM])

    assert set(payload) == MINIMAL_CLAIMS
    assert payload[ROLE_CLAIM] == "student"
    assert body["user"]["is_guest"] is True


def test_password_change_still_ends_minimal_tokens(client, db_session):
    user = User(
        name="Version Check",
        email="version.check@pampangastateu.edu.ph",
        role="student",
        school_id="2026000002",
        password_hash=get_password_hash("Correct#2026"),
        email_verified=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_user_access_token(user)
    user.password_version += 1
    db_session.commit()

    response = client.get("/notifications/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
