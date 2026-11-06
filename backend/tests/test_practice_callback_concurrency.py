"""
Practice Judge0 callbacks under concurrency (PostgreSQL only; skipped
otherwise). Each test runs in its own temporary database, migrated to head,
created and dropped by `temporary_postgresql_database`.

The races (app.services.practice_evaluation_service):
- Judge0 delivers the same callback twice at once: the attempt row lock lets
  one record the verdict; the other sees a finished attempt;
- callbacks for two attempts of the same student and task arrive together
  before any progress row exists: the unique (student_id, task_id) constraint
  and a savepoint make both count, in one row;
- the stale-attempt expiry runs while a callback is being applied: the
  expiry's "still pending" UPDATE waits for the lock and then changes nothing.

A short sleep inside the verdict step (after the attempt lock, before the
progress row) makes the transactions overlap on every run.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from alembic import command
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.models.domain_models import (PracticeAttempt, PracticeModule,
                                      PracticeProgress, PracticeTask, User)
from app.schemas.execution_schema import Judge0CallbackPayload
from app.services import practice_evaluation_service as practice
from tests.test_alembic_migrations import (  # noqa: F401  (fixture import)
    build_alembic_config, temporary_postgresql_database)

OVERLAP_SECONDS = 0.4
TIMEOUT_SECONDS = 30
ACCEPTED = Judge0CallbackPayload(status={"id": 3})


@pytest.fixture
def sessions(temporary_postgresql_database: URL, monkeypatch):
    command.upgrade(build_alembic_config(), "head")
    engine = create_engine(temporary_postgresql_database, poolclass=NullPool)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    original_judge = practice._judge

    def slow_judge(*args, **kwargs):
        time.sleep(OVERLAP_SECONDS)
        return original_judge(*args, **kwargs)

    monkeypatch.setattr(practice, "_judge", slow_judge)
    try:
        yield factory
    finally:
        engine.dispose()


def seed(factory, attempts: int):
    with factory() as db:
        student = User(name="Race Student", email=f"race.{uuid4().hex[:8]}@pampangastateu.edu.ph", role="student",
                       school_id="2026000001", password_hash="!unusable", email_verified=True, is_active=True)
        module = PracticeModule(title="Basics", order_index=0)
        db.add_all([student, module])
        db.flush()
        task = PracticeTask(module_id=module.module_id, title="Print ok", instructions="Print ok.",
                            expected_output="ok\n", order_index=0)
        db.add(task)
        db.flush()
        rows = [
            PracticeAttempt(student_id=student.user_id, task_id=task.task_id, submitted_code="print('ok')",
                            is_successful=False, status="pending", correlation_id=str(uuid4()), ast_feedback=[])
            for _ in range(attempts)
        ]
        db.add_all(rows)
        db.commit()
        return student.user_id, task.task_id, [(row.attempt_id, row.correlation_id) for row in rows]


def run_together(*calls):
    barrier = Barrier(len(calls), timeout=TIMEOUT_SECONDS)

    def start(call):
        barrier.wait()
        try:
            return call()
        except Exception as error:  # returned, not raised: the test inspects it
            return error

    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        futures = [pool.submit(start, call) for call in calls]
        return [future.result(timeout=TIMEOUT_SECONDS) for future in futures]


def deliver(factory, attempt_id: int, correlation_id: str, payload=ACCEPTED):
    def call():
        with factory() as db:
            return practice.record_judge0_result(db, attempt_id=attempt_id, correlation_id=correlation_id,
                                                 payload=payload).status
    return call


def test_a_duplicate_delivery_is_applied_once(sessions):
    student_id, task_id, [(attempt_id, correlation_id)] = seed(sessions, 1)

    results = run_together(deliver(sessions, attempt_id, correlation_id), deliver(sessions, attempt_id, correlation_id))

    assert sorted(type(result).__name__ for result in results) == ["PracticeAttemptFinishedError", "str"]
    with sessions() as db:
        progress = db.query(PracticeProgress).filter_by(student_id=student_id, task_id=task_id).one()
        assert progress.attempts_count == 1
        assert db.get(PracticeAttempt, attempt_id).status == "completed"


def test_two_attempts_judged_together_both_count_in_one_progress_row(sessions):
    student_id, task_id, [(first, first_key), (second, second_key)] = seed(sessions, 2)

    results = run_together(deliver(sessions, first, first_key), deliver(sessions, second, second_key))

    assert results == ["completed", "completed"]
    with sessions() as db:
        rows = db.query(PracticeProgress).filter_by(student_id=student_id, task_id=task_id).all()
        assert len(rows) == 1
        assert rows[0].attempts_count == 2
        assert rows[0].is_completed is True


def test_the_stale_expiry_cannot_overwrite_a_verdict_being_recorded(sessions):
    _, _, [(attempt_id, correlation_id)] = seed(sessions, 1)

    def expire_a_moment_later():
        time.sleep(OVERLAP_SECONDS / 4)
        with sessions() as db:
            return practice.mark_attempt_failed(db, attempt_id=attempt_id, message=practice.NO_ANSWER_MESSAGE)

    results = run_together(deliver(sessions, attempt_id, correlation_id), expire_a_moment_later)

    assert results == ["completed", False]
    with sessions() as db:
        attempt = db.get(PracticeAttempt, attempt_id)
        assert attempt.status == "completed"
        assert attempt.is_successful is True
