"""Admin account corrections and the filtered audit-trail search (2026-10-21).

PATCH /admin/users/{id} lets MIS fix a faculty or student name or email.
GET /admin/audit-logs/search adds filters and page numbers; the original
GET /admin/audit-logs keeps its plain-list shape for older dashboards.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import (AuditRecord, Classroom, Enrollment, OTPChallenge,
                                      PendingEnrollment, User)

DOMAIN = "@pampangastateu.edu.ph"
PASSWORD = "Original#2026"


def make_user(db: Session, *, email: str, role: str, school_id: str, name: str = "Test User", is_active: bool = True) -> User:
    user = User(
        name=name,
        email=email,
        role=role,
        school_id=school_id,
        password_hash=get_password_hash(PASSWORD),
        email_verified=True,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.user_id)})}"}


@pytest.fixture
def people(db_session):
    return {
        "admin": make_user(db_session, email=f"mis{DOMAIN}", role="admin", school_id="9000000001", name="MIS Admin"),
        "instructor": make_user(db_session, email=f"faculty{DOMAIN}", role="instructor", school_id="FAC0000001", name="Maria Santos"),
        "student": make_user(db_session, email=f"juan.delacrus{DOMAIN}", role="student", school_id="2026000001", name="Juan Dela Crus"),
        "other_student": make_user(db_session, email=f"ana.reyes{DOMAIN}", role="student", school_id="2026000002", name="Ana Reyes"),
    }


def edit(client, admin: User, user: User, **body):
    return client.patch(f"/admin/users/{user.user_id}", headers=auth(admin), json=body)


# ------------------------------------------------------------------ edit


def test_admin_corrects_a_name_and_an_email(client, people, db_session):
    student = people["student"]

    response = edit(client, people["admin"], student, name="  Juan   Dela Cruz ", email=f"Juan.DelaCruz{DOMAIN}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["name"] == "Juan Dela Cruz"
    assert body["email"] == f"juan.delacruz{DOMAIN}"
    assert body["changed_fields"] == ["name", "email"]
    assert body["school_id"] == "2026000001"
    db_session.expire_all()
    stored = db_session.get(User, student.user_id)
    assert (stored.name, stored.email, stored.role) == ("Juan Dela Cruz", f"juan.delacruz{DOMAIN}", "student")

    # The corrected address is now the sign-in name.
    assert client.post("/login", data={"username": f"juan.delacruz{DOMAIN}", "password": PASSWORD}).status_code == 200
    assert client.post("/login", data={"username": f"juan.delacrus{DOMAIN}", "password": PASSWORD}).status_code == 401


def test_name_only_and_unchanged_values(client, people):
    instructor = people["instructor"]

    renamed = edit(client, people["admin"], instructor, name="Maria L. Santos")
    unchanged = edit(client, people["admin"], instructor, name="Maria L. Santos", email=f"FACULTY{DOMAIN}")

    assert renamed.status_code == 200 and renamed.json()["changed_fields"] == ["name"]
    assert unchanged.status_code == 200 and unchanged.json()["changed_fields"] == []


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"email": "someone@gmail.com"},
        {"email": f"a@b{DOMAIN}"},
        {"email": f"guest_abc{DOMAIN}"},
        {"name": "   "},
        {"name": "x" * 151},
        {"role": "admin"},
        {"name": "Ana Reyes", "school_id": "2026999999"},
        {"name": "Ana Reyes", "password": "NewPass#2026"},
    ],
)
def test_invalid_or_forbidden_changes_are_rejected(client, people, db_session, body):
    response = edit(client, people["admin"], people["other_student"], **body)

    assert response.status_code == 422, response.text
    db_session.expire_all()
    stored = db_session.get(User, people["other_student"].user_id)
    assert (stored.name, stored.email, stored.role, stored.school_id) == ("Ana Reyes", f"ana.reyes{DOMAIN}", "student", "2026000002")


def test_email_already_used_by_another_account_is_a_conflict(client, people):
    response = edit(client, people["admin"], people["student"], email=f"ANA.REYES{DOMAIN}")

    assert response.status_code == 409
    assert response.json()["detail"] == "Another account already uses this email."


def test_admin_and_guest_accounts_cannot_be_edited(client, people, db_session):
    other_admin = make_user(db_session, email=f"mis2{DOMAIN}", role="admin", school_id="9000000002")
    guest = make_user(db_session, email=f"guest_0a1b2c3d4e5f{DOMAIN}", role="student", school_id="GST0000001")

    assert edit(client, people["admin"], other_admin, name="Renamed").status_code == 403
    assert edit(client, people["admin"], people["admin"], name="Renamed").status_code == 403
    assert edit(client, people["admin"], guest, name="Renamed").status_code == 403
    assert client.patch("/admin/users/999999", headers=auth(people["admin"]), json={"name": "X"}).status_code == 404


def test_only_admins_may_edit_accounts(client, people):
    for caller in (people["instructor"], people["student"]):
        response = client.patch(f"/admin/users/{people['other_student'].user_id}", headers=auth(caller), json={"name": "X"})
        assert response.status_code == 403
    assert client.patch(f"/admin/users/{people['other_student'].user_id}", json={"name": "X"}).status_code == 401


def test_email_change_expires_open_reset_codes_for_both_addresses(client, people, db_session):
    old_email, new_email, unrelated = f"juan.delacrus{DOMAIN}", f"juan.delacruz{DOMAIN}", f"ana.reyes{DOMAIN}"
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    for email in (old_email, new_email, unrelated):
        db_session.add(OTPChallenge(email=email, purpose="password_reset", otp_hash="x", expires_at=expires))
    db_session.commit()

    assert edit(client, people["admin"], people["student"], email=new_email).status_code == 200

    db_session.expire_all()
    consumed = {c.email: c.consumed_at is not None for c in db_session.query(OTPChallenge).all()}
    assert consumed == {old_email: True, new_email: True, unrelated: False}


def test_name_change_leaves_reset_codes_alone(client, people, db_session):
    db_session.add(OTPChallenge(email=f"juan.delacrus{DOMAIN}", purpose="password_reset", otp_hash="x",
                                expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)))
    db_session.commit()

    assert edit(client, people["admin"], people["student"], name="Juan Dela Cruz").status_code == 200

    db_session.expire_all()
    assert db_session.query(OTPChallenge).one().consumed_at is None


def test_corrected_student_email_joins_classes_that_queued_it(client, people, db_session):
    classroom = Classroom(instructor_id=people["instructor"].user_id, name="Programming 1", subject_code="CCS101",
                          section="BSIT 1A", class_code="CLASSA01", is_active=True)
    db_session.add(classroom)
    db_session.commit()
    db_session.add(PendingEnrollment(class_id=classroom.class_id, email=f"juan.delacruz{DOMAIN}"))
    db_session.commit()

    response = edit(client, people["admin"], people["student"], email=f"juan.delacruz{DOMAIN}")

    assert response.status_code == 200, response.text
    assert response.json()["pending_enrollments"]["enrolled_class_ids"] == [classroom.class_id]
    db_session.expire_all()
    assert db_session.query(Enrollment).filter(Enrollment.student_id == people["student"].user_id).count() == 1
    assert db_session.query(PendingEnrollment).count() == 0


def test_instructor_email_change_has_no_enrollment_step(client, people):
    response = edit(client, people["admin"], people["instructor"], email=f"maria.santos{DOMAIN}")

    assert response.status_code == 200
    assert response.json()["pending_enrollments"] is None


# ------------------------------------------------------------------ audit search


def add_record(db: Session, *, actor: User | None, action: str, outcome: str = "succeeded", minutes_ago: int = 0, n: int = 0) -> AuditRecord:
    record = AuditRecord(
        audit_key=f"test:{action}:{outcome}:{minutes_ago}:{n}:{actor.user_id if actor else 'system'}",
        actor_user_id=actor.user_id if actor else None,
        action_type=action,
        resource_type="user",
        resource_id=str(actor.user_id if actor else 0),
        outcome=outcome,
        audit_data={},
        occurred_at=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
    )
    db.add(record)
    db.commit()
    return record


@pytest.fixture
def records(db_session, people):
    add_record(db_session, actor=people["admin"], action="login_succeeded", minutes_ago=1)
    add_record(db_session, actor=people["student"], action="login_failed", outcome="failed", minutes_ago=2)
    add_record(db_session, actor=people["instructor"], action="classroom_created", minutes_ago=3)
    add_record(db_session, actor=people["student"], action="login_succeeded", minutes_ago=60 * 26)
    add_record(db_session, actor=None, action="classroom_updated", minutes_ago=5)
    add_record(db_session, actor=people["other_student"], action="login_failed", outcome="denied", minutes_ago=6)


def search(client, admin: User, **params):
    response = client.get("/admin/audit-logs/search", headers=auth(admin), params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_search_pages_newest_first_with_a_total(client, people, records):
    first = search(client, people["admin"], page=1, page_size=5)
    second = search(client, people["admin"], page=2, page_size=5)
    beyond = search(client, people["admin"], page=9, page_size=5)

    assert first["total"] == 6 and first["page"] == 1 and first["page_size"] == 5
    assert [i["action_type"] for i in first["items"]] == [
        "login_succeeded", "login_failed", "classroom_created", "classroom_updated", "login_failed",
    ]
    assert [i["actor_name"] for i in second["items"]] == ["Juan Dela Crus"]
    assert beyond["items"] == [] and beyond["total"] == 6
    assert "login_failed" in first["action_types"] and len(first["action_types"]) == 20
    assert first["items"][0]["actor_email"] == f"mis{DOMAIN}"


def test_search_matches_actor_name_or_email_case_insensitively(client, people, records):
    by_name = search(client, people["admin"], q="DELA")
    by_email = search(client, people["admin"], q="ana.reyes@")
    wildcard = search(client, people["admin"], q="%")
    underscore = search(client, people["admin"], q="_")

    assert {i["actor_name"] for i in by_name["items"]} == {"Juan Dela Crus"} and by_name["total"] == 2
    assert [i["actor_name"] for i in by_email["items"]] == ["Ana Reyes"]
    # % and _ are matched literally, not as wildcards.
    assert wildcard["total"] == 0 and underscore["total"] == 0


def test_search_filters_combine(client, people, records):
    failed = search(client, people["admin"], outcome="failed")
    denied_logins = search(client, people["admin"], action_type="login_failed", outcome="denied")
    instructors = search(client, people["admin"], actor_role="instructor")
    system = search(client, people["admin"], actor_role="system")
    juan_failed = search(client, people["admin"], q="juan", outcome="failed")

    assert [i["actor_name"] for i in failed["items"]] == ["Juan Dela Crus"]
    assert [i["actor_name"] for i in denied_logins["items"]] == ["Ana Reyes"]
    assert [i["action_type"] for i in instructors["items"]] == ["classroom_created"]
    assert [(i["actor_name"], i["actor_role"]) for i in system["items"]] == [("System", "system")]
    assert juan_failed["total"] == 1


def test_search_date_range_is_start_inclusive_end_exclusive(client, people, records):
    now = datetime.now(timezone.utc)
    last_day = search(client, people["admin"], occurred_from=(now - timedelta(days=1)).isoformat())
    older = search(client, people["admin"], occurred_to=(now - timedelta(days=1)).isoformat())
    # A local (UTC+8) bound is converted to UTC before comparing.
    local_tz = timezone(timedelta(hours=8))
    local_from = search(client, people["admin"], occurred_from=(now - timedelta(days=1)).astimezone(local_tz).isoformat())

    assert last_day["total"] == 5
    assert [i["action_type"] for i in older["items"]] == ["login_succeeded"] and older["total"] == 1
    assert local_from["total"] == 5


def test_search_rejects_bad_parameters_and_non_admins(client, people, records):
    admin = auth(people["admin"])
    now = datetime.now(timezone.utc)
    bad = [
        {"action_type": "user_deleted"},
        {"outcome": "maybe"},
        {"actor_role": "guest"},
        {"page": 0},
        {"page_size": 500},
        {"q": "x" * 101},
        {"occurred_from": now.isoformat(), "occurred_to": (now - timedelta(hours=1)).isoformat()},
    ]
    for params in bad:
        assert client.get("/admin/audit-logs/search", headers=admin, params=params).status_code == 422, params

    assert client.get("/admin/audit-logs/search", headers=auth(people["instructor"])).status_code == 403
    assert client.get("/admin/audit-logs/search").status_code == 401


def test_original_audit_list_keeps_its_shape(client, people, records):
    response = client.get("/admin/audit-logs?skip=0&limit=2", headers=auth(people["admin"]))

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list) and len(body) == 2
    assert set(body[0]) == {"log_id", "action_type", "resource_type", "occurred_at", "status", "actor_name", "actor_role"}
