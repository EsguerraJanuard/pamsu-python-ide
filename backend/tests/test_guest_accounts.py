"""
Self-service guest accounts (backend audit "Still open" item 4).

Owner decisions: keep "Continue as Guest Student" with a daily cap; guests
stay in the admin-owned sandbox and cannot join real classes; the sandbox
has a published demo activity; a guest is deleted, with all its data, 24
hours after creation (2026-10-24; before: deactivated after 7 days).
Admin-created guests keep the student rules.
"""

import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import (AcademicEvent, ASTAnalysis, ASTFinding,
                                      AuditRecord, BehavioralLog, Classroom,
                                      CodingSession, Enrollment,
                                      ExecutionRequest, InstructorGrade,
                                      Notification,
                                      PartnerExecutionUpdateRecord,
                                      PracticeAttempt, PracticeModule,
                                      PracticeTask, SimilarityResult,
                                      Submission, Task, TaskTestCase, User)
from app.services import guest_service
from app.services.evaluation_service import evaluate_submission_by_id
from app.services.guest_service import (DEMO_ACTIVITY_TITLE, DEMO_TEST_CASES,
                                        GUEST_CANNOT_JOIN_DETAIL,
                                        GUEST_EXPIRED_DETAIL,
                                        GUEST_LIMIT_REACHED_DETAIL,
                                        SANDBOX_CLASS_CODE,
                                        create_self_service_guest,
                                        delete_expired_guests,
                                        ensure_sandbox_demo_activity,
                                        get_or_create_sandbox_classroom,
                                        guest_limit_reached,
                                        is_self_service_guest)

DEMO_SOLUTION = "n = int(input())\nfor i in range(n, 0, -1):\n    print(i)\nprint(\"Liftoff!\")\n"

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


# ------------------------------------------------------------ 24-hour lifetime


def test_guest_stops_working_after_24_hours(client, db_session):
    recent = make_guest(db_session, 1, age=timedelta(hours=23, minutes=59))
    expired = make_guest(db_session, 2, age=timedelta(hours=24, minutes=1))

    assert client.get("/notifications/unread-count", headers=auth(recent)).status_code == 200
    response = client.get("/notifications/unread-count", headers=auth(expired))
    assert response.status_code == 403
    assert response.json()["detail"] == GUEST_EXPIRED_DETAIL


def test_old_accounts_that_are_not_self_service_guests_keep_working(client, db_session):
    old_visitor = make_user(db_session, email=f"visitor{DOMAIN}", role="student", school_id="GST7654321",
                            created_at=datetime.now(timezone.utc) - timedelta(days=400))

    assert client.get("/notifications/unread-count", headers=auth(old_visitor)).status_code == 200


def test_new_guest_sign_in_deletes_expired_guests(client, db_session, admin):
    expired = make_guest(db_session, 1, age=timedelta(hours=25))
    recent = make_guest(db_session, 2, age=timedelta(hours=23))
    old_visitor = make_user(db_session, email=f"visitor{DOMAIN}", role="student", school_id="GST7654321",
                            created_at=datetime.now(timezone.utc) - timedelta(days=400))
    expired_id = expired.user_id

    assert client.post("/guest").status_code == 200

    remaining = {user_id for (user_id,) in db_session.query(User.user_id)}
    assert expired_id not in remaining
    assert {recent.user_id, old_visitor.user_id} <= remaining


def test_cleanup_deletes_in_batches_and_is_idempotent(db_session):
    for number in range(1, 4):
        make_guest(db_session, number, age=timedelta(hours=30))

    assert delete_expired_guests(db_session, limit=2) == 2
    db_session.commit()
    assert delete_expired_guests(db_session, limit=2) == 1
    db_session.commit()
    assert delete_expired_guests(db_session) == 0


def _guest_token(response) -> tuple[int, dict[str, str]]:
    body = response.json()
    return body["user"]["user_id"], {"Authorization": f"Bearer {body['access_token']}"}


def _work_on_demo(client, headers, task_id: int, code: str) -> tuple[str, int]:
    """As a guest would: open the workspace, get counted, run, submit."""
    session = client.post("/activities/coding-sessions/", json={"task_id": task_id}, headers=headers)
    assert session.status_code == 201, session.text
    session_id = session.json()["session_id"]
    activity = client.patch(f"/activities/coding-sessions/{session_id}/activity",
                            json={"tab_switch_increment": 2, "blocked_paste_increment": 1}, headers=headers)
    assert activity.status_code == 200, activity.text
    run = client.post("/execution/requests/", json={"request_kind": "run", "task_id": task_id, "source_code": code,
                                                    "standard_input": "5\n", "coding_session_id": session_id},
                      headers=headers)
    assert run.status_code == 201, run.text
    submission = client.post("/submissions/", json={"task_id": task_id, "raw_code": code,
                                                    "coding_session_id": session_id}, headers=headers)
    assert submission.status_code == 201, submission.text
    sub_id = submission.json()["sub_id"]
    log = client.post("/logs/behavioral/", json={"sub_id": sub_id, "tab_switches_count": 2, "blocked_paste_count": 1,
                                                 "mouseleave_count": 0, "run_attempt_count": 1,
                                                 "idle_duration_seconds": 0}, headers=headers)
    assert log.status_code == 201, log.text
    return session_id, sub_id


def test_cleanup_deletes_everything_an_expired_guest_created_and_nothing_else(client, db_session, admin):
    first_id, first_headers = _guest_token(client.post("/guest"))
    second_id, second_headers = _guest_token(client.post("/guest"))
    demo = db_session.query(Task).filter(Task.title == DEMO_ACTIVITY_TITLE).one()

    _, second_sub = _work_on_demo(client, second_headers, demo.task_id, DEMO_SOLUTION)
    _, first_sub = _work_on_demo(client, first_headers, demo.task_id, DEMO_SOLUTION)

    # Evaluation: AST analysis and a similarity match against the other guest.
    evaluate_submission_by_id(db=db_session, sub_id=first_sub, instructor_id=None)
    analysis = db_session.query(ASTAnalysis).filter(ASTAnalysis.submission_id == first_sub).one()
    db_session.add(ASTFinding(analysis_id=analysis.analysis_id, rule_key="require_for_loop", label="for loop",
                              passed=True, details={}))
    db_session.add(InstructorGrade(submission_id=first_sub, instructor_id=admin.user_id, score=90, max_score=100,
                                   is_released=False))
    run = (db_session.query(ExecutionRequest)
           .filter(ExecutionRequest.student_id == first_id, ExecutionRequest.request_kind == "run").one())
    db_session.add(PartnerExecutionUpdateRecord(update_id="0d7a0ac3-1f6e-4f0e-9a52-3b8f3b6f2a11",
                                                execution_id=run.execution_id, correlation_id=run.correlation_id,
                                                sequence_number=1, status="running", payload_digest="a" * 64))
    module = PracticeModule(title="Basics", order_index=0)
    db_session.add(module)
    db_session.flush()
    practice_task = PracticeTask(module_id=module.module_id, title="Print ok", instructions="Print ok.",
                                 expected_output="ok\n", order_index=0)
    db_session.add(practice_task)
    db_session.flush()
    db_session.add(PracticeAttempt(student_id=first_id, task_id=practice_task.task_id, submitted_code="print(1)\n",
                                   is_successful=True, ast_feedback=[]))
    db_session.commit()
    assert db_session.query(SimilarityResult).count() >= 1

    # A guest who is still within 24 hours keeps everything.
    survivor = make_guest(db_session, 99, age=timedelta(hours=1))
    sandbox = db_session.query(Classroom).filter(Classroom.class_code == SANDBOX_CLASS_CODE).one()
    db_session.add(Enrollment(class_id=sandbox.class_id, student_id=survivor.user_id, status="active"))
    db_session.commit()
    survivor_session, survivor_sub = _work_on_demo(client, auth(survivor), demo.task_id, DEMO_SOLUTION)

    expired_ids = [first_id, second_id]
    for user in db_session.query(User).filter(User.user_id.in_(expired_ids)):
        user.created_at = datetime.now(timezone.utc) - timedelta(hours=25)
    db_session.commit()
    guest_events = [event_id for (event_id,) in db_session.query(AcademicEvent.event_id)
                    .filter(AcademicEvent.actor_user_id.in_(expired_ids))]
    assert guest_events and db_session.query(AuditRecord).filter(AuditRecord.actor_user_id.in_(expired_ids)).count()
    assert db_session.query(Notification).filter(Notification.event_id.in_(guest_events)).count()

    assert delete_expired_guests(db_session) == 2
    db_session.commit()
    db_session.expire_all()

    gone = {
        User: User.user_id.in_(expired_ids),
        Enrollment: Enrollment.student_id.in_(expired_ids),
        CodingSession: CodingSession.student_id.in_(expired_ids),
        ExecutionRequest: ExecutionRequest.student_id.in_(expired_ids),
        Submission: Submission.student_id.in_(expired_ids),
        AuditRecord: AuditRecord.actor_user_id.in_(expired_ids),
        AcademicEvent: AcademicEvent.actor_user_id.in_(expired_ids),
        Notification: Notification.event_id.in_(guest_events),
        PracticeAttempt: PracticeAttempt.student_id.in_(expired_ids),
        BehavioralLog: BehavioralLog.sub_id.in_([first_sub, second_sub]),
        ASTAnalysis: ASTAnalysis.submission_id.in_([first_sub, second_sub]),
        InstructorGrade: InstructorGrade.submission_id == first_sub,
    }
    for model, condition in gone.items():
        assert db_session.query(model).filter(condition).count() == 0, model.__name__
    for model in (ASTFinding, PartnerExecutionUpdateRecord, SimilarityResult):
        assert db_session.query(model).count() == 0, model.__name__

    # The survivor, the shared sandbox, the demo activity and the admin stay.
    assert db_session.get(User, survivor.user_id) is not None
    assert db_session.get(Submission, survivor_sub) is not None
    assert db_session.get(CodingSession, survivor_session) is not None
    assert db_session.query(Enrollment).filter(Enrollment.student_id == survivor.user_id).count() == 1
    assert db_session.get(Task, demo.task_id) is not None
    assert db_session.query(TaskTestCase).filter(TaskTestCase.task_id == demo.task_id).count() == len(DEMO_TEST_CASES)
    assert db_session.get(User, admin.user_id) is not None


# ------------------------------------------------------------ demo activity


def test_first_guest_finds_a_published_demo_activity_ready_to_use(client, db_session, admin):
    guest_id, headers = _guest_token(client.post("/guest"))

    demo = db_session.query(Task).filter(Task.title == DEMO_ACTIVITY_TITLE).one()
    sandbox = db_session.query(Classroom).filter(Classroom.class_code == SANDBOX_CLASS_CODE).one()
    assert (demo.class_id, demo.instructor_id) == (sandbox.class_id, admin.user_id)
    assert demo.is_published and demo.published_at is not None and demo.due_at is None
    assert demo.required_ast_rules == {"require_for_loop": 1, "require_print_call": 1}
    assert demo.starter_code.startswith("n = int(input())")
    assert demo.paste_policy == "internal_only" and demo.is_graded

    (record,) = db_session.query(AuditRecord).filter(AuditRecord.action_type == "activity_created").all()
    assert (record.actor_user_id, record.resource_id) == (None, str(demo.task_id))

    # The guest sees it, with one visible sample, and the structure check uses its rules.
    listed = client.get("/activities/", headers=headers)
    assert listed.status_code == 200, listed.text
    assert [task["title"] for task in listed.json()] == [DEMO_ACTIVITY_TITLE]
    samples = client.get(f"/activities/{demo.task_id}/sample-test-cases", headers=headers).json()
    assert [(case["standard_input"], case["expected_output"]) for case in samples] == [
        ("5\n", "5\n4\n3\n2\n1\nLiftoff!\n")
    ]

    check = client.post(f"/activities/{demo.task_id}/analyze-ast", json={"source_code": DEMO_SOLUTION}, headers=headers)
    assert check.status_code == 200, check.text
    assert check.json()["passed"] is True
    starter_check = client.post(f"/activities/{demo.task_id}/analyze-ast", json={"source_code": demo.starter_code},
                                headers=headers)
    assert starter_check.json()["passed"] is False

    session = client.post("/activities/coding-sessions/", json={"task_id": demo.task_id}, headers=headers)
    assert session.status_code == 201, session.text


def test_demo_test_cases_match_the_reference_solution():
    for case in DEMO_TEST_CASES:
        result = subprocess.run([sys.executable, "-c", DEMO_SOLUTION], input=case["standard_input"],
                                capture_output=True, text=True, timeout=10, check=True)
        assert result.stdout == case["expected_output"], case["name"]


def test_demo_activity_is_added_once_and_admin_changes_are_kept(client, db_session, admin):
    sandbox = get_or_create_sandbox_classroom(db_session)  # a sandbox from before the demo existed
    assert db_session.query(Task).count() == 0

    assert client.post("/guest").status_code == 200
    assert client.post("/guest").status_code == 200
    (demo,) = db_session.query(Task).filter(Task.class_id == sandbox.class_id).all()

    demo.is_published = False
    demo.starter_code = "# edited by MIS\n"
    db_session.commit()

    assert ensure_sandbox_demo_activity(db_session, sandbox).task_id == demo.task_id
    db_session.expire_all()
    (demo,) = db_session.query(Task).filter(Task.class_id == sandbox.class_id).all()
    assert (demo.is_published, demo.starter_code) == (False, "# edited by MIS\n")


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
