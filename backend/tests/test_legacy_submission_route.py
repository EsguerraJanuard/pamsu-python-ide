"""Legacy /execution/submissions/ routes: removed on 2026-10-22.

History ("Full backend audit", Still open, items 5 and 7): the legacy POST
once inserted attempts by itself (no audit record, notification or background
evaluation) and the legacy GET showed students the instructor-only review
indicators. Both were patched on 2026-10-21. The owner question "remove the
legacy routes?" was then decided: the frontend never called them and they
duplicated POST /submissions/, GET /submissions/{id} and
GET /instructors/submissions/{id}, so they are gone. These tests keep them
gone and check that the replacements cover what they did.
"""

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import (Classroom, Enrollment, ExecutionRequest,
                                      Submission, User)

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


@pytest.fixture
def people(db_session):
    instructor = make_user(db_session, email=f"faculty{DOMAIN}", role="instructor", school_id="9000000002")
    student = make_user(db_session, email=f"2023000001{DOMAIN}", role="student", school_id="2023000001")
    classroom = Classroom(instructor_id=instructor.user_id, name="Programming 1", subject_code="CCS101",
                          section="BSIT 1A", class_code="CLASSA01", is_active=True)
    db_session.add(classroom)
    db_session.commit()
    db_session.add(Enrollment(class_id=classroom.class_id, student_id=student.user_id, status="active"))
    db_session.commit()
    return {"instructor": instructor, "student": student, "classroom": classroom}


@pytest.fixture
def task(client, people):
    created = client.post("/instructors/tasks/", headers=auth(people["instructor"]), json={
        "title": "Loops Laboratory", "class_ids": [people["classroom"].class_id], "difficulty": "beginner",
    })
    assert created.status_code == 201, created.text
    task_id = created.json()[0]["task_id"]
    published = client.patch(f"/instructors/tasks/{task_id}/publication", headers=auth(people["instructor"]),
                             json={"is_published": True})
    assert published.status_code == 200, published.text
    return published.json()


def test_the_legacy_post_is_gone_and_saves_nothing(client, db_session, people, task):
    response = client.post("/execution/submissions/", headers=auth(people["student"]),
                           json={"task_id": task["task_id"], "raw_code": "print('hi')\n"})

    assert response.status_code == 404
    assert db_session.query(Submission).count() == 0


def test_the_legacy_get_is_gone(client, db_session, people, task):
    created = client.post("/submissions/", headers=auth(people["student"]),
                          json={"task_id": task["task_id"], "raw_code": "print('hi')\n"})
    assert created.status_code == 201, created.text
    sub_id = created.json()["sub_id"]

    for user in (people["student"], people["instructor"]):
        assert client.get(f"/execution/submissions/{sub_id}", headers=auth(user)).status_code == 404

    # The replacements: the student's own view (no review indicators) and
    # the instructor's view.
    student_view = client.get(f"/submissions/{sub_id}", headers=auth(people["student"]))
    assert student_view.status_code == 200
    assert "jaccard_score" not in student_view.json()
    instructor_view = client.get(f"/instructors/submissions/{sub_id}", headers=auth(people["instructor"]))
    assert instructor_view.status_code == 200
    assert "jaccard_score" in instructor_view.json()


def test_post_submissions_queues_exactly_one_submit_run(client, db_session, people, task, celery_calls):
    created = client.post("/submissions/", headers=auth(people["student"]),
                          json={"task_id": task["task_id"], "raw_code": "print('hi')\n"})
    assert created.status_code == 201, created.text
    sub_id = created.json()["sub_id"]

    refused = client.post("/execution/requests/", headers=auth(people["student"]), json={
        "request_kind": "submit", "task_id": task["task_id"], "submission_id": sub_id, "standard_input": "",
    })

    assert refused.status_code == 409
    runs = db_session.query(ExecutionRequest).filter(ExecutionRequest.submission_id == sub_id).all()
    assert [run.request_kind for run in runs] == ["submit"]
    assert ("evaluate_submission_background_task", (sub_id,)) in celery_calls
    assert ("dispatch_to_partner", (runs[0].execution_id,)) in celery_calls


def test_run_requests_are_limited_per_student(client, people, task):
    def run():
        return client.post("/execution/requests/", headers=auth(people["student"]), json={
            "request_kind": "run", "task_id": task["task_id"], "source_code": "print(1)\n", "standard_input": "",
        })

    statuses = [run().status_code for _ in range(6)]

    assert statuses[:5] == [201] * 5
    assert statuses[5] == 429
