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

import app.services.execution_service as execution_service_module
from app.models.domain_models import (
    Classroom,
    CodingSession,
    Enrollment,
    ExecutionRequest,
    Task,
    User,
)
from app.schemas.execution_schema import ExecutionRequestCreate
from app.services.execution_service import (
    create_student_execution_request,
)


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
ALEMBIC_INI_PATH = BACKEND_DIRECTORY / "alembic.ini"
ALEMBIC_DIRECTORY = BACKEND_DIRECTORY / "alembic"
ENV_FILE = BACKEND_DIRECTORY / ".env"

TEMPORARY_DATABASE_PREFIX = "pamsu_ide_execution_idempotency_pytest_"

THREAD_START_TIMEOUT_SECONDS = 15
THREAD_RESULT_TIMEOUT_SECONDS = 45


def _get_configured_database_url() -> URL:
    environment_value = (os.getenv("DATABASE_URL") or "").strip()

    dotenv_value = (dotenv_values(ENV_FILE).get("DATABASE_URL") or "").strip()

    database_url = environment_value or dotenv_value

    if not database_url:
        pytest.fail(
            "DATABASE_URL is required for execution idempotency concurrency tests."
        )

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
    if not database_name.startswith(
        TEMPORARY_DATABASE_PREFIX,
    ):
        raise RuntimeError(
            "Refusing to manage a database outside the "
            "execution-idempotency test prefix."
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
    _validate_temporary_database_name(
        database_name,
    )

    connection = psycopg2.connect(
        **_build_psycopg2_connection_kwargs(
            administrator_url,
        )
    )

    connection.autocommit = True

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(database_name),
                )
            )
    finally:
        connection.close()


def _drop_temporary_database(
    *,
    administrator_url: URL,
    database_name: str,
) -> None:
    _validate_temporary_database_name(
        database_name,
    )

    connection = psycopg2.connect(
        **_build_psycopg2_connection_kwargs(
            administrator_url,
        )
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
                    sql.Identifier(database_name),
                )
            )
    finally:
        connection.close()


@pytest.fixture
def execution_idempotency_session_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Any]:
    administrator_url = _get_configured_database_url()

    if administrator_url.get_backend_name() != "postgresql":
        pytest.skip("Execution idempotency concurrency tests require PostgreSQL.")

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
) -> dict[str, Any]:
    with session_factory() as db:
        instructor = User(
            name=("Pillar 15 Execution Idempotency Instructor"),
            school_id="9700000001",
            email=("p15.execution.idempotency.instructor@pampangastateu.edu.ph"),
            role="instructor",
            password_hash="fakehash",
            email_verified=True,
            is_active=True,
        )

        student = User(
            name=("Pillar 15 Execution Idempotency Student"),
            school_id="9700000002",
            email=("p15.execution.idempotency.student@pampangastateu.edu.ph"),
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

        classroom = Classroom(
            instructor_id=instructor.user_id,
            name="Execution Idempotency Class",
            subject_code="P15-IDEMP",
            section="A",
            class_code="P15IDEMP",
            is_active=True,
            archived_at=None,
        )

        db.add(classroom)
        db.flush()

        enrollment = Enrollment(
            class_id=classroom.class_id,
            student_id=student.user_id,
            status="active",
            deactivated_at=None,
        )

        task = Task(
            class_id=classroom.class_id,
            instructor_id=instructor.user_id,
            title=("Concurrent Execution Idempotency"),
            description=("PostgreSQL concurrent retry test."),
            instructions=("Queue one isolated execution request."),
            activity_type="laboratory",
            required_ast_rules={},
            starter_code="",
            paste_policy="internal_only",
            is_graded=True,
            is_published=True,
            due_at=None,
            published_at=datetime.now(
                timezone.utc,
            ),
        )

        db.add_all(
            [
                enrollment,
                task,
            ]
        )

        db.flush()

        coding_session = CodingSession(
            session_id=str(uuid4()),
            student_id=student.user_id,
            task_id=task.task_id,
            run_attempt_count=0,
        )

        db.add(coding_session)
        db.commit()

        return {
            "student_id": student.user_id,
            "task_id": task.task_id,
            "coding_session_id": (coding_session.session_id),
        }


def _create_execution_request_in_thread(
    *,
    session_factory: Any,
    start_barrier: Barrier,
    student_id: int,
    task_id: int,
    coding_session_id: str,
    idempotency_key: str,
) -> dict[str, Any]:
    with session_factory() as db:
        try:
            start_barrier.wait(
                timeout=(THREAD_START_TIMEOUT_SECONDS),
            )

            execution_request = create_student_execution_request(
                db,
                student_id=student_id,
                payload=ExecutionRequestCreate(
                    request_kind="run",
                    task_id=task_id,
                    submission_id=None,
                    coding_session_id=(coding_session_id),
                    source_code=("value = 15\nprint(value)\n"),
                    standard_input="",
                ),
                request_idempotency_key=(idempotency_key),
            )

            return {
                "execution_id": (execution_request.execution_id),
                "request_idempotency_key": (execution_request.request_idempotency_key),
                "request_payload_digest": (execution_request.request_payload_digest),
            }

        except Exception:
            db.rollback()
            raise


def test_concurrent_identical_execution_retries_create_one_request(
    execution_idempotency_session_factory: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = execution_idempotency_session_factory

    context = _seed_execution_context(
        session_factory,
    )

    idempotency_key = str(uuid4())

    start_barrier = Barrier(2)
    initial_lookup_barrier = Barrier(2)
    thread_state = local()

    original_find_request = (
        execution_service_module._find_student_execution_request_by_idempotency_key
    )

    def synchronized_find_request(
        db: Session,
        *,
        student_id: int,
        request_idempotency_key: str,
    ) -> ExecutionRequest | None:
        existing_request = original_find_request(
            db,
            student_id=student_id,
            request_idempotency_key=(request_idempotency_key),
        )

        if not getattr(
            thread_state,
            "initial_lookup_completed",
            False,
        ):
            thread_state.initial_lookup_completed = True

            assert existing_request is None

            initial_lookup_barrier.wait(
                timeout=(THREAD_START_TIMEOUT_SECONDS),
            )

        return existing_request

    monkeypatch.setattr(
        execution_service_module,
        ("_find_student_execution_request_by_idempotency_key"),
        synchronized_find_request,
    )

    with ThreadPoolExecutor(
        max_workers=2,
    ) as executor:
        futures = [
            executor.submit(
                _create_execution_request_in_thread,
                session_factory=session_factory,
                start_barrier=start_barrier,
                student_id=context["student_id"],
                task_id=context["task_id"],
                coding_session_id=(context["coding_session_id"]),
                idempotency_key=idempotency_key,
            )
            for _ in range(2)
        ]

        results = [
            future.result(
                timeout=(THREAD_RESULT_TIMEOUT_SECONDS),
            )
            for future in futures
        ]

    execution_ids = {result["execution_id"] for result in results}

    payload_digests = {result["request_payload_digest"] for result in results}

    assert len(execution_ids) == 1
    assert len(payload_digests) == 1
    assert None not in payload_digests

    assert all(
        result["request_idempotency_key"] == idempotency_key for result in results
    )

    with session_factory() as db:
        execution_requests = (
            db.query(ExecutionRequest)
            .filter(
                ExecutionRequest.student_id == context["student_id"],
                ExecutionRequest.request_idempotency_key == idempotency_key,
            )
            .all()
        )

        coding_session = (
            db.query(CodingSession)
            .filter(
                CodingSession.session_id == context["coding_session_id"],
            )
            .one()
        )

        assert len(execution_requests) == 1

        stored_request = execution_requests[0]

        assert stored_request.execution_id in execution_ids

        assert stored_request.request_payload_digest in payload_digests

        assert coding_session.run_attempt_count == 1


# DATABASE SAFETY BOUNDARY:
# This test creates a uniquely named PostgreSQL database and drops only
# a database whose name starts with the dedicated execution-idempotency
# test prefix. It never migrates, truncates, recreates, or drops the
# configured development database.

# CONCURRENCY BOUNDARY:
# Both worker sessions perform their initial idempotency lookup before
# either transaction proceeds. PostgreSQL then enforces one stored row
# for the authenticated student and UUID key.

# TRANSACTION BOUNDARY:
# The losing duplicate transaction rolls back its execution insert and
# coding-session counter increment before returning the winning request.

# TELEMETRY BOUNDARY:
# Two concurrent identical retries produce one execution request and one
# server-controlled run-attempt increment.

# EXECUTION BOUNDARY:
# The test persists execution metadata only. It never executes student
# Python inside FastAPI or the host operating system.

# PRIVACY BOUNDARY:
# Only the idempotency UUID and SHA-256 request digest are persisted as
# retry metadata. The test does not place source or input content into
# logs, audits, notifications, or telemetry.
