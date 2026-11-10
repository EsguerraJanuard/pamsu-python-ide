"""
The Judge0 contract, end to end, against mock_judge0 (no network).

The real Celery task code (dispatch_practice_attempt, dispatch_to_partner)
sends its submission to mock_judge0, which runs it and PUTs a Judge0-shaped
callback (base64 fields, status ids) to the real backend routes. This checks
that what the workers send, what Judge0 returns and what the callbacks parse
all agree, for both solo practice and the IDE Run button. Real Judge0
(RapidAPI) is still only exercised in production.
"""

import importlib.util
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import (Classroom, Enrollment, PracticeAttempt,
                                      PracticeModule, PracticeTask, User)
from app.tasks import celery_worker

MOCK = Path(__file__).resolve().parents[2] / "mock_judge0" / "main.py"
spec = importlib.util.spec_from_file_location("mock_judge0_main", MOCK)
mock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mock)

DOMAIN = "@pampangastateu.edu.ph"


def make_user(db: Session, *, email: str, role: str, school_id: str) -> User:
    user = User(name="Test User", email=email, role=role, school_id=school_id,
                password_hash=get_password_hash("Original#2026"), email_verified=True, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.user_id)})}"}


def path_of(url: str) -> str:
    parts = urlsplit(url)
    return parts.path + (f"?{parts.query}" if parts.query else "")


@pytest.fixture
def judge0(client, monkeypatch):
    """Route worker -> mock_judge0 -> backend callback through test clients."""

    from app.core import database
    from tests.conftest import TestingSessionLocal

    monkeypatch.setattr(database, "SessionLocal", TestingSessionLocal)
    monkeypatch.setenv("JUDGE0_API_URL", "http://judge0.test")
    monkeypatch.setenv("WEBHOOK_BASE_URL", "http://backend.test")
    mock.results.clear()
    mock_client = TestClient(mock.app)
    sent = []

    class WorkerClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def post(self, url, json, headers):
            sent.append(json)
            response = mock_client.post(path_of(url), json=json)
            response.raise_for_status()
            return response

    def deliver_callback(url, json, timeout):
        response = client.put(path_of(url), json=json)
        assert response.status_code == 200, response.text
        return response

    monkeypatch.setattr(httpx, "Client", WorkerClient)
    monkeypatch.setattr(mock.httpx, "put", deliver_callback)
    return sent


@pytest.fixture
def student(db_session):
    return make_user(db_session, email=f"2026000001{DOMAIN}", role="student", school_id="2026000001")


def practice_task(db_session, expected="ok\n", patterns=None):
    module = PracticeModule(title="Basics", order_index=0)
    db_session.add(module)
    db_session.commit()
    task = PracticeTask(module_id=module.module_id, title="Print ok", instructions="Print ok.",
                        expected_output=expected, expected_ast_patterns=patterns, order_index=0)
    db_session.add(task)
    db_session.commit()
    return task


@pytest.mark.parametrize(("code", "passes", "feedback"), [
    ("print('ok')\n", True, None),
    ("print('nope')\n", False, "Execution failed or output did not match expected output."),
    ("pritn('ok')\n", False, "NameError"),
])
def test_practice_round_trip_through_judge0(client, db_session, student, judge0, code, passes, feedback):
    task = practice_task(db_session)
    submitted = client.post(f"/practice/tasks/{task.task_id}/submit", json={"code": code}, headers=auth(student))
    assert submitted.json()["status"] == "pending"

    celery_worker.dispatch_practice_attempt.run(submitted.json()["attempt_id"])

    (payload,) = judge0
    assert "wait" not in payload and payload["callback_url"].startswith("http://backend.test/practice/")
    result = client.get(f"/practice/attempts/{submitted.json()['attempt_id']}", headers=auth(student)).json()
    assert result["status"] == "completed"
    assert result["is_successful"] is passes
    if feedback:
        assert feedback in result["execution_feedback"]


def test_a_run_past_the_time_limit_is_a_judged_failure(client, db_session, student, judge0, monkeypatch):
    from app.services import practice_evaluation_service as practice

    monkeypatch.setitem(practice.JUDGE0_LIMITS, "wall_time_limit", 1.0)
    task = practice_task(db_session)
    submitted = client.post(f"/practice/tasks/{task.task_id}/submit", json={"code": "while True:\n    pass\n"},
                            headers=auth(student))

    celery_worker.dispatch_practice_attempt.run(submitted.json()["attempt_id"])

    result = client.get(f"/practice/attempts/{submitted.json()['attempt_id']}", headers=auth(student)).json()
    assert (result["status"], result["is_successful"]) == ("completed", False)
    assert db_session.get(PracticeAttempt, submitted.json()["attempt_id"]).completed_at is not None


def test_ide_run_round_trip_through_judge0(client, db_session, student, judge0):
    instructor = make_user(db_session, email=f"faculty{DOMAIN}", role="instructor", school_id="FAC0000001")
    classroom = Classroom(instructor_id=instructor.user_id, name="Programming 1", subject_code="CC 102",
                          section="BSIT 1-A", class_code="JUDGE001", is_active=True)
    db_session.add(classroom)
    db_session.commit()
    db_session.add(Enrollment(class_id=classroom.class_id, student_id=student.user_id, status="active"))
    db_session.commit()
    created = client.post("/instructors/tasks/", headers=auth(instructor), json={
        "title": "Echo", "class_ids": [classroom.class_id], "difficulty": "beginner"})
    task_id = created.json()[0]["task_id"]
    client.patch(f"/instructors/tasks/{task_id}/publication", headers=auth(instructor), json={"is_published": True})

    run = client.post("/execution/requests/", headers=auth(student), json={
        "request_kind": "run", "task_id": task_id, "source_code": "print('Hello, ' + input())\n",
        "standard_input": "PAMSU\n"})
    assert run.status_code == 201, run.text

    celery_worker.dispatch_to_partner.run(run.json()["execution_id"])

    result = client.get(f"/execution/requests/{run.json()['execution_id']}", headers=auth(student)).json()
    assert result["status"] == "completed"
    assert result["stdout"] == "Hello, PAMSU\n"


def test_the_mock_answers_like_judge0_with_wait():
    mock_client = TestClient(mock.app)

    def submit(code, expected=None):
        return mock_client.post("/submissions?base64_encoded=false&wait=true", json={
            "source_code": code, "language_id": 71, "expected_output": expected}).json()

    assert submit("print(1)", "1")["status"]["id"] == 3
    assert submit("print(2)", "1")["status"]["id"] == 4
    assert submit("raise SystemExit(3)")["status"]["id"] == 11
    assert mock_client.post("/submissions", json={"source_code": "x", "language_id": 62}).status_code == 422


# ------------------------------------------------------------ IDE run races


@pytest.fixture
def ide_run(client, db_session, student):
    instructor = make_user(db_session, email=f"race.faculty{DOMAIN}", role="instructor", school_id="FAC0000002")
    classroom = Classroom(instructor_id=instructor.user_id, name="Programming 2", subject_code="CC 103",
                          section="BSIT 1-B", class_code="JUDGE002", is_active=True)
    db_session.add(classroom)
    db_session.commit()
    db_session.add(Enrollment(class_id=classroom.class_id, student_id=student.user_id, status="active"))
    db_session.commit()
    task_id = client.post("/instructors/tasks/", headers=auth(instructor), json={
        "title": "Race", "class_ids": [classroom.class_id], "difficulty": "beginner"}).json()[0]["task_id"]
    client.patch(f"/instructors/tasks/{task_id}/publication", headers=auth(instructor), json={"is_published": True})
    run = client.post("/execution/requests/", headers=auth(student), json={
        "request_kind": "run", "task_id": task_id, "source_code": "print('done')\n", "standard_input": ""})
    return run.json()["execution_id"]


def stored_status(client, student, execution_id):
    return client.get(f"/execution/requests/{execution_id}", headers=auth(student)).json()["status"]


def test_an_early_callback_is_not_overwritten_by_running(client, student, judge0, ide_run):
    # The mock calls back before its POST answer returns: the worker used to
    # set "running" afterwards and the run looked stuck forever.
    celery_worker.dispatch_to_partner.run(ide_run)

    assert stored_status(client, student, ide_run) == "completed"


def test_a_lost_answer_after_the_callback_keeps_the_result(client, student, judge0, ide_run, monkeypatch):
    original = httpx.Client

    class AnswerLost(original):
        def post(self, url, json, headers):
            super().post(url, json=json, headers=headers)  # Judge0 ran it and called back
            raise httpx.ReadTimeout("answer lost")

    monkeypatch.setattr(httpx, "Client", AnswerLost)
    monkeypatch.setattr(celery_worker.dispatch_to_partner, "max_retries", 0)

    with pytest.raises(httpx.ReadTimeout):
        celery_worker.dispatch_to_partner.run(ide_run)

    # The final "failed" write only touches runs nothing has answered.
    assert stored_status(client, student, ide_run) == "completed"


def test_a_retry_after_the_callback_sends_nothing(client, student, judge0, ide_run):
    celery_worker.dispatch_to_partner.run(ide_run)
    celery_worker.dispatch_to_partner.run(ide_run)  # e.g. a retry delivered late

    assert len(judge0) == 1
