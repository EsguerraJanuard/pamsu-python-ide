"""
Self-service guest accounts (backend audit "Still open" item 4).

Owner decisions: keep "Continue as Guest Student" with a daily cap; guests
stay in the admin-owned sandbox and cannot join real classes; a guest stops
working 7 days after creation. Admin-created guests keep the student rules.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import AuditRecord, Classroom, Enrollment, User
from app.services import guest_service
from app.services.guest_service import (GUEST_CANNOT_JOIN_DETAIL,
                                        GUEST_EXPIRED_DETAIL,
                                        GUEST_LIMIT_REACHED_DETAIL,
                                        SANDBOX_CLASS_CODE,
                                        create_self_service_guest,
                                        deactivate_expired_guests,
                                        get_or_create_sandbox_classroom,
                                        guest_limit_reached,
                                        is_self_service_guest)

DOMAIN = "@pampangastateu.edu.ph"


def make_user(db: Session, *, email: str, role: str, school_id: str, created_at: datetime | None = None) -> User:
    user = User(
        name="Test User",
        email=email,
        role=role,
        school_id=school_id,
        password_hash=get_password_hash("Original#2026"),
        email_verified=True,
        is_active=True,
    )
    if created_at is not None:
        user.created_at = created_at
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_guest(db: Session, number: int, *, age: timedelta = timedelta(0)) -> User:
    return make_user(
        db,
        email=f"guest_{number:012x}{DOMAIN}",
        role="student",
        school_id=f"GST{number:07d}",
        created_at=datetime.now(timezone.utc) - age,
    )


def auth(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.user_id), "pwd_ver": user.password_version})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin(db_session):
    return make_user(db_session, email=f"mis{DOMAIN}", role="admin", school_id="9000000001")


@pytest.fixture
def instructor(db_session):
    return make_user(db_session, email=f"faculty{DOMAIN}", role="instructor", school_id="9000000002")


@pytest.fixture
def real_class(db_session, instructor):
    classroom = Classroom(instructor_id=instructor.user_id, name="Programming 1", subject_code="CCS101",
                          section="BSIT 1A", class_code="CLASSA01", is_active=True)
    db_session.add(classroom)
    db_session.commit()
    return classroom


# ------------------------------------------------------------ identity


def test_self_service_guest_identity():
    def user(email, school_id, role="student"):
        return User(name="x", email=email, school_id=school_id, role=role)

    assert is_self_service_guest(user(f"guest_ab12cd34ef56{DOMAIN}", "GST1234567"))
    assert not is_self_service_guest(user(f"visitor{DOMAIN}", "GST1234567"))  # admin-created guest
    assert not is_self_service_guest(user(f"guest_ab12{DOMAIN}", "2023000001"))
    assert not is_self_service_guest(user("guest_ab12@gmail.com", "GST1234567"))
    assert not is_self_service_guest(user(f"guest_ab12{DOMAIN}", "GST1234567", role="instructor"))


def test_guest_has_no_usable_password(client, db_session, admin):
    response = client.post("/guest")
    assert response.status_code == 200, response.text
    guest = db_session.query(User).filter(User.user_id == response.json()["user"]["user_id"]).one()

    assert is_self_service_guest(guest)
    assert guest.password_hash.startswith("!")
    assert client.post("/login", data={"username": guest.email, "password": guest.password_hash}).status_code == 401


# ------------------------------------------------------------ daily cap


def test_daily_cap_counts_only_self_service_guests_in_the_last_24_hours(db_session, monkeypatch):
    monkeypatch.setattr(guest_service, "GUEST_DAILY_LIMIT", 2)
    make_guest(db_session, 1)
    make_guest(db_session, 2, age=timedelta(hours=25))
    make_user(db_session, email=f"visitor{DOMAIN}", role="student", school_id="GST7654321")
    make_user(db_session, email=f"guest_like_real{DOMAIN}", role="student", school_id="2023000009")

    assert not guest_limit_reached(db_session)

    make_guest(db_session, 3)
    assert guest_limit_reached(db_session)


def test_guest_endpoint_refuses_when_the_daily_cap_is_reached(client, db_session, admin, monkeypatch):
    monkeypatch.setattr(guest_service, "GUEST_DAILY_LIMIT", 1)
    make_guest(db_session, 1)
    before = db_session.query(User).count()

    response = client.post("/guest")

    assert response.status_code == 429
    assert response.json()["detail"] == GUEST_LIMIT_REACHED_DETAIL
    assert db_session.query(User).count() == before


# ------------------------------------------------------------ sandbox only


def test_guest_cannot_join_a_real_class(client, db_session, admin, real_class):
    token = client.post("/guest").json()["access_token"]

    response = client.post("/classrooms/join", json={"class_code": real_class.class_code},
                           headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == GUEST_CANNOT_JOIN_DETAIL
    assert db_session.query(Enrollment).filter(Enrollment.class_id == real_class.class_id).count() == 0


def test_students_and_admin_created_guests_can_still_join(client, db_session, real_class):
    student = make_user(db_session, email=f"2023000001{DOMAIN}", role="student", school_id="2023000001")
    visitor = make_user(db_session, email=f"visitor{DOMAIN}", role="student", school_id="GST7654321")

    for user in (student, visitor):
        response = client.post("/classrooms/join", json={"class_code": real_class.class_code}, headers=auth(user))
        assert response.status_code == 201, response.text


# ------------------------------------------------------------ 7-day lifetime


def test_guest_stops_working_after_seven_days(client, db_session):
    recent = make_guest(db_session, 1, age=timedelta(days=6, hours=23))
    expired = make_guest(db_session, 2, age=timedelta(days=7, minutes=1))

    assert client.get("/notifications/unread-count", headers=auth(recent)).status_code == 200
    response = client.get("/notifications/unread-count", headers=auth(expired))
    assert response.status_code == 403
    assert response.json()["detail"] == GUEST_EXPIRED_DETAIL


def test_old_accounts_that_are_not_self_service_guests_keep_working(client, db_session):
    old_visitor = make_user(db_session, email=f"visitor{DOMAIN}", role="student", school_id="GST7654321",
                            created_at=datetime.now(timezone.utc) - timedelta(days=400))

    assert client.get("/notifications/unread-count", headers=auth(old_visitor)).status_code == 200


def test_new_guest_sign_in_deactivates_expired_guests(client, db_session, admin):
    expired = make_guest(db_session, 1, age=timedelta(days=8))
    recent = make_guest(db_session, 2, age=timedelta(days=1))
    old_visitor = make_user(db_session, email=f"visitor{DOMAIN}", role="student", school_id="GST7654321",
                            created_at=datetime.now(timezone.utc) - timedelta(days=400))

    assert client.post("/guest").status_code == 200

    db_session.expire_all()
    assert (expired.is_active, recent.is_active, old_visitor.is_active) == (False, True, True)
    # Deactivated, never deleted: the account and its history remain.
    assert db_session.query(User).filter(User.user_id == expired.user_id).count() == 1


def test_deactivation_sweep_is_idempotent(db_session):
    make_guest(db_session, 1, age=timedelta(days=8))

    assert deactivate_expired_guests(db_session) == 1
    db_session.commit()
    assert deactivate_expired_guests(db_session) == 0


# ------------------------------------------------------------ sandbox owner


def test_sandbox_is_owned_by_the_first_active_admin_not_an_instructor(db_session, instructor, admin):
    assert instructor.user_id < admin.user_id  # an instructor comes first

    sandbox = get_or_create_sandbox_classroom(db_session)

    assert sandbox.class_code == SANDBOX_CLASS_CODE
    assert sandbox.instructor_id == admin.user_id
    assert get_or_create_sandbox_classroom(db_session).class_id == sandbox.class_id


def test_existing_instructor_owned_sandbox_moves_to_an_admin_with_an_audit_record(db_session, instructor, admin):
    sandbox = Classroom(instructor_id=instructor.user_id, name="Guest Sandbox Classroom", subject_code="DEMO101",
                        section="Sandbox", class_code=SANDBOX_CLASS_CODE, is_active=True)
    db_session.add(sandbox)
    db_session.commit()

    assert get_or_create_sandbox_classroom(db_session).instructor_id == admin.user_id

    (record,) = db_session.query(AuditRecord).filter(AuditRecord.action_type == "classroom_updated").all()
    assert (record.actor_user_id, record.resource_id) == (None, str(sandbox.class_id))
    assert record.audit_data == {"changed_fields": ["instructor_id"], "reason": "guest_sandbox_owned_by_admin",
                                 "previous_owner_role": "instructor"}

    get_or_create_sandbox_classroom(db_session)
    assert db_session.query(AuditRecord).filter(AuditRecord.action_type == "classroom_updated").count() == 1


def test_without_an_admin_no_sandbox_is_created_but_the_guest_still_works(client, db_session, instructor):
    response = client.post("/guest")

    assert response.status_code == 200
    assert db_session.query(Classroom).filter(Classroom.class_code == SANDBOX_CLASS_CODE).count() == 0


# ------------------------------------------------------------ admin user list


def test_admin_user_list_can_include_guests(client, db_session, admin):
    guest = create_self_service_guest(db_session)
    student = make_user(db_session, email=f"2023000001{DOMAIN}", role="student", school_id="2023000001")

    default_ids = {user["user_id"] for user in client.get("/admin/users", headers=auth(admin)).json()}
    all_ids = {user["user_id"] for user in client.get("/admin/users?include_guests=true", headers=auth(admin)).json()}

    assert student.user_id in default_ids and guest.user_id not in default_ids
    assert {student.user_id, guest.user_id} <= all_ids
