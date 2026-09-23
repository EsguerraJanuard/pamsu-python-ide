from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.domain_models import (
    CodingSession,
    Submission,
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
    name: str = "Programming Fundamentals",
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
    is_graded: bool = True,
    publish: bool = True,
) -> dict:
    create_response = client.post(
        "/instructors/tasks/",
        headers=bearer_header(instructor_token),
        json={
            "class_ids": [class_id],
            "title": title,
            "description": ("Submission workflow test activity."),
            "instructions": ("Write and submit a Python program."),
            "activity_type": "laboratory",
            "required_ast_rules": {},
            "starter_code": ("def solve():\n    pass\n"),
            "paste_policy": "internal_only",
            "is_graded": is_graded,
            "due_at": None,
        },
    )

    assert create_response.status_code == 201

    task = create_response.json()[0]

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


def setup_enrolled_student_and_task(
    client,
    db_session,
    *,
    instructor_school_id: str,
    instructor_email: str,
    student_school_id: str,
    student_email: str,
    task_title: str,
    is_graded: bool = True,
    publish: bool = True,
):
    instructor = create_test_user(
        db_session,
        name="Submission Instructor",
        role="instructor",
        school_id=instructor_school_id,
        email=instructor_email,
    )

    student = create_test_user(
        db_session,
        name="Submission Student",
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
        is_graded=is_graded,
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


def test_new_attempt_becomes_official_and_preserves_history(
    client,
    db_session,
):
    setup = setup_enrolled_student_and_task(
        client,
        db_session,
        instructor_school_id="6100000001",
        instructor_email=("submissionfaculty1@pampangastateu.edu.ph"),
        student_school_id="6200000001",
        student_email=("submissionstudent1@pampangastateu.edu.ph"),
        task_title="Official Attempt Test",
    )

    first_code = "number = int(input())\nprint(number * 2)\n"

    first_response = create_submission(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        raw_code=first_code,
        standard_input="5\n",
    )

    assert first_response.status_code == 201

    first_attempt = first_response.json()

    assert first_attempt["attempt_number"] == 1
    assert first_attempt["is_official"] is True
    assert first_attempt["status"] == "submitted"
    assert first_attempt["accepted_at"] is not None
    assert first_attempt["raw_code"] == first_code
    assert first_attempt["standard_input"] == "5\n"

    assert "student_id" not in first_attempt
    assert "jaccard_score" not in first_attempt
    assert "ast_pass_fail" not in first_attempt

    second_code = "number = int(input())\nresult = number * 3\nprint(result)\n"

    second_response = create_submission(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        raw_code=second_code,
        standard_input="7\n",
    )

    assert second_response.status_code == 201

    second_attempt = second_response.json()

    assert second_attempt["attempt_number"] == 2
    assert second_attempt["is_official"] is True
    assert second_attempt["raw_code"] == second_code

    db_session.expire_all()

    stored_attempts = (
        db_session.query(Submission)
        .filter(
            Submission.student_id == setup["student"].user_id,
            Submission.task_id == setup["task"]["task_id"],
        )
        .order_by(Submission.attempt_number.asc())
        .all()
    )

    assert len(stored_attempts) == 2

    assert stored_attempts[0].attempt_number == 1
    assert stored_attempts[0].is_official is False
    assert stored_attempts[0].raw_code == first_code
    assert stored_attempts[0].standard_input == "5\n"

    assert stored_attempts[1].attempt_number == 2
    assert stored_attempts[1].is_official is True
    assert stored_attempts[1].raw_code == second_code
    assert stored_attempts[1].standard_input == "7\n"

    official_response = client.get(
        (f"/submissions/official/{setup['task']['task_id']}"),
        headers=bearer_header(setup["student_token"]),
    )

    assert official_response.status_code == 200
    assert official_response.json()["sub_id"] == second_attempt["sub_id"]


def test_student_can_view_only_owned_submission_attempts(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Shared Class Instructor",
        role="instructor",
        school_id="6100000002",
        email=("submissionfaculty2@pampangastateu.edu.ph"),
    )

    first_student = create_test_user(
        db_session,
        name="First Student",
        role="student",
        school_id="6200000002",
        email=("submissionstudent2@pampangastateu.edu.ph"),
    )

    second_student = create_test_user(
        db_session,
        name="Second Student",
        role="student",
        school_id="6200000003",
        email=("submissionstudent3@pampangastateu.edu.ph"),
    )

    instructor_token = login_and_get_token(
        client,
        email=instructor.email,
    )

    first_student_token = login_and_get_token(
        client,
        email=first_student.email,
    )

    second_student_token = login_and_get_token(
        client,
        email=second_student.email,
    )

    classroom = create_classroom(
        client,
        instructor_token=instructor_token,
    )

    enroll_student(
        client,
        student_token=first_student_token,
        class_code=classroom["class_code"],
    )

    enroll_student(
        client,
        student_token=second_student_token,
        class_code=classroom["class_code"],
    )

    task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=classroom["class_id"],
        title="Submission Ownership Test",
    )

    first_submission_response = create_submission(
        client,
        student_token=first_student_token,
        task_id=task["task_id"],
        raw_code="print('first student')\n",
    )

    second_submission_response = create_submission(
        client,
        student_token=second_student_token,
        task_id=task["task_id"],
        raw_code="print('second student')\n",
    )

    assert first_submission_response.status_code == 201
    assert second_submission_response.status_code == 201

    first_submission = first_submission_response.json()
    second_submission = second_submission_response.json()

    list_response = client.get(
        "/submissions/",
        headers=bearer_header(first_student_token),
    )

    assert list_response.status_code == 200

    listed_submissions = list_response.json()

    assert len(listed_submissions) == 1
    assert listed_submissions[0]["sub_id"] == first_submission["sub_id"]

    own_detail_response = client.get(
        (f"/submissions/{first_submission['sub_id']}"),
        headers=bearer_header(first_student_token),
    )

    assert own_detail_response.status_code == 200

    other_detail_response = client.get(
        (f"/submissions/{second_submission['sub_id']}"),
        headers=bearer_header(first_student_token),
    )

    assert other_detail_response.status_code == 404


def test_student_submission_list_filters_by_task_and_official_state(
    client,
    db_session,
):
    setup = setup_enrolled_student_and_task(
        client,
        db_session,
        instructor_school_id="6100000003",
        instructor_email=("submissionfaculty3@pampangastateu.edu.ph"),
        student_school_id="6200000004",
        student_email=("submissionstudent4@pampangastateu.edu.ph"),
        task_title="Submission Filter Task One",
    )

    second_task = create_task(
        client,
        instructor_token=setup["instructor_token"],
        class_id=setup["classroom"]["class_id"],
        title="Submission Filter Task Two",
    )

    first_attempt = create_submission(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        raw_code="print('attempt one')\n",
    )

    second_attempt = create_submission(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        raw_code="print('attempt two')\n",
    )

    other_task_attempt = create_submission(
        client,
        student_token=setup["student_token"],
        task_id=second_task["task_id"],
        raw_code="print('other task')\n",
    )

    assert first_attempt.status_code == 201
    assert second_attempt.status_code == 201
    assert other_task_attempt.status_code == 201

    filtered_response = client.get(
        "/submissions/",
        headers=bearer_header(setup["student_token"]),
        params={
            "task_id": setup["task"]["task_id"],
            "official_only": True,
        },
    )

    assert filtered_response.status_code == 200

    filtered_attempts = filtered_response.json()

    assert len(filtered_attempts) == 1
    assert filtered_attempts[0]["sub_id"] == second_attempt.json()["sub_id"]
    assert filtered_attempts[0]["is_official"] is True

    status_response = client.get(
        "/submissions/",
        headers=bearer_header(setup["student_token"]),
        params={
            "status": "submitted",
        },
    )

    assert status_response.status_code == 200
    assert len(status_response.json()) == 3


def test_submission_requires_published_graded_active_enrollment(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Submission Access Instructor",
        role="instructor",
        school_id="6100000004",
        email=("submissionfaculty4@pampangastateu.edu.ph"),
    )

    enrolled_student = create_test_user(
        db_session,
        name="Enrolled Student",
        role="student",
        school_id="6200000005",
        email=("submissionstudent5@pampangastateu.edu.ph"),
    )

    unenrolled_student = create_test_user(
        db_session,
        name="Unenrolled Student",
        role="student",
        school_id="6200000006",
        email=("submissionstudent6@pampangastateu.edu.ph"),
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

    enroll_student(
        client,
        student_token=enrolled_token,
        class_code=classroom["class_code"],
    )

    draft_task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=classroom["class_id"],
        title="Draft Submission Task",
        publish=False,
    )

    draft_response = create_submission(
        client,
        student_token=enrolled_token,
        task_id=draft_task["task_id"],
        raw_code="print('draft')\n",
    )

    assert draft_response.status_code == 404

    ungraded_task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=classroom["class_id"],
        title="Ungraded Published Task",
        is_graded=False,
        publish=True,
    )

    ungraded_response = create_submission(
        client,
        student_token=enrolled_token,
        task_id=ungraded_task["task_id"],
        raw_code="print('ungraded')\n",
    )

    assert ungraded_response.status_code == 409

    graded_task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=classroom["class_id"],
        title="Published Graded Task",
    )

    unenrolled_response = create_submission(
        client,
        student_token=unenrolled_token,
        task_id=graded_task["task_id"],
        raw_code="print('unenrolled')\n",
    )

    assert unenrolled_response.status_code == 404

    deactivate_response = client.patch(
        (f"/classrooms/{classroom['class_id']}"),
        headers=bearer_header(instructor_token),
        json={
            "is_active": False,
        },
    )

    assert deactivate_response.status_code == 200

    inactive_class_response = create_submission(
        client,
        student_token=enrolled_token,
        task_id=graded_task["task_id"],
        raw_code="print('inactive class')\n",
    )

    assert inactive_class_response.status_code == 404


def test_disabled_enrollment_blocks_new_attempt_but_keeps_history(
    client,
    db_session,
):
    setup = setup_enrolled_student_and_task(
        client,
        db_session,
        instructor_school_id="6100000005",
        instructor_email=("submissionfaculty5@pampangastateu.edu.ph"),
        student_school_id="6200000007",
        student_email=("submissionstudent7@pampangastateu.edu.ph"),
        task_title="Enrollment History Test",
    )

    initial_response = create_submission(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        raw_code="print('saved history')\n",
    )

    assert initial_response.status_code == 201

    disable_response = client.patch(
        (f"/classrooms/enrollments/{setup['enrollment']['enrollment_id']}/status"),
        headers=bearer_header(setup["instructor_token"]),
        json={
            "status": "disabled",
        },
    )

    assert disable_response.status_code == 200

    blocked_response = create_submission(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        raw_code="print('blocked attempt')\n",
    )

    assert blocked_response.status_code == 404

    history_response = client.get(
        "/submissions/",
        headers=bearer_header(setup["student_token"]),
    )

    assert history_response.status_code == 200
    assert len(history_response.json()) == 1
    assert history_response.json()[0]["sub_id"] == initial_response.json()["sub_id"]


def test_instructor_can_review_only_owned_task_submissions(
    client,
    db_session,
):
    setup = setup_enrolled_student_and_task(
        client,
        db_session,
        instructor_school_id="6100000006",
        instructor_email=("submissionfaculty6@pampangastateu.edu.ph"),
        student_school_id="6200000008",
        student_email=("submissionstudent8@pampangastateu.edu.ph"),
        task_title="Instructor Review Test",
    )

    other_instructor = create_test_user(
        db_session,
        name="Other Instructor",
        role="instructor",
        school_id="6100000007",
        email=("submissionfaculty7@pampangastateu.edu.ph"),
    )

    other_instructor_token = login_and_get_token(
        client,
        email=other_instructor.email,
    )

    first_response = create_submission(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        raw_code="print('first review attempt')\n",
    )

    second_response = create_submission(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        raw_code="print('official review attempt')\n",
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    official_submission_id = second_response.json()["sub_id"]

    submission = db_session.get(
        Submission,
        official_submission_id,
    )

    assert submission is not None

    submission.jaccard_score = 72.5
    submission.ast_pass_fail = False

    db_session.commit()

    list_response = client.get(
        (f"/instructors/tasks/{setup['task']['task_id']}/submissions"),
        headers=bearer_header(setup["instructor_token"]),
        params={
            "official_only": True,
        },
    )

    assert list_response.status_code == 200

    submissions = list_response.json()

    assert len(submissions) == 1
    assert submissions[0]["sub_id"] == official_submission_id
    assert submissions[0]["student_id"] == setup["student"].user_id
    assert submissions[0]["jaccard_score"] == 72.5
    assert submissions[0]["ast_pass_fail"] is False

    detail_response = client.get(
        (f"/instructors/submissions/{official_submission_id}"),
        headers=bearer_header(setup["instructor_token"]),
    )

    assert detail_response.status_code == 200
    assert detail_response.json()["jaccard_score"] == 72.5

    unauthorized_list_response = client.get(
        (f"/instructors/tasks/{setup['task']['task_id']}/submissions"),
        headers=bearer_header(other_instructor_token),
    )

    assert unauthorized_list_response.status_code == 403

    unauthorized_detail_response = client.get(
        (f"/instructors/submissions/{official_submission_id}"),
        headers=bearer_header(other_instructor_token),
    )

    assert unauthorized_detail_response.status_code == 403


def test_submission_rejects_client_controlled_fields_and_invalid_session(
    client,
    db_session,
):
    setup = setup_enrolled_student_and_task(
        client,
        db_session,
        instructor_school_id="6100000008",
        instructor_email=("submissionfaculty8@pampangastateu.edu.ph"),
        student_school_id="6200000009",
        student_email=("submissionstudent9@pampangastateu.edu.ph"),
        task_title="Submission Security Test",
    )

    controlled_fields_response = client.post(
        "/submissions/",
        headers=bearer_header(setup["student_token"]),
        json={
            "task_id": setup["task"]["task_id"],
            "raw_code": "print('invalid fields')\n",
            "standard_input": "",
            "student_id": setup["student"].user_id,
            "attempt_number": 99,
            "status": "graded",
            "is_official": True,
            "accepted_at": ("2026-07-15T00:00:00Z"),
            "jaccard_score": 0,
            "ast_pass_fail": True,
        },
    )

    assert controlled_fields_response.status_code == 422

    malformed_uuid_response = create_submission(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        raw_code="print('bad uuid')\n",
        coding_session_id="not-a-valid-uuid",
    )

    assert malformed_uuid_response.status_code == 422

    missing_session_response = create_submission(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        raw_code="print('missing session')\n",
        coding_session_id=str(uuid4()),
    )

    assert missing_session_response.status_code == 404
    assert db_session.query(Submission).count() == 0


def test_coding_session_must_match_student_and_task(
    client,
    db_session,
):
    setup = setup_enrolled_student_and_task(
        client,
        db_session,
        instructor_school_id="6100000009",
        instructor_email=("submissionfaculty9@pampangastateu.edu.ph"),
        student_school_id="6200000010",
        student_email=("submissionstudent10@pampangastateu.edu.ph"),
        task_title="Coding Session Ownership Test",
    )

    other_student = create_test_user(
        db_session,
        name="Other Session Student",
        role="student",
        school_id="6200000011",
        email=("submissionstudent11@pampangastateu.edu.ph"),
    )

    valid_session_id = str(uuid4())

    valid_session = CodingSession(
        session_id=valid_session_id,
        student_id=setup["student"].user_id,
        task_id=setup["task"]["task_id"],
    )

    other_student_session_id = str(uuid4())

    other_student_session = CodingSession(
        session_id=other_student_session_id,
        student_id=other_student.user_id,
        task_id=setup["task"]["task_id"],
    )

    db_session.add_all(
        [
            valid_session,
            other_student_session,
        ]
    )
    db_session.commit()

    valid_response = create_submission(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        raw_code="print('valid session')\n",
        coding_session_id=valid_session_id,
    )

    assert valid_response.status_code == 201
    assert valid_response.json()["coding_session_id"] == valid_session_id

    wrong_owner_response = create_submission(
        client,
        student_token=setup["student_token"],
        task_id=setup["task"]["task_id"],
        raw_code="print('wrong owner')\n",
        coding_session_id=other_student_session_id,
    )

    assert wrong_owner_response.status_code == 404
