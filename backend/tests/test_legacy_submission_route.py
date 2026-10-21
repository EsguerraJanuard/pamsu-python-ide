"""Legacy /execution/submissions/ routes ("Full backend audit", Still open, item 7).

The legacy POST used to insert the attempt by itself: no audit record, no
academic event, no instructor notification and no background evaluation. A
student calling it directly could therefore hand in an official attempt that
skipped the structure and similarity checks. It now saves the attempt through
the same service as POST /submissions/ and queues the same follow-up work,
while keeping its documented status codes and its strict deadline.

The legacy GET used to show students the instructor-only review indicators
(similarity score and structure result). Students now get them as null.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import (AcademicEvent, AuditRecord, Classroom,
                                      Enrollment, ExecutionRequest,
                                      Notification, Submission, Task, User)
from app.services import submission_service
from app.services.audit_service import AuditServiceError

DOMAIN = "@pampangastateu.edu.ph"
PASSWORD = "Original#2026"
LEGACY = "/execution/submissions/"


def make_user(db: Session, *, email: str, role: str, school_id: str) -> User:
    user = User(
        name="Test User",
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
    instructor = make_user(db_session, email=f"faculty{DOMAIN}", role="instructor", school_id="9000000002")
    other_instructor = make_user(db_session, email=f"faculty2{DOMAIN}", role="instructor", school_id="9000000003")
    student = make_user(db_session, email=f"2023000001{DOMAIN}", role="student", school_id="2023000001")
    outsider = make_user(db_session, email=f"2023000002{DOMAIN}", role="student", school_id="2023000002")
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
        "instructor": instructor,
        "other_instructor": other_instructor,
        "student": student,
        "outsider": outsider,
        "classroom": classroom,
    }


def create_task(client, people, *, publish: bool = True, due_at: datetime | None = None) -> dict:
    response = client.post(
        "/instructors/tasks/",
        headers=auth(people["instructor"]),
        json={
            "title": "Loops Laboratory",
            "class_ids": [people["classroom"].class_id],
            "difficulty": "beginner",
            "due_at": due_at.isoformat() if due_at else None,
        },
    )
    assert response.status_code == 201, response.text
    task = response.json()[0]
    if not publish:
        return task
    published = client.patch(
        f"/instructors/tasks/{task['task_id']}/publication",
        headers=auth(people["instructor"]),
        json={"is_published": True},
    )
    assert published.status_code == 200, published.text
    return published.json()


def legacy_submit(client, student: User, task_id: int, code: str = "print('hi')\n"):
    return client.post(LEGACY, headers=auth(student), json={"task_id": task_id, "raw_code": code})


def test_legacy_submit_saves_the_same_records_as_submissions(client, people, db_session, celery_calls):
    task = create_task(client, people)

    response = legacy_submit(client, people["student"], task["task_id"])

    assert response.status_code == 201, response.text
    body = response.json()
    sub_id = body["sub_id"]
    assert body["student_id"] == people["student"].user_id
    assert body["attempt_number"] == 1
    assert body["is_official"] is True
    assert body["status"] == "submitted"
    assert body["jaccard_score"] is None
    assert body["ast_pass_fail"] is None

    db_session.expire_all()
    audit = db_session.query(AuditRecord).filter(
        AuditRecord.action_type == "submission_created",
        AuditRecord.resource_id == str(sub_id),
    ).all()
    assert len(audit) == 1
    assert audit[0].actor_user_id == people["student"].user_id

    events = db_session.query(AcademicEvent).filter(
        AcademicEvent.event_key == f"submission_created:submission:{sub_id}",
    ).all()
    assert len(events) == 1

    notices = db_session.query(Notification).filter(
        Notification.recipient_id == people["instructor"].user_id,
        Notification.event_id == events[0].event_id,
    ).count()
    assert notices == 1

    assert ("evaluate_submission_background_task", (sub_id,)) in celery_calls
    runs = db_session.query(ExecutionRequest).filter(
        ExecutionRequest.submission_id == sub_id,
        ExecutionRequest.request_kind == "submit",
    ).count()
    assert runs == 1


def test_legacy_submit_makes_the_newest_attempt_official(client, people, db_session):
    task = create_task(client, people)

    first = legacy_submit(client, people["student"], task["task_id"])
    second = legacy_submit(client, people["student"], task["task_id"], code="print('again')\n")

    assert first.status_code == 201 and second.status_code == 201
    assert second.json()["attempt_number"] == 2
    db_session.expire_all()
    official = db_session.query(Submission).filter(Submission.is_official.is_(True)).all()
    assert [s.sub_id for s in official] == [second.json()["sub_id"]]


def test_legacy_submit_keeps_its_documented_status_codes(client, people):
    draft = create_task(client, people, publish=False)
    published = create_task(client, people)

    assert legacy_submit(client, people["student"], draft["task_id"]).status_code == 403
    assert legacy_submit(client, people["outsider"], published["task_id"]).status_code == 403
    assert legacy_submit(client, people["student"], 999999).status_code == 404


def test_legacy_submit_stays_deadline_strict_even_with_a_retake(client, people, db_session):
    task = create_task(client, people, due_at=datetime.now(timezone.utc) + timedelta(days=1))
    sub_id = legacy_submit(client, people["student"], task["task_id"]).json()["sub_id"]

    stored = db_session.query(Task).filter(Task.task_id == task["task_id"]).one()
    stored.due_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()
    granted = client.post(f"/instructors/submissions/{sub_id}/retake", headers=auth(people["instructor"]))
    assert granted.status_code == 200, granted.text

    late = legacy_submit(client, people["student"], task["task_id"])

    assert late.status_code == 409
    db_session.expire_all()
    assert db_session.query(Submission).count() == 1
    # The allowance is still there for POST /submissions/, which honours it.
    assert db_session.query(Submission).filter(Submission.retake_allowed.is_(True)).count() == 1
    main_route = client.post(
        "/submissions/",
        headers=auth(people["student"]),
        json={"task_id": task["task_id"], "raw_code": "print('late')\n"},
    )
    assert main_route.status_code == 201, main_route.text


def test_legacy_submit_saves_nothing_when_the_audit_record_fails(client, people, db_session, celery_calls, monkeypatch):
    task = create_task(client, people)

    def broken_audit(*args, **kwargs):
        raise AuditServiceError("audit store unavailable")

    monkeypatch.setattr(submission_service, "create_audit_record", broken_audit)

    response = legacy_submit(client, people["student"], task["task_id"])

    assert response.status_code == 503
    db_session.expire_all()
    assert db_session.query(Submission).count() == 0
    assert db_session.query(Notification).filter(
        Notification.recipient_id == people["instructor"].user_id,
    ).count() == 0
    assert not [call for call in celery_calls if call[0] == "evaluate_submission_background_task"]


def test_legacy_get_hides_review_indicators_from_students(client, people, db_session):
    task = create_task(client, people)
    sub_id = legacy_submit(client, people["student"], task["task_id"]).json()["sub_id"]

    # Stand-in for a finished background evaluation.
    stored = db_session.query(Submission).filter(Submission.sub_id == sub_id).one()
    stored.jaccard_score = 12.5
    stored.ast_pass_fail = True
    db_session.commit()

    as_student = client.get(f"{LEGACY}{sub_id}", headers=auth(people["student"]))
    as_instructor = client.get(f"{LEGACY}{sub_id}", headers=auth(people["instructor"]))
    as_other_instructor = client.get(f"{LEGACY}{sub_id}", headers=auth(people["other_instructor"]))
    as_outsider = client.get(f"{LEGACY}{sub_id}", headers=auth(people["outsider"]))

    assert as_student.status_code == 200, as_student.text
    assert as_student.json()["sub_id"] == sub_id
    assert as_student.json()["jaccard_score"] is None
    assert as_student.json()["ast_pass_fail"] is None

    assert as_instructor.status_code == 200, as_instructor.text
    assert as_instructor.json()["jaccard_score"] == 12.5
    assert as_instructor.json()["ast_pass_fail"] is True

    assert as_other_instructor.status_code == 403
    assert as_outsider.status_code == 403

    db_session.expire_all()
    unchanged = db_session.query(Submission).filter(Submission.sub_id == sub_id).one()
    assert unchanged.jaccard_score == 12.5
    assert unchanged.ast_pass_fail is True
