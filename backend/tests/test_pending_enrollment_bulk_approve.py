"""
MIS queued class enrollments: sorting and "Approve all ready" (2026-11-04).

GET /admin/pending-enrollments can be sorted by queue date, class,
instructor or student email, and names each class's instructor.
POST /admin/pending-enrollments/apply-ready applies every ready row in short
batches (3-second rule), exactly as the per-student "Apply" does.
"""

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import (AuditRecord, Classroom, Enrollment,
                                      PendingEnrollment, User)
from app.routers import admin as admin_router
from app.services.classroom_service import StudentNotEligibleForEnrollmentError

DOMAIN = "@pampangastateu.edu.ph"
PASSWORD_HASH = get_password_hash("test12345")
APPLY_READY = "/admin/pending-enrollments/apply-ready"


def make_user(db: Session, *, email: str, role: str, school_id: str, name: str = "Test User",
              is_active: bool = True) -> User:
    user = User(name=name, email=email, role=role, school_id=school_id, password_hash=PASSWORD_HASH,
                email_verified=True, is_active=is_active)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_classroom(db: Session, instructor: User, code: str, name: str, *, is_active: bool = True) -> Classroom:
    classroom = Classroom(instructor_id=instructor.user_id, name=name, subject_code="CC 102",
                          section="BSIT 1-A", class_code=code, is_active=is_active)
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.user_id)})}"}


def queue(db: Session, classroom: Classroom, email: str) -> None:
    db.add(PendingEnrollment(class_id=classroom.class_id, email=email))
    db.commit()


def enrolled_class_ids(db: Session, student: User) -> list[int]:
    db.expire_all()
    return sorted(e.class_id for e in db.query(Enrollment).filter(Enrollment.student_id == student.user_id))


@pytest.fixture
def world(db_session):
    db = db_session
    admin = make_user(db, email=f"mis{DOMAIN}", role="admin", school_id="9000000001", name="MIS Admin")
    zamora = make_user(db, email=f"zamora{DOMAIN}", role="instructor", school_id="FAC0000001", name="Zeny Zamora")
    abad = make_user(db, email=f"abad{DOMAIN}", role="instructor", school_id="FAC0000002", name="Arnel Abad")
    python = make_classroom(db, zamora, "CLASSP01", "Python Basics")
    algorithms = make_classroom(db, abad, "CLASSA01", "Algorithms")
    archived = make_classroom(db, abad, "CLASSO01", "Old Section", is_active=False)

    # Accounts made before their queued rows were applied: ready.
    ana = make_user(db, email=f"ana.reyes{DOMAIN}", role="student", school_id="2026000001", name="Ana Reyes")
    ben = make_user(db, email=f"ben.cruz{DOMAIN}", role="student", school_id="2026000002", name="Ben Cruz")
    suspended = make_user(db, email=f"sus.pended{DOMAIN}", role="student", school_id="2026000003",
                          is_active=False)
    queue(db, python, ana.email)
    queue(db, algorithms, ana.email)
    queue(db, archived, ana.email)  # waits: class archived
    queue(db, algorithms, ben.email)
    queue(db, python, f"no.account{DOMAIN}")  # waits: no account yet
    queue(db, python, suspended.email)  # waits: account suspended
    return {
        "admin": admin, "zamora": zamora, "abad": abad, "python": python, "algorithms": algorithms,
        "archived": archived, "ana": ana, "ben": ben, "suspended": suspended,
    }


# ------------------------------------------------------------ sorting


def listed(client, world, **params) -> dict:
    response = client.get("/admin/pending-enrollments", headers=auth(world["admin"]), params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_rows_name_the_instructor_and_echo_the_sort(client, world):
    body = listed(client, world)

    assert body["sort"] == "newest"
    assert body["can_apply_ready"] is True
    by_class = {item["class_name"]: item["instructor_name"] for item in body["items"]}
    assert by_class == {"Python Basics": "Zeny Zamora", "Algorithms": "Arnel Abad", "Old Section": "Arnel Abad"}


def test_sort_by_class_instructor_student_and_date(client, world):
    by_class = listed(client, world, sort="class")
    assert by_class["sort"] == "class"
    assert [item["class_name"] for item in by_class["items"]] == [
        "Algorithms", "Algorithms", "Old Section", "Python Basics", "Python Basics", "Python Basics",
    ]
    # Within a class, rows go by student email.
    assert [item["email"] for item in by_class["items"][:2]] == [world["ana"].email, world["ben"].email]

    by_instructor = listed(client, world, sort="instructor")
    assert [item["instructor_name"] for item in by_instructor["items"]] == ["Arnel Abad"] * 3 + ["Zeny Zamora"] * 3

    by_student = listed(client, world, sort="student")
    emails = [item["email"] for item in by_student["items"]]
    assert emails == sorted(emails)

    newest = [item["pending_id"] for item in listed(client, world)["items"]]
    oldest = [item["pending_id"] for item in listed(client, world, sort="oldest")["items"]]
    assert oldest == sorted(oldest)
    assert newest == list(reversed(oldest))


def test_sort_keeps_state_filter_and_counts(client, world):
    ready = listed(client, world, state="ready", sort="class")

    assert (ready["total"], ready["ready"]) == (3, 3)
    assert [(item["class_name"], item["email"]) for item in ready["items"]] == [
        ("Algorithms", world["ana"].email),
        ("Algorithms", world["ben"].email),
        ("Python Basics", world["ana"].email),
    ]


def test_unknown_sort_is_refused(client, world):
    response = client.get("/admin/pending-enrollments?sort=random", headers=auth(world["admin"]))

    assert response.status_code == 422


def test_search_matches_instructor_name(client, world):
    body = listed(client, world, q="zamora")

    assert body["total"] == 3
    assert {item["class_name"] for item in body["items"]} == {"Python Basics"}


# ------------------------------------------------------------ approve all ready


def test_approve_all_ready_enrolls_every_ready_row_and_leaves_the_rest(client, db_session, world):
    response = client.post(APPLY_READY, headers=auth(world["admin"]))

    assert response.status_code == 200, response.text
    assert response.json() == {
        "students": 2,
        "enrolled": 3,
        "already_enrolled": 0,
        # Ana's archived class is hers too: it stays queued, as with "Apply".
        "skipped": 1,
        "ineligible_students": 0,
        "remaining_ready": 0,
    }
    assert enrolled_class_ids(db_session, world["ana"]) == sorted(
        [world["python"].class_id, world["algorithms"].class_id]
    )
    assert enrolled_class_ids(db_session, world["ben"]) == [world["algorithms"].class_id]

    after = listed(client, world)
    assert (after["total"], after["ready"]) == (3, 0)
    assert {item["email"] for item in after["items"]} == {
        world["ana"].email, f"no.account{DOMAIN}", world["suspended"].email,
    }


def test_approve_all_ready_is_audited_with_mis_as_the_actor(client, db_session, world):
    client.post(APPLY_READY, headers=auth(world["admin"]))

    db_session.expire_all()
    records = db_session.query(AuditRecord).filter(AuditRecord.action_type == "student_enrolled").all()
    assert len(records) == 3
    assert {r.actor_user_id for r in records} == {world["admin"].user_id}
    assert {r.audit_data["source"] for r in records} == {"pending_enrollment"}


def test_approve_all_ready_again_changes_nothing(client, db_session, world):
    client.post(APPLY_READY, headers=auth(world["admin"]))

    again = client.post(APPLY_READY, headers=auth(world["admin"]))

    assert again.status_code == 200
    assert again.json() == {
        "students": 0, "enrolled": 0, "already_enrolled": 0, "skipped": 0,
        "ineligible_students": 0, "remaining_ready": 0,
    }
    db_session.expire_all()
    assert db_session.query(Enrollment).count() == 3


def test_a_stale_row_for_an_existing_enrollment_is_consumed(client, db_session, world):
    db_session.add(Enrollment(class_id=world["algorithms"].class_id, student_id=world["ben"].user_id,
                              status="active"))
    db_session.commit()

    body = client.post(APPLY_READY, headers=auth(world["admin"])).json()

    assert (body["enrolled"], body["already_enrolled"], body["remaining_ready"]) == (2, 1, 0)
    db_session.expire_all()
    assert db_session.query(Enrollment).filter_by(student_id=world["ben"].user_id).count() == 1


def test_batches_until_nothing_ready_is_left(client, db_session, world, monkeypatch):
    monkeypatch.setattr(admin_router, "APPLY_READY_MAX_STUDENTS", 1)
    admin = auth(world["admin"])

    first = client.post(APPLY_READY, headers=admin).json()
    second = client.post(APPLY_READY, headers=admin).json()

    # Oldest queued first: Ana's rows were queued before Ben's.
    assert (first["students"], first["enrolled"], first["remaining_ready"]) == (1, 2, 1)
    assert (second["students"], second["enrolled"], second["remaining_ready"]) == (1, 1, 0)
    assert enrolled_class_ids(db_session, world["ben"]) == [world["algorithms"].class_id]


def test_an_exhausted_time_budget_still_handles_one_student(client, world, monkeypatch):
    monkeypatch.setattr(admin_router, "APPLY_READY_TIME_BUDGET_SECONDS", 0)

    body = client.post(APPLY_READY, headers=auth(world["admin"])).json()

    assert (body["students"], body["remaining_ready"]) == (1, 1)


def test_a_student_who_became_ineligible_is_reported_and_others_still_join(client, db_session, world,
                                                                           monkeypatch):
    real_apply = admin_router.apply_pending_enrollments

    def apply_refusing_ana(*, db, student, actor_user_id):
        if student.user_id == world["ana"].user_id:
            raise StudentNotEligibleForEnrollmentError("suspended meanwhile")
        return real_apply(db=db, student=student, actor_user_id=actor_user_id)

    monkeypatch.setattr(admin_router, "apply_pending_enrollments", apply_refusing_ana)

    body = client.post(APPLY_READY, headers=auth(world["admin"])).json()

    assert (body["students"], body["enrolled"], body["ineligible_students"]) == (1, 1, 1)
    # Ana's rows are still queued (and still ready here, since the refusal was simulated).
    assert body["remaining_ready"] == 2
    assert enrolled_class_ids(db_session, world["ana"]) == []
    assert enrolled_class_ids(db_session, world["ben"]) == [world["algorithms"].class_id]


def test_only_mis_can_approve_all(client, db_session, world):
    student = world["ben"]

    for caller in (world["zamora"], student):
        assert client.post(APPLY_READY, headers=auth(caller)).status_code == 403
    assert client.post(APPLY_READY).status_code == 401

    db_session.expire_all()
    assert db_session.query(Enrollment).count() == 0
    assert db_session.query(PendingEnrollment).count() == 6
