"""Timed activities: the instructor's time limit and each student's timer.

The timer is a server-side window (timed_attempts): it starts on "Start Now",
cannot be paused or reset by the browser, and submissions are checked
against it, with a short grace for the workspace's automatic submit.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import Classroom, Enrollment, Submission, Task, TimedAttempt, User
from app.services.timed_activity_service import TIME_UP_GRACE

DOMAIN = "@pampangastateu.edu.ph"


def make_user(db: Session, *, email: str, role: str, school_id: str) -> User:
    user = User(
        name="Timed Test User",
        email=email,
        role=role,
        school_id=school_id,
        password_hash=get_password_hash("Timed#2026"),
        email_verified=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.user_id)})}"}


@pytest.fixture
def people(db_session):
    instructor = make_user(db_session, email=f"timed.faculty{DOMAIN}", role="instructor", school_id="9100000001")
    student = make_user(db_session, email=f"2026100001{DOMAIN}", role="student", school_id="2026100001")
    outsider = make_user(db_session, email=f"2026100002{DOMAIN}", role="student", school_id="2026100002")
    classroom = Classroom(
        instructor_id=instructor.user_id,
        name="Programming 1",
        subject_code="CCS101",
        section="BSIT 1A",
        class_code="TIMED001",
        is_active=True,
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.add(Enrollment(class_id=classroom.class_id, student_id=student.user_id, status="active"))
    db_session.commit()
    return {"instructor": instructor, "student": student, "outsider": outsider, "classroom": classroom}


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def future(**delta) -> datetime:
    return datetime.now(timezone.utc) + timedelta(**delta)


def create_task(client, people, **fields):
    payload = {
        "title": "Timed Quiz",
        "class_ids": [people["classroom"].class_id],
        "difficulty": "beginner",
        **fields,
    }
    if isinstance(payload.get("due_at"), datetime):
        payload["due_at"] = payload["due_at"].isoformat()
    return client.post("/instructors/tasks/", headers=auth(people["instructor"]), json=payload)


def create_published_task(client, people, **fields) -> dict:
    created = create_task(client, people, **fields)
    assert created.status_code == 201, created.text
    task = created.json()[0]
    published = client.patch(
        f"/instructors/tasks/{task['task_id']}/publication",
        headers=auth(people["instructor"]),
        json={"is_published": True},
    )
    assert published.status_code == 200, published.text
    return published.json()


def submit(client, student: User, task_id: int):
    return client.post("/submissions/", headers=auth(student), json={"task_id": task_id, "raw_code": "print('hi')\n"})


def timer(client, student: User, task_id: int):
    return client.get(f"/activities/{task_id}/timer", headers=auth(student))


def start(client, student: User, task_id: int):
    return client.post(f"/activities/{task_id}/timer/start", headers=auth(student))


def shift_window(db: Session, *, task_id: int, ended_ago: timedelta) -> None:
    """Move the student's latest window so that it ended `ended_ago` ago."""

    window = db.query(TimedAttempt).filter(TimedAttempt.task_id == task_id).order_by(TimedAttempt.window_number.desc()).first()
    window.expires_at = datetime.now(timezone.utc) - ended_ago
    window.started_at = window.expires_at - timedelta(minutes=window.time_limit_minutes)
    db.commit()


# ---------------------------------------------------------------- instructor settings


def test_instructor_creates_a_timed_activity(client, people):
    response = create_task(client, people, is_timed=True, time_limit_minutes=30)

    assert response.status_code == 201, response.text
    task = response.json()[0]
    assert task["is_timed"] is True
    assert task["time_limit_minutes"] == 30


def test_untimed_activities_store_no_limit_and_old_payloads_still_work(client, people):
    with_limit = create_task(client, people, is_timed=False, time_limit_minutes=45)
    assert with_limit.status_code == 201, with_limit.text
    assert with_limit.json()[0]["time_limit_minutes"] is None

    # The frontend sends neither field for an untimed activity.
    plain = create_task(client, people)
    assert plain.status_code == 201, plain.text
    assert plain.json()[0]["is_timed"] is False
    assert plain.json()[0]["time_limit_minutes"] is None


@pytest.mark.parametrize("fields", [{"is_timed": True}, {"is_timed": True, "time_limit_minutes": 0}, {"is_timed": True, "time_limit_minutes": 481}])
def test_a_timed_activity_needs_a_limit_between_1_and_480_minutes(client, people, fields):
    assert create_task(client, people, **fields).status_code == 422


def test_editing_the_timer_checks_the_resulting_activity(client, people):
    task = create_task(client, people).json()[0]
    url = f"/instructors/tasks/{task['task_id']}"
    headers = auth(people["instructor"])

    no_limit = client.patch(url, headers=headers, json={"is_timed": True})
    assert no_limit.status_code == 422
    assert "time limit" in no_limit.json()["detail"]

    turned_on = client.patch(url, headers=headers, json={"is_timed": True, "time_limit_minutes": 20})
    assert turned_on.status_code == 200, turned_on.text
    assert (turned_on.json()["is_timed"], turned_on.json()["time_limit_minutes"]) == (True, 20)

    only_limit = client.patch(url, headers=headers, json={"time_limit_minutes": 25})
    assert only_limit.json()["time_limit_minutes"] == 25

    turned_off = client.patch(url, headers=headers, json={"is_timed": False})
    assert (turned_off.json()["is_timed"], turned_off.json()["time_limit_minutes"]) == (False, None)

    assert client.patch(url, headers=headers, json={"is_timed": None}).status_code == 422


def test_students_see_the_time_limit_in_their_activity_list(client, people):
    create_published_task(client, people, is_timed=True, time_limit_minutes=15)

    listed = client.get("/activities/", headers=auth(people["student"]))

    assert listed.status_code == 200
    assert (listed.json()[0]["is_timed"], listed.json()[0]["time_limit_minutes"]) == (True, 15)


# ---------------------------------------------------------------- hidden problem


PROBLEM = {
    "description": "Add two numbers.",
    "instructions": "Read a and b, then print their sum.",
    "scenario": "A cashier totals two items.",
    "starter_code": "a = int(input())\n",
    "required_ast_rules": {"require_print_call": {"required": True, "min_count": 1}},
}


def add_sample_case(client, people, task_id: int) -> None:
    response = client.post(
        f"/instructors/tasks/{task_id}/test-cases",
        headers=auth(people["instructor"]),
        json={"name": "Sample", "standard_input": "1\n2\n", "expected_output": "3\n", "is_hidden": False},
    )
    assert response.status_code == 201, response.text


def test_the_problem_stays_hidden_until_the_timer_starts(client, people, db_session):
    task_id = create_published_task(client, people, is_timed=True, time_limit_minutes=30, **PROBLEM)["task_id"]
    add_sample_case(client, people, task_id)
    student = people["student"]

    detail = client.get(f"/activities/{task_id}", headers=auth(student)).json()
    listed = client.get("/activities/", headers=auth(student)).json()[0]
    for body in (detail, listed):
        assert body["content_withheld"] is True
        assert body["title"] == "Timed Quiz"
        assert (body["is_timed"], body["time_limit_minutes"]) == (True, 30)
        for field in ("description", "instructions", "scenario"):
            assert body[field] is None
        assert body["starter_code"] == ""
        assert body["required_ast_rules"] == {}

    samples = client.get(f"/activities/{task_id}/sample-test-cases", headers=auth(student))
    assert samples.status_code == 403
    check = client.post(f"/activities/{task_id}/analyze-ast", headers=auth(student), json={"source_code": "print(1)\n"})
    assert check.status_code == 403

    # Only the response is changed, never the stored activity.
    db_session.expire_all()
    stored = db_session.query(Task).filter(Task.task_id == task_id).one()
    assert (stored.description, stored.starter_code) == (PROBLEM["description"], PROBLEM["starter_code"])

    assert start(client, student, task_id).status_code == 200

    detail = client.get(f"/activities/{task_id}", headers=auth(student)).json()
    assert detail["content_withheld"] is False
    assert detail["description"] == PROBLEM["description"]
    assert detail["starter_code"] == PROBLEM["starter_code"]
    assert "require_print_call" in detail["required_ast_rules"]
    assert client.get("/activities/", headers=auth(student)).json()[0]["content_withheld"] is False
    assert client.get(f"/activities/{task_id}/sample-test-cases", headers=auth(student)).json()[0]["expected_output"] == "3\n"
    assert client.post(f"/activities/{task_id}/analyze-ast", headers=auth(student), json={"source_code": "print(1)\n"}).status_code == 200


def test_the_problem_stays_visible_after_the_time_is_up(client, people, db_session):
    task_id = create_published_task(client, people, is_timed=True, time_limit_minutes=5, **PROBLEM)["task_id"]
    start(client, people["student"], task_id)
    shift_window(db_session, task_id=task_id, ended_ago=timedelta(hours=1))

    detail = client.get(f"/activities/{task_id}", headers=auth(people["student"])).json()

    assert detail["content_withheld"] is False
    assert detail["instructions"] == PROBLEM["instructions"]


def test_untimed_activities_are_never_withheld(client, people):
    task_id = create_published_task(client, people, title="Untimed Lab", **PROBLEM)["task_id"]

    detail = client.get(f"/activities/{task_id}", headers=auth(people["student"])).json()

    assert detail["content_withheld"] is False
    assert detail["description"] == PROBLEM["description"]
    assert client.get(f"/activities/{task_id}/sample-test-cases", headers=auth(people["student"])).status_code == 200


# ---------------------------------------------------------------- student timer


def test_timer_starts_once_and_cannot_be_restarted(client, people):
    task = create_published_task(client, people, is_timed=True, time_limit_minutes=30)
    task_id = task["task_id"]
    student = people["student"]

    before = timer(client, student, task_id)
    assert before.status_code == 200, before.text
    assert before.json()["state"] == "not_started"
    assert before.json()["time_limit_minutes"] == 30

    # No submission before the timer runs.
    refused = submit(client, student, task_id)
    assert refused.status_code == 403
    assert "Start the timer" in refused.json()["detail"]

    started = start(client, student, task_id)
    assert started.status_code == 200, started.text
    body = started.json()
    assert body["state"] == "running"
    assert utc(body["ends_at"]) - utc(body["started_at"]) == timedelta(minutes=30)
    assert utc(body["submit_until"]) == utc(body["ends_at"]) + TIME_UP_GRACE

    # Starting again (a reload, a second tab) returns the same window.
    again = start(client, student, task_id)
    assert again.json()["started_at"] == body["started_at"]
    assert again.json()["window_number"] == 1

    assert submit(client, student, task_id).status_code == 201
    assert submit(client, student, task_id).status_code == 201
    assert timer(client, student, task_id).json()["submitted_in_window"] is True


def test_submissions_close_after_the_time_and_its_grace(client, people, db_session):
    task_id = create_published_task(client, people, is_timed=True, time_limit_minutes=10)["task_id"]
    student = people["student"]
    assert start(client, student, task_id).status_code == 200

    # Just after 00:00 the automatic submit is still accepted.
    shift_window(db_session, task_id=task_id, ended_ago=timedelta(seconds=30))
    assert timer(client, student, task_id).json()["state"] == "expired"
    assert submit(client, student, task_id).status_code == 201

    shift_window(db_session, task_id=task_id, ended_ago=TIME_UP_GRACE + timedelta(seconds=5))
    late = submit(client, student, task_id)
    assert late.status_code == 403
    assert "time limit" in late.json()["detail"]

    restart = start(client, student, task_id)
    assert restart.status_code == 403
    assert db_session.query(TimedAttempt).count() == 1


def test_the_deadline_cuts_the_window_short(client, people):
    due_at = future(minutes=10)
    task_id = create_published_task(client, people, is_timed=True, time_limit_minutes=60, due_at=due_at)["task_id"]

    body = start(client, people["student"], task_id).json()

    assert abs(utc(body["ends_at"]) - due_at) < timedelta(seconds=1)


def test_a_deadline_that_passed_before_starting_closes_the_timer(client, people, db_session):
    task_id = create_published_task(client, people, is_timed=True, time_limit_minutes=30, due_at=future(days=1))["task_id"]
    task = db_session.query(Task).filter(Task.task_id == task_id).one()
    task.due_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    assert timer(client, people["student"], task_id).json()["state"] == "closed"
    assert start(client, people["student"], task_id).status_code == 403


def test_another_attempt_opens_one_new_window(client, people, db_session):
    task_id = create_published_task(client, people, is_timed=True, time_limit_minutes=10)["task_id"]
    student = people["student"]
    start(client, student, task_id)
    sub_id = submit(client, student, task_id).json()["sub_id"]
    shift_window(db_session, task_id=task_id, ended_ago=timedelta(hours=1))
    assert start(client, student, task_id).status_code == 403

    granted = client.post(f"/instructors/submissions/{sub_id}/retake", headers=auth(people["instructor"]))
    assert granted.status_code == 200, granted.text
    offered = timer(client, student, task_id).json()
    assert (offered["state"], offered["retake_available"]) == ("not_started", True)

    second = start(client, student, task_id).json()
    assert (second["state"], second["window_number"], second["opened_with_retake"]) == ("running", 2, True)
    db_session.expire_all()
    assert db_session.query(Submission).filter(Submission.retake_allowed.is_(True)).count() == 0
    assert submit(client, student, task_id).status_code == 201

    shift_window(db_session, task_id=task_id, ended_ago=timedelta(hours=1))
    assert start(client, student, task_id).status_code == 403


def test_a_new_limit_applies_only_to_windows_started_after_it(client, people, db_session):
    task_id = create_published_task(client, people, is_timed=True, time_limit_minutes=30)["task_id"]
    first = start(client, people["student"], task_id).json()

    client.patch(f"/instructors/tasks/{task_id}", headers=auth(people["instructor"]), json={"time_limit_minutes": 5})

    now = timer(client, people["student"], task_id).json()
    assert now["ends_at"] == first["ends_at"]
    assert now["time_limit_minutes"] == 30


def test_timer_routes_respect_enrollment_and_timing(client, people):
    timed_id = create_published_task(client, people, is_timed=True, time_limit_minutes=30)["task_id"]
    untimed_id = create_published_task(client, people, title="Untimed Lab")["task_id"]

    assert timer(client, people["outsider"], timed_id).status_code == 404
    assert start(client, people["outsider"], timed_id).status_code == 404
    assert timer(client, people["student"], untimed_id).status_code == 409
    assert start(client, people["student"], untimed_id).status_code == 409
    assert timer(client, people["instructor"], timed_id).status_code == 403

    # Untimed activities keep accepting submissions without a timer.
    assert submit(client, people["student"], untimed_id).status_code == 201
