from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.domain_models import (
    CodingSession,
    User,
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
    response = client.post(
        "/instructors/tasks/",
        headers=bearer_header(instructor_token),
        json={
            "class_ids": [class_id],
            "title": title,
            "description": ("Coding-session workflow test."),
            "instructions": ("Write and test a Python program."),
            "activity_type": "laboratory",
            "required_ast_rules": {},
            "starter_code": ("def solve():\n    pass\n"),
            "paste_policy": "internal_only",
            "is_graded": is_graded,
            "due_at": None,
        },
    )

    assert response.status_code == 201

    task = response.json()[0]

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


def start_coding_session(
    client,
    *,
    student_token: str,
    task_id: int,
):
    return client.post(
        "/activities/coding-sessions/",
        headers=bearer_header(student_token),
        json={
            "task_id": task_id,
        },
    )


def update_coding_session(
    client,
    *,
    student_token: str,
    session_id: str,
    tab_switch_increment: int = 0,
    blocked_paste_increment: int = 0,
    idle_duration_increment_seconds: int = 0,
):
    return client.patch(
        (f"/activities/coding-sessions/{session_id}/activity"),
        headers=bearer_header(student_token),
        json={
            "tab_switch_increment": (tab_switch_increment),
            "blocked_paste_increment": (blocked_paste_increment),
            "idle_duration_increment_seconds": (idle_duration_increment_seconds),
        },
    )


def end_coding_session(
    client,
    *,
    student_token: str,
    session_id: str,
):
    return client.post(
        (f"/activities/coding-sessions/{session_id}/end"),
        headers=bearer_header(student_token),
    )


def create_execution_request(
    client,
    *,
    student_token: str,
    task_id: int,
    request_kind: str,
    coding_session_id: str | None = None,
    source_code: str | None = None,
    submission_id: int | None = None,
):
    payload = {
        "task_id": task_id,
        "request_kind": request_kind,
        "standard_input": "",
    }

    if coding_session_id is not None:
        payload["coding_session_id"] = coding_session_id

    if source_code is not None:
        payload["source_code"] = source_code

    if submission_id is not None:
        payload["submission_id"] = submission_id

    return client.post(
        "/execution/requests/",
        headers=bearer_header(student_token),
        json=payload,
    )


def setup_coding_session_context(
    client,
    db_session,
    *,
    instructor_school_id: str,
    instructor_email: str,
    student_school_id: str,
    student_email: str,
    task_title: str,
    publish: bool = True,
) -> dict:
    instructor = create_test_user(
        db_session,
        name="Coding Session Instructor",
        role="instructor",
        school_id=instructor_school_id,
        email=instructor_email,
    )

    student = create_test_user(
        db_session,
        name="Coding Session Student",
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


def test_student_can_start_resume_list_and_get_sessions(
    client,
    db_session,
):
    setup = setup_coding_session_context(
        client,
        db_session,
        instructor_school_id="8100000001",
        instructor_email=("sessionfaculty1@pampangastateu.edu.ph"),
        student_school_id="8200000001",
        student_email=("sessionstudent1@pampangastateu.edu.ph"),
        task_title="Session Lifecycle Test",
    )

    first_response = start_coding_session(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
    )

    assert first_response.status_code == 201

    first_session = first_response.json()

    assert first_session["task_id"] == setup["task"]["task_id"]
    assert first_session["started_at"] is not None
    assert first_session["last_activity_at"] is not None
    assert first_session["ended_at"] is None
    assert first_session["tab_switch_count"] == 0
    assert first_session["blocked_paste_count"] == 0
    assert first_session["run_attempt_count"] == 0
    assert first_session["idle_duration_seconds"] == 0
    assert first_session["last_blocked_paste_at"] is None
    assert "student_id" not in first_session

    resumed_response = start_coding_session(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
    )

    assert resumed_response.status_code == 201

    resumed_session = resumed_response.json()

    assert resumed_session["session_id"] == first_session["session_id"]
    assert resumed_session["started_at"] == first_session["started_at"]

    list_response = client.get(
        "/activities/coding-sessions/",
        headers=bearer_header(setup["student_token"]),
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["session_id"] == first_session["session_id"]

    filtered_response = client.get(
        "/activities/coding-sessions/",
        headers=bearer_header(setup["student_token"]),
        params={
            "task_id": setup["task"]["task_id"],
            "active_only": True,
        },
    )

    assert filtered_response.status_code == 200
    assert len(filtered_response.json()) == 1

    detail_response = client.get(
        (f"/activities/coding-sessions/{first_session['session_id']}"),
        headers=bearer_header(setup["student_token"]),
    )

    assert detail_response.status_code == 200
    assert detail_response.json()["session_id"] == first_session["session_id"]

    stored_sessions = (
        db_session.query(CodingSession)
        .filter(
            CodingSession.student_id == setup["student"].user_id,
            CodingSession.task_id == setup["task"]["task_id"],
        )
        .all()
    )

    assert len(stored_sessions) == 1


def test_session_activity_uses_aggregate_increments_only(
    client,
    db_session,
):
    setup = setup_coding_session_context(
        client,
        db_session,
        instructor_school_id="8100000002",
        instructor_email=("sessionfaculty2@pampangastateu.edu.ph"),
        student_school_id="8200000002",
        student_email=("sessionstudent2@pampangastateu.edu.ph"),
        task_title="Aggregate Telemetry Test",
    )

    start_response = start_coding_session(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
    )

    assert start_response.status_code == 201

    session_id = start_response.json()["session_id"]

    activity_response = update_coding_session(
        client,
        student_token=setup["student_token"],
        session_id=session_id,
        tab_switch_increment=3,
        blocked_paste_increment=2,
        idle_duration_increment_seconds=45,
    )

    assert activity_response.status_code == 200

    activity = activity_response.json()

    assert activity["tab_switch_count"] == 3
    assert activity["blocked_paste_count"] == 2
    assert activity["idle_duration_seconds"] == 45
    assert activity["run_attempt_count"] == 0
    assert activity["last_blocked_paste_at"] is not None
    assert activity["last_activity_at"] is not None

    first_blocked_timestamp = activity["last_blocked_paste_at"]

    heartbeat_response = update_coding_session(
        client,
        student_token=setup["student_token"],
        session_id=session_id,
    )

    assert heartbeat_response.status_code == 200

    heartbeat = heartbeat_response.json()

    assert heartbeat["tab_switch_count"] == 3
    assert heartbeat["blocked_paste_count"] == 2
    assert heartbeat["idle_duration_seconds"] == 45
    assert heartbeat["last_blocked_paste_at"] == first_blocked_timestamp

    prohibited_response = client.patch(
        (f"/activities/coding-sessions/{session_id}/activity"),
        headers=bearer_header(setup["student_token"]),
        json={
            "tab_switch_increment": 1,
            "run_attempt_count": 999,
            "clipboard_content": "secret text",
            "pasted_text": "copied source code",
            "keystrokes": ["p", "r", "i", "n", "t"],
            "browsing_history": ["https://example.invalid"],
            "screen_recording": "forbidden",
            "webcam": "forbidden",
            "microphone": "forbidden",
        },
    )

    assert prohibited_response.status_code == 422

    detail_response = client.get(
        (f"/activities/coding-sessions/{session_id}"),
        headers=bearer_header(setup["student_token"]),
    )

    assert detail_response.status_code == 200

    unchanged_session = detail_response.json()

    assert unchanged_session["tab_switch_count"] == 3
    assert unchanged_session["blocked_paste_count"] == 2
    assert unchanged_session["run_attempt_count"] == 0
    assert unchanged_session["idle_duration_seconds"] == 45

    response_text = str(unchanged_session).lower()

    for prohibited_field in {
        "clipboard_content",
        "pasted_text",
        "keystrokes",
        "browsing_history",
        "screen_recording",
        "webcam",
        "microphone",
        "behavior_score",
        "misconduct_verdict",
    }:
        assert prohibited_field not in response_text


def test_session_access_requires_available_task_and_owner(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Session Access Instructor",
        role="instructor",
        school_id="8100000003",
        email=("sessionfaculty3@pampangastateu.edu.ph"),
    )

    first_student = create_test_user(
        db_session,
        name="First Session Student",
        role="student",
        school_id="8200000003",
        email=("sessionstudent3@pampangastateu.edu.ph"),
    )

    second_student = create_test_user(
        db_session,
        name="Second Session Student",
        role="student",
        school_id="8200000004",
        email=("sessionstudent4@pampangastateu.edu.ph"),
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

    published_task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=classroom["class_id"],
        title="Published Session Activity",
    )

    draft_task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=classroom["class_id"],
        title="Draft Session Activity",
        publish=False,
    )

    draft_response = start_coding_session(
        client,
        student_token=first_token,
        task_id=draft_task["task_id"],
    )

    assert draft_response.status_code == 404

    unenrolled_response = start_coding_session(
        client,
        student_token=second_token,
        task_id=published_task["task_id"],
    )

    assert unenrolled_response.status_code == 404

    owner_response = start_coding_session(
        client,
        student_token=first_token,
        task_id=published_task["task_id"],
    )

    assert owner_response.status_code == 201

    session_id = owner_response.json()["session_id"]

    other_student_detail = client.get(
        (f"/activities/coding-sessions/{session_id}"),
        headers=bearer_header(second_token),
    )

    assert other_student_detail.status_code == 404

    other_student_update = update_coding_session(
        client,
        student_token=second_token,
        session_id=session_id,
        tab_switch_increment=1,
    )

    assert other_student_update.status_code == 404

    other_student_end = end_coding_session(
        client,
        student_token=second_token,
        session_id=session_id,
    )

    assert other_student_end.status_code == 404

    owner_detail = client.get(
        (f"/activities/coding-sessions/{session_id}"),
        headers=bearer_header(first_token),
    )

    assert owner_detail.status_code == 200
    assert owner_detail.json()["tab_switch_count"] == 0
    assert owner_detail.json()["ended_at"] is None


def test_ending_session_is_idempotent_and_blocks_activity(
    client,
    db_session,
):
    setup = setup_coding_session_context(
        client,
        db_session,
        instructor_school_id="8100000004",
        instructor_email=("sessionfaculty4@pampangastateu.edu.ph"),
        student_school_id="8200000005",
        student_email=("sessionstudent5@pampangastateu.edu.ph"),
        task_title="End Session Test",
    )

    start_response = start_coding_session(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
    )

    assert start_response.status_code == 201

    session_id = start_response.json()["session_id"]

    first_end_response = end_coding_session(
        client,
        student_token=setup["student_token"],
        session_id=session_id,
    )

    assert first_end_response.status_code == 200

    first_ended_session = first_end_response.json()

    assert first_ended_session["ended_at"] is not None
    assert first_ended_session["last_activity_at"] is not None

    second_end_response = end_coding_session(
        client,
        student_token=setup["student_token"],
        session_id=session_id,
    )

    assert second_end_response.status_code == 200
    assert second_end_response.json()["ended_at"] == first_ended_session["ended_at"]

    activity_response = update_coding_session(
        client,
        student_token=setup["student_token"],
        session_id=session_id,
        tab_switch_increment=1,
    )

    assert activity_response.status_code == 409

    run_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        request_kind="run",
        coding_session_id=session_id,
        source_code="print('ended session')\n",
    )

    assert run_response.status_code == 404

    active_list_response = client.get(
        "/activities/coding-sessions/",
        headers=bearer_header(setup["student_token"]),
        params={
            "active_only": True,
        },
    )

    assert active_list_response.status_code == 200
    assert active_list_response.json() == []

    all_sessions_response = client.get(
        "/activities/coding-sessions/",
        headers=bearer_header(setup["student_token"]),
    )

    assert all_sessions_response.status_code == 200
    assert len(all_sessions_response.json()) == 1
    assert (
        all_sessions_response.json()[0]["ended_at"] == first_ended_session["ended_at"]
    )


def test_execution_requests_increment_backend_session_counter(
    client,
    db_session,
):
    setup = setup_coding_session_context(
        client,
        db_session,
        instructor_school_id="8100000005",
        instructor_email=("sessionfaculty5@pampangastateu.edu.ph"),
        student_school_id="8200000006",
        student_email=("sessionstudent6@pampangastateu.edu.ph"),
        task_title="Execution Counter Test",
    )

    start_response = start_coding_session(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
    )

    assert start_response.status_code == 201

    session_id = start_response.json()["session_id"]

    run_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        request_kind="run",
        coding_session_id=session_id,
        source_code=("value = int(input())\nprint(value * 2)\n"),
    )

    assert run_response.status_code == 201

    after_run_response = client.get(
        (f"/activities/coding-sessions/{session_id}"),
        headers=bearer_header(setup["student_token"]),
    )

    assert after_run_response.status_code == 200
    assert after_run_response.json()["run_attempt_count"] == 1

    check_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        request_kind="check",
        coding_session_id=session_id,
        source_code=("def solve(value):\n    return value * 2\n"),
    )

    assert check_response.status_code == 201

    after_check_response = client.get(
        (f"/activities/coding-sessions/{session_id}"),
        headers=bearer_header(setup["student_token"]),
    )

    assert after_check_response.status_code == 200
    assert after_check_response.json()["run_attempt_count"] == 2

    submission_response = client.post(
        "/submissions/",
        headers=bearer_header(setup["student_token"]),
        json={
            "task_id": setup["task"]["task_id"],
            "coding_session_id": session_id,
            "raw_code": ("print('official submission')\n"),
            "standard_input": "",
        },
    )

    assert submission_response.status_code == 201

    submission = submission_response.json()

    end_response = end_coding_session(
        client,
        student_token=setup["student_token"],
        session_id=session_id,
    )

    assert end_response.status_code == 200

    submit_response = create_execution_request(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        request_kind="submit",
        submission_id=submission["sub_id"],
    )

    assert submit_response.status_code == 201
    assert submit_response.json()["coding_session_id"] == session_id
    assert submit_response.json()["source_code"] == submission["raw_code"]

    after_submit_response = client.get(
        (f"/activities/coding-sessions/{session_id}"),
        headers=bearer_header(setup["student_token"]),
    )

    assert after_submit_response.status_code == 200
    assert after_submit_response.json()["run_attempt_count"] == 3

    stored_session = db_session.get(
        CodingSession,
        session_id,
    )

    assert stored_session is not None

    db_session.refresh(stored_session)

    assert stored_session.run_attempt_count == 3

    forged_counter_response = client.patch(
        (f"/activities/coding-sessions/{session_id}/activity"),
        headers=bearer_header(setup["student_token"]),
        json={
            "run_attempt_count": 1000,
        },
    )

    assert forged_counter_response.status_code == 422

    db_session.refresh(stored_session)

    assert stored_session.run_attempt_count == 3


def test_instructor_can_review_only_owned_coding_sessions(
    client,
    db_session,
):
    setup = setup_coding_session_context(
        client,
        db_session,
        instructor_school_id="8100000006",
        instructor_email=("sessionfaculty6@pampangastateu.edu.ph"),
        student_school_id="8200000007",
        student_email=("sessionstudent7@pampangastateu.edu.ph"),
        task_title="Instructor Session Review",
    )

    other_instructor = create_test_user(
        db_session,
        name="Other Session Instructor",
        role="instructor",
        school_id="8100000007",
        email=("sessionfaculty7@pampangastateu.edu.ph"),
    )

    other_instructor_token = login_and_get_token(
        client,
        email=other_instructor.email,
    )

    start_response = start_coding_session(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
    )

    assert start_response.status_code == 201

    session_id = start_response.json()["session_id"]

    activity_response = update_coding_session(
        client,
        student_token=setup["student_token"],
        session_id=session_id,
        tab_switch_increment=4,
        blocked_paste_increment=1,
        idle_duration_increment_seconds=30,
    )

    assert activity_response.status_code == 200

    list_response = client.get(
        (f"/instructors/tasks/{setup['task']['task_id']}/coding-sessions"),
        headers=bearer_header(setup["instructor_token"]),
        params={
            "student_id": setup["student"].user_id,
            "active_only": True,
        },
    )

    assert list_response.status_code == 200

    listed_sessions = list_response.json()

    assert len(listed_sessions) == 1

    listed_session = listed_sessions[0]

    assert listed_session["session_id"] == session_id
    assert listed_session["student_id"] == setup["student"].user_id
    assert listed_session["tab_switch_count"] == 4
    assert listed_session["blocked_paste_count"] == 1
    assert listed_session["idle_duration_seconds"] == 30
    assert listed_session["last_blocked_paste_at"] is not None

    detail_response = client.get(
        (f"/instructors/coding-sessions/{session_id}"),
        headers=bearer_header(setup["instructor_token"]),
    )

    assert detail_response.status_code == 200

    detail = detail_response.json()

    assert detail["session_id"] == session_id
    assert detail["student_id"] == setup["student"].user_id

    prohibited_fields = {
        "clipboard_content",
        "pasted_text",
        "paste_content",
        "keystrokes",
        "browsing_history",
        "screen_recording",
        "webcam",
        "microphone",
        "behavior_score",
        "automatic_grade",
        "official_grade",
        "cheating_verdict",
        "misconduct_verdict",
    }

    assert prohibited_fields.isdisjoint(detail)

    unauthorized_list_response = client.get(
        (f"/instructors/tasks/{setup['task']['task_id']}/coding-sessions"),
        headers=bearer_header(other_instructor_token),
    )

    assert unauthorized_list_response.status_code == 403

    unauthorized_detail_response = client.get(
        (f"/instructors/coding-sessions/{session_id}"),
        headers=bearer_header(other_instructor_token),
    )

    assert unauthorized_detail_response.status_code == 403
