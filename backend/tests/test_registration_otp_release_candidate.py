import os
from collections.abc import Generator
from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


os.environ.setdefault(
    "DATABASE_URL",
    "sqlite:///./test_registration_otp_rc_bootstrap.db",
)
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-jwt-secret-key-with-at-least-thirty-two-characters",
)
os.environ.setdefault(
    "OTP_SECRET_KEY",
    "test-otp-secret-key-with-at-least-thirty-two-characters",
)
os.environ.setdefault(
    "OTP_EXPIRE_SECONDS",
    "600",
)
os.environ.setdefault(
    "OTP_RESEND_COOLDOWN_SECONDS",
    "60",
)
os.environ.setdefault(
    "OTP_MAX_ATTEMPTS",
    "5",
)
os.environ.setdefault(
    "OTP_MAX_RESENDS",
    "3",
)


from app.core.database import Base
from app.core.security import get_password_hash
from app.models.domain_models import (
    OTPChallenge,
    PendingRegistration,
    User,
)
from app.schemas.otp_schema import (
    OTPVerificationRequest,
    RegistrationStartRequest,
)
from app.services.otp_service import (
    OTP_MAX_ATTEMPTS,
    OTP_MAX_RESENDS,
    OTP_RESEND_COOLDOWN_SECONDS,
    OTPAttemptLimitError,
    OTPChallengeExpiredError,
    OTPResendLimitError,
    OTPResendTooSoonError,
    RegistrationConflictError,
    resend_registration_otp,
    start_registration,
    utc_now,
    verify_registration_otp,
)


class FakeOTPDeliveryAdapter:
    def __init__(self) -> None:
        self.deliveries: list[dict[str, object]] = []

    def send_otp(
        self,
        *,
        recipient_email: str,
        otp_code: str,
        purpose: str,
        expires_in_seconds: int,
    ) -> None:
        self.deliveries.append(
            {
                "recipient_email": recipient_email,
                "otp_code": otp_code,
                "purpose": purpose,
                "expires_in_seconds": (expires_in_seconds),
            }
        )

    @property
    def last_code(self) -> str:
        return str(self.deliveries[-1]["otp_code"])


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
    )

    testing_session = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)

    session = testing_session()

    try:
        yield session
    finally:
        session.close()

        Base.metadata.drop_all(bind=engine)

        engine.dispose()


def make_registration_request(
    *,
    email: str = ("student@pampangastateu.edu.ph"),
    school_id: str = "0012345678",
) -> RegistrationStartRequest:
    return RegistrationStartRequest(
        name="Juan Dela Cruz",
        school_id=school_id,
        email=email,
        password="SecurePassword123",
        confirm_password="SecurePassword123",
        data_collection_acknowledged=True,
    )


def create_existing_user(
    db_session: Session,
    *,
    email: str,
    school_id: str,
) -> User:
    user = User(
        name="Existing User",
        school_id=school_id,
        email=email.lower(),
        role="student",
        password_hash=get_password_hash("ExistingPassword123"),
        email_verified=True,
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def get_challenge(
    db_session: Session,
    *,
    challenge_id: str,
) -> OTPChallenge:
    challenge = db_session.get(
        OTPChallenge,
        challenge_id,
    )

    assert challenge is not None

    return challenge


def make_invalid_code(
    valid_code: str,
) -> str:
    if valid_code != "999999":
        return "999999"

    return "000000"


def test_school_id_persists_as_string(
    db_session: Session,
) -> None:
    delivery_adapter = FakeOTPDeliveryAdapter()

    challenge_response = start_registration(
        db=db_session,
        registration_data=(make_registration_request(school_id="0012345678")),
        delivery_adapter=(delivery_adapter),
    )

    verify_registration_otp(
        db=db_session,
        verification_data=(
            OTPVerificationRequest(
                challenge_id=(challenge_response.challenge_id),
                otp_code=(delivery_adapter.last_code),
            )
        ),
    )

    db_session.expire_all()

    persisted_user = (
        db_session.query(User)
        .filter(User.email == ("student@pampangastateu.edu.ph"))
        .one()
    )

    assert isinstance(
        persisted_user.school_id,
        str,
    )
    assert persisted_user.school_id == ("0012345678")


def test_existing_email_blocks_registration(
    db_session: Session,
) -> None:
    create_existing_user(
        db_session,
        email=("existing@pampangastateu.edu.ph"),
        school_id="0000000001",
    )

    delivery_adapter = FakeOTPDeliveryAdapter()

    with pytest.raises(
        RegistrationConflictError,
        match="university email",
    ):
        start_registration(
            db=db_session,
            registration_data=(
                make_registration_request(
                    email=("EXISTING@pampangastateu.edu.ph"),
                    school_id=("0000000002"),
                )
            ),
            delivery_adapter=(delivery_adapter),
        )

    assert delivery_adapter.deliveries == []
    assert db_session.query(OTPChallenge).count() == 0
    assert db_session.query(PendingRegistration).count() == 0


def test_existing_school_id_blocks_registration(
    db_session: Session,
) -> None:
    create_existing_user(
        db_session,
        email=("existing@pampangastateu.edu.ph"),
        school_id="0000000003",
    )

    delivery_adapter = FakeOTPDeliveryAdapter()

    with pytest.raises(
        RegistrationConflictError,
        match="school ID",
    ):
        start_registration(
            db=db_session,
            registration_data=(
                make_registration_request(
                    email=("different@pampangastateu.edu.ph"),
                    school_id=("0000000003"),
                )
            ),
            delivery_adapter=(delivery_adapter),
        )

    assert delivery_adapter.deliveries == []
    assert db_session.query(OTPChallenge).count() == 0
    assert db_session.query(PendingRegistration).count() == 0


def test_expired_otp_is_rejected(
    db_session: Session,
) -> None:
    delivery_adapter = FakeOTPDeliveryAdapter()

    challenge_response = start_registration(
        db=db_session,
        registration_data=(make_registration_request()),
        delivery_adapter=(delivery_adapter),
    )

    challenge = get_challenge(
        db_session,
        challenge_id=(challenge_response.challenge_id),
    )

    challenge.expires_at = utc_now() - timedelta(seconds=1)

    db_session.commit()

    with pytest.raises(
        OTPChallengeExpiredError,
        match="expired",
    ):
        verify_registration_otp(
            db=db_session,
            verification_data=(
                OTPVerificationRequest(
                    challenge_id=(challenge_response.challenge_id),
                    otp_code=(delivery_adapter.last_code),
                )
            ),
        )

    db_session.expire_all()

    persisted_challenge = get_challenge(
        db_session,
        challenge_id=(challenge_response.challenge_id),
    )

    assert persisted_challenge.consumed_at is None
    assert db_session.query(User).count() == 0
    assert db_session.query(PendingRegistration).count() == 1


def test_maximum_otp_attempts_are_enforced(
    db_session: Session,
) -> None:
    delivery_adapter = FakeOTPDeliveryAdapter()

    challenge_response = start_registration(
        db=db_session,
        registration_data=(make_registration_request()),
        delivery_adapter=(delivery_adapter),
    )

    challenge = get_challenge(
        db_session,
        challenge_id=(challenge_response.challenge_id),
    )

    assert challenge.max_attempts == (OTP_MAX_ATTEMPTS)

    challenge.attempt_count = challenge.max_attempts - 1

    db_session.commit()

    invalid_code = make_invalid_code(delivery_adapter.last_code)

    with pytest.raises(
        OTPAttemptLimitError,
        match="maximum number",
    ):
        verify_registration_otp(
            db=db_session,
            verification_data=(
                OTPVerificationRequest(
                    challenge_id=(challenge_response.challenge_id),
                    otp_code=invalid_code,
                )
            ),
        )

    db_session.expire_all()

    persisted_challenge = get_challenge(
        db_session,
        challenge_id=(challenge_response.challenge_id),
    )

    assert persisted_challenge.attempt_count == OTP_MAX_ATTEMPTS
    assert persisted_challenge.consumed_at is None

    with pytest.raises(
        OTPAttemptLimitError,
        match="maximum number",
    ):
        verify_registration_otp(
            db=db_session,
            verification_data=(
                OTPVerificationRequest(
                    challenge_id=(challenge_response.challenge_id),
                    otp_code=(delivery_adapter.last_code),
                )
            ),
        )

    assert db_session.query(User).count() == 0


def test_resend_cooldown_is_enforced(
    db_session: Session,
) -> None:
    delivery_adapter = FakeOTPDeliveryAdapter()

    challenge_response = start_registration(
        db=db_session,
        registration_data=(make_registration_request()),
        delivery_adapter=(delivery_adapter),
    )

    challenge = get_challenge(
        db_session,
        challenge_id=(challenge_response.challenge_id),
    )

    original_hash = challenge.otp_hash
    original_expiration = challenge.expires_at

    with pytest.raises(
        OTPResendTooSoonError,
        match="too soon",
    ) as error:
        resend_registration_otp(
            db=db_session,
            challenge_id=(challenge_response.challenge_id),
            delivery_adapter=(delivery_adapter),
        )

    assert error.value.retry_after_seconds > 0
    assert error.value.retry_after_seconds <= (OTP_RESEND_COOLDOWN_SECONDS)

    db_session.expire_all()

    persisted_challenge = get_challenge(
        db_session,
        challenge_id=(challenge_response.challenge_id),
    )

    assert persisted_challenge.resend_count == 0
    assert persisted_challenge.otp_hash == original_hash
    assert persisted_challenge.expires_at == original_expiration
    assert len(delivery_adapter.deliveries) == 1


def test_maximum_otp_resends_are_enforced(
    db_session: Session,
) -> None:
    delivery_adapter = FakeOTPDeliveryAdapter()

    challenge_response = start_registration(
        db=db_session,
        registration_data=(make_registration_request()),
        delivery_adapter=(delivery_adapter),
    )

    challenge = get_challenge(
        db_session,
        challenge_id=(challenge_response.challenge_id),
    )

    challenge.resend_count = OTP_MAX_RESENDS
    challenge.last_sent_at = utc_now() - timedelta(
        seconds=(OTP_RESEND_COOLDOWN_SECONDS + 1)
    )

    original_hash = challenge.otp_hash

    db_session.commit()

    with pytest.raises(
        OTPResendLimitError,
        match="maximum number",
    ):
        resend_registration_otp(
            db=db_session,
            challenge_id=(challenge_response.challenge_id),
            delivery_adapter=(delivery_adapter),
        )

    db_session.expire_all()

    persisted_challenge = get_challenge(
        db_session,
        challenge_id=(challenge_response.challenge_id),
    )

    assert persisted_challenge.resend_count == OTP_MAX_RESENDS
    assert persisted_challenge.otp_hash == original_hash
    assert len(delivery_adapter.deliveries) == 1
