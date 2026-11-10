from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.domain_models import (
    ExecutionRequest,
    PartnerExecutionUpdateRecord,
    User,
)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(
        dbapi_connection,
        _connection_record,
    ) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)

    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    session = testing_session_local()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def create_student(
    db: Session,
    *,
    school_id: str = "0000000001",
    email: str = "student@pampangastateu.edu.ph",
) -> User:
    student = User(
        name="Partner Model Student",
        school_id=school_id,
        email=email,
        role="student",
        password_hash="hashed-password",
        email_verified=True,
        is_active=True,
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    return student


def create_execution_request(
    db: Session,
    *,
    student_id: int,
    correlation_id: str | None = None,
    dispatch_idempotency_key: str | None = None,
    last_partner_sequence: int = 0,
) -> ExecutionRequest:
    execution = ExecutionRequest(
        student_id=student_id,
        task_id=None,
        submission_id=None,
        coding_session_id=None,
        request_kind="run",
        status="queued",
        source_code="print('hello')\n",
        standard_input="",
        stdout="",
        stderr="",
        exit_code=None,
        execution_time_ms=None,
        limit_reason=None,
        worker_task_id=None,
        started_at=None,
        completed_at=None,
        last_partner_sequence=last_partner_sequence,
    )

    if correlation_id is not None:
        execution.correlation_id = correlation_id

    if dispatch_idempotency_key is not None:
        execution.dispatch_idempotency_key = dispatch_idempotency_key

    db.add(execution)
    db.commit()
    db.refresh(execution)

    return execution


def create_partner_update(
    db: Session,
    *,
    execution: ExecutionRequest,
    update_id: str | None = None,
    sequence_number: int = 1,
    status: str = "running",
    payload_digest: str = "a" * 64,
) -> PartnerExecutionUpdateRecord:
    update = PartnerExecutionUpdateRecord(
        update_id=update_id or str(uuid4()),
        execution_id=execution.execution_id,
        correlation_id=execution.correlation_id,
        sequence_number=sequence_number,
        status=status,
        payload_digest=payload_digest,
    )

    db.add(update)
    db.commit()
    db.refresh(update)

    return update


def test_execution_request_generates_partner_identifiers(
    db_session: Session,
):
    student = create_student(db_session)
    execution = create_execution_request(
        db_session,
        student_id=student.user_id,
    )

    assert str(UUID(execution.execution_id)) == execution.execution_id
    assert str(UUID(execution.correlation_id)) == execution.correlation_id
    assert (
        str(UUID(execution.dispatch_idempotency_key))
        == execution.dispatch_idempotency_key
    )
    assert execution.last_partner_sequence == 0


def test_execution_request_partner_identifiers_are_unique(
    db_session: Session,
):
    student = create_student(db_session)
    correlation_id = str(uuid4())
    idempotency_key = str(uuid4())

    create_execution_request(
        db_session,
        student_id=student.user_id,
        correlation_id=correlation_id,
        dispatch_idempotency_key=idempotency_key,
    )

    duplicate_correlation = ExecutionRequest(
        student_id=student.user_id,
        request_kind="run",
        status="queued",
        source_code="print('second')\n",
        standard_input="",
        stdout="",
        stderr="",
        correlation_id=correlation_id,
        dispatch_idempotency_key=str(uuid4()),
        last_partner_sequence=0,
    )
    db_session.add(duplicate_correlation)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()

    duplicate_idempotency = ExecutionRequest(
        student_id=student.user_id,
        request_kind="run",
        status="queued",
        source_code="print('third')\n",
        standard_input="",
        stdout="",
        stderr="",
        correlation_id=str(uuid4()),
        dispatch_idempotency_key=idempotency_key,
        last_partner_sequence=0,
    )
    db_session.add(duplicate_idempotency)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_execution_request_rejects_negative_partner_sequence(
    db_session: Session,
):
    student = create_student(db_session)

    execution = ExecutionRequest(
        student_id=student.user_id,
        request_kind="run",
        status="queued",
        source_code="print('hello')\n",
        standard_input="",
        stdout="",
        stderr="",
        correlation_id=str(uuid4()),
        dispatch_idempotency_key=str(uuid4()),
        last_partner_sequence=-1,
    )

    db_session.add(execution)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_partner_update_persists_immutable_identity_metadata(
    db_session: Session,
):
    student = create_student(db_session)
    execution = create_execution_request(
        db_session,
        student_id=student.user_id,
    )
    update_id = str(uuid4())

    update = create_partner_update(
        db_session,
        execution=execution,
        update_id=update_id,
        sequence_number=1,
        status="running",
        payload_digest="b" * 64,
    )

    assert update.update_id == update_id
    assert update.execution_id == execution.execution_id
    assert update.correlation_id == execution.correlation_id
    assert update.sequence_number == 1
    assert update.status == "running"
    assert update.payload_digest == "b" * 64
    assert update.accepted_at is not None


def test_partner_update_relationship_is_bidirectional(
    db_session: Session,
):
    student = create_student(db_session)
    execution = create_execution_request(
        db_session,
        student_id=student.user_id,
    )
    update = create_partner_update(
        db_session,
        execution=execution,
    )

    db_session.refresh(execution)

    assert update.execution_request.execution_id == execution.execution_id
    assert [item.update_id for item in execution.partner_updates] == [update.update_id]


def test_partner_update_id_is_globally_unique(
    db_session: Session,
):
    student = create_student(db_session)
    first_execution = create_execution_request(
        db_session,
        student_id=student.user_id,
    )
    second_execution = create_execution_request(
        db_session,
        student_id=student.user_id,
    )
    update_id = str(uuid4())

    create_partner_update(
        db_session,
        execution=first_execution,
        update_id=update_id,
    )

    duplicate_update = PartnerExecutionUpdateRecord(
        update_id=update_id,
        execution_id=second_execution.execution_id,
        correlation_id=second_execution.correlation_id,
        sequence_number=1,
        status="running",
        payload_digest="c" * 64,
    )
    db_session.add(duplicate_update)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_partner_update_sequence_is_unique_per_execution(
    db_session: Session,
):
    student = create_student(db_session)
    execution = create_execution_request(
        db_session,
        student_id=student.user_id,
    )

    create_partner_update(
        db_session,
        execution=execution,
        sequence_number=1,
    )

    duplicate_sequence = PartnerExecutionUpdateRecord(
        update_id=str(uuid4()),
        execution_id=execution.execution_id,
        correlation_id=execution.correlation_id,
        sequence_number=1,
        status="completed",
        payload_digest="d" * 64,
    )
    db_session.add(duplicate_sequence)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


@pytest.mark.parametrize(
    "sequence_number",
    [
        0,
        -1,
    ],
)
def test_partner_update_requires_positive_sequence(
    db_session: Session,
    sequence_number: int,
):
    student = create_student(db_session)
    execution = create_execution_request(
        db_session,
        student_id=student.user_id,
    )

    invalid_update = PartnerExecutionUpdateRecord(
        update_id=str(uuid4()),
        execution_id=execution.execution_id,
        correlation_id=execution.correlation_id,
        sequence_number=sequence_number,
        status="running",
        payload_digest="e" * 64,
    )
    db_session.add(invalid_update)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


@pytest.mark.parametrize(
    "payload_digest",
    [
        "",
        "a" * 63,
        "a" * 65,
    ],
)
def test_partner_update_requires_sha256_length_digest(
    db_session: Session,
    payload_digest: str,
):
    student = create_student(db_session)
    execution = create_execution_request(
        db_session,
        student_id=student.user_id,
    )

    invalid_update = PartnerExecutionUpdateRecord(
        update_id=str(uuid4()),
        execution_id=execution.execution_id,
        correlation_id=execution.correlation_id,
        sequence_number=1,
        status="running",
        payload_digest=payload_digest,
    )
    db_session.add(invalid_update)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_partner_update_rejects_unknown_status(
    db_session: Session,
):
    student = create_student(db_session)
    execution = create_execution_request(
        db_session,
        student_id=student.user_id,
    )

    invalid_update = PartnerExecutionUpdateRecord(
        update_id=str(uuid4()),
        execution_id=execution.execution_id,
        correlation_id=execution.correlation_id,
        sequence_number=1,
        status="queued",
        payload_digest="f" * 64,
    )
    db_session.add(invalid_update)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_partner_update_model_excludes_sensitive_payload_fields():
    prohibited_fields = {
        "source_code",
        "standard_input",
        "stdout",
        "stderr",
        "password",
        "password_hash",
        "otp",
        "otp_code",
        "jwt",
        "access_token",
        "refresh_token",
        "api_key",
        "shared_secret",
        "score",
        "max_score",
        "feedback",
        "ast_findings",
        "similarity_details",
        "session_telemetry",
        "clipboard_content",
        "pasted_text",
        "browsing_history",
        "keystrokes",
        "screen_recording",
        "webcam",
        "microphone",
        "plagiarism_verdict",
        "cheating_verdict",
        "misconduct_verdict",
    }

    actual_fields = {
        column.name for column in PartnerExecutionUpdateRecord.__table__.columns
    }

    assert prohibited_fields.isdisjoint(actual_fields)
