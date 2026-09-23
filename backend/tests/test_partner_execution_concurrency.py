from __future__ import annotations

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Barrier, local
from typing import Any
from uuid import uuid4

import psycopg2
import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from psycopg2 import sql
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

import app.services.execution_service as execution_service
from app.models.domain_models import (
    ExecutionRequest,
    PartnerExecutionUpdateRecord,
    Task,
    User,
)
from app.schemas.execution_schema import (
    PartnerExecutionResultUpdate,
)


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
ALEMBIC_INI_PATH = BACKEND_DIRECTORY / "alembic.ini"
ALEMBIC_DIRECTORY = BACKEND_DIRECTORY / "alembic"
ENV_FILE = BACKEND_DIRECTORY / ".env"

TEMPORARY_DATABASE_PREFIX = "pamsu_ide_partner_replay_pytest_"

BARRIER_TIMEOUT_SECONDS = 15
WORKER_TIMEOUT_SECONDS = 45


def _get_configured_database_url() -> URL:
    environment_value = (os.getenv("DATABASE_URL") or "").strip()

    dotenv_value = (dotenv_values(ENV_FILE).get("DATABASE_URL") or "").strip()

    database_url = environment_value or dotenv_value

    if not database_url:
        pytest.fail("DATABASE_URL is required for partner execution concurrency tests.")

    try:
        return make_url(database_url)
    except Exception as error:
        pytest.fail(
            f"DATABASE_URL is not a valid SQLAlchemy URL: {type(error).__name__}"
        )


def _build_alembic_config() -> Config:
    config = Config(
        str(ALEMBIC_INI_PATH),
    )

    config.set_main_option(
        "script_location",
        str(ALEMBIC_DIRECTORY),
    )

    return config


def _build_psycopg2_connection_kwargs(
    database_url: URL,
) -> dict[str, object]:
    connection_kwargs: dict[str, object] = {}

    if database_url.database:
        connection_kwargs["dbname"] = database_url.database

    if database_url.username:
        connection_kwargs["user"] = database_url.username

    if database_url.password:
        connection_kwargs["password"] = database_url.password

    if database_url.host:
        connection_kwargs["host"] = database_url.host

    if database_url.port:
        connection_kwargs["port"] = database_url.port

    return connection_kwargs


def _validate_temporary_database_name(
    database_name: str,
) -> None:
    if not database_name.startswith(TEMPORARY_DATABASE_PREFIX):
        raise RuntimeError(
            "Refusing to manage a database outside the partner-replay test prefix."
        )

    if not all(character.isalnum() or character == "_" for character in database_name):
        raise RuntimeError(
            "The temporary database name contains an unsupported character."
        )


def _create_temporary_database(
    *,
    administrator_url: URL,
    database_name: str,
) -> None:
    _validate_temporary_database_name(database_name)

    connection = psycopg2.connect(
        **_build_psycopg2_connection_kwargs(administrator_url)
    )

    connection.autocommit = True

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
            )
    finally:
        connection.close()


def _drop_temporary_database(
    *,
    administrator_url: URL,
    database_name: str,
) -> None:
    _validate_temporary_database_name(database_name)

    connection = psycopg2.connect(
        **_build_psycopg2_connection_kwargs(administrator_url)
    )

    connection.autocommit = True

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s
                  AND pid <> pg_backend_pid()
                """,
                (database_name,),
            )

            cursor.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(
                    sql.Identifier(database_name)
                )
            )
    finally:
        connection.close()


@pytest.fixture
def partner_execution_session_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Any]:
    administrator_url = _get_configured_database_url()

    if administrator_url.get_backend_name() != "postgresql":
        pytest.skip("Partner execution concurrency tests require PostgreSQL.")

    if not administrator_url.database:
        pytest.fail("The configured PostgreSQL URL must include a database name.")

    database_name = TEMPORARY_DATABASE_PREFIX + uuid4().hex[:12]

    _create_temporary_database(
        administrator_url=administrator_url,
        database_name=database_name,
    )

    temporary_url = administrator_url.set(
        database=database_name,
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        temporary_url.render_as_string(
            hide_password=False,
        ),
    )

    engine = None

    try:
        command.upgrade(
            _build_alembic_config(),
            "head",
        )

        engine = create_engine(
            temporary_url,
            poolclass=NullPool,
            pool_pre_ping=True,
            connect_args={
                "options": ("-c lock_timeout=15000 -c statement_timeout=45000"),
            },
        )

        testing_session_factory = sessionmaker(
            bind=engine,
            class_=Session,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

        yield testing_session_factory

    finally:
        if engine is not None:
            engine.dispose()

        _drop_temporary_database(
            administrator_url=administrator_url,
            database_name=database_name,
        )


def _seed_execution_context(
    session_factory: Any,
) -> dict[str, str | int]:
    with session_factory() as db:
        instructor = User(
            name="Partner Replay Instructor",
            school_id="9700000001",
            email=("p15.partner.replay.instructor@pampangastateu.edu.ph"),
            role="instructor",
            password_hash="fakehash",
            email_verified=True,
            is_active=True,
        )

        student = User(
            name="Partner Replay Student",
            school_id="9700000002",
            email=("p15.partner.replay.student@pampangastateu.edu.ph"),
            role="student",
            password_hash="fakehash",
            email_verified=True,
            is_active=True,
        )

        db.add_all(
            [
                instructor,
                student,
            ]
        )

        db.flush()

        task = Task(
            class_id=None,
            instructor_id=instructor.user_id,
            title="Concurrent Partner Replay",
            description=("PostgreSQL partner replay test."),
            instructions=("Run the submitted Python program."),
            activity_type="laboratory",
            required_ast_rules={},
            starter_code="",
            paste_policy="internal_only",
            is_graded=True,
            is_published=True,
            published_at=datetime.now(timezone.utc),
        )

        db.add(task)
        db.flush()

        execution = ExecutionRequest(
            student_id=student.user_id,
            task_id=task.task_id,
            submission_id=None,
            coding_session_id=None,
            request_kind="run",
            status="queued",
            source_code="print('partner replay')\n",
            standard_input="",
            stdout="",
            stderr="",
            exit_code=None,
            execution_time_ms=None,
            limit_reason=None,
            worker_task_id=None,
            started_at=None,
            completed_at=None,
            last_partner_sequence=0,
        )

        db.add(execution)
        db.commit()
        db.refresh(execution)

        return {
            "execution_id": execution.execution_id,
            "correlation_id": execution.correlation_id,
            "student_id": student.user_id,
            "task_id": task.task_id,
        }


def _build_identical_update_payload(
    *,
    execution_id: str,
    correlation_id: str,
    update_id: str,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc)

    update = PartnerExecutionResultUpdate(
        execution_id=execution_id,
        correlation_id=correlation_id,
        update_id=update_id,
        sequence_number=1,
        worker_task_id="worker-concurrent-replay",
        status="running",
        stdout="",
        stderr="",
        exit_code=None,
        execution_time_ms=25,
        limit_reason=None,
        error_code=None,
        error_message=None,
        started_at=started_at,
        completed_at=None,
    )

    return update.model_dump(
        mode="json",
    )


def _apply_partner_update_in_thread(
    *,
    session_factory: Any,
    payload_data: dict[str, Any],
) -> dict[str, Any]:
    with session_factory() as db:
        try:
            update_data = PartnerExecutionResultUpdate.model_validate(payload_data)

            result = execution_service.apply_partner_execution_result_update(
                db,
                update_data=update_data,
            )

            return {
                "accepted": result.accepted,
                "replayed": result.replayed,
                "update_id": result.update_id,
                "sequence_number": (result.sequence_number),
                "status": result.status,
            }

        except Exception:
            db.rollback()
            raise


def test_concurrent_identical_partner_update_is_idempotent_replay(
    partner_execution_session_factory: Any,
    monkeypatch: pytest.MonkeyPatch,
):
    context = _seed_execution_context(partner_execution_session_factory)

    update_id = str(uuid4())

    payload_data = _build_identical_update_payload(
        execution_id=str(context["execution_id"]),
        correlation_id=str(context["correlation_id"]),
        update_id=update_id,
    )

    initial_lookup_barrier = Barrier(2)

    thread_lookup_state = local()

    original_find_partner_update_record = execution_service._find_partner_update_record

    def synchronized_find_partner_update_record(
        db: Session,
        *,
        update_id: str,
    ):
        record = original_find_partner_update_record(
            db,
            update_id=update_id,
        )

        lookup_count = getattr(
            thread_lookup_state,
            "lookup_count",
            0,
        )

        thread_lookup_state.lookup_count = lookup_count + 1

        if lookup_count == 0:
            initial_lookup_barrier.wait(timeout=BARRIER_TIMEOUT_SECONDS)

        return record

    monkeypatch.setattr(
        execution_service,
        "_find_partner_update_record",
        synchronized_find_partner_update_record,
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                _apply_partner_update_in_thread,
                session_factory=(partner_execution_session_factory),
                payload_data=payload_data,
            ),
            executor.submit(
                _apply_partner_update_in_thread,
                session_factory=(partner_execution_session_factory),
                payload_data=payload_data,
            ),
        ]

        results = [future.result(timeout=WORKER_TIMEOUT_SECONDS) for future in futures]

    assert all(result["accepted"] is True for result in results)

    assert sorted(result["replayed"] for result in results) == [
        False,
        True,
    ]

    assert {result["update_id"] for result in results} == {
        update_id,
    }

    assert {result["sequence_number"] for result in results} == {
        1,
    }

    assert {result["status"] for result in results} == {
        "running",
    }

    with partner_execution_session_factory() as db:
        execution = (
            db.query(ExecutionRequest)
            .filter(
                ExecutionRequest.execution_id == context["execution_id"],
            )
            .one()
        )

        assert execution.status == "running"
        assert execution.last_partner_sequence == 1

        assert execution.worker_task_id == "worker-concurrent-replay"

        records = (
            db.query(PartnerExecutionUpdateRecord)
            .filter(
                PartnerExecutionUpdateRecord.update_id == update_id,
            )
            .all()
        )

        assert len(records) == 1

        assert records[0].execution_id == context["execution_id"]

        assert records[0].sequence_number == 1
        assert records[0].status == "running"


# DATABASE SAFETY BOUNDARY:
# The test creates and drops only a uniquely named PostgreSQL database
# whose name starts with the dedicated partner-replay test prefix.

# CONCURRENCY BOUNDARY:
# Both workers use independent SQLAlchemy sessions and PostgreSQL
# connections. Their initial update-ID lookups are synchronized so both
# transactions miss the record before competing for the execution lock.

# REPLAY BOUNDARY:
# Two simultaneous deliveries of the same authenticated update are one
# accepted mutation plus one idempotent replay acknowledgment.

# SEQUENCE BOUNDARY:
# An identical concurrent replay does not advance the partner sequence
# twice and does not become a stale-sequence conflict.

# PRIVACY BOUNDARY:
# The replay record stores only identifiers, sequence, status, digest,
# and acceptance metadata. It does not store execution payload contents.
