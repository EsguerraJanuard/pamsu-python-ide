"""
Migration b7e4c2a91f03: practice attempt status, correlation id, completion time.

PostgreSQL only (skipped otherwise). Each test runs in its own temporary
database created and dropped by `temporary_postgresql_database`; the
configured development database is never touched.

`alembic check` does not compare CHECK constraints, so the allowed statuses
are also compared with the ORM model here.
"""

import re
from uuid import uuid4

import pytest
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import IntegrityError

from app.models.domain_models import PracticeAttempt
from tests.test_alembic_migrations import (  # noqa: F401  (fixture import)
    build_alembic_config, temporary_postgresql_database)

REVISION = "b7e4c2a91f03"
PREVIOUS_REVISION = "61330560eec5"


def _execute(url: URL, sql: str, params: dict | None = None):
    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            result = connection.execute(text(sql), params or {})
            return result.scalar_one() if result.returns_rows else None
    finally:
        engine.dispose()


def _seed_attempt(url: URL) -> int:
    """A student, a practice task and one attempt, as the pre-migration code wrote them."""

    suffix = uuid4().hex[:8]
    user_id = _execute(url, (
        "INSERT INTO users (name, email, school_id, role, password_hash, email_verified, is_active) "
        "VALUES ('Old Student', :email, '2026000001', 'student', '!', true, true) RETURNING user_id"
    ), {"email": f"old.{suffix}@pampangastateu.edu.ph"})
    module_id = _execute(url, "INSERT INTO practice_modules (title, order_index) VALUES ('M', 0) RETURNING module_id")
    task_id = _execute(url, (
        "INSERT INTO practice_tasks (module_id, title, instructions, expected_output, order_index) "
        "VALUES (:module, 'T', 'Print ok', 'ok', 0) RETURNING task_id"
    ), {"module": module_id})
    return _execute(url, (
        "INSERT INTO practice_attempts (student_id, task_id, submitted_code, is_successful, ast_feedback) "
        "VALUES (:user, :task, 'print(1)', false, '[]') RETURNING attempt_id"
    ), {"user": user_id, "task": task_id})


def _database_statuses(url: URL) -> set[str]:
    definition = _execute(url, (
        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
        "WHERE conrelid = 'practice_attempts'::regclass AND conname = 'ck_practice_attempts_status'"
    ))
    return set(re.findall(r"'([a-z_]+)'", definition))


def _model_statuses() -> set[str]:
    for constraint in PracticeAttempt.__table__.constraints:
        if constraint.name == "ck_practice_attempts_status":
            return set(re.findall(r"'([a-z_]+)'", str(constraint.sqltext)))
    raise AssertionError("ck_practice_attempts_status is not declared on PracticeAttempt")


def test_upgrade_marks_existing_attempts_completed_and_matches_the_model(temporary_postgresql_database: URL):
    url = temporary_postgresql_database
    config = build_alembic_config()

    command.upgrade(config, PREVIOUS_REVISION)
    old_attempt = _seed_attempt(url)
    command.upgrade(config, REVISION)

    # Old rows were judged synchronously: they read as completed, untouched otherwise.
    assert _execute(url, "SELECT status FROM practice_attempts WHERE attempt_id = :id", {"id": old_attempt}) == "completed"
    assert _execute(url, "SELECT correlation_id IS NULL AND completed_at IS NULL FROM practice_attempts "
                         "WHERE attempt_id = :id", {"id": old_attempt}) is True
    assert _database_statuses(url) == _model_statuses() == {"pending", "completed", "failed"}

    with pytest.raises(IntegrityError):
        _execute(url, "UPDATE practice_attempts SET status = 'judging' WHERE attempt_id = :id", {"id": old_attempt})

    key = str(uuid4())
    _execute(url, "UPDATE practice_attempts SET correlation_id = :key WHERE attempt_id = :id",
             {"key": key, "id": old_attempt})
    second = _execute(url, (
        "INSERT INTO practice_attempts (student_id, task_id, submitted_code, is_successful, ast_feedback) "
        "SELECT student_id, task_id, 'print(2)', false, '[]' FROM practice_attempts WHERE attempt_id = :id "
        "RETURNING attempt_id"
    ), {"id": old_attempt})
    with pytest.raises(IntegrityError):
        _execute(url, "UPDATE practice_attempts SET correlation_id = :key WHERE attempt_id = :id",
                 {"key": key, "id": second})

    command.check(config)


def test_downgrade_refuses_while_attempts_are_pending_or_failed(temporary_postgresql_database: URL):
    url = temporary_postgresql_database
    config = build_alembic_config()

    command.upgrade(config, PREVIOUS_REVISION)
    attempt = _seed_attempt(url)
    command.upgrade(config, REVISION)
    _execute(url, "UPDATE practice_attempts SET status = 'failed' WHERE attempt_id = :id", {"id": attempt})

    with pytest.raises(RuntimeError, match="Cannot downgrade b7e4c2a91f03"):
        command.downgrade(config, PREVIOUS_REVISION)

    assert _execute(url, "SELECT version_num FROM alembic_version") == REVISION
    assert _execute(url, "SELECT status FROM practice_attempts WHERE attempt_id = :id", {"id": attempt}) == "failed"


def test_downgrade_drops_the_columns_when_every_attempt_is_judged(temporary_postgresql_database: URL):
    url = temporary_postgresql_database
    config = build_alembic_config()

    command.upgrade(config, PREVIOUS_REVISION)
    attempt = _seed_attempt(url)
    command.upgrade(config, REVISION)
    command.downgrade(config, PREVIOUS_REVISION)

    columns = _execute(url, (
        "SELECT string_agg(column_name, ',' ORDER BY column_name) FROM information_schema.columns "
        "WHERE table_name = 'practice_attempts' AND column_name IN ('status', 'correlation_id', 'completed_at')"
    ))
    assert columns is None
    assert _execute(url, "SELECT count(*) FROM practice_attempts WHERE attempt_id = :id", {"id": attempt}) == 1
