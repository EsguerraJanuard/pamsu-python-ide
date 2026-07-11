from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.domain_models import Submission, User


TEST_PASSWORD = "test12345"


def create_test_user(
    db: Session,
    name: str,
    role: str,
) -> User:
    user = User(
        name=name,
        role=role,
        password_hash=get_password_hash(TEST_PASSWORD),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def login_and_get_token(
    client,
    user_id: int,
    password: str = TEST_PASSWORD,
) -> str:
    response = client.post(
        "/login",
        data={
            "username": str(user_id),
            "password": password,
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["token_type"] == "bearer"
    assert response_data["access_token"]

    return response_data["access_token"]


def bearer_header(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }


def test_login_rejects_wrong_password(client, db_session):
    user = create_test_user(
        db=db_session,
        name="Test Student",
        role="student",
    )

    response = client.post(
        "/login",
        data={
            "username": str(user.user_id),
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid login credentials."


def test_protected_route_requires_token(client):
    response = client.get("/instructors/tasks/1")

    assert response.status_code == 401


def test_student_cannot_create_instructor_task(client, db_session):
    student = create_test_user(
        db=db_session,
        name="Test Student",
        role="student",
    )

    student_token = login_and_get_token(
        client=client,
        user_id=student.user_id,
    )

    response = client.post(
        "/instructors/tasks/",
        headers=bearer_header(student_token),
        json={
            "title": "Unauthorized Task",
            "required_ast_rules": {
                "require_for_loop": True,
            },
            "instructor_id": student.user_id,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Instructor access required."


def test_complete_evaluation_workflow(client, db_session):
    instructor = create_test_user(
        db=db_session,
        name="Test Instructor",
        role="instructor",
    )

    student = create_test_user(
        db=db_session,
        name="Test Student",
        role="student",
    )

    instructor_token = login_and_get_token(
        client=client,
        user_id=instructor.user_id,
    )

    student_token = login_and_get_token(
        client=client,
        user_id=student.user_id,
    )

    instructor_headers = bearer_header(instructor_token)
    student_headers = bearer_header(student_token)

    task_response = client.post(
        "/instructors/tasks/",
        headers=instructor_headers,
        json={
            "title": "For Loop and Function Activity",
            "required_ast_rules": {
                "require_for_loop": True,
                "require_while_loop": False,
                "require_function_def": True,
            },
            "instructor_id": instructor.user_id,
        },
    )

    assert task_response.status_code == 201

    task_data = task_response.json()
    task_id = task_data["task_id"]

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
            "raw_code": (
                "def solve():\n"
                "    for number in range(5):\n"
                "        print(number)\n"
                "\n"
                "solve()"
            ),
            "student_id": student.user_id,
            "task_id": task_id,
        },
    )

    assert submission_response.status_code == 201

    submission_data = submission_response.json()
    sub_id = submission_data["sub_id"]

    assert submission_data["ast_pass_fail"] is None
    assert submission_data["jaccard_score"] is None

    log_response = client.post(
        "/logs/behavioral/",
        headers=student_headers,
        json={
            "sub_id": sub_id,
            "tab_switches_count": 3,
        },
    )

    assert log_response.status_code == 201

    log_data = log_response.json()

    assert log_data["sub_id"] == sub_id
    assert log_data["tab_switches_count"] == 3

    get_log_response = client.get(
        f"/logs/behavioral/{log_data['log_id']}",
        headers=instructor_headers,
    )

    assert get_log_response.status_code == 200

    evaluation_response = client.post(
        f"/evaluation/submissions/{sub_id}",
        headers=student_headers,
    )

    assert evaluation_response.status_code == 200

    evaluation_data = evaluation_response.json()

    assert evaluation_data["sub_id"] == sub_id
    assert evaluation_data["ast_pass_fail"] is True
    assert evaluation_data["jaccard_score"] == 0.0
    assert evaluation_data["highest_match_sub_id"] is None
    assert evaluation_data["ast_details"]["passed"] is True

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
