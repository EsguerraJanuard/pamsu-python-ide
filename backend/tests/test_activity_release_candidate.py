from datetime import datetime, timedelta, timezone

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


def future_due_at() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()


def create_classroom(
    client,
    *,
    instructor_token: str,
) -> dict:
    response = client.post(
        "/classrooms/",
        headers=bearer_header(instructor_token),
        json={
            "name": "Release Candidate Activities",
            "subject_code": "RC-ACT",
            "section": "BSIT RC",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_task(
    client,
    *,
    instructor_token: str,
    class_id: int,
    title: str = "Release Candidate Laboratory",
) -> dict:
    response = client.post(
        "/instructors/tasks/",
        headers=bearer_header(instructor_token),
        json={
            "class_ids": [class_id],
            "title": title,
            "description": "Release-candidate activity.",
            "instructions": "Complete the required Python program.",
            "activity_type": "laboratory",
            "required_ast_rules": {},
            "starter_code": "def solve():\n    pass\n",
            "paste_policy": "internal_only",
            "is_graded": True,
            "due_at": future_due_at(),
        },
    )

    assert response.status_code == 201

    return response.json()[0]


def test_unsupported_activity_type_is_rejected(
    client,
    db_session: Session,
) -> None:
    instructor = create_test_user(
        db_session,
        name="Activity Owner",
        role="instructor",
        school_id="3300000001",
        email="rc-activity-owner@pampangastateu.edu.ph",
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
            "title": "Unsupported Activity",
            "description": "This activity type is not approved.",
            "instructions": "This request must be rejected.",
            "activity_type": "quiz",
            "required_ast_rules": {},
            "starter_code": "",
            "paste_policy": "internal_only",
            "is_graded": True,
            "due_at": future_due_at(),
        },
    )

    assert response.status_code == 422
    assert db_session.query(Task).count() == 0


def test_non_owner_cannot_update_or_publish_task(
    client,
    db_session: Session,
) -> None:
    owner = create_test_user(
        db_session,
        name="Activity Owner",
        role="instructor",
        school_id="3300000002",
        email="rc-task-owner@pampangastateu.edu.ph",
    )

    other_instructor = create_test_user(
        db_session,
        name="Other Instructor",
        role="instructor",
        school_id="3300000003",
        email="rc-task-other@pampangastateu.edu.ph",
    )

    owner_token = login_and_get_token(
        client,
        email=owner.email,
    )

    other_token = login_and_get_token(
        client,
        email=other_instructor.email,
    )

    classroom = create_classroom(
        client,
        instructor_token=owner_token,
    )

    task = create_task(
        client,
        instructor_token=owner_token,
        class_id=classroom["class_id"],
    )

    update_response = client.patch(
        f"/instructors/tasks/{task['task_id']}",
        headers=bearer_header(other_token),
        json={
            "title": "Unauthorized Task Update",
            "paste_policy": "disabled",
        },
    )

    assert update_response.status_code == 403

    publish_response = client.patch(
        f"/instructors/tasks/{task['task_id']}/publication",
        headers=bearer_header(other_token),
        json={
            "is_published": True,
        },
    )

    assert publish_response.status_code == 403

    db_session.expire_all()

    stored_task = db_session.get(
        Task,
        task["task_id"],
    )

    assert stored_task is not None
    assert stored_task.instructor_id == owner.user_id
    assert stored_task.title == "Release Candidate Laboratory"
    assert stored_task.paste_policy == "internal_only"
    assert stored_task.is_published is False
    assert stored_task.published_at is None


def test_non_owner_cannot_unpublish_task(
    client,
    db_session: Session,
) -> None:
    owner = create_test_user(
        db_session,
        name="Published Activity Owner",
        role="instructor",
        school_id="3300000004",
        email="rc-published-owner@pampangastateu.edu.ph",
    )

    other_instructor = create_test_user(
        db_session,
        name="Other Instructor",
        role="instructor",
        school_id="3300000005",
        email="rc-published-other@pampangastateu.edu.ph",
    )

    owner_token = login_and_get_token(
        client,
        email=owner.email,
    )

    other_token = login_and_get_token(
        client,
        email=other_instructor.email,
    )

    classroom = create_classroom(
        client,
        instructor_token=owner_token,
    )

    task = create_task(
        client,
        instructor_token=owner_token,
        class_id=classroom["class_id"],
        title="Published Release Candidate Activity",
    )

    owner_publish_response = client.patch(
        f"/instructors/tasks/{task['task_id']}/publication",
        headers=bearer_header(owner_token),
        json={
            "is_published": True,
        },
    )

    assert owner_publish_response.status_code == 200
    assert owner_publish_response.json()["is_published"] is True

    unauthorized_unpublish_response = client.patch(
        f"/instructors/tasks/{task['task_id']}/publication",
        headers=bearer_header(other_token),
        json={
            "is_published": False,
        },
    )

    assert unauthorized_unpublish_response.status_code == 403

    db_session.expire_all()

    stored_task = db_session.get(
        Task,
        task["task_id"],
    )

    assert stored_task is not None
    assert stored_task.instructor_id == owner.user_id
    assert stored_task.is_published is True
    assert stored_task.published_at is not None
