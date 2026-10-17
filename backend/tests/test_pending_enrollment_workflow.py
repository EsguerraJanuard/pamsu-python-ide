"""
Bulk enrollment, pending enrollment, and MIS account provisioning.

Students queued by an instructor before they have an account must be
enrolled when MIS creates a student account with the same university
email, and never through any weaker match.
"""

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import (AuditRecord, Classroom, Enrollment,
                                      PendingEnrollment, Submission, Task,
                                      User)
from app.services import classroom_service
from app.services.audit_service import AuditServiceError

DOMAIN = "@pampangastateu.edu.ph"
PASSWORD_HASH = get_password_hash("test12345")


def make_user(
    db: Session,
    *,
    email: str,
    role: str,
    school_id: str,
    name: str = "Test User",
    is_active: bool = True,
) -> User:
    user = User(
        name=name,
        email=email,
        role=role,
        school_id=school_id,
        password_hash=PASSWORD_HASH,
        email_verified=True,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_classroom(db: Session, *, instructor: User, code: str, is_active: bool = True) -> Classroom:
    classroom = Classroom(
        instructor_id=instructor.user_id,
        name=f"Programming {code}",
        subject_code="CCS101",
        section="BSIT 1A",
        class_code=code,
        is_active=is_active,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


def auth(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.user_id)})
    return {"Authorization": f"Bearer {token}"}


def bulk_enroll(client, instructor: User, class_id: int, emails: list[str]):
    return client.post(
        f"/classrooms/{class_id}/bulk-enroll",
        headers=auth(instructor),
        json={"emails": emails},
    )


def mis_create_student(client, admin: User, *, email: str, school_id: str, first="Juan", last="Dela Cruz"):
    return client.post(
        "/admin/students",
        headers=auth(admin),
        json={
            "email": email,
            "first_name": first,
            "last_name": last,
            "school_id": school_id,
            "password": "Temporary#2026",
        },
    )


def enrollments_for(db: Session, email: str) -> list[Enrollment]:
    db.expire_all()
    return (
        db.query(Enrollment)
        .join(User, User.user_id == Enrollment.student_id)
        .filter(User.email == email)
        .order_by(Enrollment.class_id)
        .all()
    )


def pending_for(db: Session, email: str) -> list[PendingEnrollment]:
    db.expire_all()
    return db.query(PendingEnrollment).filter(PendingEnrollment.email == email).all()


@pytest.fixture
def actors(db_session):
    admin = make_user(db_session, email=f"mis{DOMAIN}", role="admin", school_id="9000000001", name="MIS Admin")
    instructor = make_user(db_session, email=f"faculty1{DOMAIN}", role="instructor", school_id="9000000002")
    other_instructor = make_user(db_session, email=f"faculty2{DOMAIN}", role="instructor", school_id="9000000003")
    classroom = make_classroom(db_session, instructor=instructor, code="CLASSA01")
    return {
        "admin": admin,
        "instructor": instructor,
        "other_instructor": other_instructor,
        "classroom": classroom,
    }


def test_bulk_enroll_enrolls_existing_students_and_queues_unknown_addresses(client, db_session, actors):
    instructor, classroom = actors["instructor"], actors["classroom"]
    # Stored with mixed case: login matches emails case-insensitively, so must enrollment.
    make_user(db_session, email=f"Maria.Santos{DOMAIN}", role="student", school_id="2026000001")

    response = bulk_enroll(
        client,
        instructor,
        classroom.class_id,
        [f"maria.santos{DOMAIN}", f"new.student{DOMAIN}", "someone@gmail.com"],
    )

    assert response.status_code == 200
    assert response.json() == {
        "enrolled": 1,
        "queued": 1,
        "invalid": 1,
        "already_enrolled": 0,
        "ineligible": 0,
    }
    assert [e.class_id for e in enrollments_for(db_session, f"Maria.Santos{DOMAIN}")] == [classroom.class_id]
    assert pending_for(db_session, f"maria.santos{DOMAIN}") == []
    assert [p.class_id for p in pending_for(db_session, f"new.student{DOMAIN}")] == [classroom.class_id]

    # Re-submitting is reported but stores nothing new.
    again = bulk_enroll(client, instructor, classroom.class_id, [f"maria.santos{DOMAIN}", f"new.student{DOMAIN}"])
    assert again.status_code == 200
    assert again.json()["enrolled"] == 0
    assert again.json()["already_enrolled"] == 1
    assert again.json()["queued"] == 1
    assert len(enrollments_for(db_session, f"Maria.Santos{DOMAIN}")) == 1
    assert len(pending_for(db_session, f"new.student{DOMAIN}")) == 1


def test_bulk_enroll_reports_staff_addresses_instead_of_queueing_them(client, db_session, actors):
    response = bulk_enroll(
        client,
        actors["instructor"],
        actors["classroom"].class_id,
        [actors["other_instructor"].email, actors["admin"].email],
    )

    assert response.status_code == 200
    assert response.json()["ineligible"] == 2
    assert response.json()["queued"] == 0
    db_session.expire_all()
    assert db_session.query(PendingEnrollment).count() == 0
    assert db_session.query(Enrollment).count() == 0


def test_mis_account_creation_completes_pending_enrollment(client, db_session, actors):
    email = f"juan.delacruz{DOMAIN}"
    classroom = actors["classroom"]
    assert bulk_enroll(client, actors["instructor"], classroom.class_id, [email]).json()["queued"] == 1

    response = mis_create_student(client, actors["admin"], email=email, school_id="2026000010")

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == email
    assert body["name"] == "Juan Dela Cruz"
    assert body["pending_enrollments"] == {
        "enrolled_class_ids": [classroom.class_id],
        "already_enrolled_class_ids": [],
        "skipped": [],
    }

    enrollments = enrollments_for(db_session, email)
    assert [(e.class_id, e.status) for e in enrollments] == [(classroom.class_id, "active")]
    assert pending_for(db_session, email) == []

    audit = (
        db_session.query(AuditRecord)
        .filter(
            AuditRecord.action_type == "student_enrolled",
            AuditRecord.resource_id == str(enrollments[0].enrollment_id),
        )
        .one()
    )
    assert audit.actor_user_id == actors["admin"].user_id
    assert audit.audit_data["source"] == "pending_enrollment"

    # The student sees the class through the normal student endpoint.
    student = db_session.query(User).filter(User.email == email).one()
    classes = client.get("/classrooms/mine", headers=auth(student))
    assert classes.status_code == 200
    assert [c["classroom"]["class_id"] for c in classes.json()] == [classroom.class_id]


def test_multiple_pending_enrollments_for_one_student(client, db_session, actors):
    email = f"multi.class{DOMAIN}"
    second = make_classroom(db_session, instructor=actors["other_instructor"], code="CLASSB02")
    bulk_enroll(client, actors["instructor"], actors["classroom"].class_id, [email])
    bulk_enroll(client, actors["other_instructor"], second.class_id, [email])

    response = mis_create_student(client, actors["admin"], email=email, school_id="2026000020")

    assert response.status_code == 200
    assert sorted(response.json()["pending_enrollments"]["enrolled_class_ids"]) == sorted(
        [actors["classroom"].class_id, second.class_id]
    )
    assert sorted(e.class_id for e in enrollments_for(db_session, email)) == sorted(
        [actors["classroom"].class_id, second.class_id]
    )
    assert pending_for(db_session, email) == []


def test_non_matching_email_is_never_enrolled_even_with_the_same_name(client, db_session, actors):
    queued = f"juan.cruz{DOMAIN}"
    bulk_enroll(client, actors["instructor"], actors["classroom"].class_id, [queued])

    # Same person's name, different university email: not a match.
    response = mis_create_student(
        client, actors["admin"], email=f"jcruz{DOMAIN}", school_id="2026000030", first="Juan", last="Cruz"
    )

    assert response.status_code == 200
    assert response.json()["pending_enrollments"]["enrolled_class_ids"] == []
    assert enrollments_for(db_session, f"jcruz{DOMAIN}") == []
    assert len(pending_for(db_session, queued)) == 1


def test_mis_bulk_registration_completes_pending_enrollments(client, db_session, actors):
    email = f"from.masterlist{DOMAIN}"
    bulk_enroll(client, actors["instructor"], actors["classroom"].class_id, [email])

    response = client.post(
        "/admin/students/bulk-register/file",
        headers=auth(actors["admin"]),
        files={"file": ("masterlist.csv", f"email\n{email}\n".encode(), "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["registered"] == 1
    assert response.json()["enrolled_from_pending"] == 1
    assert response.json()["pending_left"] == 0
    assert [e.class_id for e in enrollments_for(db_session, email)] == [actors["classroom"].class_id]
    assert pending_for(db_session, email) == []


def test_retrying_pending_enrollment_never_duplicates(client, db_session, actors):
    email = f"retry.student{DOMAIN}"
    bulk_enroll(client, actors["instructor"], actors["classroom"].class_id, [email])
    created = mis_create_student(client, actors["admin"], email=email, school_id="2026000040")
    user_id = created.json()["user_id"]

    for _ in range(2):
        retry = client.post(f"/admin/students/{user_id}/pending-enrollments/apply", headers=auth(actors["admin"]))
        assert retry.status_code == 200
        assert retry.json() == {"enrolled_class_ids": [], "already_enrolled_class_ids": [], "skipped": []}

    assert len(enrollments_for(db_session, email)) == 1

    # A stale pending row next to an existing enrollment is consumed, not re-applied.
    db_session.add(PendingEnrollment(class_id=actors["classroom"].class_id, email=email))
    db_session.commit()
    retry = client.post(f"/admin/students/{user_id}/pending-enrollments/apply", headers=auth(actors["admin"]))
    assert retry.json()["already_enrolled_class_ids"] == [actors["classroom"].class_id]
    assert len(enrollments_for(db_session, email)) == 1
    assert pending_for(db_session, email) == []


def test_apply_pending_enrollments_twice_in_service_is_idempotent(db_session, actors):
    email = f"service.retry{DOMAIN}"
    db_session.add(PendingEnrollment(class_id=actors["classroom"].class_id, email=email))
    db_session.commit()
    student = make_user(db_session, email=email, role="student", school_id="2026000045")

    first = classroom_service.apply_pending_enrollments(
        db=db_session, student=student, actor_user_id=actors["admin"].user_id
    )
    second = classroom_service.apply_pending_enrollments(
        db=db_session, student=student, actor_user_id=actors["admin"].user_id
    )
    db_session.commit()

    assert first.enrolled_class_ids == [actors["classroom"].class_id]
    assert second.enrolled_class_ids == [] and second.skipped == []
    assert len(enrollments_for(db_session, email)) == 1


def test_inactive_classroom_keeps_enrollment_pending_until_retried(client, db_session, actors):
    email = f"archived.class{DOMAIN}"
    classroom = actors["classroom"]
    bulk_enroll(client, actors["instructor"], classroom.class_id, [email])
    classroom.is_active = False
    db_session.commit()

    created = mis_create_student(client, actors["admin"], email=email, school_id="2026000050")

    # The account is still created; only the enrollment waits.
    assert created.status_code == 200
    assert created.json()["pending_enrollments"]["skipped"] == [
        {"class_id": classroom.class_id, "reason": "classroom_inactive"}
    ]
    assert enrollments_for(db_session, email) == []
    assert len(pending_for(db_session, email)) == 1

    db_session.expire_all()
    db_session.get(Classroom, classroom.class_id).is_active = True
    db_session.commit()
    retry = client.post(
        f"/admin/students/{created.json()['user_id']}/pending-enrollments/apply",
        headers=auth(actors["admin"]),
    )
    assert retry.json()["enrolled_class_ids"] == [classroom.class_id]
    assert len(enrollments_for(db_session, email)) == 1


def test_bulk_enroll_rejects_inactive_classroom(client, db_session, actors):
    archived = make_classroom(db_session, instructor=actors["instructor"], code="CLASSZ09", is_active=False)

    response = bulk_enroll(client, actors["instructor"], archived.class_id, [f"anyone{DOMAIN}"])

    assert response.status_code == 409
    assert db_session.query(PendingEnrollment).count() == 0


def test_bulk_enroll_authorization_failures(client, db_session, actors):
    student = make_user(db_session, email=f"student.x{DOMAIN}", role="student", school_id="2026000060")
    class_id = actors["classroom"].class_id
    emails = [f"target{DOMAIN}"]

    assert bulk_enroll(client, actors["other_instructor"], class_id, emails).status_code == 403
    assert bulk_enroll(client, actors["instructor"], 999999, emails).status_code == 404
    assert bulk_enroll(client, student, class_id, emails).status_code == 403
    assert client.post(f"/classrooms/{class_id}/bulk-enroll", json={"emails": emails}).status_code == 401

    file_response = client.post(
        f"/classrooms/{class_id}/bulk-enroll/file",
        headers=auth(actors["other_instructor"]),
        files={"file": ("list.csv", f"target{DOMAIN}".encode(), "text/csv")},
    )
    assert file_response.status_code == 403

    db_session.expire_all()
    assert db_session.query(PendingEnrollment).count() == 0


def test_mis_endpoints_require_admin(client, db_session, actors):
    student = make_user(db_session, email=f"student.y{DOMAIN}", role="student", school_id="2026000070")

    for caller in (actors["instructor"], student):
        create = mis_create_student(client, caller, email=f"blocked{DOMAIN}", school_id="2026000071")
        assert create.status_code == 403
        apply = client.post(f"/admin/students/{student.user_id}/pending-enrollments/apply", headers=auth(caller))
        assert apply.status_code == 403

    db_session.expire_all()
    assert db_session.query(User).filter(User.email == f"blocked{DOMAIN}").count() == 0


def test_apply_endpoint_rejects_ineligible_accounts(client, db_session, actors):
    suspended = make_user(
        db_session, email=f"suspended{DOMAIN}", role="student", school_id="2026000080", is_active=False
    )
    db_session.add(PendingEnrollment(class_id=actors["classroom"].class_id, email=suspended.email))
    db_session.commit()

    for target in (actors["instructor"], suspended):
        response = client.post(
            f"/admin/students/{target.user_id}/pending-enrollments/apply",
            headers=auth(actors["admin"]),
        )
        assert response.status_code == 409

    assert client.post("/admin/students/999999/pending-enrollments/apply", headers=auth(actors["admin"])).status_code == 404
    assert enrollments_for(db_session, suspended.email) == []
    assert len(pending_for(db_session, suspended.email)) == 1


def test_one_failed_pending_enrollment_does_not_break_account_or_others(client, db_session, actors, monkeypatch):
    email = f"partial.failure{DOMAIN}"
    failing = make_classroom(db_session, instructor=actors["other_instructor"], code="CLASSF07")
    bulk_enroll(client, actors["instructor"], actors["classroom"].class_id, [email])
    bulk_enroll(client, actors["other_instructor"], failing.class_id, [email])

    real_record_audit = classroom_service._record_audit

    def record_audit_failing_for_one_class(**kwargs):
        if kwargs["audit_data"].get("class_id") == failing.class_id:
            raise AuditServiceError("simulated audit outage")
        return real_record_audit(**kwargs)

    monkeypatch.setattr(classroom_service, "_record_audit", record_audit_failing_for_one_class)

    response = mis_create_student(client, actors["admin"], email=email, school_id="2026000090")

    assert response.status_code == 200
    result = response.json()["pending_enrollments"]
    assert result["enrolled_class_ids"] == [actors["classroom"].class_id]
    assert result["skipped"] == [{"class_id": failing.class_id, "reason": "audit_failed"}]

    # Account exists; the good class is enrolled; the failed class left no
    # half-written enrollment and is still pending.
    db_session.expire_all()
    student = db_session.query(User).filter(User.email == email).one()
    assert [e.class_id for e in enrollments_for(db_session, email)] == [actors["classroom"].class_id]
    assert [p.class_id for p in pending_for(db_session, email)] == [failing.class_id]

    monkeypatch.setattr(classroom_service, "_record_audit", real_record_audit)
    retry = client.post(f"/admin/students/{student.user_id}/pending-enrollments/apply", headers=auth(actors["admin"]))
    assert retry.json()["enrolled_class_ids"] == [failing.class_id]
    assert sorted(e.class_id for e in enrollments_for(db_session, email)) == sorted(
        [actors["classroom"].class_id, failing.class_id]
    )


def test_bulk_enroll_failure_rolls_back_the_whole_batch(client, db_session, actors, monkeypatch):
    make_user(db_session, email=f"existing.one{DOMAIN}", role="student", school_id="2026000100")

    def failing_audit(**_kwargs):
        raise AuditServiceError("simulated audit outage")

    monkeypatch.setattr(classroom_service, "_record_audit", failing_audit)

    response = bulk_enroll(
        client,
        actors["instructor"],
        actors["classroom"].class_id,
        [f"existing.one{DOMAIN}", f"not.yet{DOMAIN}"],
    )

    assert response.status_code == 503
    db_session.expire_all()
    assert db_session.query(Enrollment).count() == 0
    assert db_session.query(PendingEnrollment).count() == 0


def test_existing_enrollment_and_assessment_records_are_preserved(client, db_session, actors):
    classroom = actors["classroom"]
    student = make_user(db_session, email=f"returning{DOMAIN}", role="student", school_id="2026000110")
    enrollment = Enrollment(class_id=classroom.class_id, student_id=student.user_id, status="removed")
    task = Task(instructor_id=actors["instructor"].user_id, class_id=classroom.class_id, title="Loops")
    db_session.add_all([enrollment, task])
    db_session.commit()
    submission = Submission(student_id=student.user_id, task_id=task.task_id, raw_code="print('hi')")
    db_session.add(submission)
    db_session.commit()
    enrollment_id, submission_id = enrollment.enrollment_id, submission.sub_id

    response = bulk_enroll(client, actors["instructor"], classroom.class_id, [student.email])
    assert response.json()["already_enrolled"] == 1

    db_session.add(PendingEnrollment(class_id=classroom.class_id, email=student.email))
    db_session.commit()
    retry = client.post(f"/admin/students/{student.user_id}/pending-enrollments/apply", headers=auth(actors["admin"]))
    assert retry.json()["already_enrolled_class_ids"] == [classroom.class_id]

    db_session.expire_all()
    kept = db_session.query(Enrollment).filter(Enrollment.student_id == student.user_id).all()
    assert [(e.enrollment_id, e.status) for e in kept] == [(enrollment_id, "removed")]
    kept_submission = db_session.get(Submission, submission_id)
    assert kept_submission.student_id == student.user_id
    assert kept_submission.raw_code == "print('hi')"
    kept_student = db_session.get(User, student.user_id)
    assert (kept_student.name, kept_student.school_id) == ("Test User", "2026000110")
