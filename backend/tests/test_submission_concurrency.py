import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Barrier
from typing import Any
from uuid import uuid4

import psycopg2
import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from psycopg2 import sql
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url  # Fixed line
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.models.domain_models import (
    AcademicEvent,
    AuditRecord,
    Classroom,
    Enrollment,
    Notification,
    Submission,
    Task,
    User,
)
from app.schemas.submission_schema import SubmissionCreate
from app.services.submission_service import (
    create_student_submission,
)


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
ALEMBIC_INI_PATH = BACKEND_DIRECTORY / "alembic.ini"
ALEMBIC_DIRECTORY = BACKEND_DIRECTORY / "alembic"
ENV_FILE = BACKEND_DIRECTORY / ".env"

TEMPORARY_DATABASE_PREFIX = "pamsu_ide_submission_pytest_"

THREAD_START_TIMEOUT_SECONDS = 15
THREAD_RESULT_TIMEOUT_SECONDS = 45


def _get_configured_database_url() -> URL:
    environment_value = (os.getenv("DATABASE_URL") or "").strip()

    dotenv_value = (dotenv_values(ENV_FILE).get("DATABASE_URL") or "").strip()

    database_url = environment_value or dotenv_value

    if not database_url:
        pytest.fail("DATABASE_URL is required for submission concurrency tests.")

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
    connection_kwargs: dict[
        str,
        object,
    ] = {}

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
            "Refusing to manage a database outside the submission-test prefix."
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
def submission_session_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Any]:
    administrator_url = _get_configured_database_url()

    if administrator_url.get_backend_name() != "postgresql":
        pytest.skip("Submission concurrency tests require PostgreSQL.")

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


def _seed_submission_context(
    session_factory: Any,
) -> dict[str, int]:
    with session_factory() as db:
        instructor = User(
            name="Pillar 15 Concurrency Instructor",
            school_id="9500000001",
            email=("p15.concurrent.instructor@pampangastateu.edu.ph"),
            role="instructor",
            password_hash="fakehash",
            email_verified=True,
            is_active=True,
        )

        student = User(
            name="Pillar 15 Concurrency Student",
            school_id="9500000002",
            email=("p15.concurrent.student@pampangastateu.edu.ph"),
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
            name="Concurrency Programming",
            subject_code="P15-101",
            section="A",
            class_code="P15C001",
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
            title="Concurrent Official Attempts",
            description=("PostgreSQL row-locking test activity."),
            instructions=("Submit a small Python program."),
            activity_type="laboratory",
            required_ast_rules={},
            starter_code="",
            paste_policy="internal_only",
            is_graded=True,
            is_published=True,
            due_at=None,
            published_at=datetime.now(timezone.utc),
        )

        db.add_all(
            [
                enrollment,
                task,
            ]
        )

        db.commit()

        return {
            "instructor_id": (instructor.user_id),
            "student_id": student.user_id,
            "class_id": classroom.class_id,
            "task_id": task.task_id,
        }


def _create_submission_in_thread(
    *,
    session_factory: Any,
    start_barrier: Barrier,
    student_id: int,
    task_id: int,
    raw_code: str,
) -> dict[str, Any]:
    with session_factory() as db:
        try:
            start_barrier.wait(timeout=(THREAD_START_TIMEOUT_SECONDS))

            submission = create_student_submission(
                db,
                student_id=student_id,
                payload=SubmissionCreate(
                    task_id=task_id,
                    coding_session_id=None,
                    raw_code=raw_code,
                    standard_input="",
                ),
            )

            return {
                "sub_id": submission.sub_id,
                "attempt_number": (submission.attempt_number),
                "accepted_at": (submission.accepted_at),
            }

        except Exception:
            db.rollback()
            raise


def test_concurrent_submissions_allocate_unique_attempts_and_one_official(
    submission_session_factory: Any,
):
    context = _seed_submission_context(submission_session_factory)

    start_barrier = Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                _create_submission_in_thread,
                session_factory=(submission_session_factory),
                start_barrier=start_barrier,
                student_id=context["student_id"],
                task_id=context["task_id"],
                raw_code=("value = 1\nprint(value)\n"),
            ),
            executor.submit(
                _create_submission_in_thread,
                session_factory=(submission_session_factory),
                start_barrier=start_barrier,
                student_id=context["student_id"],
                task_id=context["task_id"],
                raw_code=("value = 2\nprint(value)\n"),
            ),
        ]

        results = [
            future.result(timeout=(THREAD_RESULT_TIMEOUT_SECONDS)) for future in futures
        ]

    assert sorted(result["attempt_number"] for result in results) == [
        1,
        2,
    ]

    assert len({result["sub_id"] for result in results}) == 2

    with submission_session_factory() as db:
        attempts = (
            db.query(Submission)
            .filter(
                Submission.student_id == context["student_id"],
                Submission.task_id == context["task_id"],
            )
            .order_by(
                Submission.attempt_number.asc(),
                Submission.sub_id.asc(),
            )
            .all()
        )

        assert len(attempts) == 2

        assert [attempt.attempt_number for attempt in attempts] == [
            1,
            2,
        ]

        assert len({attempt.attempt_number for attempt in attempts}) == 2

        official_attempts = [attempt for attempt in attempts if attempt.is_official]

        assert len(official_attempts) == 1

        official_attempt = official_attempts[0]

        assert official_attempt.attempt_number == 2

        assert attempts[0].is_official is False

        assert official_attempt.accepted_at >= attempts[0].accepted_at

        submission_ids = {attempt.sub_id for attempt in attempts}

        audit_records = (
            db.query(AuditRecord)
            .filter(
                AuditRecord.actor_user_id == context["student_id"],
                AuditRecord.action_type == "submission_created",
                AuditRecord.resource_type == "submission",
            )
            .order_by(
                AuditRecord.occurred_at.asc(),
                AuditRecord.audit_id.asc(),
            )
            .all()
        )

        assert len(audit_records) == 2

        assert {record.resource_id for record in audit_records} == {
            str(submission_id) for submission_id in submission_ids
        }

        assert sorted(
            int(record.audit_data["attempt_number"]) for record in audit_records
        ) == [
            1,
            2,
        ]

        academic_events = (
            db.query(AcademicEvent)
            .filter(
                AcademicEvent.event_type == "submission_created",
                AcademicEvent.actor_user_id == context["student_id"],
                AcademicEvent.resource_type == "submission",
            )
            .order_by(
                AcademicEvent.occurred_at.asc(),
                AcademicEvent.event_id.asc(),
            )
            .all()
        )

        assert len(academic_events) == 2

        assert {event.resource_id for event in academic_events} == {
            str(submission_id) for submission_id in submission_ids
        }

        assert sorted(
            int(event.event_data["attempt_number"]) for event in academic_events
        ) == [
            1,
            2,
        ]

        event_ids = [event.event_id for event in academic_events]

        notifications = (
            db.query(Notification)
            .filter(
                Notification.event_id.in_(event_ids),
                Notification.recipient_id == context["instructor_id"],
            )
            .order_by(
                Notification.created_at.asc(),
                Notification.notification_id.asc(),
            )
            .all()
        )

        assert len(notifications) == 2

        assert {notification.event_id for notification in notifications} == set(
            event_ids
        )

        assert all(
            notification.title == "Submission received"
            for notification in notifications
        )


# DATABASE SAFETY BOUNDARY:
# This test creates a uniquely named PostgreSQL database and drops only
# a database whose name starts with the dedicated submission-test prefix.
# It never migrates, truncates, recreates, or drops the configured
# development database.

# CONCURRENCY BOUNDARY:
# Each worker uses an independent SQLAlchemy session and PostgreSQL
# connection. Both workers begin together and contend for the same task
# row before calculating the next attempt number.

# OFFICIAL-ATTEMPT BOUNDARY:
# Concurrent attempts receive unique sequential numbers. Exactly one
# attempt remains official, and the highest accepted attempt is official.

# TRANSACTION BOUNDARY:
# Every committed submission has one matching audit record, one academic
# event, and one instructor notification. No partial workflow record is
# accepted as a successful result.

# PRIVACY BOUNDARY:
# The test validates record counts and privacy-safe metadata only. It
# does not place source code or standard input in audits, academic-event
# metadata, or notifications.
