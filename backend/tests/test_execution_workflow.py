from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.domain_models import (
    CodingSession,
    ExecutionRequest,
    Submission,
    User,
)
from app.schemas.execution_schema import (
    ExecutionWorkerUpdate,
)
from app.services.execution_service import (
    ExecutionStateConflictError,
    assign_worker_task_id,
    update_execution_from_worker,
)


TEST_PASSWORD = "TestPass123!"


def create_test_user(
    db: Session,
    *,
    name: str,
    role: str,
    school_id: str,
    email: str,
) -> User:
    user = User(
        name=name,
        role=role,
        school_id=school_id,
        email=email.lower(),
        password_hash=get_password_hash(TEST_PASSWORD),
        email_verified=True,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def login_and_get_token(
    client,
    *,
    email: str,
) -> str:
    response = client.post(
        "/login",
        data={
            "username": email,
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def bearer_header(
    token: str,
) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }


def create_classroom(
    client,
    *,
    instructor_token: str,
    name: str = "Python Programming",
    subject_code: str = "CCS101",
    section: str = "BSIT 1A",
) -> dict:
    response = client.post(
        "/classrooms/",
        headers=bearer_header(instructor_token),
        json={
            "name": name,
            "subject_code": subject_code,
            "section": section,
        },
    )

    assert response.status_code == 201

    return response.json()


def enroll_student(
    client,
    *,
    student_token: str,
    class_code: str,
) -> dict:
    response = client.post(
        "/classrooms/join",
        headers=bearer_header(student_token),
        json={
            "class_code": class_code,
        },
    )

    assert response.status_code == 201

    return response.json()


def create_task(
    client,
    *,
    instructor_token: str,
    class_id: int,
    title: str,
    publish: bool = True,
    is_graded: bool = True,
) -> dict:
    create_response = client.post(
        "/instructors/tasks/",
        headers=bearer_header(instructor_token),
        json={
            "class_id": class_id,
            "title": title,
            "description": ("Execution-request workflow test."),
            "instructions": ("Write and test a Python program."),
            "activity_type": "laboratory",
            "required_ast_rules": {},
            "starter_code": ("def solve():\n    pass\n"),
            "paste_policy": "internal_only",
            "is_graded": is_graded,
            "due_at": None,
        },
    )

    assert create_response.status_code == 201

    task = create_response.json()

    if not publish:
        return task

    publication_response = client.patch(
        (f"/instructors/tasks/{task['task_id']}/publication"),
        headers=bearer_header(instructor_token),
        json={
            "is_published": True,
        },
    )

    assert publication_response.status_code == 200

    return publication_response.json()


def create_submission(
    client,
    *,
    student_token: str,
    task_id: int,
    raw_code: str,
    standard_input: str = "",
    coding_session_id: str | None = None,
):
    payload = {
        "task_id": task_id,
        "raw_code": raw_code,
        "standard_input": standard_input,
    }

    if coding_session_id is not None:
        payload["coding_session_id"] = coding_session_id

    return client.post(
        "/submissions/",
        headers=bearer_header(student_token),
        json=payload,
    )


def create_execution_request(
    client,
    *,
    student_token: str,
    request_kind: str,
    task_id: int,
    source_code: str | None = None,
    standard_input: str = "",
    submission_id: int | None = None,
    coding_session_id: str | None = None,
    idempotency_key: str | None = None,
):
    payload = {
        "request_kind": request_kind,
        "task_id": task_id,
        "standard_input": standard_input,
    }

    if source_code is not None:
        payload["source_code"] = source_code

    if submission_id is not None:
        payload["submission_id"] = submission_id

    if coding_session_id is not None:
        payload["coding_session_id"] = coding_session_id

    headers = bearer_header(student_token)

    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key

    return client.post(
        "/execution/requests/",
        headers=headers,
        json=payload,
    )


def setup_execution_context(
    client,
    db_session,
    *,
    instructor_school_id: str,
    instructor_email: str,
    student_school_id: str,
    student_email: str,
    task_title: str,
    publish: bool = True,
    is_graded: bool = True,
) -> dict:
    instructor = create_test_user(
        db_session,
        name="Execution Instructor",
        role="instructor",
        school_id=instructor_school_id,
        email=instructor_email,
    )

    student = create_test_user(
        db_session,
        name="Execution Student",
        role="student",
        school_id=student_school_id,
        email=student_email,
    )

    instructor_token = login_and_get_token(
        client,
        email=instructor.email,
    )

    student_token = login_and_get_token(
        client,
        email=student.email,
    )

    classroom = create_classroom(
        client,
        instructor_token=instructor_token,
    )

    enrollment = enroll_student(
        client,
        student_token=student_token,
        class_code=classroom["class_code"],
    )

    task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=classroom["class_id"],
        title=task_title,
        publish=publish,
        is_graded=is_graded,
    )

    return {
        "instructor": instructor,
        "student": student,
        "instructor_token": instructor_token,
        "student_token": student_token,
        "classroom": classroom,
        "enrollment": enrollment,
        "task": task,
    }


def test_student_can_queue_run_and_check_requests(
    client,
    db_session,
):
    setup = setup_execution_context(
        client,
        db_session,
        instructor_school_id="7100000001",
        instructor_email=("executionfaculty1@pampangastateu.edu.ph"),
        student_school_id="7200000001",
        student_email=("executionstudent1@pampangastateu.edu.ph"),
        task_title="Run and Check Test",
    )

    run_code = "number = int(input())\nprint(number * 2)\n"

    run_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="run",
        task_id=setup["task"]["task_id"],
        source_code=run_code,
        standard_input="5\n",
    )

    assert run_response.status_code == 201

    run_request = run_response.json()

    assert run_request["request_kind"] == "run"
    assert run_request["status"] == "queued"
    assert run_request["task_id"] == setup["task"]["task_id"]
    assert run_request["submission_id"] is None
    assert run_request["coding_session_id"] is None
    assert run_request["source_code"] == run_code
    assert run_request["standard_input"] == "5\n"
    assert run_request["stdout"] == ""
    assert run_request["stderr"] == ""
    assert run_request["exit_code"] is None
    assert run_request["execution_time_ms"] is None
    assert run_request["limit_reason"] is None
    assert run_request["started_at"] is None
    assert run_request["completed_at"] is None
    assert run_request["queued_at"] is not None

    assert "student_id" not in run_request
    assert "worker_task_id" not in run_request

    check_code = "def solve(value):\n    return value + 1\n"

    check_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="check",
        task_id=setup["task"]["task_id"],
        source_code=check_code,
    )

    assert check_response.status_code == 201

    check_request = check_response.json()

    assert check_request["request_kind"] == "check"
    assert check_request["status"] == "queued"
    assert check_request["source_code"] == check_code

    stored_requests = (
        db_session.query(ExecutionRequest)
        .filter(
            ExecutionRequest.student_id == setup["student"].user_id,
        )
        .all()
    )

    assert len(stored_requests) == 2

    for stored_request in stored_requests:
        assert stored_request.status == "queued"
        assert stored_request.worker_task_id is None


def test_execution_request_idempotency_header_replays_same_request(
    client,
    db_session,
):
    setup = setup_execution_context(
        client,
        db_session,
        instructor_school_id="7100000010",
        instructor_email=("executionfaculty10@pampangastateu.edu.ph"),
        student_school_id="7200000012",
        student_email=("executionstudent12@pampangastateu.edu.ph"),
        task_title=("Execution Idempotency Replay Test"),
    )

    idempotency_key = str(uuid4()).upper()
    normalized_key = str(
        UUID(idempotency_key),
    )
    source_code = "print('safe retry')\n"

    first_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="run",
        task_id=setup["task"]["task_id"],
        source_code=source_code,
        standard_input="",
        idempotency_key=idempotency_key,
    )

    second_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="run",
        task_id=setup["task"]["task_id"],
        source_code=source_code,
        standard_input="",
        idempotency_key=idempotency_key,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_request = first_response.json()
    second_request = second_response.json()

    assert second_request["execution_id"] == first_request["execution_id"]

    for response_data in (
        first_request,
        second_request,
    ):
        assert "request_idempotency_key" not in response_data
        assert "request_payload_digest" not in response_data
        assert "dispatch_idempotency_key" not in response_data
        assert "correlation_id" not in response_data
        assert "worker_task_id" not in response_data

    db_session.expire_all()

    stored_requests = (
        db_session.query(ExecutionRequest)
        .filter(
            ExecutionRequest.student_id == setup["student"].user_id,
            ExecutionRequest.request_idempotency_key == normalized_key,
        )
        .all()
    )

    assert len(stored_requests) == 1
    assert stored_requests[0].execution_id == first_request["execution_id"]
    assert stored_requests[0].request_idempotency_key == normalized_key
    assert stored_requests[0].request_payload_digest is not None
    assert len(stored_requests[0].request_payload_digest) == 64


def test_execution_request_idempotency_header_rejects_changed_payload(
    client,
    db_session,
):
    setup = setup_execution_context(
        client,
        db_session,
        instructor_school_id="7100000011",
        instructor_email=("executionfaculty11@pampangastateu.edu.ph"),
        student_school_id="7200000013",
        student_email=("executionstudent13@pampangastateu.edu.ph"),
        task_title=("Execution Idempotency Conflict Test"),
    )

    idempotency_key = str(uuid4())

    first_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="run",
        task_id=setup["task"]["task_id"],
        source_code=("print('first payload')\n"),
        idempotency_key=idempotency_key,
    )

    conflicting_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="run",
        task_id=setup["task"]["task_id"],
        source_code=("print('changed payload')\n"),
        idempotency_key=idempotency_key,
    )

    assert first_response.status_code == 201
    assert conflicting_response.status_code == 409
    assert "already used" in conflicting_response.json()["detail"]

    db_session.expire_all()

    stored_requests = (
        db_session.query(ExecutionRequest)
        .filter(
            ExecutionRequest.student_id == setup["student"].user_id,
            ExecutionRequest.request_idempotency_key == idempotency_key,
        )
        .all()
    )

    assert len(stored_requests) == 1
    assert stored_requests[0].execution_id == first_response.json()["execution_id"]


def test_execution_request_rejects_invalid_idempotency_header(
    client,
    db_session,
):
    setup = setup_execution_context(
        client,
        db_session,
        instructor_school_id="7100000012",
        instructor_email=("executionfaculty12@pampangastateu.edu.ph"),
        student_school_id="7200000014",
        student_email=("executionstudent14@pampangastateu.edu.ph"),
        task_title=("Invalid Execution Idempotency Key Test"),
    )

    response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="run",
        task_id=setup["task"]["task_id"],
        source_code=("print('invalid key')\n"),
        idempotency_key="not-a-uuid",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("Idempotency-Key must be a valid UUID.")

    db_session.expire_all()

    stored_count = (
        db_session.query(ExecutionRequest)
        .filter(
            ExecutionRequest.student_id == setup["student"].user_id,
        )
        .count()
    )

    assert stored_count == 0


def test_submit_request_uses_immutable_submission_snapshot(
    client,
    db_session,
):
    setup = setup_execution_context(
        client,
        db_session,
        instructor_school_id="7100000002",
        instructor_email=("executionfaculty2@pampangastateu.edu.ph"),
        student_school_id="7200000002",
        student_email=("executionstudent2@pampangastateu.edu.ph"),
        task_title="Submit Snapshot Test",
    )

    submitted_code = "name = input()\nprint(f'Hello, {name}')\n"

    submission_response = create_submission(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        raw_code=submitted_code,
        standard_input="PAMSU\n",
    )

    assert submission_response.status_code == 201

    submission = submission_response.json()

    execution_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="submit",
        task_id=setup["task"]["task_id"],
        submission_id=submission["sub_id"],
        standard_input=("THIS MUST BE IGNORED\n"),
    )

    assert execution_response.status_code == 201

    execution_request = execution_response.json()

    assert execution_request["request_kind"] == "submit"
    assert execution_request["submission_id"] == submission["sub_id"]
    assert execution_request["source_code"] == submitted_code
    assert execution_request["standard_input"] == "PAMSU\n"
    assert execution_request["status"] == "queued"

    stored_request = db_session.get(
        ExecutionRequest,
        execution_request["execution_id"],
    )

    assert stored_request is not None
    assert stored_request.source_code == submitted_code
    assert stored_request.standard_input == "PAMSU\n"

    stored_submission = db_session.get(
        Submission,
        submission["sub_id"],
    )

    assert stored_submission is not None
    assert stored_submission.raw_code == submitted_code
    assert stored_submission.standard_input == "PAMSU\n"


def test_execution_request_kind_contract_is_enforced(
    client,
    db_session,
):
    setup = setup_execution_context(
        client,
        db_session,
        instructor_school_id="7100000003",
        instructor_email=("executionfaculty3@pampangastateu.edu.ph"),
        student_school_id="7200000003",
        student_email=("executionstudent3@pampangastateu.edu.ph"),
        task_title="Request Contract Test",
    )

    missing_source_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="run",
        task_id=setup["task"]["task_id"],
    )

    assert missing_source_response.status_code == 422

    run_with_submission_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="run",
        task_id=setup["task"]["task_id"],
        source_code="print('run')\n",
        submission_id=1,
    )

    assert run_with_submission_response.status_code == 422

    submit_without_submission_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="submit",
        task_id=setup["task"]["task_id"],
    )

    assert submit_without_submission_response.status_code == 422

    submit_with_source_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="submit",
        task_id=setup["task"]["task_id"],
        source_code=("print('client source')\n"),
        submission_id=1,
    )

    assert submit_with_source_response.status_code == 422

    controlled_fields_response = client.post(
        "/execution/requests/",
        headers=bearer_header(setup["student_token"]),
        json={
            "request_kind": "run",
            "task_id": (setup["task"]["task_id"]),
            "source_code": ("print('test')\n"),
            "standard_input": "",
            "student_id": (setup["student"].user_id),
            "execution_id": str(uuid4()),
            "status": "completed",
            "stdout": "forged",
            "stderr": "",
            "exit_code": 0,
            "execution_time_ms": 1,
            "limit_reason": None,
            "worker_task_id": ("forged-worker"),
            "queued_at": ("2026-07-15T00:00:00Z"),
            "started_at": ("2026-07-15T00:00:00Z"),
            "completed_at": ("2026-07-15T00:00:01Z"),
        },
    )

    assert controlled_fields_response.status_code == 422
    assert db_session.query(ExecutionRequest).count() == 0


def test_execution_requires_published_task_and_active_enrollment(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Execution Access Instructor",
        role="instructor",
        school_id="7100000004",
        email=("executionfaculty4@pampangastateu.edu.ph"),
    )

    enrolled_student = create_test_user(
        db_session,
        name="Enrolled Execution Student",
        role="student",
        school_id="7200000004",
        email=("executionstudent4@pampangastateu.edu.ph"),
    )

    unenrolled_student = create_test_user(
        db_session,
        name="Unenrolled Execution Student",
        role="student",
        school_id="7200000005",
        email=("executionstudent5@pampangastateu.edu.ph"),
    )

    instructor_token = login_and_get_token(
        client,
        email=instructor.email,
    )

    enrolled_token = login_and_get_token(
        client,
        email=enrolled_student.email,
    )

    unenrolled_token = login_and_get_token(
        client,
        email=unenrolled_student.email,
    )

    classroom = create_classroom(
        client,
        instructor_token=instructor_token,
    )

    enrollment = enroll_student(
        client,
        student_token=enrolled_token,
        class_code=classroom["class_code"],
    )

    draft_task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=classroom["class_id"],
        title="Draft Execution Task",
        publish=False,
    )

    draft_response = create_execution_request(
        client,
        student_token=enrolled_token,
        request_kind="run",
        task_id=draft_task["task_id"],
        source_code="print('draft')\n",
    )

    assert draft_response.status_code == 404

    published_task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=classroom["class_id"],
        title="Published Execution Task",
    )

    unenrolled_response = create_execution_request(
        client,
        student_token=unenrolled_token,
        request_kind="run",
        task_id=published_task["task_id"],
        source_code=("print('unenrolled')\n"),
    )

    assert unenrolled_response.status_code == 404

    disable_response = client.patch(
        (f"/classrooms/enrollments/{enrollment['enrollment_id']}/status"),
        headers=bearer_header(instructor_token),
        json={
            "status": "disabled",
        },
    )

    assert disable_response.status_code == 200

    disabled_response = create_execution_request(
        client,
        student_token=enrolled_token,
        request_kind="run",
        task_id=published_task["task_id"],
        source_code=("print('disabled')\n"),
    )

    assert disabled_response.status_code == 404

    reactivate_response = client.patch(
        (f"/classrooms/enrollments/{enrollment['enrollment_id']}/status"),
        headers=bearer_header(instructor_token),
        json={
            "status": "active",
        },
    )

    assert reactivate_response.status_code == 200

    deactivate_class_response = client.patch(
        (f"/classrooms/{classroom['class_id']}"),
        headers=bearer_header(instructor_token),
        json={
            "is_active": False,
        },
    )

    assert deactivate_class_response.status_code == 200

    inactive_class_response = create_execution_request(
        client,
        student_token=enrolled_token,
        request_kind="check",
        task_id=published_task["task_id"],
        source_code=("print('inactive')\n"),
    )

    assert inactive_class_response.status_code == 404


def test_coding_session_must_match_student_and_task(
    client,
    db_session,
):
    setup = setup_execution_context(
        client,
        db_session,
        instructor_school_id="7100000005",
        instructor_email=("executionfaculty5@pampangastateu.edu.ph"),
        student_school_id="7200000006",
        student_email=("executionstudent6@pampangastateu.edu.ph"),
        task_title="Coding Session Test",
    )

    second_task = create_task(
        client,
        instructor_token=(setup["instructor_token"]),
        class_id=setup["classroom"]["class_id"],
        title="Second Coding Session Task",
    )

    other_student = create_test_user(
        db_session,
        name="Other Coding Session Student",
        role="student",
        school_id="7200000007",
        email=("executionstudent7@pampangastateu.edu.ph"),
    )

    valid_session_id = str(uuid4())
    wrong_task_session_id = str(uuid4())
    wrong_owner_session_id = str(uuid4())

    db_session.add_all(
        [
            CodingSession(
                session_id=valid_session_id,
                student_id=(setup["student"].user_id),
                task_id=(setup["task"]["task_id"]),
            ),
            CodingSession(
                session_id=wrong_task_session_id,
                student_id=(setup["student"].user_id),
                task_id=second_task["task_id"],
            ),
            CodingSession(
                session_id=wrong_owner_session_id,
                student_id=other_student.user_id,
                task_id=(setup["task"]["task_id"]),
            ),
        ]
    )

    db_session.commit()

    valid_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="run",
        task_id=setup["task"]["task_id"],
        source_code=("print('valid session')\n"),
        coding_session_id=valid_session_id,
    )

    assert valid_response.status_code == 201
    assert valid_response.json()["coding_session_id"] == valid_session_id

    wrong_task_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="run",
        task_id=setup["task"]["task_id"],
        source_code=("print('wrong task')\n"),
        coding_session_id=wrong_task_session_id,
    )

    assert wrong_task_response.status_code == 404

    wrong_owner_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="check",
        task_id=setup["task"]["task_id"],
        source_code=("print('wrong owner')\n"),
        coding_session_id=wrong_owner_session_id,
    )

    assert wrong_owner_response.status_code == 404

    malformed_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="run",
        task_id=setup["task"]["task_id"],
        source_code=("print('malformed')\n"),
        coding_session_id="not-a-valid-uuid",
    )

    assert malformed_response.status_code == 422


def test_student_can_view_only_owned_execution_requests(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Shared Execution Instructor",
        role="instructor",
        school_id="7100000006",
        email=("executionfaculty6@pampangastateu.edu.ph"),
    )

    first_student = create_test_user(
        db_session,
        name="First Execution Student",
        role="student",
        school_id="7200000008",
        email=("executionstudent8@pampangastateu.edu.ph"),
    )

    second_student = create_test_user(
        db_session,
        name="Second Execution Student",
        role="student",
        school_id="7200000009",
        email=("executionstudent9@pampangastateu.edu.ph"),
    )

    instructor_token = login_and_get_token(
        client,
        email=instructor.email,
    )

    first_token = login_and_get_token(
        client,
        email=first_student.email,
    )

    second_token = login_and_get_token(
        client,
        email=second_student.email,
    )

    classroom = create_classroom(
        client,
        instructor_token=instructor_token,
    )

    enroll_student(
        client,
        student_token=first_token,
        class_code=classroom["class_code"],
    )

    enroll_student(
        client,
        student_token=second_token,
        class_code=classroom["class_code"],
    )

    task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=classroom["class_id"],
        title="Execution Ownership Test",
    )

    first_response = create_execution_request(
        client,
        student_token=first_token,
        request_kind="run",
        task_id=task["task_id"],
        source_code=("print('first student')\n"),
    )

    second_response = create_execution_request(
        client,
        student_token=second_token,
        request_kind="check",
        task_id=task["task_id"],
        source_code=("print('second student')\n"),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_execution = first_response.json()
    second_execution = second_response.json()

    list_response = client.get(
        "/execution/requests/",
        headers=bearer_header(first_token),
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["execution_id"] == first_execution["execution_id"]

    filtered_response = client.get(
        "/execution/requests/",
        headers=bearer_header(first_token),
        params={
            "task_id": task["task_id"],
            "request_kind": "run",
            "status": "queued",
        },
    )

    assert filtered_response.status_code == 200
    assert len(filtered_response.json()) == 1

    own_detail_response = client.get(
        (f"/execution/requests/{first_execution['execution_id']}"),
        headers=bearer_header(first_token),
    )

    assert own_detail_response.status_code == 200

    other_detail_response = client.get(
        (f"/execution/requests/{second_execution['execution_id']}"),
        headers=bearer_header(first_token),
    )

    assert other_detail_response.status_code == 404


def test_instructor_can_review_only_owned_execution_requests(
    client,
    db_session,
):
    setup = setup_execution_context(
        client,
        db_session,
        instructor_school_id="7100000007",
        instructor_email=("executionfaculty7@pampangastateu.edu.ph"),
        student_school_id="7200000010",
        student_email=("executionstudent10@pampangastateu.edu.ph"),
        task_title="Instructor Execution Review",
    )

    other_instructor = create_test_user(
        db_session,
        name="Other Execution Instructor",
        role="instructor",
        school_id="7100000008",
        email=("executionfaculty8@pampangastateu.edu.ph"),
    )

    other_instructor_token = login_and_get_token(
        client,
        email=other_instructor.email,
    )

    execution_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="run",
        task_id=setup["task"]["task_id"],
        source_code=("print('review this')\n"),
    )

    assert execution_response.status_code == 201

    execution = execution_response.json()

    assign_worker_task_id(
        db_session,
        execution_id=execution["execution_id"],
        worker_task_id="worker-review-001",
    )

    update_execution_from_worker(
        db_session,
        execution_id=execution["execution_id"],
        update_data=ExecutionWorkerUpdate(
            status="completed",
            stdout="review output\n",
            stderr="",
            exit_code=0,
            execution_time_ms=15,
        ),
    )

    list_response = client.get(
        (f"/instructors/tasks/{setup['task']['task_id']}/execution-requests"),
        headers=bearer_header(setup["instructor_token"]),
        params={
            "student_id": (setup["student"].user_id),
            "request_kind": "run",
            "status": "completed",
        },
    )

    assert list_response.status_code == 200

    listed_requests = list_response.json()

    assert len(listed_requests) == 1
    assert listed_requests[0]["execution_id"] == execution["execution_id"]
    assert listed_requests[0]["student_id"] == setup["student"].user_id
    assert listed_requests[0]["stdout"] == "review output\n"
    assert "worker_task_id" not in listed_requests[0]

    detail_response = client.get(
        (f"/instructors/execution-requests/{execution['execution_id']}"),
        headers=bearer_header(setup["instructor_token"]),
    )

    assert detail_response.status_code == 200
    assert detail_response.json()["exit_code"] == 0
    assert "worker_task_id" not in detail_response.json()

    unauthorized_list_response = client.get(
        (f"/instructors/tasks/{setup['task']['task_id']}/execution-requests"),
        headers=bearer_header(other_instructor_token),
    )

    assert unauthorized_list_response.status_code == 403

    unauthorized_detail_response = client.get(
        (f"/instructors/execution-requests/{execution['execution_id']}"),
        headers=bearer_header(other_instructor_token),
    )

    assert unauthorized_detail_response.status_code == 403


def test_worker_lifecycle_updates_and_terminal_state_are_enforced(
    client,
    db_session,
):
    setup = setup_execution_context(
        client,
        db_session,
        instructor_school_id="7100000009",
        instructor_email=("executionfaculty9@pampangastateu.edu.ph"),
        student_school_id="7200000011",
        student_email=("executionstudent11@pampangastateu.edu.ph"),
        task_title="Worker Lifecycle Test",
    )

    execution_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        request_kind="run",
        task_id=setup["task"]["task_id"],
        source_code=("print('worker lifecycle')\n"),
    )

    assert execution_response.status_code == 201

    execution_id = execution_response.json()["execution_id"]

    assigned_request = assign_worker_task_id(
        db_session,
        execution_id=execution_id,
        worker_task_id="worker-task-001",
    )

    assert assigned_request.worker_task_id == "worker-task-001"

    same_assignment = assign_worker_task_id(
        db_session,
        execution_id=execution_id,
        worker_task_id="worker-task-001",
    )

    assert same_assignment.worker_task_id == "worker-task-001"

    with pytest.raises(
        ExecutionStateConflictError,
    ):
        assign_worker_task_id(
            db_session,
            execution_id=execution_id,
            worker_task_id="worker-task-002",
        )

    running_request = update_execution_from_worker(
        db_session,
        execution_id=execution_id,
        update_data=ExecutionWorkerUpdate(
            status="running",
        ),
    )

    assert running_request.status == "running"
    assert running_request.started_at is not None
    assert running_request.completed_at is None

    completed_at = datetime.now(timezone.utc) + timedelta(seconds=1)

    completed_request = update_execution_from_worker(
        db_session,
        execution_id=execution_id,
        update_data=ExecutionWorkerUpdate(
            status="completed",
            stdout="worker result\n",
            stderr="",
            exit_code=0,
            execution_time_ms=25,
            completed_at=completed_at,
        ),
    )

    assert completed_request.status == "completed"
    assert completed_request.stdout == "worker result\n"
    assert completed_request.stderr == ""
    assert completed_request.exit_code == 0
    assert completed_request.execution_time_ms == 25
    assert completed_request.completed_at is not None

    with pytest.raises(
        ExecutionStateConflictError,
    ):
        update_execution_from_worker(
            db_session,
            execution_id=execution_id,
            update_data=ExecutionWorkerUpdate(
                status="running",
            ),
        )

    db_session.expire_all()

    stored_request = db_session.get(
        ExecutionRequest,
        execution_id,
    )

    assert stored_request is not None
    assert stored_request.student_id == setup["student"].user_id
    assert stored_request.task_id == setup["task"]["task_id"]
    assert stored_request.source_code == ("print('worker lifecycle')\n")
    assert stored_request.worker_task_id == "worker-task-001"
