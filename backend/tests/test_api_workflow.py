from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.domain_models import (
    Classroom,
    Enrollment,
    Submission,
    User,
)


TEST_PASSWORD = "test12345"


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
        school_id=school_id,
        email=email.lower(),
        role=role,
        password_hash=get_password_hash(TEST_PASSWORD),
        email_verified=True,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_test_classroom(
    db: Session,
    *,
    instructor_id: int,
) -> Classroom:
    classroom = Classroom(
        instructor_id=instructor_id,
        name="Programming Fundamentals",
        subject_code="CCS101",
        section="BSIT 1A",
        class_code="TESTCLASS01",
        is_active=True,
    )

    db.add(classroom)
    db.commit()
    db.refresh(classroom)

    return classroom


def enroll_student(
    db: Session,
    *,
    class_id: int,
    student_id: int,
) -> Enrollment:
    enrollment = Enrollment(
        class_id=class_id,
        student_id=student_id,
        status="active",
    )

    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    return enrollment


def login_and_get_token(
    client,
    *,
    email: str,
    password: str = TEST_PASSWORD,
) -> str:
    response = client.post(
        "/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["token_type"] == "bearer"
    assert response_data["access_token"]
    assert response_data["expires_in"] > 0
    assert response_data["user"]["email"] == email.lower()

    return response_data["access_token"]


def bearer_header(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }


def test_login_rejects_wrong_password(
    client,
    db_session,
):
    user = create_test_user(
        db_session,
        name="Test Student",
        role="student",
        school_id="0000000001",
        email="student1@pampangastateu.edu.ph",
    )

    response = client.post(
        "/login",
        data={
            "username": user.email,
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_protected_route_requires_token(client):
    response = client.get("/instructors/tasks/1")

    assert response.status_code == 401


def test_student_cannot_create_instructor_task(
    client,
    db_session,
):
    student = create_test_user(
        db_session,
        name="Test Student",
        role="student",
        school_id="0000000002",
        email="student2@pampangastateu.edu.ph",
    )

    student_token = login_and_get_token(
        client,
        email=student.email,
    )

    response = client.post(
        "/instructors/tasks/",
        headers=bearer_header(student_token),
        json={
            "class_ids": [1],
            "title": "Unauthorized Task",
            "activity_type": "laboratory",
            "required_ast_rules": {
                "require_for_loop": True,
            },
            "starter_code": "",
            "paste_policy": "internal_only",
            "is_graded": True,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Instructor access required."


def test_complete_evaluation_workflow(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="0000000003",
        email="instructor@pampangastateu.edu.ph",
    )

    student = create_test_user(
        db_session,
        name="Test Student",
        role="student",
        school_id="0000000004",
        email="student3@pampangastateu.edu.ph",
    )

    classroom = create_test_classroom(
        db_session,
        instructor_id=instructor.user_id,
    )

    enroll_student(
        db_session,
        class_id=classroom.class_id,
        student_id=student.user_id,
    )

    instructor_token = login_and_get_token(
        client,
        email=instructor.email,
    )

    student_token = login_and_get_token(
        client,
        email=student.email,
    )

    instructor_headers = bearer_header(instructor_token)
    student_headers = bearer_header(student_token)

    task_response = client.post(
        "/instructors/tasks/",
        headers=instructor_headers,
        json={
            "class_ids": [classroom.class_id],
            "title": "For Loop and Function Activity",
            "description": ("Create a function that prints numbers using a for loop."),
            "instructions": ("Define solve(), use a for loop, and call the function."),
            "activity_type": "laboratory",
            "required_ast_rules": {
                "require_for_loop": True,
                "require_while_loop": False,
                "require_function_def": True,
            },
            "starter_code": "",
            "paste_policy": "internal_only",
            "is_graded": True,
            "due_at": None,
        },
    )

    assert task_response.status_code == 201

    task_data = task_response.json()[0]
    task_id = task_data["task_id"]

    assert task_data["instructor_id"] == instructor.user_id
    assert task_data["class_id"] == classroom.class_id
    assert task_data["is_published"] is False

    publication_response = client.patch(
        f"/instructors/tasks/{task_id}/publication",
        headers=instructor_headers,
        json={
            "is_published": True,
        },
    )

    assert publication_response.status_code == 200
    assert publication_response.json()["is_published"] is True

    get_task_response = client.get(
        f"/instructors/tasks/{task_id}",
        headers=instructor_headers,
    )

    assert get_task_response.status_code == 200
    assert get_task_response.json()["task_id"] == task_id

    submission_response = client.post(
        "/execution/submissions/",
        headers=student_headers,
        json={
            "task_id": task_id,
            "raw_code": (
                "def solve():\n"
                "    for number in range(5):\n"
                "        print(number)\n"
                "\n"
                "solve()"
            ),
            "standard_input": "",
        },
    )

    assert submission_response.status_code == 201

    submission_data = submission_response.json()
    sub_id = submission_data["sub_id"]

    assert submission_data["student_id"] == student.user_id
    assert submission_data["attempt_number"] == 1
    assert submission_data["is_official"] is True
    assert submission_data["status"] == "awaiting_review"
    assert submission_data["ast_pass_fail"] is None
    assert submission_data["jaccard_score"] is None

    log_response = client.post(
        "/logs/behavioral/",
        headers=student_headers,
        json={
            "sub_id": sub_id,
            "tab_switches_count": 3,
            "blocked_paste_count": 1,
            "run_attempt_count": 2,
            "idle_duration_seconds": 30,
            "last_blocked_paste_at": None,
        },
    )

    assert log_response.status_code == 201

    log_data = log_response.json()

    assert log_data["sub_id"] == sub_id
    assert log_data["tab_switches_count"] == 3
    assert log_data["blocked_paste_count"] == 1
    assert log_data["run_attempt_count"] == 2
    assert log_data["idle_duration_seconds"] == 30

    get_log_response = client.get(
        f"/logs/behavioral/{log_data['log_id']}",
        headers=instructor_headers,
    )

    assert get_log_response.status_code == 200

    evaluation_response = client.post(
        f"/evaluation/submissions/{sub_id}",
        headers=instructor_headers,
    )

    assert evaluation_response.status_code == 200

    evaluation_data = evaluation_response.json()

    assert evaluation_data["sub_id"] == sub_id
    assert evaluation_data["ast_pass_fail"] is True
    assert evaluation_data["jaccard_score"] == 0.0
    assert evaluation_data["highest_match_sub_id"] is None
    assert evaluation_data["ast_details"]["passed"] is True
    assert "review indicators only" in (evaluation_data["review_notice"])

    get_submission_response = client.get(
        f"/execution/submissions/{sub_id}",
        headers=student_headers,
    )

    assert get_submission_response.status_code == 200
    assert get_submission_response.json()["ast_pass_fail"] is True
    assert get_submission_response.json()["jaccard_score"] == 0.0

    db_session.expire_all()

    stored_submission = (
        db_session.query(Submission).filter(Submission.sub_id == sub_id).first()
    )

    assert stored_submission is not None
    assert stored_submission.ast_pass_fail is True
    assert stored_submission.jaccard_score == 0.0
