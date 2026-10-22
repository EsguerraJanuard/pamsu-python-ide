"""
MIS and enrollment follow-ups decided on 2026-10-22 (audit-status.md, "Audit
follow-ups: what is still open", items 6 and 8):

- MIS can correct a student's school ID (students only; audited);
- faculty accounts get no emailed password (see test_provisioning_email.py
  for the email itself);
- account lists flag self-service guests, so the dashboard can show them;
- enrollment decision 1: bulk enroll reports suspended students instead of
  enrolling them;
- enrollment decision 4: self-service guests are never enrolled by bulk
  enroll or by queued (pending) enrollments;
- enrollment decision 5: MIS (not instructors) can list queued enrollments
  and see which ones "Apply" would complete now.
"""

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import (AuditRecord, Classroom, Enrollment,
                                      PendingEnrollment, User)

DOMAIN = "@pampangastateu.edu.ph"
PASSWORD_HASH = get_password_hash("test12345")


def make_user(db: Session, *, email: str, role: str, school_id: str, is_active: bool = True,
              name: str = "Test User") -> User:
    user = User(name=name, email=email, role=role, school_id=school_id, password_hash=PASSWORD_HASH,
                email_verified=True, is_active=is_active)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_classroom(db: Session, instructor: User, code: str, *, is_active: bool = True, name: str | None = None):
    classroom = Classroom(instructor_id=instructor.user_id, name=name or f"Programming {code}",
                          subject_code="CC 102", section="BSIT 1-A", class_code=code, is_active=is_active)
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.user_id)})}"}


@pytest.fixture
def people(db_session):
    return {
        "admin": make_user(db_session, email=f"mis{DOMAIN}", role="admin", school_id="9000000001"),
        "instructor": make_user(db_session, email=f"faculty{DOMAIN}", role="instructor", school_id="FAC0000001"),
        "student": make_user(db_session, email=f"2026000001{DOMAIN}", role="student", school_id="2026000001"),
        "other": make_user(db_session, email=f"2026000002{DOMAIN}", role="student", school_id="2026000002"),
        "guest": make_user(db_session, email=f"guest_ab12cd34{DOMAIN}", role="student", school_id="GST1234567"),
    }


def audits(db: Session, action: str) -> list[AuditRecord]:
    db.expire_all()
    return db.query(AuditRecord).filter(AuditRecord.action_type == action).all()


# ------------------------------------------------------------ school ID


@pytest.mark.parametrize("new_id", ["2026009999", "2026-09999"])
def test_mis_can_correct_a_student_school_id(client, db_session, people, new_id):
    student = people["student"]

    response = client.patch(f"/admin/users/{student.user_id}", headers=auth(people["admin"]),
                            json={"school_id": new_id})

    assert response.status_code == 200, response.text
    assert response.json()["school_id"] == new_id
    assert response.json()["changed_fields"] == ["school_id"]
    (record,) = audits(db_session, "user_updated")
    # Which field changed, never the old or new value.
    assert record.audit_data == {"role": "student", "changed_fields": ["school_id"], "enrolled_from_pending": 0}
    assert new_id not in str(record.audit_data)


def test_a_school_id_in_use_is_refused_and_recorded(client, db_session, people):
    response = client.patch(f"/admin/users/{people['student'].user_id}", headers=auth(people["admin"]),
                            json={"school_id": people["other"].school_id, "name": "Changed Name"})

    assert response.status_code == 409
    db_session.expire_all()
    student = db_session.get(User, people["student"].user_id)
    # The name change in the same request is discarded too.
    assert (student.school_id, student.name) == ("2026000001", "Test User")
    (record,) = audits(db_session, "user_updated")
    assert (record.outcome, record.audit_data["reason"]) == ("failed", "school_id_in_use")


def test_faculty_school_ids_stay_placeholders(client, db_session, people):
    response = client.patch(f"/admin/users/{people['instructor'].user_id}", headers=auth(people["admin"]),
                            json={"school_id": "2026009999"})

    assert response.status_code == 400
    assert db_session.get(User, people["instructor"].user_id).school_id == "FAC0000001"


@pytest.mark.parametrize("bad", ["12345", "GST1234567", "2026_00001", "20260000011"])
def test_school_ids_must_be_student_numbers(client, people, bad):
    response = client.patch(f"/admin/users/{people['student'].user_id}", headers=auth(people["admin"]),
                            json={"school_id": bad})

    assert response.status_code == 422


def test_guest_school_ids_cannot_be_edited(client, people):
    response = client.patch(f"/admin/users/{people['guest'].user_id}", headers=auth(people["admin"]),
                            json={"school_id": "2026009999"})

    assert response.status_code == 403


# ------------------------------------------------------------ faculty without a password


def test_faculty_can_be_created_without_a_password(client, db_session, people):
    response = client.post("/admin/instructors", headers=auth(people["admin"]), json={
        "email": f"new.faculty{DOMAIN}", "first_name": "New", "last_name": "Faculty",
    })

    assert response.status_code == 200, response.text
    created = db_session.query(User).filter(User.email == f"new.faculty{DOMAIN}").one()
    # Nobody knows a password for it (not a bcrypt hash, so nothing verifies):
    # the instructor sets one with a reset code.
    assert not created.password_hash.startswith("$2")
    record = next(r for r in audits(db_session, "user_created") if r.resource_id == str(created.user_id))
    assert record.audit_data["sign_in_setup"] == "set_by_instructor"


def test_a_short_password_is_still_refused(client, people):
    response = client.post("/admin/instructors", headers=auth(people["admin"]), json={
        "email": f"new.faculty{DOMAIN}", "first_name": "New", "last_name": "Faculty", "password": "short",
    })

    assert response.status_code == 422


# ------------------------------------------------------------ guests in the directory


def test_account_lists_flag_guests_and_hide_them_by_default(client, people):
    default = client.get("/admin/users", headers=auth(people["admin"])).json()
    with_guests = client.get("/admin/users?include_guests=true", headers=auth(people["admin"])).json()

    assert people["guest"].user_id not in {user["user_id"] for user in default}
    flags = {user["user_id"]: user["is_guest"] for user in with_guests}
    assert flags[people["guest"].user_id] is True
    assert flags[people["student"].user_id] is False
    assert flags[people["instructor"].user_id] is False


# ------------------------------------------------------------ bulk enroll


def test_bulk_enroll_reports_suspended_students_and_guests_without_enrolling_them(client, db_session, people):
    classroom = make_classroom(db_session, people["instructor"], "CLASSA01")
    suspended = make_user(db_session, email=f"2026000003{DOMAIN}", role="student", school_id="2026000003",
                          is_active=False)

    response = client.post(f"/classrooms/{classroom.class_id}/bulk-enroll", headers=auth(people["instructor"]),
                           json={"emails": [people["student"].email, suspended.email, people["guest"].email]})

    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["enrolled"], body["suspended"], body["ineligible"], body["queued"]) == (1, 1, 1, 0)
    enrolled = {row.student_id for row in db_session.query(Enrollment).filter_by(class_id=classroom.class_id)}
    assert enrolled == {people["student"].user_id}
    assert db_session.query(PendingEnrollment).count() == 0


def test_queued_enrollments_never_reach_a_guest(client, db_session, people):
    classroom = make_classroom(db_session, people["instructor"], "CLASSA02")
    db_session.add(PendingEnrollment(class_id=classroom.class_id, email=people["guest"].email))
    db_session.commit()

    response = client.post(f"/admin/students/{people['guest'].user_id}/pending-enrollments/apply",
                           headers=auth(people["admin"]))

    assert response.status_code == 409
    assert db_session.query(Enrollment).count() == 0
    assert db_session.query(PendingEnrollment).count() == 1


# ------------------------------------------------------------ pending list


@pytest.fixture
def queued(db_session, people):
    active = make_classroom(db_session, people["instructor"], "CLASSB01", name="Python Basics")
    archived = make_classroom(db_session, people["instructor"], "CLASSB02", is_active=False, name="Old Section")
    suspended = make_user(db_session, email=f"2026000004{DOMAIN}", role="student", school_id="2026000004",
                          is_active=False)
    db_session.add_all([
        # An account made before pending rows were applied on creation: ready.
        PendingEnrollment(class_id=active.class_id, email=people["student"].email),
        # No account yet: waiting.
        PendingEnrollment(class_id=active.class_id, email=f"2026000099{DOMAIN}"),
        # Archived class: waiting (decision 2: kept, applied after reactivation).
        PendingEnrollment(class_id=archived.class_id, email=people["other"].email),
        # Suspended account: waiting.
        PendingEnrollment(class_id=active.class_id, email=suspended.email),
    ])
    db_session.commit()
    return {"active": active, "archived": archived}


def test_mis_lists_queued_enrollments_with_what_is_ready(client, people, queued):
    body = client.get("/admin/pending-enrollments", headers=auth(people["admin"])).json()

    assert (body["total"], body["ready"]) == (4, 1)
    by_email = {item["email"]: item for item in body["items"]}
    ready = by_email[people["student"].email]
    assert (ready["ready"], ready["user_id"], ready["class_name"]) == (True, people["student"].user_id, "Python Basics")
    assert by_email[f"2026000099{DOMAIN}"]["user_id"] is None
    assert by_email[people["other"].email]["class_active"] is False
    assert not any(item["ready"] for email, item in by_email.items() if email != people["student"].email)


def test_pending_list_filters(client, people, queued):
    admin = auth(people["admin"])

    ready = client.get("/admin/pending-enrollments?state=ready", headers=admin).json()
    waiting = client.get("/admin/pending-enrollments?state=waiting", headers=admin).json()
    searched = client.get("/admin/pending-enrollments?q=old%20sec", headers=admin).json()

    assert [item["email"] for item in ready["items"]] == [people["student"].email]
    assert waiting["total"] == 3
    assert [item["email"] for item in searched["items"]] == [people["other"].email]


def test_applying_a_ready_row_enrolls_the_student(client, db_session, people, queued):
    response = client.post(f"/admin/students/{people['student'].user_id}/pending-enrollments/apply",
                           headers=auth(people["admin"]))

    assert response.status_code == 200
    assert response.json()["enrolled_class_ids"] == [queued["active"].class_id]
    after = client.get("/admin/pending-enrollments", headers=auth(people["admin"])).json()
    assert (after["total"], after["ready"]) == (3, 0)


def test_instructors_cannot_list_queued_addresses(client, people, queued):
    assert client.get("/admin/pending-enrollments", headers=auth(people["instructor"])).status_code == 403


# ------------------------------------------------------------ item 9


def test_a_classroom_without_a_section_does_not_break_the_class_list(client, db_session, people):
    # The API always sets a section; a class created another way may not.
    classroom = Classroom(instructor_id=people["instructor"].user_id, name="Seeded Class", subject_code=None,
                          section=None, class_code="NOSECT01", is_active=True)
    db_session.add(classroom)
    db_session.commit()
    db_session.add(Enrollment(class_id=classroom.class_id, student_id=people["student"].user_id, status="active"))
    db_session.commit()

    instructor_view = client.get("/classrooms/", headers=auth(people["instructor"]))
    student_view = client.get("/classrooms/mine", headers=auth(people["student"]))

    assert instructor_view.status_code == 200, instructor_view.text
    assert [row["section"] for row in instructor_view.json()] == [None]
    assert student_view.status_code == 200, student_view.text
    assert [row["classroom"]["section"] for row in student_view.json()] == [None]
