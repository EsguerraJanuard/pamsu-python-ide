"""Regression tests for the oral-defense panel recommendations (2026-09-30).

Covers the activity analyzer, scenario and solution-explanation fields,
deadline-change and due-soon notifications, per-student retakes, the
faculty sign-in lockout and the optional middle name.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import AuditRecord, Classroom, Enrollment, Submission, Task, User
from app.services.academic_event_service import ensure_deadline_reminders
from app.services.ast_analyzer import analyze_activity
from app.services.login_security_service import FACULTY_LOCKOUT_THRESHOLD

DOMAIN = "@pampangastateu.edu.ph"
PASSWORD = "Original#2026"


def make_user(db: Session, *, email: str, role: str, school_id: str, name: str = "Test User") -> User:
    user = User(
        name=name,
        email=email,
        role=role,
        school_id=school_id,
        password_hash=get_password_hash(PASSWORD),
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
    admin = make_user(db_session, email=f"mis{DOMAIN}", role="admin", school_id="9000000001", name="MIS Admin")
    instructor = make_user(db_session, email=f"faculty{DOMAIN}", role="instructor", school_id="9000000002", name="Faculty One")
    other_instructor = make_user(db_session, email=f"faculty2{DOMAIN}", role="instructor", school_id="9000000003")
    student = make_user(db_session, email=f"2023000001{DOMAIN}", role="student", school_id="2023000001", name="Juan Dela Cruz")
    classroom = Classroom(
        instructor_id=instructor.user_id,
        name="Programming 1",
        subject_code="CCS101",
        section="BSIT 1A",
        class_code="CLASSA01",
        is_active=True,
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.add(Enrollment(class_id=classroom.class_id, student_id=student.user_id, status="active"))
    db_session.commit()
    return {
        "admin": admin,
        "instructor": instructor,
        "other_instructor": other_instructor,
        "student": student,
        "classroom": classroom,
    }


def create_published_task(client, people, *, due_at: datetime | None = None, **fields) -> dict:
    payload = {
        "title": fields.pop("title", "Loops Laboratory"),
        "class_ids": [people["classroom"].class_id],
        "difficulty": "beginner",
        "due_at": due_at.isoformat() if due_at else None,
        **fields,
    }
    response = client.post("/instructors/tasks/", headers=auth(people["instructor"]), json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    task = body[0] if isinstance(body, list) else body
    published = client.patch(
        f"/instructors/tasks/{task['task_id']}/publication",
        headers=auth(people["instructor"]),
        json={"is_published": True},
    )
    assert published.status_code == 200, published.text
    return published.json()


def submit(client, student: User, task_id: int, code: str = "print('hi')\n"):
    return client.post("/submissions/", headers=auth(student), json={"task_id": task_id, "raw_code": code})


def notification_titles(client, user: User) -> list[str]:
    response = client.get("/notifications/?page_size=100", headers=auth(user))
    assert response.status_code == 200, response.text
    return [item["title"] for item in response.json()["items"]]


def future(**delta) -> datetime:
    return datetime.now(timezone.utc) + timedelta(**delta)


# ---------------------------------------------------------------- analyzer


def test_analyzer_reads_constructs_from_the_problem_description():
    result = analyze_activity(
        description=(
            "Ask the user to enter five quiz scores. Use a for loop to add them, "
            "then save the average to report.txt."
        )
    )

    rules = result["suggested_ast_rules"]
    assert {"require_input_call", "require_for_loop", "require_open_call"} <= set(rules)
    assert all(config == {"required": True, "min_count": 1} for config in rules.values())
    # open() is file handling, an intermediate construct.
    assert result["difficulty_level"] == "intermediate"

    by_rule = {construct["rule"]: construct for construct in result["constructs"]}
    assert by_rule["require_open_call"]["source"] == "description"
    assert ".txt" in by_rule["require_open_call"]["description_terms"]


def test_reference_solution_alone_sets_the_difficulty():
    code = (
        "class Account:\n"
        "    def __init__(self, balance):\n"
        "        self.balance = balance\n"
        "for amount in [1, 2]:\n"
        "    print(amount)\n"
    )
    result = analyze_activity(reference_code=code, description="Use a for loop.")

    assert result["difficulty_level"] == "expert"
    assert "class definition" in result["difficulty_reason"].lower()
    by_rule = {construct["rule"]: construct for construct in result["constructs"]}
    assert by_rule["require_for_loop"]["source"] == "both"
    assert by_rule["require_class_def"]["source"] == "solution"
    assert by_rule["require_class_def"]["solution_count"] == 1


def test_plain_statements_are_beginner():
    result = analyze_activity(reference_code="name = input()\nprint(name)\n")

    assert result["difficulty_level"] == "beginner"
    assert set(result["suggested_ast_rules"]) == {"require_input_call"}


def test_analyze_endpoint_accepts_a_description_and_needs_some_input(client, people):
    headers = auth(people["instructor"])

    empty = client.post("/instructors/tasks/analyze-solution", headers=headers, json={})
    assert empty.status_code == 422

    blank = client.post(
        "/instructors/tasks/analyze-solution",
        headers=headers,
        json={"reference_code": "   ", "description": ""},
    )
    assert blank.status_code == 422

    response = client.post(
        "/instructors/tasks/analyze-solution",
        headers=headers,
        json={"description": "Write a function that returns the largest number in a list."},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["difficulty_level"] == "intermediate"
    assert "require_function_def" in body["suggested_ast_rules"]

    invalid = client.post(
        "/instructors/tasks/analyze-solution",
        headers=headers,
        json={"reference_code": "def broken(:\n"},
    )
    assert invalid.status_code == 400


def test_analyze_endpoint_is_instructor_only(client, people):
    response = client.post(
        "/instructors/tasks/analyze-solution",
        headers=auth(people["student"]),
        json={"description": "Use a loop."},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------- scenario and explanation


def test_scenario_is_shared_and_explanation_waits_for_the_released_grade(client, people):
    task = create_published_task(
        client,
        people,
        scenario="A canteen cashier totals orders.",
        solution_explanation="Accumulate each price in a running total.",
    )
    assert task["scenario"] == "A canteen cashier totals orders."
    assert task["solution_explanation"] == "Accumulate each price in a running total."

    student_view = client.get(f"/activities/{task['task_id']}", headers=auth(people["student"]))
    assert student_view.status_code == 200
    assert student_view.json()["scenario"] == "A canteen cashier totals orders."
    assert "solution_explanation" not in student_view.json()

    submission = submit(client, people["student"], task["task_id"])
    assert submission.status_code == 201, submission.text
    sub_id = submission.json()["sub_id"]

    before = client.get(f"/evaluation/submissions/{sub_id}", headers=auth(people["student"]))
    assert before.status_code == 200
    assert before.json()["solution_explanation"] is None

    graded = client.put(
        f"/evaluation/submissions/{sub_id}/grade",
        headers=auth(people["instructor"]),
        json={"score": 90, "max_score": 100, "feedback": "Good", "is_released": False},
    )
    assert graded.status_code in (200, 201), graded.text

    unreleased = client.get(f"/evaluation/submissions/{sub_id}", headers=auth(people["student"]))
    assert unreleased.json()["solution_explanation"] is None

    released = client.put(
        f"/evaluation/submissions/{sub_id}/grade",
        headers=auth(people["instructor"]),
        json={"score": 90, "max_score": 100, "feedback": "Good", "is_released": True},
    )
    assert released.status_code in (200, 201), released.text

    after = client.get(f"/evaluation/submissions/{sub_id}", headers=auth(people["student"]))
    assert after.json()["solution_explanation"] == "Accumulate each price in a running total."


def test_scenario_and_explanation_can_be_edited(client, people):
    task = create_published_task(client, people)

    response = client.patch(
        f"/instructors/tasks/{task['task_id']}",
        headers=auth(people["instructor"]),
        json={"scenario": "  A library tracks loans.  ", "solution_explanation": ""},
    )
    assert response.status_code == 200, response.text
    assert response.json()["scenario"] == "A library tracks loans."
    assert response.json()["solution_explanation"] is None


# ---------------------------------------------------------------- deadlines


def test_moving_a_published_deadline_notifies_students_once(client, people):
    task = create_published_task(client, people, due_at=future(days=3))
    new_due = future(days=5).replace(microsecond=0)

    for _ in range(2):
        response = client.patch(
            f"/instructors/tasks/{task['task_id']}",
            headers=auth(people["instructor"]),
            json={"due_at": new_due.isoformat()},
        )
        assert response.status_code == 200, response.text

    assert notification_titles(client, people["student"]).count("Deadline changed") == 1


def test_draft_deadline_changes_do_not_notify(client, people):
    created = client.post(
        "/instructors/tasks/",
        headers=auth(people["instructor"]),
        json={"title": "Draft", "class_ids": [people["classroom"].class_id], "difficulty": "beginner"},
    )
    task = created.json()[0] if isinstance(created.json(), list) else created.json()

    response = client.patch(
        f"/instructors/tasks/{task['task_id']}",
        headers=auth(people["instructor"]),
        json={"due_at": future(days=2).isoformat()},
    )
    assert response.status_code == 200, response.text
    assert "Deadline changed" not in notification_titles(client, people["student"])


def test_due_soon_reminder_is_created_once_for_unsubmitted_work(client, people, db_session):
    due_soon = create_published_task(client, people, title="Due soon", due_at=future(hours=3))
    already_done = create_published_task(client, people, title="Already submitted", due_at=future(hours=5))
    later = create_published_task(client, people, title="Due later", due_at=future(days=3))
    assert submit(client, people["student"], already_done["task_id"]).status_code == 201

    count = client.get("/notifications/unread-count", headers=auth(people["student"]))
    assert count.status_code == 200

    titles = notification_titles(client, people["student"])
    assert titles.count("Deadline in less than 24 hours") == 1

    response = client.get("/notifications/?page_size=100", headers=auth(people["student"]))
    reminder = next(item for item in response.json()["items"] if item["event_type"] == "deadline_reminder")
    assert reminder["resource_id"] == str(due_soon["task_id"])
    assert later["task_id"] != due_soon["task_id"]

    # Repeating the read creates nothing new.
    assert ensure_deadline_reminders(db_session, student_id=people["student"].user_id) == 0


def test_instructors_do_not_get_due_soon_reminders(client, people):
    create_published_task(client, people, due_at=future(hours=2))

    assert "Deadline in less than 24 hours" not in notification_titles(client, people["instructor"])


# ---------------------------------------------------------------- retake


def close_deadline(db: Session, task_id: int) -> None:
    task = db.query(Task).filter(Task.task_id == task_id).one()
    task.due_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()


def test_retake_allows_exactly_one_late_attempt(client, people, db_session):
    task = create_published_task(client, people, due_at=future(days=1))
    first = submit(client, people["student"], task["task_id"])
    assert first.status_code == 201
    sub_id = first.json()["sub_id"]

    close_deadline(db_session, task["task_id"])
    assert submit(client, people["student"], task["task_id"]).status_code == 404

    denied = client.post(f"/instructors/submissions/{sub_id}/retake", headers=auth(people["other_instructor"]))
    assert denied.status_code == 403

    granted = client.post(f"/instructors/submissions/{sub_id}/retake", headers=auth(people["instructor"]))
    assert granted.status_code == 200, granted.text
    assert granted.json()["retake_allowed"] is True

    again = client.post(f"/instructors/submissions/{sub_id}/retake", headers=auth(people["instructor"]))
    assert again.status_code == 200
    assert "Another attempt allowed" in notification_titles(client, people["student"])
    assert notification_titles(client, people["student"]).count("Another attempt allowed") == 1

    late = submit(client, people["student"], task["task_id"])
    assert late.status_code == 201, late.text
    assert late.json()["is_official"] is True
    assert late.json()["attempt_number"] == 2

    db_session.expire_all()
    assert db_session.query(Submission).filter(Submission.retake_allowed.is_(True)).count() == 0
    assert submit(client, people["student"], task["task_id"]).status_code == 404

    audit = (
        db_session.query(AuditRecord)
        .filter(AuditRecord.action_type == "submission_status_changed", AuditRecord.resource_id == str(sub_id))
        .all()
    )
    assert len(audit) == 1
    assert audit[0].audit_data["change"] == "retake_allowed"


def test_retake_is_kept_for_attempts_before_the_deadline(client, people, db_session):
    task = create_published_task(client, people, due_at=future(days=1))
    sub_id = submit(client, people["student"], task["task_id"]).json()["sub_id"]

    assert client.post(f"/instructors/submissions/{sub_id}/retake", headers=auth(people["instructor"])).status_code == 200
    assert submit(client, people["student"], task["task_id"]).status_code == 201

    db_session.expire_all()
    assert db_session.query(Submission).filter(Submission.retake_allowed.is_(True)).count() == 1


# ---------------------------------------------------------------- faculty lockout


def login(client, email: str, password: str):
    return client.post("/login", data={"username": email, "password": password})


def test_faculty_account_locks_after_repeated_wrong_passwords(client, people, db_session):
    email = people["instructor"].email

    for _ in range(FACULTY_LOCKOUT_THRESHOLD):
        assert login(client, email, "Wrong#2026").status_code == 401

    locked = login(client, email, PASSWORD)
    assert locked.status_code == 423
    assert "locked" in locked.json()["detail"]
    assert int(locked.headers["Retry-After"]) > 0

    # Refused attempts are recorded as denied and do not extend the lock.
    assert login(client, email, "Wrong#2026").status_code == 423
    records = db_session.query(AuditRecord).filter(
        AuditRecord.action_type == "login_failed",
        AuditRecord.actor_user_id == people["instructor"].user_id,
    )
    assert records.filter(AuditRecord.outcome == "failed").count() == FACULTY_LOCKOUT_THRESHOLD
    assert records.filter(AuditRecord.outcome == "denied").count() == 2

    # Once the failures leave the 15-minute window the account opens again.
    for record in records.all():
        record.occurred_at = datetime.now(timezone.utc) - timedelta(minutes=16)
    db_session.commit()

    assert login(client, email, PASSWORD).status_code == 200


def test_student_accounts_are_not_locked(client, people):
    email = people["student"].email

    for _ in range(FACULTY_LOCKOUT_THRESHOLD + 1):
        assert login(client, email, "Wrong#2026").status_code == 401

    assert login(client, email, PASSWORD).status_code == 200


# ---------------------------------------------------------------- names


def test_admin_can_record_a_middle_name(client, people):
    response = client.post(
        "/admin/instructors",
        headers=auth(people["admin"]),
        json={
            "email": f"ana.reyes{DOMAIN}",
            "first_name": "Ana",
            "middle_name": "Santos",
            "last_name": "Reyes",
            "password": "Temporary#2026",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Ana Santos Reyes"


def test_full_name_is_limited_to_the_name_column(client, people):
    response = client.post(
        "/admin/instructors",
        headers=auth(people["admin"]),
        json={
            "email": f"long.name{DOMAIN}",
            "first_name": "A" * 70,
            "middle_name": "B" * 70,
            "last_name": "C" * 70,
            "password": "Temporary#2026",
        },
    )
    assert response.status_code == 422
