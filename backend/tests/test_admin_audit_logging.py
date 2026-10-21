"""
Audit records for administrator actions (routers/admin.py).

Every admin mutation writes one record in the same transaction as the
change (outcome "succeeded"); refused or failed attempts write a separate
"denied"/"failed" record and never a success record. Metadata never holds
credentials, hashes, OTPs or tokens.
"""

import json

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.core.system_settings import read_stored_system_settings
from app.models.domain_models import AcademicEvent, AuditRecord, Classroom, User
from app.schemas.audit_schema import is_sensitive_audit_key, validate_audit_data
from app.services import admin_audit_service, student_provisioning_service
from app.services.admin_audit_service import AdminAuditError, record_admin_action, record_admin_failure

DOMAIN = "@pampangastateu.edu.ph"
NEW_PASSWORD = "Chosen#Pass2026"


def make_user(db: Session, *, email: str, role: str, school_id: str, name: str = "Existing User",
              is_active: bool = True) -> User:
    user = User(
        name=name,
        email=email,
        role=role,
        school_id=school_id,
        password_hash=get_password_hash("Existing#2026"),
        email_verified=True,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.user_id), 'pwd_ver': user.password_version})}"}


def audits(db: Session, action_type: str | None = None) -> list[AuditRecord]:
    db.expire_all()
    query = db.query(AuditRecord)
    if action_type:
        query = query.filter(AuditRecord.action_type == action_type)
    return query.order_by(AuditRecord.occurred_at, AuditRecord.audit_id).all()


def walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item)


def assert_no_secrets(records: list[AuditRecord], *secrets: str) -> None:
    for record in records:
        serialized = json.dumps(record.audit_data)
        assert not [key for key in walk_keys(record.audit_data) if is_sensitive_audit_key(key)]
        assert "$2b$" not in serialized and "eyJ" not in serialized
        for secret in secrets:
            assert secret not in serialized


@pytest.fixture
def admin(db_session):
    return make_user(db_session, email=f"mis{DOMAIN}", role="admin", school_id="9000000001", name="MIS Admin")


@pytest.fixture
def student(db_session):
    return make_user(db_session, email=f"student{DOMAIN}", role="student", school_id="2023000001", name="Stu Dent")


@pytest.fixture
def instructor(db_session):
    return make_user(db_session, email=f"faculty{DOMAIN}", role="instructor", school_id="9000000002", name="Fac Ulty")


@pytest.fixture
def sent_emails(monkeypatch):
    sent = []
    monkeypatch.setattr(
        "app.routers.admin.send_provisioning_email",
        lambda email, first_name, temp_password, role, **details: sent.append((email, role)),
    )
    return sent


def student_body(**overrides):
    body = {"email": f"new{DOMAIN}", "first_name": "New", "last_name": "Student",
            "password": NEW_PASSWORD, "school_id": "2023000099"}
    body.update(overrides)
    return body


# ------------------------------------------------------------ account creation


def test_account_creation_records_user_created_for_each_kind(client, db_session, admin, sent_emails):
    created = {
        "admin_student_form": client.post("/admin/students", headers=auth(admin), json=student_body()),
        "admin_guest_form": client.post("/admin/guests", headers=auth(admin), json={
            "email": f"guest.one{DOMAIN}", "first_name": "Guest", "last_name": "One", "password": NEW_PASSWORD}),
        "admin_instructor_form": client.post("/admin/instructors", headers=auth(admin), json={
            "email": f"prof{DOMAIN}", "first_name": "Pro", "last_name": "Fessor", "password": NEW_PASSWORD}),
    }
    assert {source: response.status_code for source, response in created.items()} == dict.fromkeys(created, 200)

    records = audits(db_session, "user_created")
    by_source = {record.audit_data["source"]: record for record in records}
    assert set(by_source) == set(created)
    for source, response in created.items():
        record = by_source[source]
        assert record.actor_user_id == admin.user_id
        assert (record.resource_type, record.resource_id) == ("user", str(response.json()["user_id"]))
        assert record.outcome == "succeeded"
        assert record.audit_data["role"] == response.json()["role"]
    assert by_source["admin_guest_form"].audit_data["guest"] is True
    # Only the queueing is claimed; delivery happens later and is not audited.
    assert by_source["admin_instructor_form"].audit_data["setup_email"] == "queued_after_commit"
    assert_no_secrets(records, NEW_PASSWORD)


def test_rejected_creation_writes_no_success_record(client, db_session, admin, student):
    response = client.post("/admin/students", headers=auth(admin), json=student_body(email=student.email))

    assert response.status_code == 400
    assert audits(db_session, "user_created") == []


# ------------------------------------------------------------ status, password


def test_status_change_records_previous_and_new_state(client, db_session, admin, student):
    first = client.patch(f"/admin/users/{student.user_id}/status", headers=auth(admin))
    second = client.patch(f"/admin/users/{student.user_id}/status", headers=auth(admin))

    assert [first.json()["is_active"], second.json()["is_active"]] == [False, True]
    records = audits(db_session, "user_status_changed")
    assert [(r.audit_data["previous_is_active"], r.audit_data["is_active"]) for r in records] in (
        [(True, False), (False, True)], [(False, True), (True, False)])
    assert {(r.actor_user_id, r.resource_id, r.outcome, r.audit_data["role"]) for r in records} == {
        (admin.user_id, str(student.user_id), "succeeded", "student")}


def test_refused_and_missing_targets_are_recorded_truthfully(client, db_session, admin):
    own = client.patch(f"/admin/users/{admin.user_id}/status", headers=auth(admin))
    own_delete = client.delete(f"/admin/users/{admin.user_id}", headers=auth(admin))
    missing = client.patch("/admin/users/999999/password", headers=auth(admin), json={"new_password": NEW_PASSWORD})

    assert (own.status_code, own_delete.status_code, missing.status_code) == (400, 400, 404)
    outcomes = {(r.action_type, r.resource_id, r.outcome, r.audit_data["reason"]) for r in audits(db_session)}
    assert outcomes == {
        ("user_status_changed", str(admin.user_id), "denied", "own_account"),
        ("user_deleted", str(admin.user_id), "denied", "own_account"),
        ("user_password_reset", "999999", "failed", "not_found"),
    }
    assert not [r for r in audits(db_session) if r.outcome == "succeeded"]


# ------------------------------------------------------------ account edits


def test_account_edit_records_which_fields_changed_never_their_values(client, db_session, admin, student):
    response = client.patch(f"/admin/users/{student.user_id}", headers=auth(admin),
                            json={"name": "Stu Dent Corrected", "email": f"stu.corrected{DOMAIN}"})

    assert response.status_code == 200, response.text
    [record] = audits(db_session, "user_updated")
    assert (record.actor_user_id, record.resource_type, record.resource_id, record.outcome) == (
        admin.user_id, "user", str(student.user_id), "succeeded")
    assert record.audit_data == {"role": "student", "changed_fields": ["name", "email"], "enrolled_from_pending": 0}
    assert_no_secrets([record], "Stu Dent", "stu.corrected", f"student{DOMAIN}")


def test_account_edit_without_a_change_writes_no_record(client, db_session, admin, student):
    response = client.patch(f"/admin/users/{student.user_id}", headers=auth(admin), json={"name": student.name})

    assert response.status_code == 200, response.text
    assert response.json()["changed_fields"] == []
    assert audits(db_session) == []


def test_refused_account_edits_are_recorded_and_change_nothing(client, db_session, admin, student, instructor):
    guest = make_user(db_session, email=f"guest_abc123{DOMAIN}", role="student", school_id="GST0000001", name="Guest")
    taken = client.patch(f"/admin/users/{student.user_id}", headers=auth(admin),
                         json={"name": "Renamed In Same Request", "email": instructor.email})
    admin_target = client.patch(f"/admin/users/{admin.user_id}", headers=auth(admin), json={"name": "New Admin Name"})
    guest_target = client.patch(f"/admin/users/{guest.user_id}", headers=auth(admin), json={"name": "Not A Guest"})
    missing = client.patch("/admin/users/999999", headers=auth(admin), json={"name": "Nobody"})

    assert (taken.status_code, admin_target.status_code, guest_target.status_code, missing.status_code) == (
        409, 403, 403, 404)
    db_session.expire_all()
    # The rename sent with the refused email is not saved by the failure record's commit.
    assert db_session.get(User, student.user_id).name == "Stu Dent"
    assert {(r.resource_id, r.outcome, r.audit_data["reason"]) for r in audits(db_session, "user_updated")} == {
        (str(student.user_id), "failed", "email_in_use"),
        (str(admin.user_id), "denied", "admin_account"),
        (str(guest.user_id), "denied", "guest_account"),
        ("999999", "failed", "not_found"),
    }
    assert not [r for r in audits(db_session) if r.outcome == "succeeded"]


def test_account_edit_is_rolled_back_when_its_audit_record_fails(client, db_session, admin, student, monkeypatch):
    def broken(*args, **kwargs):
        raise SQLAlchemyError("audit table unavailable")

    monkeypatch.setattr(admin_audit_service, "create_audit_record", broken)

    response = client.patch(f"/admin/users/{student.user_id}", headers=auth(admin), json={"name": "Never Saved"})

    assert response.status_code == 503
    db_session.expire_all()
    assert db_session.get(User, student.user_id).name == "Stu Dent"
    assert audits(db_session) == []


def test_password_reset_records_version_only_and_revokes_sessions(client, db_session, admin, student):
    old_headers = auth(student)
    old_hash = student.password_hash
    assert client.get("/audit-records/", headers=old_headers).status_code == 200

    response = client.patch(f"/admin/users/{student.user_id}/password", headers=auth(admin),
                            json={"new_password": NEW_PASSWORD})

    assert response.status_code == 200
    (record,) = audits(db_session, "user_password_reset")
    assert (record.actor_user_id, record.resource_id, record.outcome) == (admin.user_id, str(student.user_id), "succeeded")
    assert record.audit_data == {"role": "student", "password_version": 2}
    db_session.refresh(student)
    assert_no_secrets([record], NEW_PASSWORD, old_hash, student.password_hash)
    # The recorded version bump really invalidates the earlier session.
    assert client.get("/audit-records/", headers=old_headers).status_code == 401


# ------------------------------------------------------------------ deletion


def test_deletion_record_stays_useful_after_the_account_is_gone(client, db_session, admin):
    target = make_user(db_session, email=f"leaving{DOMAIN}", role="student", school_id="2023000555", name="Lea Ving")
    target_id = target.user_id

    response = client.delete(f"/admin/users/{target_id}", headers=auth(admin))

    assert response.status_code == 200
    db_session.expire_all()
    assert db_session.get(User, target_id) is None
    (record,) = audits(db_session, "user_deleted")
    assert (record.resource_type, record.resource_id, record.outcome) == ("user", str(target_id), "succeeded")
    assert record.audit_data == {"role": "student", "was_active": True}
    # No email or school ID of the deleted account is retained.
    assert "leaving" not in json.dumps(record.audit_data) and "2023000555" not in json.dumps(record.audit_data)

    logs = client.get("/admin/audit-logs", headers=auth(admin)).json()
    entry = next(log for log in logs if log["action_type"] == "user_deleted")
    assert (entry["target_user_id"], entry["target_exists"], entry["target_name"]) == (target_id, False, None)
    assert entry["resource_id"] == str(target_id)


def test_account_created_after_a_deletion_is_audited_even_if_its_id_is_reused(client, db_session, admin, sent_emails):
    # SQLite may hand the deleted account's id to the next account; each
    # creation is its own event, so the audit keys must never collide.
    first = client.post("/admin/students", headers=auth(admin), json=student_body())
    assert client.delete(f"/admin/users/{first.json()['user_id']}", headers=auth(admin)).status_code == 200

    second = client.post("/admin/students", headers=auth(admin),
                         json=student_body(email=f"second{DOMAIN}", school_id="2023000098"))

    assert second.status_code == 200
    assert len(audits(db_session, "user_created")) == 2


def test_refused_deletion_records_failure_and_no_success(client, db_session, admin, instructor):
    db_session.add(Classroom(instructor_id=instructor.user_id, name="Programming 1", subject_code="CCS101",
                             section="BSIT 1A", class_code="ABC123"))
    db_session.commit()

    response = client.delete(f"/admin/users/{instructor.user_id}", headers=auth(admin))

    assert response.status_code == 409
    db_session.expire_all()
    assert db_session.get(User, instructor.user_id) is not None
    (record,) = audits(db_session, "user_deleted")
    assert (record.outcome, record.audit_data) == ("failed", {"role": "instructor", "reason": "has_dependent_records"})


@pytest.mark.parametrize("history", ["audit_record", "academic_event"])
def test_deleting_a_user_with_history_is_refused_and_history_is_untouched(client, db_session, admin, student, history):
    # The ORM used to set the nullable actor_user_id to NULL and delete the
    # account anyway, rewriting immutable history.
    if history == "audit_record":
        db_session.add(AuditRecord(audit_key="history:login", actor_user_id=student.user_id, action_type="login_succeeded",
                                   resource_type="user", resource_id=str(student.user_id), audit_data={}))
    else:
        db_session.add(AcademicEvent(event_key="history:event", event_type="submission_created", actor_user_id=student.user_id,
                                     resource_type="submission", resource_id="1", event_data={}))
    db_session.commit()

    response = client.delete(f"/admin/users/{student.user_id}", headers=auth(admin))

    assert response.status_code == 409
    db_session.expire_all()
    assert db_session.get(User, student.user_id) is not None
    if history == "audit_record":
        kept = db_session.query(AuditRecord).filter(AuditRecord.audit_key == "history:login").one()
    else:
        kept = db_session.query(AcademicEvent).filter(AcademicEvent.event_key == "history:event").one()
    assert kept.actor_user_id == student.user_id
    assert [(r.outcome, r.audit_data["reason"]) for r in audits(db_session, "user_deleted")] == [
        ("failed", "has_dependent_records")]


# ------------------------------------------------------------------ settings


SETTINGS = {"maintenance_mode": True, "default_ast_strictness": "strict", "registration_enabled": False}


def test_settings_change_is_recorded_with_changed_keys_only(client, db_session, admin):
    response = client.patch("/admin/settings", headers=auth(admin), json=SETTINGS)
    repeat = client.patch("/admin/settings", headers=auth(admin), json=SETTINGS)

    assert (response.status_code, repeat.status_code) == (200, 200)
    (record,) = audits(db_session, "system_settings_updated")
    assert (record.resource_type, record.resource_id, record.outcome) == ("system_setting", "global", "succeeded")
    assert record.audit_data == {"changes": {
        "maintenance_mode": {"from": False, "to": True},
        "default_ast_strictness": {"from": "moderate", "to": "strict"},
    }}


def test_settings_failure_partway_changes_nothing(client, db_session, admin, monkeypatch):
    from app.core import system_settings
    calls = {"count": 0}

    def fail_on_second(db, key, value, *, commit=True):
        calls["count"] += 1
        if calls["count"] == 2:
            raise SQLAlchemyError("simulated write failure")
        return system_settings.set_system_setting(db, key, value, commit=commit)

    monkeypatch.setattr("app.routers.admin.set_system_setting", fail_on_second)

    response = client.patch("/admin/settings", headers=auth(admin), json=SETTINGS)

    assert response.status_code == 503
    db_session.expire_all()
    assert read_stored_system_settings(db_session) == {
        "maintenance_mode": False, "default_ast_strictness": "moderate", "registration_enabled": False}
    (record,) = audits(db_session, "system_settings_updated")
    assert (record.outcome, record.audit_data["reason"]) == ("failed", "database_error")


def test_settings_are_not_saved_when_their_audit_record_fails(client, db_session, admin, monkeypatch):
    def broken(*args, **kwargs):
        raise SQLAlchemyError("audit table unavailable")

    monkeypatch.setattr(admin_audit_service, "create_audit_record", broken)

    response = client.patch("/admin/settings", headers=auth(admin), json=SETTINGS)

    assert response.status_code == 503
    assert "not saved" in response.json()["detail"]
    db_session.expire_all()
    assert read_stored_system_settings(db_session)["maintenance_mode"] is False


# ------------------------------------------------------------ audit failures


def test_audit_failure_rolls_back_the_action_and_reports_it(client, db_session, admin, student, monkeypatch):
    def broken(*args, **kwargs):
        raise SQLAlchemyError("audit table unavailable")

    monkeypatch.setattr(admin_audit_service, "create_audit_record", broken)

    status = client.patch(f"/admin/users/{student.user_id}/status", headers=auth(admin))
    created = client.post("/admin/students", headers=auth(admin), json=student_body())
    deleted = client.delete(f"/admin/users/{student.user_id}", headers=auth(admin))

    assert (status.status_code, created.status_code, deleted.status_code) == (503, 503, 503)
    db_session.expire_all()
    assert db_session.get(User, student.user_id).is_active is True
    assert db_session.query(User).filter(User.email == f"new{DOMAIN}").first() is None
    assert audits(db_session) == []


# ------------------------------------------------------------------ masterlist


def upload(client, user, content: bytes, filename: str = "masterlist.csv"):
    return client.post("/admin/students/bulk-register/file", headers=auth(user),
                       files={"file": (filename, content, "text/csv")})


def test_masterlist_records_one_summary_and_only_created_accounts(client, db_session, admin, student, sent_emails):
    content = "\n".join([
        "email,school_id,name",
        f"one{DOMAIN},2023000011,Student One",
        f"two{DOMAIN},2023000012,Student Two",
        f"{student.email},{student.school_id},Stu Dent",
        f"three{DOMAIN},,Missing Number",
    ]).encode()

    response = upload(client, admin, content)

    body = response.json()
    assert (response.status_code, body["created"], body["skipped"], body["failed"]) == (200, 2, 1, 1)
    (summary,) = audits(db_session, "masterlist_imported")
    assert (summary.actor_user_id, summary.resource_type, summary.outcome) == (admin.user_id, "masterlist_import", "succeeded")
    assert summary.audit_data == {"file_type": "csv", "rows": 4, "created": 2, "skipped": 1, "failed": 1,
                                  "enrolled_from_pending": 0, "pending_left": 0}
    created = audits(db_session, "user_created")
    created_ids = {str(user.user_id) for user in db_session.query(User).filter(User.email.in_([f"one{DOMAIN}", f"two{DOMAIN}"]))}
    assert {record.resource_id for record in created} == created_ids
    assert {record.audit_data["import_id"] for record in created} == {summary.resource_id}
    assert {record.audit_data["row"] for record in created} == {2, 3}
    serialized = json.dumps([summary.audit_data, *[record.audit_data for record in created]])
    assert DOMAIN not in serialized and "Student One" not in serialized and "2023000011" not in serialized


def test_masterlist_conflict_records_failed_summary_and_no_account(client, db_session, admin, sent_emails, monkeypatch):
    def conflict(**kwargs):
        raise IntegrityError("INSERT", {}, Exception("duplicate key"))

    monkeypatch.setattr(student_provisioning_service, "apply_pending_enrollments", conflict)

    response = upload(client, admin, f"email,school_id,name\none{DOMAIN},2023000011,Student One\n".encode())

    assert response.status_code == 409
    assert audits(db_session, "user_created") == []
    (summary,) = audits(db_session, "masterlist_imported")
    assert (summary.outcome, summary.audit_data) == ("failed", {"file_type": "csv", "reason": "database_conflict"})


def test_masterlist_invalid_file_records_failed_summary(client, db_session, admin, sent_emails):
    response = upload(client, admin, b"not,a,masterlist\n1,2,3\n")

    assert response.status_code == 400
    (summary,) = audits(db_session, "masterlist_imported")
    assert (summary.outcome, summary.audit_data["reason"]) == ("failed", "invalid_file")


def test_masterlist_audit_failure_creates_no_account(client, db_session, admin, sent_emails, monkeypatch):
    def broken(*args, **kwargs):
        raise AdminAuditError("simulated")

    monkeypatch.setattr(student_provisioning_service, "record_admin_action", broken)

    response = upload(client, admin, f"email,school_id,name\none{DOMAIN},2023000011,Student One\n".encode())

    assert response.status_code == 503
    assert db_session.query(User).filter(User.email == f"one{DOMAIN}").first() is None
    assert sent_emails == []


# --------------------------------------------------------------- authorization


@pytest.mark.parametrize("role", ["student", "instructor"])
def test_non_admins_cannot_mutate_or_read_admin_audit_logs(client, db_session, role, student, instructor):
    caller = student if role == "student" else instructor
    target = instructor if role == "student" else student
    requests = [
        ("post", "/admin/students", {"json": student_body()}),
        ("post", "/admin/guests", {"json": {"email": f"g{DOMAIN}", "first_name": "G", "last_name": "H", "password": NEW_PASSWORD}}),
        ("post", "/admin/instructors", {"json": {"email": f"i{DOMAIN}", "first_name": "I", "last_name": "J", "password": NEW_PASSWORD}}),
        ("patch", f"/admin/users/{target.user_id}/status", {}),
        ("patch", f"/admin/users/{target.user_id}/password", {"json": {"new_password": NEW_PASSWORD}}),
        ("delete", f"/admin/users/{target.user_id}", {}),
        ("patch", "/admin/settings", {"json": SETTINGS}),
        ("post", "/admin/students/bulk-register/file", {"files": {"file": ("m.csv", b"email,school_id,name\n", "text/csv")}}),
        ("get", "/admin/audit-logs", {}),
    ]
    for method, url, kwargs in requests:
        assert getattr(client, method)(url, headers=auth(caller), **kwargs).status_code == 403, url
        assert getattr(client, method)(url, **kwargs).status_code == 401, url
    assert audits(db_session) == []


# ------------------------------------------------------------ audit-log endpoint


def test_audit_log_endpoint_keeps_old_fields_and_adds_target(client, db_session, admin, student):
    client.patch(f"/admin/users/{student.user_id}/status", headers=auth(admin))

    logs = client.get("/admin/audit-logs", headers=auth(admin)).json()

    (entry,) = [log for log in logs if log["action_type"] == "user_status_changed"]
    assert {"log_id", "action_type", "resource_type", "occurred_at", "status", "actor_name", "actor_role"} <= entry.keys()
    assert (entry["actor_name"], entry["actor_role"], entry["status"]) == ("MIS Admin", "admin", "succeeded")
    assert (entry["target_user_id"], entry["target_exists"], entry["target_name"], entry["target_role"]) == (
        student.user_id, True, "Stu Dent", "student")
    assert entry["details"] == {"role": "student", "previous_is_active": True, "is_active": False}


def test_audit_log_endpoint_handles_records_from_other_features(client, db_session, admin, student):
    db_session.add(AuditRecord(audit_key="legacy:login", actor_user_id=student.user_id, action_type="login_succeeded",
                               resource_type="user", resource_id=str(student.user_id), audit_data={}))
    db_session.add(AuditRecord(audit_key="legacy:system", actor_user_id=None, action_type="grade_released",
                               resource_type="grade", resource_id="g-1", audit_data={}))
    db_session.commit()

    logs = client.get("/admin/audit-logs", headers=auth(admin)).json()

    by_action = {log["action_type"]: log for log in logs}
    assert by_action["login_succeeded"]["target_user_id"] == student.user_id
    assert (by_action["grade_released"]["actor_name"], by_action["grade_released"]["target_user_id"]) == ("System", None)
    assert by_action["grade_released"]["target_exists"] is None


TYPED_PASSWORD = "my-secret-pass-123"


def test_audit_log_endpoint_masks_stored_unrecognized_login_identifiers(client, db_session, admin, student):
    # Rows written before the login handler stopped storing unrecognized
    # identifiers: audit rows are immutable, so the endpoint must mask them.
    unknown_email = f"no.such.student{DOMAIN}"
    rows = {
        "legacy:password": (None, TYPED_PASSWORD, {"email": TYPED_PASSWORD}),
        "legacy:malformed": (None, f"a b{DOMAIN}", {"email": f"a b{DOMAIN}"}),
        "legacy:unknown-email": (None, unknown_email, {"email": unknown_email}),
        "legacy:wrong-password": (student.user_id, str(student.user_id), {"email": student.email}),
    }
    for key, (actor, resource_id, data) in rows.items():
        db_session.add(AuditRecord(audit_key=key, actor_user_id=actor, action_type="login_failed",
                                   resource_type="user", resource_id=resource_id, outcome="failed", audit_data=data))
    db_session.commit()

    response = client.get("/admin/audit-logs", headers=auth(admin))

    assert response.status_code == 200
    assert TYPED_PASSWORD not in response.text
    assert f"a b{DOMAIN}" not in response.text
    entries = [(log["resource_id"], log["details"], log["target_user_id"])
               for log in response.json() if log["action_type"] == "login_failed"]
    assert sorted(entries, key=str) == sorted([
        ("unrecognized", {"identifier": "unrecognized"}, None),
        ("unrecognized", {"identifier": "unrecognized"}, None),
        (unknown_email, {"email": unknown_email}, None),
        (str(student.user_id), {"email": student.email}, student.user_id),
    ], key=str)

    # Masking happens on display only; the immutable rows are unchanged.
    stored = {record.audit_key: record for record in audits(db_session, "login_failed")}
    assert stored["legacy:password"].resource_id == TYPED_PASSWORD
    assert stored["legacy:password"].audit_data == {"email": TYPED_PASSWORD}


def test_password_typed_as_login_email_never_reaches_admin_audit_log(client, db_session, admin):
    assert client.post("/login", data={"username": TYPED_PASSWORD, "password": "x"}).status_code == 401

    response = client.get("/admin/audit-logs", headers=auth(admin))

    (entry,) = [log for log in response.json() if log["action_type"] == "login_failed"]
    assert (entry["resource_id"], entry["details"]) == ("unrecognized", {"identifier": "unrecognized"})
    assert TYPED_PASSWORD not in response.text


def test_masking_leaves_other_action_types_unchanged(client, db_session, admin):
    db_session.add(AuditRecord(audit_key="legacy:other", actor_user_id=None, action_type="grade_released",
                               resource_type="grade", resource_id="not-an-email", audit_data={"note": "kept"}))
    db_session.commit()

    logs = client.get("/admin/audit-logs", headers=auth(admin)).json()

    (entry,) = [log for log in logs if log["action_type"] == "grade_released"]
    assert (entry["resource_id"], entry["details"]) == ("not-an-email", {"note": "kept"})


# ------------------------------------------------------------ metadata privacy


@pytest.mark.parametrize("key", [
    "password", "new_password", "newPassword", "temp-password", "password_hash", "PasswordHash", "pass_word",
    "token", "access_token", "refreshToken", "otp", "otp_code", "reset_code", "resetCode", "verification code",
    "api_key", "apiKey", "client_secret", "jwt", "credentials", "session.key",
])
def test_credential_like_keys_are_rejected(key):
    assert is_sensitive_audit_key(key)
    with pytest.raises(ValueError):
        validate_audit_data({"outer": {key: "x"}})


@pytest.mark.parametrize("key", [
    "password_version", "role", "is_active", "previous_is_active", "class_code", "subject_code", "import_id",
    "reason", "changes", "maintenance_mode", "rows", "keyboard_layout",
])
def test_useful_metadata_keys_are_kept(key):
    assert not is_sensitive_audit_key(key)
    assert validate_audit_data({key: 1}) == {key: 1}


@pytest.mark.parametrize("value", [
    "$2b$08$abcdefghijklmnopqrstuuJk1x8i7rYc0bTq7n2vAJcqbWv0sR7a2",
    "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2lnbmF0dXJl",
])
def test_credential_like_values_are_rejected(value):
    with pytest.raises(ValueError):
        validate_audit_data({"note": value})


# --------------------------------------------------------- logs never leak values


SECRET = "SuperSecret#Value1"
FAKE_HASH = "$2b$08$abcdefghijklmnopqrstuuJk1x8i7rYc0bTq7n2vAJcqbWv0sR7a2"


def test_rejected_metadata_never_reaches_the_error_or_its_chain(db_session, admin):
    with pytest.raises(AdminAuditError) as caught:
        record_admin_action(db_session, actor_user_id=admin.user_id, action_type="user_password_reset",
                            resource_type="user", resource_id=admin.user_id, audit_data={"new_password": SECRET})

    assert SECRET not in str(caught.value)
    assert caught.value.__cause__ is None and caught.value.__suppress_context__
    db_session.rollback()


def test_audit_failures_log_no_secret_values(client, db_session, admin, student, monkeypatch, caplog):
    def broken(*args, **kwargs):
        # SQLAlchemy errors carry statement parameters, e.g. a flushed hash.
        raise SQLAlchemyError(f"UPDATE users SET password_hash='{FAKE_HASH}' new={NEW_PASSWORD} {SECRET}")

    monkeypatch.setattr(admin_audit_service, "create_audit_record", broken)
    caplog.set_level("DEBUG")

    reset = client.patch(f"/admin/users/{student.user_id}/password", headers=auth(admin),
                         json={"new_password": NEW_PASSWORD})
    settings = client.patch("/admin/settings", headers=auth(admin), json=SETTINGS)
    record_admin_failure(db_session, actor_user_id=admin.user_id, action_type="user_deleted",
                         resource_type="user", resource_id=1, reason="not_found")

    assert (reset.status_code, settings.status_code) == (503, 503)
    logged = caplog.text + "".join(str(record.exc_info) for record in caplog.records if record.exc_info)
    assert "rolled back" in logged and "Could not record" in logged
    for value in (FAKE_HASH, NEW_PASSWORD, SECRET):
        assert value not in logged
    db_session.expire_all()
    assert db_session.get(User, student.user_id).password_version == 1


def test_non_ascii_digit_resource_ids_are_not_treated_as_users(client, db_session, admin):
    db_session.add(AuditRecord(audit_key="odd:id", actor_user_id=admin.user_id, action_type="login_succeeded",
                               resource_type="user", resource_id="²", audit_data={}))
    db_session.commit()

    logs = client.get("/admin/audit-logs", headers=auth(admin))

    assert logs.status_code == 200
    (entry,) = [log for log in logs.json() if log["resource_id"] == "²"]
    assert entry["target_user_id"] is None
