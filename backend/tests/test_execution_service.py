from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.domain_models import (
    ExecutionRequest,
    PartnerExecutionUpdateRecord,
    Task,
    User,
)
from app.schemas.execution_schema import (
    PartnerExecutionLimits,
    PartnerExecutionResultUpdate,
)
from app.services.execution_service import (
    ExecutionPartnerCorrelationError,
    ExecutionPartnerReplayConflictError,
    ExecutionPartnerSequenceConflictError,
    ExecutionPersistenceError,
    ExecutionStateConflictError,
    apply_partner_execution_result_update,
    assign_worker_task_id,
    build_partner_execution_dispatch,
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


def create_user(
    db: Session,
    *,
    name: str,
    school_id: str,
    email: str,
    role: str,
) -> User:
    user = User(
        name=name,
        school_id=school_id,
        email=email,
        role=role,
        password_hash="hashed-password",
        email_verified=True,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_task(
    db: Session,
    *,
    instructor_id: int,
) -> Task:
    task = Task(
        class_id=None,
        instructor_id=instructor_id,
        title="Partner Contract Activity",
        description="Execution partner service test.",
        instructions="Run the submitted Python program.",
        activity_type="laboratory",
        required_ast_rules={},
        starter_code="print('starter')\n",
        paste_policy="internal_only",
        is_graded=True,
        is_published=True,
        published_at=datetime.now(timezone.utc),
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


def create_execution_request(
    db: Session,
    *,
    student_id: int,
    task_id: int,
    status: str = "queued",
    worker_task_id: str | None = None,
) -> ExecutionRequest:
    execution = ExecutionRequest(
        student_id=student_id,
        task_id=task_id,
        submission_id=None,
        coding_session_id=None,
        request_kind="run",
        status=status,
        source_code="print('hello')\n",
        standard_input="",
        stdout="",
        stderr="",
        exit_code=None,
        execution_time_ms=None,
        limit_reason=None,
        worker_task_id=worker_task_id,
        started_at=None,
        completed_at=None,
        last_partner_sequence=0,
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    return execution


@pytest.fixture
def execution_context(
    db_session: Session,
) -> tuple[ExecutionRequest, User, User, Task]:
    instructor = create_user(
        db_session,
        name="Partner Instructor",
        school_id="1000000001",
        email="partner.instructor@pampangastateu.edu.ph",
        role="instructor",
    )
    student = create_user(
        db_session,
        name="Partner Student",
        school_id="2000000001",
        email="partner.student@pampangastateu.edu.ph",
        role="student",
    )
    task = create_task(
        db_session,
        instructor_id=instructor.user_id,
    )
    execution = create_execution_request(
        db_session,
        student_id=student.user_id,
        task_id=task.task_id,
    )

    return execution, student, instructor, task


def build_result_update(
    execution: ExecutionRequest,
    *,
    status: str,
    sequence_number: int,
    update_id: str | None = None,
    worker_task_id: str = "worker-task-1",
    correlation_id: str | None = None,
    stdout: str = "",
    stderr: str = "",
    exit_code: int | None = None,
    limit_reason: str | None = None,
) -> PartnerExecutionResultUpdate:
    started_at = datetime.now(timezone.utc)

    if status == "completed" and exit_code is None:
        exit_code = 0

    return PartnerExecutionResultUpdate(
        execution_id=execution.execution_id,
        correlation_id=(
            correlation_id if correlation_id is not None else execution.correlation_id
        ),
        update_id=update_id or str(uuid4()),
        sequence_number=sequence_number,
        worker_task_id=worker_task_id,
        status=status,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        execution_time_ms=25,
        limit_reason=limit_reason,
        error_code=None,
        error_message=None,
        started_at=started_at,
        completed_at=(
            None if status == "running" else started_at + timedelta(milliseconds=25)
        ),
    )


def test_build_partner_execution_dispatch_uses_persisted_identifiers(
    db_session: Session,
    execution_context,
):
    execution, _, _, task = execution_context

    limits = PartnerExecutionLimits(
        time_limit_ms=5_000,
        memory_limit_bytes=134_217_728,
        output_limit_bytes=50_000,
        process_limit=4,
    )

    dispatch = build_partner_execution_dispatch(
        execution,
        limits=limits,
    )

    assert dispatch.execution_id == execution.execution_id
    assert dispatch.correlation_id == execution.correlation_id
    assert dispatch.idempotency_key == execution.dispatch_idempotency_key
    assert dispatch.task_id == task.task_id
    assert dispatch.request_kind == "run"
    assert dispatch.source_code == execution.source_code
    assert dispatch.standard_input == execution.standard_input
    assert dispatch.limits.time_limit_ms == 5_000
    assert dispatch.limits.process_limit == 4
    assert dispatch.queued_at.utcoffset() == timedelta(0)


def test_apply_running_partner_update(
    db_session: Session,
    execution_context,
):
    execution, _, _, _ = execution_context

    result = apply_partner_execution_result_update(
        db_session,
        update_data=build_result_update(
            execution,
            status="running",
            sequence_number=1,
        ),
    )

    db_session.refresh(execution)

    assert result.accepted is True
    assert result.replayed is False
    assert result.status == "running"
    assert result.sequence_number == 1
    assert execution.status == "running"
    assert execution.last_partner_sequence == 1
    assert execution.worker_task_id == "worker-task-1"
    assert execution.started_at is not None
    assert execution.completed_at is None


def test_apply_ordered_running_then_completed_updates(
    db_session: Session,
    execution_context,
):
    execution, _, _, _ = execution_context

    apply_partner_execution_result_update(
        db_session,
        update_data=build_result_update(
            execution,
            status="running",
            sequence_number=1,
        ),
    )

    completed = apply_partner_execution_result_update(
        db_session,
        update_data=build_result_update(
            execution,
            status="completed",
            sequence_number=2,
            stdout="hello\n",
        ),
    )

    db_session.refresh(execution)

    assert completed.replayed is False
    assert completed.status == "completed"
    assert completed.sequence_number == 2
    assert execution.status == "completed"
    assert execution.stdout == "hello\n"
    assert execution.exit_code == 0
    assert execution.completed_at is not None
    assert execution.last_partner_sequence == 2

    records = (
        db_session.query(PartnerExecutionUpdateRecord)
        .filter(
            PartnerExecutionUpdateRecord.execution_id == execution.execution_id,
        )
        .order_by(
            PartnerExecutionUpdateRecord.sequence_number,
        )
        .all()
    )

    assert [record.sequence_number for record in records] == [
        1,
        2,
    ]
    assert [record.status for record in records] == [
        "running",
        "completed",
    ]


def test_identical_partner_update_is_idempotent_replay(
    db_session: Session,
    execution_context,
):
    execution, _, _, _ = execution_context
    update_id = str(uuid4())

    payload = build_result_update(
        execution,
        status="running",
        sequence_number=1,
        update_id=update_id,
    )

    first = apply_partner_execution_result_update(
        db_session,
        update_data=payload,
    )
    second = apply_partner_execution_result_update(
        db_session,
        update_data=payload,
    )

    db_session.refresh(execution)

    assert first.replayed is False
    assert second.replayed is True
    assert second.update_id == update_id
    assert execution.last_partner_sequence == 1

    record_count = (
        db_session.query(PartnerExecutionUpdateRecord)
        .filter(
            PartnerExecutionUpdateRecord.update_id == update_id,
        )
        .count()
    )

    assert record_count == 1


def test_reused_update_id_with_different_payload_is_rejected(
    db_session: Session,
    execution_context,
):
    execution, _, _, _ = execution_context
    update_id = str(uuid4())

    apply_partner_execution_result_update(
        db_session,
        update_data=build_result_update(
            execution,
            status="running",
            sequence_number=1,
            update_id=update_id,
        ),
    )

    with pytest.raises(
        ExecutionPartnerReplayConflictError,
        match="already used for different content",
    ):
        apply_partner_execution_result_update(
            db_session,
            update_data=build_result_update(
                execution,
                status="running",
                sequence_number=1,
                update_id=update_id,
                stdout="different output",
            ),
        )

    db_session.refresh(execution)

    assert execution.last_partner_sequence == 1
    assert (
        db_session.query(PartnerExecutionUpdateRecord)
        .filter(
            PartnerExecutionUpdateRecord.update_id == update_id,
        )
        .count()
        == 1
    )


def test_partner_update_rejects_correlation_mismatch(
    db_session: Session,
    execution_context,
):
    execution, _, _, _ = execution_context

    with pytest.raises(
        ExecutionPartnerCorrelationError,
        match="does not match",
    ):
        apply_partner_execution_result_update(
            db_session,
            update_data=build_result_update(
                execution,
                status="running",
                sequence_number=1,
                correlation_id=str(uuid4()),
            ),
        )

    db_session.refresh(execution)

    assert execution.status == "queued"
    assert execution.last_partner_sequence == 0
    assert (
        db_session.query(PartnerExecutionUpdateRecord)
        .filter(
            PartnerExecutionUpdateRecord.execution_id == execution.execution_id,
        )
        .count()
        == 0
    )


def test_partner_update_rejects_out_of_order_sequence(
    db_session: Session,
    execution_context,
):
    execution, _, _, _ = execution_context

    with pytest.raises(
        ExecutionPartnerSequenceConflictError,
        match="Expected 1, received 2",
    ):
        apply_partner_execution_result_update(
            db_session,
            update_data=build_result_update(
                execution,
                status="running",
                sequence_number=2,
            ),
        )

    db_session.refresh(execution)

    assert execution.last_partner_sequence == 0


def test_partner_update_rejects_stale_sequence_with_new_update_id(
    db_session: Session,
    execution_context,
):
    execution, _, _, _ = execution_context

    apply_partner_execution_result_update(
        db_session,
        update_data=build_result_update(
            execution,
            status="running",
            sequence_number=1,
        ),
    )

    with pytest.raises(
        ExecutionPartnerSequenceConflictError,
        match="Expected 2, received 1",
    ):
        apply_partner_execution_result_update(
            db_session,
            update_data=build_result_update(
                execution,
                status="running",
                sequence_number=1,
            ),
        )


def test_partner_update_rejects_different_worker_task(
    db_session: Session,
    execution_context,
):
    execution, _, _, _ = execution_context

    apply_partner_execution_result_update(
        db_session,
        update_data=build_result_update(
            execution,
            status="running",
            sequence_number=1,
            worker_task_id="worker-task-a",
        ),
    )

    with pytest.raises(
        ExecutionStateConflictError,
        match="assigned to a different worker task",
    ):
        apply_partner_execution_result_update(
            db_session,
            update_data=build_result_update(
                execution,
                status="completed",
                sequence_number=2,
                worker_task_id="worker-task-b",
            ),
        )

    db_session.refresh(execution)

    assert execution.worker_task_id == "worker-task-a"
    assert execution.status == "running"
    assert execution.last_partner_sequence == 1


def test_partner_update_rejects_lifecycle_change_after_terminal_status(
    db_session: Session,
    execution_context,
):
    execution, _, _, _ = execution_context

    apply_partner_execution_result_update(
        db_session,
        update_data=build_result_update(
            execution,
            status="completed",
            sequence_number=1,
        ),
    )

    with pytest.raises(
        ExecutionStateConflictError,
        match="terminal execution request",
    ):
        apply_partner_execution_result_update(
            db_session,
            update_data=build_result_update(
                execution,
                status="failed",
                sequence_number=2,
            ),
        )

    db_session.refresh(execution)

    assert execution.status == "completed"
    assert execution.last_partner_sequence == 1


def test_assign_worker_task_id_is_idempotent(
    db_session: Session,
    execution_context,
):
    execution, _, _, _ = execution_context

    first = assign_worker_task_id(
        db_session,
        execution_id=execution.execution_id,
        worker_task_id=" worker-task-1 ",
    )
    second = assign_worker_task_id(
        db_session,
        execution_id=execution.execution_id,
        worker_task_id="worker-task-1",
    )

    assert first.worker_task_id == "worker-task-1"
    assert second.worker_task_id == "worker-task-1"


def test_assign_worker_task_id_rejects_reassignment(
    db_session: Session,
    execution_context,
):
    execution, _, _, _ = execution_context

    assign_worker_task_id(
        db_session,
        execution_id=execution.execution_id,
        worker_task_id="worker-task-1",
    )

    with pytest.raises(
        ExecutionStateConflictError,
        match="different worker task ID",
    ):
        assign_worker_task_id(
            db_session,
            execution_id=execution.execution_id,
            worker_task_id="worker-task-2",
        )


def test_partner_update_rolls_back_execution_and_record_on_commit_failure(
    db_session: Session,
    execution_context,
    monkeypatch: pytest.MonkeyPatch,
):
    execution, _, _, _ = execution_context
    execution_id = execution.execution_id

    update = build_result_update(
        execution,
        status="running",
        sequence_number=1,
    )

    def fail_commit() -> None:
        raise SQLAlchemyError("simulated partner persistence failure")

    monkeypatch.setattr(
        db_session,
        "commit",
        fail_commit,
    )

    with pytest.raises(
        ExecutionPersistenceError,
        match="could not be saved",
    ):
        apply_partner_execution_result_update(
            db_session,
            update_data=update,
        )

    monkeypatch.undo()
    db_session.expire_all()

    persisted_execution = (
        db_session.query(ExecutionRequest)
        .filter(
            ExecutionRequest.execution_id == execution_id,
        )
        .one()
    )

    assert persisted_execution.status == "queued"
    assert persisted_execution.worker_task_id is None
    assert persisted_execution.last_partner_sequence == 0
    assert (
        db_session.query(PartnerExecutionUpdateRecord)
        .filter(
            PartnerExecutionUpdateRecord.execution_id == execution_id,
        )
        .count()
        == 0
    )


def test_partner_update_records_store_no_execution_payload(
    db_session: Session,
    execution_context,
):
    execution, _, _, _ = execution_context

    apply_partner_execution_result_update(
        db_session,
        update_data=build_result_update(
            execution,
            status="completed",
            sequence_number=1,
            stdout="student output",
            stderr="",
        ),
    )

    record = (
        db_session.query(PartnerExecutionUpdateRecord)
        .filter(
            PartnerExecutionUpdateRecord.execution_id == execution.execution_id,
        )
        .one()
    )

    record_fields = {column.name for column in record.__table__.columns}

    assert {
        "source_code",
        "standard_input",
        "stdout",
        "stderr",
        "password",
        "otp",
        "access_token",
        "score",
        "feedback",
        "plagiarism_verdict",
        "misconduct_verdict",
    }.isdisjoint(record_fields)
