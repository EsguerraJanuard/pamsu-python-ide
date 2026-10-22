"""
Solo practice submissions judged in the background ("Full backend audit"
item 5: the submit request no longer waits on Judge0).

POST /practice/tasks/{id}/submit saves a pending attempt and queues
dispatch_practice_attempt; Judge0 calls PUT /practice/internal/judge0-callback;
the page polls GET /practice/attempts/{id}. Celery and Judge0 are stubbed: no
test makes a network call. PostgreSQL races are in
test_practice_callback_concurrency.py.
"""

import base64
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import (PracticeAttempt, PracticeModule,
                                      PracticeProgress, PracticeTask, User)
from app.services import practice_evaluation_service as practice
from app.tasks import celery_worker

DOMAIN = "@pampangastateu.edu.ph"
CODE = "print('ok')\n"
NAME_ERROR = "NameError: name 'pritn' is not defined"


def b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def make_user(db: Session, *, school_id: str, role: str = "student") -> User:
    user = User(name="Test User", email=f"{school_id}{DOMAIN}", role=role, school_id=school_id,
                password_hash=get_password_hash("Original#2026"), email_verified=True, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.user_id), 'pwd_ver': user.password_version})}"}


@pytest.fixture
def student(db_session):
    return make_user(db_session, school_id="2023000001")


@pytest.fixture
def other_student(db_session):
    return make_user(db_session, school_id="2023000002")


@pytest.fixture
def practice_task(db_session):
    module = PracticeModule(title="Basics", order_index=0)
    db_session.add(module)
    db_session.commit()
    task = PracticeTask(module_id=module.module_id, title="Print ok", instructions="Print `ok`.",
                        expected_output="ok\n", order_index=0)
    db_session.add(task)
    db_session.commit()
    return task


def submit(client, student, task):
    return client.post(f"/practice/tasks/{task.task_id}/submit", json={"code": CODE}, headers=auth(student))


def callback(client, db: Session, attempt_id: int, result: dict, *, correlation_id: str | None = None):
    db.expire_all()
    correlation_id = correlation_id or db.get(PracticeAttempt, attempt_id).correlation_id
    return client.put(
        f"/practice/internal/judge0-callback?attempt_id={attempt_id}&correlation_id={correlation_id}",
        json=result,
    )


def poll(client, student, attempt_id: int):
    return client.get(f"/practice/attempts/{attempt_id}", headers=auth(student))


def progress_of(db: Session, student, task) -> PracticeProgress | None:
    db.expire_all()
    return db.query(PracticeProgress).filter_by(student_id=student.user_id, task_id=task.task_id).one_or_none()


# ------------------------------------------------------------ submit


def test_submit_answers_pending_and_queues_the_attempt_without_calling_judge0(
        client, db_session, student, practice_task, celery_calls, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("the request must not call Judge0")

    monkeypatch.setattr(httpx, "Client", no_network)

    response = submit(client, student, practice_task)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "pending"
    assert body["is_successful"] is False
    attempt = db_session.get(PracticeAttempt, body["attempt_id"])
    assert attempt.status == "pending"
    assert len(attempt.correlation_id) == 36
    assert ("dispatch_practice_attempt", (attempt.attempt_id,)) in celery_calls
    # The secret that binds the callback is never shown to the student.
    assert attempt.correlation_id not in response.text
    # Nothing is counted until the attempt is judged.
    assert progress_of(db_session, student, practice_task) is None


def test_an_unavailable_queue_closes_the_attempt_and_answers_503(client, db_session, student, practice_task,
                                                                 monkeypatch):
    def broken_delay(*args):
        raise ConnectionError("broker down")

    monkeypatch.setattr(celery_worker.dispatch_practice_attempt, "delay", broken_delay)

    response = submit(client, student, practice_task)

    assert response.status_code == 503
    attempt = db_session.query(PracticeAttempt).one()
    assert attempt.status == "failed"
    assert attempt.execution_feedback == practice.RUNNER_UNAVAILABLE_MESSAGE
    assert progress_of(db_session, student, practice_task) is None


def test_unknown_task_is_not_found(client, student, celery_calls):
    assert client.post("/practice/tasks/999/submit", json={"code": CODE}, headers=auth(student)).status_code == 404
    assert celery_calls == []


# ------------------------------------------------------------ callback and poll


def test_an_accepted_run_completes_the_attempt_and_the_task(client, db_session, student, practice_task):
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]

    assert callback(client, db_session, attempt_id, {"status": {"id": 3}, "stdout": b64("ok\n")}).status_code == 200

    body = poll(client, student, attempt_id).json()
    assert body["status"] == "completed"
    assert body["is_successful"] is True
    assert body["message"] == practice.PASSED_MESSAGE
    progress = progress_of(db_session, student, practice_task)
    assert progress.attempts_count == 1
    assert progress.is_completed is True
    assert db_session.get(PracticeAttempt, attempt_id).completed_at is not None


def test_a_runtime_error_is_a_judged_failed_try_with_the_error_text(client, db_session, student, practice_task):
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]

    callback(client, db_session, attempt_id, {"status": {"id": 11}, "stderr": b64(NAME_ERROR)})

    body = poll(client, student, attempt_id).json()
    assert body["status"] == "completed"
    assert body["is_successful"] is False
    assert body["execution_feedback"] == NAME_ERROR
    progress = progress_of(db_session, student, practice_task)
    assert progress.attempts_count == 1
    assert progress.is_completed is False


def test_a_wrong_answer_uses_the_default_feedback(client, db_session, student, practice_task):
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]

    callback(client, db_session, attempt_id, {"status": {"id": 4}, "stdout": b64("nope\n")})

    body = poll(client, student, attempt_id).json()
    assert body["is_successful"] is False
    assert body["execution_feedback"] == practice.DEFAULT_FAILURE_FEEDBACK


@pytest.mark.parametrize("status", [None, {"id": 1}, {"id": 13}, {"id": 14}, {"id": "3"}, {"id": True}])
def test_a_judge0_failure_closes_the_attempt_without_counting_a_try(client, db_session, student, practice_task,
                                                                    status):
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]

    callback(client, db_session, attempt_id, {"status": status} if status is not None else {})

    body = poll(client, student, attempt_id).json()
    assert body["status"] == "failed"
    assert body["is_successful"] is False
    assert body["execution_feedback"] == practice.RUNNER_ERROR_MESSAGE
    assert progress_of(db_session, student, practice_task) is None


def test_a_wrong_correlation_id_changes_nothing(client, db_session, student, practice_task):
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]

    response = callback(client, db_session, attempt_id, {"status": {"id": 3}},
                        correlation_id="00000000-0000-4000-8000-000000000000")

    assert response.status_code == 404
    assert poll(client, student, attempt_id).json()["status"] == "pending"


def test_a_repeated_callback_is_refused_and_counted_once(client, db_session, student, practice_task):
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]

    assert callback(client, db_session, attempt_id, {"status": {"id": 11}, "stderr": b64(NAME_ERROR)}).status_code == 200
    second = callback(client, db_session, attempt_id, {"status": {"id": 3}})

    assert second.status_code == 409
    assert poll(client, student, attempt_id).json()["is_successful"] is False
    assert progress_of(db_session, student, practice_task).attempts_count == 1


def test_each_judged_attempt_counts_once(client, db_session, student, practice_task):
    first = submit(client, student, practice_task).json()["attempt_id"]
    second = submit(client, student, practice_task).json()["attempt_id"]

    callback(client, db_session, second, {"status": {"id": 3}})
    callback(client, db_session, first, {"status": {"id": 11}, "stderr": b64(NAME_ERROR)})

    progress = progress_of(db_session, student, practice_task)
    assert progress.attempts_count == 2
    # A later failed run does not undo a completed task.
    assert progress.is_completed is True


def test_another_students_attempt_is_not_found(client, db_session, student, other_student, practice_task):
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]

    assert poll(client, other_student, attempt_id).status_code == 404


def test_a_pending_attempt_that_judge0_never_answers_is_closed_when_read(client, db_session, student,
                                                                         practice_task):
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]
    attempt = db_session.get(PracticeAttempt, attempt_id)
    attempt.created_at = datetime.now(timezone.utc) - practice.PENDING_ATTEMPT_TIMEOUT - timedelta(seconds=1)
    db_session.commit()

    body = poll(client, student, attempt_id).json()

    assert body["status"] == "failed"
    assert body["execution_feedback"] == practice.NO_ANSWER_MESSAGE
    # A late callback cannot reopen it.
    assert callback(client, db_session, attempt_id, {"status": {"id": 3}}).status_code == 409


def test_a_recent_pending_attempt_stays_pending(client, db_session, student, practice_task):
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]

    assert poll(client, student, attempt_id).json()["status"] == "pending"


# ------------------------------------------------------------ hints and statistics


def test_hints_wait_for_the_verdict_and_skip_failed_runs(client, db_session, student, practice_task):
    pending = submit(client, student, practice_task).json()["attempt_id"]
    assert client.post(f"/practice/attempts/{pending}/ai-hint", headers=auth(student)).status_code == 409

    callback(client, db_session, pending, {"status": {"id": 13}})
    assert client.post(f"/practice/attempts/{pending}/ai-hint", headers=auth(student)).status_code == 400


def test_growth_statistics_count_only_judged_attempts(client, db_session, student, practice_task):
    judged = submit(client, student, practice_task).json()["attempt_id"]
    broken = submit(client, student, practice_task).json()["attempt_id"]
    submit(client, student, practice_task)  # still pending

    callback(client, db_session, judged, {"status": {"id": 3}})
    callback(client, db_session, broken, {"status": {"id": 13}})

    growth = client.get("/practice/analytics/growth", headers=auth(student)).json()
    assert growth["total_attempts"] == 1
    assert growth["successful_attempts"] == 1


# ------------------------------------------------------------ the worker task


@pytest.fixture
def worker_db(monkeypatch):
    """The Celery task opens its own session: point it at the test database."""

    from app.core import database
    from tests.conftest import TestingSessionLocal

    monkeypatch.setattr(database, "SessionLocal", TestingSessionLocal)


def fake_httpx(monkeypatch, *, fail: bool):
    sent = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def post(self, url, json, headers):
            sent.append((url, json))
            if fail:
                raise httpx.ConnectError("refused")
            return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"token": "t-1"})

    monkeypatch.setattr(httpx, "Client", FakeClient)
    return sent


def test_the_worker_sends_the_attempt_with_its_callback(client, db_session, student, practice_task, worker_db,
                                                        monkeypatch):
    monkeypatch.setenv("WEBHOOK_BASE_URL", "https://api.example.test/")
    monkeypatch.setenv("JUDGE0_API_URL", "judge0.example.test")
    sent = fake_httpx(monkeypatch, fail=False)
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]
    attempt = db_session.get(PracticeAttempt, attempt_id)

    celery_worker.dispatch_practice_attempt.run(attempt_id)

    (url, payload), = sent
    assert url == "https://judge0.example.test/submissions?base64_encoded=true"
    assert "wait" not in url
    assert payload["callback_url"] == (
        "https://api.example.test/practice/internal/judge0-callback"
        f"?attempt_id={attempt_id}&correlation_id={attempt.correlation_id}"
    )
    assert base64.b64decode(payload["source_code"]).decode() == CODE
    assert base64.b64decode(payload["expected_output"]).decode() == "ok\n"
    assert payload["enable_network"] is False


def test_the_worker_skips_an_attempt_that_is_no_longer_pending(client, db_session, student, practice_task,
                                                               worker_db, monkeypatch):
    sent = fake_httpx(monkeypatch, fail=False)
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]
    callback(client, db_session, attempt_id, {"status": {"id": 3}})

    celery_worker.dispatch_practice_attempt.run(attempt_id)

    assert sent == []


def test_the_worker_closes_the_attempt_after_its_last_try(client, db_session, student, practice_task, worker_db,
                                                          monkeypatch):
    fake_httpx(monkeypatch, fail=True)
    monkeypatch.setattr(celery_worker.dispatch_practice_attempt, "max_retries", 0)
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]

    celery_worker.dispatch_practice_attempt.run(attempt_id)

    body = poll(client, student, attempt_id).json()
    assert body["status"] == "failed"
    assert body["execution_feedback"] == practice.RUNNER_UNAVAILABLE_MESSAGE


# ------------------------------------------------------------ no double runs


def _response(status: int) -> httpx.Response:
    return httpx.Response(status, request=httpx.Request("POST", "https://judge0.example.test/submissions"))


@pytest.mark.parametrize(("error", "outcome"), [
    (httpx.ConnectError("refused"), "retry"),
    (httpx.ConnectTimeout("slow connect"), "retry"),
    (httpx.HTTPStatusError("busy", request=_response(429).request, response=_response(429)), "retry"),
    (httpx.HTTPStatusError("down", request=_response(503).request, response=_response(503)), "retry"),
    (httpx.HTTPStatusError("bad", request=_response(422).request, response=_response(422)), "fail"),
    (httpx.ReadTimeout("no answer"), "wait"),
    (httpx.RemoteProtocolError("cut off"), "wait"),
    (RuntimeError("database read failed"), "retry"),
])
def test_retries_only_when_judge0_certainly_did_not_queue_the_code(error, outcome):
    assert celery_worker.judge0_dispatch_outcome(error) == outcome


def failing_judge0(monkeypatch, error):
    sent = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def post(self, url, json, headers):
            sent.append(url)
            raise error

    monkeypatch.setattr(httpx, "Client", FakeClient)
    return sent


def test_a_lost_answer_is_not_resent(client, db_session, student, practice_task, worker_db, monkeypatch):
    # Judge0 may have queued it: a second send could run (and bill) it twice.
    sent = failing_judge0(monkeypatch, httpx.ReadTimeout("no answer"))
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]

    celery_worker.dispatch_practice_attempt.run(attempt_id)

    assert len(sent) == 1
    # Still pending: the callback can complete it, or the 120 s expiry closes it.
    assert poll(client, student, attempt_id).json()["status"] == "pending"


def test_an_unsent_submission_is_retried(client, db_session, student, practice_task, worker_db, monkeypatch):
    failing_judge0(monkeypatch, httpx.ConnectError("refused"))
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]

    # Called outside a worker, Celery's retry re-raises the error it was given.
    with pytest.raises(httpx.ConnectError):
        celery_worker.dispatch_practice_attempt.run(attempt_id)

    assert poll(client, student, attempt_id).json()["status"] == "pending"


def test_a_refused_submission_is_closed_at_once(client, db_session, student, practice_task, worker_db, monkeypatch):
    failing_judge0(monkeypatch, httpx.HTTPStatusError("bad", request=_response(422).request, response=_response(422)))
    attempt_id = submit(client, student, practice_task).json()["attempt_id"]

    celery_worker.dispatch_practice_attempt.run(attempt_id)

    body = poll(client, student, attempt_id).json()
    assert body["status"] == "failed"
    assert body["execution_feedback"] == practice.RUNNER_ERROR_MESSAGE
