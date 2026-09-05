from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.domain_models import Task, User


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


def bearer_header(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }


def create_classroom(
    client,
    *,
    instructor_token: str,
) -> dict:
    response = client.post(
        "/classrooms/",
        headers=bearer_header(instructor_token),
        json={
            "name": "Paste Policy Verification",
            "subject_code": "RC-PST",
            "section": "BSIT RC",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_valid_task(
    client,
    *,
    instructor_token: str,
    class_id: int,
) -> dict:
    response = client.post(
        "/instructors/tasks/",
        headers=bearer_header(instructor_token),
        json={
            "class_ids": [class_id],
            "title": "Valid Paste Policy Activity",
            "description": "Release-candidate paste-policy verification.",
            "instructions": "Complete the required Python program.",
            "activity_type": "laboratory",
            "required_ast_rules": {},
            "starter_code": "def solve():\n    pass\n",
            "paste_policy": "internal_only",
            "is_graded": True,
            "due_at": None,
        },
    )

    assert response.status_code == 201

    return response.json()[0]


def test_unsupported_paste_policy_is_rejected_during_task_creation(
    client,
    db_session: Session,
) -> None:
    instructor = create_test_user(
        db_session,
        name="Paste Policy Instructor",
        role="instructor",
        school_id="3400000001",
        email="rc-paste-create@pampangastateu.edu.ph",
    )

    instructor_token = login_and_get_token(
        client,
        email=instructor.email,
    )

    classroom = create_classroom(
        client,
        instructor_token=instructor_token,
    )

    response = client.post(
        "/instructors/tasks/",
        headers=bearer_header(instructor_token),
        json={
            "class_ids": [classroom["class_id"]],
            "title": "Unsupported Paste Policy",
            "description": "This request must be rejected.",
            "instructions": "Do not create this activity.",
            "activity_type": "laboratory",
            "required_ast_rules": {},
            "starter_code": "",
            "paste_policy": "external_allowed",
            "is_graded": True,
            "due_at": None,
        },
    )

    assert response.status_code == 422
    assert db_session.query(Task).count() == 0


def test_unsupported_paste_policy_is_rejected_during_task_update(
    client,
    db_session: Session,
) -> None:
    instructor = create_test_user(
        db_session,
        name="Paste Policy Instructor",
        role="instructor",
        school_id="3400000002",
        email="rc-paste-update@pampangastateu.edu.ph",
    )

    instructor_token = login_and_get_token(
        client,
        email=instructor.email,
    )

    classroom = create_classroom(
        client,
        instructor_token=instructor_token,
    )

    task = create_valid_task(
        client,
        instructor_token=instructor_token,
        class_id=classroom["class_id"],
    )

    response = client.patch(
        f"/instructors/tasks/{task['task_id']}",
        headers=bearer_header(instructor_token),
        json={
            "paste_policy": "unrestricted",
        },
    )

    assert response.status_code == 422

    db_session.expire_all()

    stored_task = db_session.get(
        Task,
        task["task_id"],
    )

    assert stored_task is not None
    assert stored_task.paste_policy == "internal_only"
    assert db_session.query(Task).count() == 1
