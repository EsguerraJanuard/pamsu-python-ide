from __future__ import annotations

import os
from collections import Counter
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
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.models.domain_models import (
    AcademicEvent,
    AuditRecord,
    Classroom,
    InstructorGrade,
    Notification,
    Submission,
    Task,
    User,
)
from app.schemas.evaluation_schema import (
    InstructorGradeCreate,
)
from app.services.evaluation_service import (
    create_or_update_grade,
)


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
ALEMBIC_INI_PATH = BACKEND_DIRECTORY / "alembic.ini"
ALEMBIC_DIRECTORY = BACKEND_DIRECTORY / "alembic"
ENV_FILE = BACKEND_DIRECTORY / ".env"

TEMPORARY_DATABASE_PREFIX = "pamsu_ide_grade_pytest_"

THREAD_START_TIMEOUT_SECONDS = 15
THREAD_RESULT_TIMEOUT_SECONDS = 45


def _get_configured_database_url() -> URL:
    environment_value = (os.getenv("DATABASE_URL") or "").strip()

    dotenv_value = (dotenv_values(ENV_FILE).get("DATABASE_URL") or "").strip()

    database_url = environment_value or dotenv_value

    if not database_url:
        pytest.fail("DATABASE_URL is required for grade concurrency tests.")

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
            "Refusing to manage a database outside the grade-test prefix."
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
def grade_session_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Any]:
    administrator_url = _get_configured_database_url()

    if administrator_url.get_backend_name() != "postgresql":
        pytest.skip("Grade concurrency tests require PostgreSQL.")

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


def _seed_grade_context(
    session_factory: Any,
) -> dict[str, int]:
    with session_factory() as db:
        instructor = User(
            name="Pillar 15 Grade Instructor",
            school_id="9600000001",
            email=("p15.grade.instructor@pampangastateu.edu.ph"),
            role="instructor",
            password_hash="fakehash",
            email_verified=True,
            is_active=True,
        )

        student = User(
            name="Pillar 15 Grade Student",
            school_id="9600000002",
            email=("p15.grade.student@pampangastateu.edu.ph"),
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
            name="Concurrent Grading",
            subject_code="P15-201",
            section="A",
            class_code="P15G001",
            is_active=True,
            archived_at=None,
        )

        db.add(classroom)

        db.flush()

        task = Task(
            class_id=classroom.class_id,
            instructor_id=instructor.user_id,
            title="Concurrent Grade Write",
            description=("PostgreSQL grade-locking test activity."),
            instructions=("Submit a program for manual grading."),
            activity_type="laboratory",
            required_ast_rules={},
            starter_code="",
            paste_policy="internal_only",
            is_graded=True,
            is_published=True,
            due_at=None,
            published_at=datetime.now(timezone.utc),
        )

        db.add(task)

        db.flush()

        submission = Submission(
            student_id=student.user_id,
            task_id=task.task_id,
            coding_session_id=None,
            attempt_number=1,
            raw_code=("value = 10\nprint(value)\n"),
            standard_input="",
            status="awaiting_review",
            is_official=True,
            accepted_at=datetime.now(timezone.utc),
        )

        db.add(submission)

        db.commit()

        return {
            "instructor_id": (instructor.user_id),
            "student_id": student.user_id,
            "class_id": classroom.class_id,
            "task_id": task.task_id,
            "submission_id": submission.sub_id,
        }


def _write_grade_in_thread(
    *,
    session_factory: Any,
    start_barrier: Barrier,
    instructor_id: int,
    submission_id: int,
    score: float,
    max_score: float,
    feedback: str,
) -> dict[str, Any]:
    with session_factory() as db:
        try:
            start_barrier.wait(timeout=(THREAD_START_TIMEOUT_SECONDS))

            instructor = db.get(
                User,
                instructor_id,
            )

            if instructor is None:
                raise RuntimeError("The test instructor was not found.")

            grade = create_or_update_grade(
                db,
                sub_id=submission_id,
                grade_in=InstructorGradeCreate(
                    score=score,
                    max_score=max_score,
                    feedback=feedback,
                    is_released=False,
                ),
                current_user=instructor,
            )

            return {
                "grade_id": grade.grade_id,
                "score": float(grade.score),
                "max_score": float(grade.max_score),
                "feedback": grade.feedback,
                "is_released": bool(grade.is_released),
            }

        except Exception:
            db.rollback()
            raise


def test_concurrent_grade_writes_create_one_atomic_grade(
    grade_session_factory: Any,
):
    context = _seed_grade_context(grade_session_factory)

    first_payload = {
        "score": 81.0,
        "max_score": 100.0,
        "feedback": "First complete grade payload.",
        "is_released": False,
    }

    second_payload = {
        "score": 94.0,
        "max_score": 120.0,
        "feedback": "Second complete grade payload.",
        "is_released": False,
    }

    start_barrier = Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                _write_grade_in_thread,
                session_factory=(grade_session_factory),
                start_barrier=start_barrier,
                instructor_id=context["instructor_id"],
                submission_id=context["submission_id"],
                score=first_payload["score"],
                max_score=first_payload["max_score"],
                feedback=first_payload["feedback"],
            ),
            executor.submit(
                _write_grade_in_thread,
                session_factory=(grade_session_factory),
                start_barrier=start_barrier,
                instructor_id=context["instructor_id"],
                submission_id=context["submission_id"],
                score=second_payload["score"],
                max_score=second_payload["max_score"],
                feedback=second_payload["feedback"],
            ),
        ]

        results = [
            future.result(timeout=(THREAD_RESULT_TIMEOUT_SECONDS)) for future in futures
        ]

    assert len({result["grade_id"] for result in results}) == 1

    assert all(result["is_released"] is False for result in results)

    with grade_session_factory() as db:
        grades = (
            db.query(InstructorGrade)
            .filter(
                InstructorGrade.submission_id == context["submission_id"],
            )
            .all()
        )

        assert len(grades) == 1

        grade = grades[0]

        assert grade.instructor_id == context["instructor_id"]

        assert grade.is_released is False

        final_payload = {
            "score": float(grade.score),
            "max_score": float(grade.max_score),
            "feedback": grade.feedback,
            "is_released": bool(grade.is_released),
        }

        assert final_payload in (
            first_payload,
            second_payload,
        )

        assert final_payload not in (
            {
                "score": first_payload["score"],
                "max_score": second_payload["max_score"],
                "feedback": first_payload["feedback"],
                "is_released": False,
            },
            {
                "score": second_payload["score"],
                "max_score": first_payload["max_score"],
                "feedback": second_payload["feedback"],
                "is_released": False,
            },
        )

        audit_records = (
            db.query(AuditRecord)
            .filter(
                AuditRecord.resource_type == "grade",
                AuditRecord.resource_id == str(grade.grade_id),
            )
            .order_by(
                AuditRecord.occurred_at.asc(),
                AuditRecord.audit_id.asc(),
            )
            .all()
        )

        assert len(audit_records) == 2

        assert Counter(record.action_type for record in audit_records) == Counter(
            {
                "grade_created": 1,
                "grade_updated": 1,
            }
        )

        assert all(
            record.actor_user_id == context["instructor_id"] for record in audit_records
        )

        serialized_audit_data = repr([record.audit_data for record in audit_records])

        assert first_payload["feedback"] not in serialized_audit_data

        assert second_payload["feedback"] not in serialized_audit_data

        assert str(first_payload["score"]) not in serialized_audit_data

        assert str(second_payload["score"]) not in serialized_audit_data

        release_events = (
            db.query(AcademicEvent)
            .filter(
                AcademicEvent.event_type == "grade_released",
            )
            .all()
        )

        assert release_events == []

        assert db.query(Notification).count() == 0

        stored_submission = db.get(
            Submission,
            context["submission_id"],
        )

        assert stored_submission is not None

        assert stored_submission.status == "awaiting_review"

        assert stored_submission.is_official is True


# DATABASE SAFETY BOUNDARY:
# This test creates a uniquely named PostgreSQL database and drops only
# a database whose name starts with the dedicated grade-test prefix. It
# never migrates, truncates, recreates, or drops the configured
# development database.

# CONCURRENCY BOUNDARY:
# Both workers use independent SQLAlchemy sessions and PostgreSQL
# connections. They contend for the same submission row before reading
# or creating the manual grade.

# GRADE-ROW BOUNDARY:
# Concurrent writes create only one InstructorGrade row. The final grade
# contains one complete instructor payload and never a mixed combination
# of values from competing requests.

# AUDIT BOUNDARY:
# The first write creates one grade-created record and the serialized
# later write creates one grade-updated record. Audit metadata excludes
# grade values and feedback text.

# NOTIFICATION BOUNDARY:
# Both writes remain unreleased, so neither write may create a
# grade-release academic event or student notification.

# GRADING BOUNDARY:
# The test verifies only instructor-controlled manual grade writes.
# Automated AST, similarity, execution, and behavioral indicators do not
# provide or modify grade values.
