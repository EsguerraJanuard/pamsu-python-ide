import os
from collections.abc import Generator
from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


os.environ.setdefault(
    "DATABASE_URL",
    "sqlite:///./test_otp_bootstrap.db",
)
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-jwt-secret-key-with-at-least-thirty-two-characters",
)
os.environ.setdefault(
    "OTP_SECRET_KEY",
    "test-otp-secret-key-with-at-least-thirty-two-characters",
)
os.environ.setdefault("OTP_EXPIRE_SECONDS", "600")
os.environ.setdefault("OTP_RESEND_COOLDOWN_SECONDS", "60")
os.environ.setdefault("OTP_MAX_ATTEMPTS", "5")
os.environ.setdefault("OTP_MAX_RESENDS", "3")


from app.core.database import Base
from app.integrations.otp_email import (
    OTPEmailAdapter,
    OTPEmailAdapterRejectedError,
    OTPEmailAdapterUnavailableError,
    validate_otp_email_adapter,
)
from app.models.domain_models import (
    InstructorAllowlist,
    OTPChallenge,
    PendingRegistration,
    User,
)
from app.schemas.otp_schema import (
    OTPVerificationRequest,
    RegistrationStartRequest,
)
from app.services.otp_service import (
    OTPDeliveryAdapter,
    OTPDeliveryError,
    OTPInvalidCodeError,
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
                "expires_in_seconds": expires_in_seconds,
            }
        )

    @property
    def last_code(self) -> str:
        return str(self.deliveries[-1]["otp_code"])


class RejectedOTPDeliveryAdapter:
    def send_otp(
        self,
        *,
        recipient_email: str,
        otp_code: str,
        purpose: str,
        expires_in_seconds: int,
    ) -> None:
        raise OTPEmailAdapterRejectedError("Simulated provider rejection.")


class UnexpectedFailureOTPDeliveryAdapter:
    def send_otp(
        self,
        *,
        recipient_email: str,
        otp_code: str,
        purpose: str,
        expires_in_seconds: int,
    ) -> None:
        raise RuntimeError("Simulated unexpected provider failure.")


class IncompatibleOTPDeliveryAdapter:
    pass


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

    db = testing_session()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def make_registration_request(
    *,
    email: str = "student@pampangastateu.edu.ph",
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


def test_service_keeps_backward_compatible_adapter_alias():
    assert OTPDeliveryAdapter is OTPEmailAdapter


def test_runtime_adapter_validation_accepts_compatible_adapter():
    adapter = FakeOTPDeliveryAdapter()

    assert validate_otp_email_adapter(adapter) is adapter


def test_runtime_adapter_validation_rejects_incompatible_adapter():
    with pytest.raises(
        OTPEmailAdapterUnavailableError,
        match="compatible OTP email-delivery adapter",
    ):
        validate_otp_email_adapter(IncompatibleOTPDeliveryAdapter())


def test_start_registration_stores_only_hashed_otp(
    db_session: Session,
):
    delivery_adapter = FakeOTPDeliveryAdapter()

    response = start_registration(
        db=db_session,
        registration_data=make_registration_request(),
        delivery_adapter=delivery_adapter,
    )

    assert len(response.challenge_id) == 36
    assert response.email == "student@pampangastateu.edu.ph"
    assert len(delivery_adapter.last_code) == 6
    assert delivery_adapter.last_code.isdigit()

    challenge = db_session.get(
        OTPChallenge,
        response.challenge_id,
    )

    pending_registration = (
        db_session.query(PendingRegistration)
        .filter(PendingRegistration.challenge_id == response.challenge_id)
        .first()
    )

    assert challenge is not None
    assert pending_registration is not None
    assert challenge.otp_hash != delivery_adapter.last_code
    assert pending_registration.password_hash != ("SecurePassword123")

    response_data = response.model_dump()

    assert "otp_code" not in response_data
    assert delivery_adapter.last_code not in str(response_data)
    assert delivery_adapter.last_code not in challenge.otp_hash


def test_valid_otp_creates_verified_student(
    db_session: Session,
):
    delivery_adapter = FakeOTPDeliveryAdapter()

    challenge_response = start_registration(
        db=db_session,
        registration_data=make_registration_request(),
        delivery_adapter=delivery_adapter,
    )

    registration_response = verify_registration_otp(
        db=db_session,
        verification_data=OTPVerificationRequest(
            challenge_id=challenge_response.challenge_id,
            otp_code=delivery_adapter.last_code,
        ),
    )

    assert registration_response.user.role == "student"
    assert registration_response.user.email_verified is True
    assert registration_response.user.is_active is True
    assert registration_response.user.school_id == "0012345678"

    user = (
        db_session.query(User)
        .filter(User.email == "student@pampangastateu.edu.ph")
        .first()
    )

    challenge = db_session.get(
        OTPChallenge,
        challenge_response.challenge_id,
    )

    pending_registration = (
        db_session.query(PendingRegistration)
        .filter(PendingRegistration.challenge_id == challenge_response.challenge_id)
        .first()
    )

    assert user is not None
    assert challenge is not None
    assert challenge.consumed_at is not None
    assert pending_registration is None


def test_allowlisted_email_becomes_instructor(
    db_session: Session,
):
    instructor_email = "faculty@pampangastateu.edu.ph"

    db_session.add(
        InstructorAllowlist(
            email=instructor_email,
            is_active=True,
        )
    )
    db_session.commit()

    delivery_adapter = FakeOTPDeliveryAdapter()

    challenge_response = start_registration(
        db=db_session,
        registration_data=make_registration_request(
            email=instructor_email,
            school_id="0012345679",
        ),
        delivery_adapter=delivery_adapter,
    )

    registration_response = verify_registration_otp(
        db=db_session,
        verification_data=OTPVerificationRequest(
            challenge_id=challenge_response.challenge_id,
            otp_code=delivery_adapter.last_code,
        ),
    )

    assert registration_response.user.role == "instructor"


def test_invalid_otp_increments_attempt_count(
    db_session: Session,
):
    delivery_adapter = FakeOTPDeliveryAdapter()

    challenge_response = start_registration(
        db=db_session,
        registration_data=make_registration_request(),
        delivery_adapter=delivery_adapter,
    )

    invalid_code = "999999" if delivery_adapter.last_code != "999999" else "000000"

    with pytest.raises(OTPInvalidCodeError) as error:
        verify_registration_otp(
            db=db_session,
            verification_data=OTPVerificationRequest(
                challenge_id=challenge_response.challenge_id,
                otp_code=invalid_code,
            ),
        )

    db_session.expire_all()

    challenge = db_session.get(
        OTPChallenge,
        challenge_response.challenge_id,
    )

    assert challenge is not None
    assert challenge.attempt_count == 1
    assert error.value.remaining_attempts == 4


def test_resend_updates_challenge_and_delivers_new_email(
    db_session: Session,
):
    delivery_adapter = FakeOTPDeliveryAdapter()

    challenge_response = start_registration(
        db=db_session,
        registration_data=make_registration_request(),
        delivery_adapter=delivery_adapter,
    )

    challenge = db_session.get(
        OTPChallenge,
        challenge_response.challenge_id,
    )

    assert challenge is not None

    challenge.last_sent_at = utc_now() - timedelta(seconds=120)
    db_session.commit()

    resend_response = resend_registration_otp(
        db=db_session,
        challenge_id=challenge_response.challenge_id,
        delivery_adapter=delivery_adapter,
    )

    db_session.refresh(challenge)

    assert resend_response.challenge_id == (challenge_response.challenge_id)
    assert challenge.resend_count == 1
    assert challenge.attempt_count == 0
    assert len(delivery_adapter.deliveries) == 2
    assert (
        delivery_adapter.deliveries[-1]["recipient_email"]
        == "student@pampangastateu.edu.ph"
    )
    assert delivery_adapter.deliveries[-1]["purpose"] == "registration"
    assert delivery_adapter.deliveries[-1]["expires_in_seconds"] == 600


@pytest.mark.parametrize(
    "delivery_adapter",
    [
        RejectedOTPDeliveryAdapter(),
        UnexpectedFailureOTPDeliveryAdapter(),
        IncompatibleOTPDeliveryAdapter(),
    ],
)
def test_start_registration_rolls_back_when_delivery_fails(
    db_session: Session,
    delivery_adapter: object,
):
    with pytest.raises(
        OTPDeliveryError,
        match="verification email could not be delivered",
    ):
        start_registration(
            db=db_session,
            registration_data=make_registration_request(),
            delivery_adapter=delivery_adapter,
        )

    assert db_session.query(OTPChallenge).count() == 0
    assert db_session.query(PendingRegistration).count() == 0
    assert db_session.query(User).count() == 0


@pytest.mark.parametrize(
    "delivery_adapter",
    [
        RejectedOTPDeliveryAdapter(),
        UnexpectedFailureOTPDeliveryAdapter(),
        IncompatibleOTPDeliveryAdapter(),
    ],
)
def test_resend_rolls_back_challenge_when_delivery_fails(
    db_session: Session,
    delivery_adapter: object,
):
    working_adapter = FakeOTPDeliveryAdapter()

    challenge_response = start_registration(
        db=db_session,
        registration_data=make_registration_request(),
        delivery_adapter=working_adapter,
    )

    challenge = db_session.get(
        OTPChallenge,
        challenge_response.challenge_id,
    )

    assert challenge is not None

    challenge.last_sent_at = utc_now() - timedelta(seconds=120)
    db_session.commit()
    db_session.refresh(challenge)

    original_hash = challenge.otp_hash
    original_attempt_count = challenge.attempt_count
    original_resend_count = challenge.resend_count
    original_expires_at = challenge.expires_at
    original_last_sent_at = challenge.last_sent_at

    with pytest.raises(
        OTPDeliveryError,
        match="verification email could not be delivered",
    ):
        resend_registration_otp(
            db=db_session,
            challenge_id=challenge.challenge_id,
            delivery_adapter=delivery_adapter,
        )

    db_session.expire_all()

    persisted_challenge = db_session.get(
        OTPChallenge,
        challenge.challenge_id,
    )

    assert persisted_challenge is not None
    assert persisted_challenge.otp_hash == original_hash
    assert persisted_challenge.attempt_count == original_attempt_count
    assert persisted_challenge.resend_count == original_resend_count
    assert persisted_challenge.expires_at == original_expires_at
    assert persisted_challenge.last_sent_at == original_last_sent_at


def test_delivery_adapter_receives_plaintext_otp_only_transiently(
    db_session: Session,
):
    delivery_adapter = FakeOTPDeliveryAdapter()

    response = start_registration(
        db=db_session,
        registration_data=make_registration_request(),
        delivery_adapter=delivery_adapter,
    )

    challenge = db_session.get(
        OTPChallenge,
        response.challenge_id,
    )

    assert challenge is not None

    delivered_code = delivery_adapter.last_code

    persisted_values = {
        str(value)
        for column in challenge.__table__.columns
        for value in [getattr(challenge, column.name)]
        if value is not None
    }

    assert delivered_code not in persisted_values
    assert delivered_code not in str(response.model_dump())


def test_otp_models_exclude_plaintext_and_provider_credentials():
    prohibited_fields = {
        "otp_code",
        "plaintext_otp",
        "smtp_password",
        "provider_api_key",
        "provider_token",
        "access_token",
        "shared_secret",
    }

    for model in (
        OTPChallenge,
        PendingRegistration,
    ):
        actual_fields = {column.name for column in model.__table__.columns}

        assert prohibited_fields.isdisjoint(actual_fields)
