import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4

from app.core.database import get_db
from app.core.rate_limit import enforce_rate_limit, limit_per_ip
from app.core.token_revocation import revoke_token
from app.core.security import (ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM,
                               MAINTENANCE_MODE_MESSAGE, SECRET_KEY,
                               create_access_token, get_password_hash,
                               oauth2_scheme, verify_password)
from app.core.system_settings import get_system_setting
from app.models.domain_models import User
from app.schemas.audit_schema import AuditRecordCreateInternal
from app.schemas.user_schema import UNIVERSITY_EMAIL_DOMAIN
from app.services.audit_service import create_audit_record
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, Field, computed_field
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Authentication"],
)

# A valid bcrypt hash of a random value, used only to equalize login timing.
DUMMY_PASSWORD_HASH = get_password_hash(secrets.token_urlsafe(16))


class AuthenticatedUserResponse(BaseModel):
    user_id: int
    name: str
    school_id: str
    email: str
    role: str
    email_verified: bool
    ast_strictness_level: str

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def first_name(self) -> str:
        parts = self.name.split()
        return parts[0] if parts else ""

    @computed_field
    @property
    def last_name(self) -> str:
        parts = self.name.split()
        return " ".join(parts[1:]) if len(parts) > 1 else ""


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


# Matches the audit resource_id limit, so a recorded identifier always fits.
MAX_RECORDED_LOGIN_IDENTIFIER_LENGTH = 100
UNRECOGNIZED_LOGIN_IDENTIFIER = "unrecognized"


def recordable_login_identifier(normalized_email: str) -> str | None:
    """
    The login identifier if it is safe to keep in the audit trail.

    Only a well-formed university email is kept. Anything else may be a
    password typed into the email field, so it is never stored or logged.
    """

    local_part = normalized_email.removesuffix(UNIVERSITY_EMAIL_DOMAIN)

    if (
        not normalized_email.endswith(UNIVERSITY_EMAIL_DOMAIN)
        or not local_part
        or "@" in local_part
        or any(character.isspace() for character in local_part)
        or len(normalized_email) > MAX_RECORDED_LOGIN_IDENTIFIER_LENGTH
    ):
        return None

    return normalized_email


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

    # Per account email, not per IP: every request reaches the app through
    # the platform proxy, so an IP limit would lock out the whole school.
    enforce_rate_limit(
        scope="login",
        identifier=normalized_email,
        limit=10,
        window_seconds=60,
    )

    def raise_invalid(user_obj=None):
        try:
            actor_id = user_obj.user_id if user_obj else None
            identifier = recordable_login_identifier(normalized_email)

            if user_obj:
                res_id = str(user_obj.user_id)
            else:
                res_id = identifier or UNRECOGNIZED_LOGIN_IDENTIFIER

            audit_data = (
                {"email": identifier}
                if identifier
                else {"identifier": UNRECOGNIZED_LOGIN_IDENTIFIER}
            )
            create_audit_record(
                db=db,
                payload=AuditRecordCreateInternal(
                    audit_key=f"login_failed_{actor_id or 'anon'}_{uuid4().hex[:8]}",
                    actor_user_id=actor_id,
                    action_type="login_failed",
                    resource_type="user",
                    resource_id=res_id,
                    outcome="failed",
                    audit_data=audit_data,
                )
            )
        except Exception as exc:
            # Class name only: the exception text can echo the rejected input.
            logger.error(
                "Could not record a failed login attempt (%s).",
                type(exc).__name__,
            )
        raise invalid_credentials_exception()

    if not normalized_email.endswith(UNIVERSITY_EMAIL_DOMAIN):
        raise_invalid(None)

    user = get_user_by_email(
        db=db,
        email=normalized_email,
    )

    if user is None:
        # Spend the same hashing work as a real check so response timing
        # does not reveal which university emails have accounts.
        verify_password(form_data.password, DUMMY_PASSWORD_HASH)
        raise_invalid(None)

    if not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise_invalid(user)

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
    if get_system_setting(db, "maintenance_mode", default=False) and user.role == "student":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=MAINTENANCE_MODE_MESSAGE,
        )

    if user.role not in {
        "student",
        "instructor",
        "admin",
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
            "pwd_ver": user.password_version,
        },
        expires_delta=access_token_expires,
    )

    create_audit_record(
        db=db,
        payload=AuditRecordCreateInternal(
            audit_key=f"login_{user.user_id}_{uuid4().hex[:8]}",
            actor_user_id=user.user_id,
            action_type="login_succeeded",
            resource_type="user",
            resource_id=str(user.user_id),
            outcome="succeeded",
            audit_data={"email": user.email}
        )
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
                # Kept in memory too, so a Redis outage cannot undo it.
                revoke_token(jti, ttl)
    except JWTError:
        # An invalid or expired token is already unusable.
        return

@router.post(
    "/guest",
    response_model=TokenResponse,
    dependencies=[Depends(limit_per_ip("guest", limit=2, window_seconds=60))],
)
def login_guest(db: Session = Depends(get_db)):
    import random
    import secrets
    import uuid

    from app.models.domain_models import Classroom, Enrollment

    # Guest accounts are student accounts, so the student maintenance-mode
    # rule enforced by /login applies here as well.
    if get_system_setting(db, "maintenance_mode", default=False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=MAINTENANCE_MODE_MESSAGE,
        )

    short_id = str(uuid.uuid4())[:6]
    guest_email = f"guest_{short_id}@pampangastateu.edu.ph"

    guest = User(
        email=guest_email,
        name=f"Guest {short_id.upper()}",
        role="student",
        # Guests sign in only through this endpoint. A random, never-disclosed
        # password keeps the ephemeral account from being reachable through
        # /login with a shared, guessable password.
        password_hash=get_password_hash(secrets.token_urlsafe(32)),
        school_id=f"GST{random.randint(1000000, 9999999)}",
        # Guests have no university mailbox to verify. Same as
        # admin-provisioned guests (POST /admin/guests); without it every
        # authenticated request is rejected by get_current_user.
        email_verified=True,
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)
    
    # Auto-enroll guest into dedicated sandbox classroom to avoid polluting real classrooms
    sandbox_class = (
        db.query(Classroom)
        .filter(Classroom.class_code == "SANDBOX01")
        .first()
    )
    if not sandbox_class:
        sandbox_instructor = (
            db.query(User)
            .filter(User.role.in_(["instructor", "admin"]))
            .first()
        )
        if sandbox_instructor:
            sandbox_class = Classroom(
                name="Guest Sandbox Classroom",
                subject_code="DEMO101",
                section="Sandbox",
                class_code="SANDBOX01",
                instructor_id=sandbox_instructor.user_id,
                is_active=True,
            )
            db.add(sandbox_class)
            db.commit()
            db.refresh(sandbox_class)

    if sandbox_class:
        enroll = Enrollment(
            class_id=sandbox_class.class_id,
            student_id=guest.user_id,
            status="active",
            joined_at=datetime.now(timezone.utc),
        )
        db.add(enroll)
        db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(guest.user_id),
            "role": guest.role,
            "name": guest.name,
            "email": guest.email,
            "pwd_ver": guest.password_version,
        },
        expires_delta=access_token_expires,
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=AuthenticatedUserResponse.model_validate(guest)
    )
