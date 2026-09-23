from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.domain_models import (
    Task,
    TaskTestCase,
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


def future_due_at(
    *,
    days: int = 7,
) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def past_due_at() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()


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


def create_task(
    client,
    *,
    instructor_token: str,
    class_id: int,
    title: str = "Loops Laboratory",
    activity_type: str = "laboratory",
    due_at: str | None = None,
) -> dict:
    response = client.post(
        "/instructors/tasks/",
        headers=bearer_header(instructor_token),
        json={
            "class_ids": [class_id],
            "title": title,
            "description": "Activity description.",
            "instructions": "Complete the required Python program.",
            "activity_type": activity_type,
            "required_ast_rules": {},
            "starter_code": "def solve():\n    pass\n",
            "paste_policy": "internal_only",
            "is_graded": True,
            "due_at": due_at,
        },
    )

    assert response.status_code == 201

    return response.json()[0]


def publish_task(
    client,
    *,
    instructor_token: str,
    task_id: int,
) -> dict:
    response = client.patch(
        f"/instructors/tasks/{task_id}/publication",
        headers=bearer_header(instructor_token),
        json={
            "is_published": True,
        },
    )

    assert response.status_code == 200

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


def create_test_case(
    client,
    *,
    instructor_token: str,
    task_id: int,
    name: str,
    standard_input: str,
    expected_output: str,
    is_hidden: bool,
    display_order: int,
) -> dict:
    response = client.post(
        f"/instructors/tasks/{task_id}/test-cases",
        headers=bearer_header(instructor_token),
        json={
            "name": name,
            "standard_input": standard_input,
            "expected_output": expected_output,
            "is_hidden": is_hidden,
            "display_order": display_order,
        },
    )

    assert response.status_code == 201

    return response.json()


def test_instructor_can_create_update_filter_and_publish_tasks(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="3000000001",
        email="taskfaculty1@pampangastateu.edu.ph",
    )

    token = login_and_get_token(
        client,
        email=instructor.email,
    )

    classroom = create_classroom(
        client,
        instructor_token=token,
    )

    laboratory = create_task(
        client,
        instructor_token=token,
        class_id=classroom["class_id"],
        title="Loop Laboratory",
        activity_type="laboratory",
    )

    homework = create_task(
        client,
        instructor_token=token,
        class_id=classroom["class_id"],
        title="Function Homework",
        activity_type="homework",
        due_at=future_due_at(),
    )

    assert laboratory["activity_type"] == "laboratory"
    assert homework["activity_type"] == "homework"
    assert laboratory["is_published"] is False
    assert homework["is_published"] is False

    list_response = client.get(
        "/instructors/tasks/",
        headers=bearer_header(token),
        params={
            "class_id": classroom["class_id"],
            "activity_type": "homework",
        },
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["task_id"] == homework["task_id"]

    update_response = client.patch(
        f"/instructors/tasks/{homework['task_id']}",
        headers=bearer_header(token),
        json={
            "title": "Updated Function Homework",
            "paste_policy": "disabled",
            "required_ast_rules": {
                "require_function_def": True,
            },
        },
    )

    assert update_response.status_code == 200

    updated_task = update_response.json()

    assert updated_task["title"] == "Updated Function Homework"
    assert updated_task["paste_policy"] == "disabled"
    assert updated_task["required_ast_rules"] == {
        "require_function_def": True,
    }

    published_task = publish_task(
        client,
        instructor_token=token,
        task_id=homework["task_id"],
    )

    assert published_task["is_published"] is True
    assert published_task["published_at"] is not None

    stored_task = db_session.get(
        Task,
        homework["task_id"],
    )

    assert stored_task is not None
    assert stored_task.is_published is True


def test_instructor_cannot_create_task_in_another_classroom(
    client,
    db_session,
):
    owner = create_test_user(
        db_session,
        name="Class Owner",
        role="instructor",
        school_id="3000000002",
        email="taskfaculty2@pampangastateu.edu.ph",
    )

    other_instructor = create_test_user(
        db_session,
        name="Other Instructor",
        role="instructor",
        school_id="3000000003",
        email="taskfaculty3@pampangastateu.edu.ph",
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

    response = client.post(
        "/instructors/tasks/",
        headers=bearer_header(other_token),
        json={
            "class_ids": [classroom["class_id"]],
            "title": "Unauthorized Activity",
            "activity_type": "laboratory",
            "required_ast_rules": {},
            "starter_code": "",
            "paste_policy": "internal_only",
            "is_graded": True,
            "due_at": None,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You can only manage activities in your own classrooms."
    )


def test_publication_requires_active_class_and_future_deadline(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="3000000004",
        email="taskfaculty4@pampangastateu.edu.ph",
    )

    token = login_and_get_token(
        client,
        email=instructor.email,
    )

    classroom = create_classroom(
        client,
        instructor_token=token,
    )

    expired_task = create_task(
        client,
        instructor_token=token,
        class_id=classroom["class_id"],
        title="Expired Homework",
        activity_type="homework",
        due_at=past_due_at(),
    )

    expired_publish_response = client.patch(
        f"/instructors/tasks/{expired_task['task_id']}/publication",
        headers=bearer_header(token),
        json={
            "is_published": True,
        },
    )

    assert expired_publish_response.status_code == 409
    assert (
        expired_publish_response.json()["detail"]
        == "The task due date must be in the future."
    )

    valid_task = create_task(
        client,
        instructor_token=token,
        class_id=classroom["class_id"],
        title="Future Homework",
        activity_type="homework",
        due_at=future_due_at(),
    )

    deactivate_response = client.patch(
        f"/classrooms/{classroom['class_id']}",
        headers=bearer_header(token),
        json={
            "is_active": False,
        },
    )

    assert deactivate_response.status_code == 200

    inactive_publish_response = client.patch(
        f"/instructors/tasks/{valid_task['task_id']}/publication",
        headers=bearer_header(token),
        json={
            "is_published": True,
        },
    )

    assert inactive_publish_response.status_code == 409
    assert inactive_publish_response.json()["detail"] == (
        "Activities cannot be created or published inside an inactive classroom."
    )


def test_instructor_can_manage_public_and_hidden_test_cases(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="3000000005",
        email="taskfaculty5@pampangastateu.edu.ph",
    )

    token = login_and_get_token(
        client,
        email=instructor.email,
    )

    classroom = create_classroom(
        client,
        instructor_token=token,
    )

    task = create_task(
        client,
        instructor_token=token,
        class_id=classroom["class_id"],
    )

    public_case = create_test_case(
        client,
        instructor_token=token,
        task_id=task["task_id"],
        name="Public Sample",
        standard_input="5\n",
        expected_output="15\n",
        is_hidden=False,
        display_order=1,
    )

    hidden_case = create_test_case(
        client,
        instructor_token=token,
        task_id=task["task_id"],
        name="Hidden Edge Case",
        standard_input="100\n",
        expected_output="5050\n",
        is_hidden=True,
        display_order=2,
    )

    list_response = client.get(
        f"/instructors/tasks/{task['task_id']}/test-cases",
        headers=bearer_header(token),
    )

    assert list_response.status_code == 200

    test_cases = list_response.json()

    assert len(test_cases) == 2
    assert test_cases[0]["test_case_id"] == public_case["test_case_id"]
    assert test_cases[1]["test_case_id"] == hidden_case["test_case_id"]
    assert test_cases[1]["expected_output"] == "5050\n"
    assert test_cases[1]["is_hidden"] is True

    get_response = client.get(
        f"/instructors/test-cases/{hidden_case['test_case_id']}",
        headers=bearer_header(token),
    )

    assert get_response.status_code == 200
    assert get_response.json()["is_hidden"] is True

    update_response = client.patch(
        f"/instructors/test-cases/{hidden_case['test_case_id']}",
        headers=bearer_header(token),
        json={
            "name": "Updated Hidden Edge Case",
            "display_order": 0,
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Hidden Edge Case"
    assert update_response.json()["display_order"] == 0

    delete_response = client.delete(
        f"/instructors/test-cases/{public_case['test_case_id']}",
        headers=bearer_header(token),
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    assert (
        db_session.query(TaskTestCase)
        .filter(TaskTestCase.task_id == task["task_id"])
        .count()
        == 1
    )


def test_student_sees_only_published_tasks_from_active_enrollment(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="3000000006",
        email="taskfaculty6@pampangastateu.edu.ph",
    )

    student = create_test_user(
        db_session,
        name="Test Student",
        role="student",
        school_id="4000000001",
        email="taskstudent1@pampangastateu.edu.ph",
    )

    instructor_token = login_and_get_token(
        client,
        email=instructor.email,
    )

    student_token = login_and_get_token(
        client,
        email=student.email,
    )

    enrolled_classroom = create_classroom(
        client,
        instructor_token=instructor_token,
        name="Enrolled Classroom",
        section="BSIT 1A",
    )

    other_classroom = create_classroom(
        client,
        instructor_token=instructor_token,
        name="Other Classroom",
        subject_code="CCS102",
        section="BSIT 1B",
    )

    enroll_student(
        client,
        student_token=student_token,
        class_code=enrolled_classroom["class_code"],
    )

    available_task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=enrolled_classroom["class_id"],
        title="Available Laboratory",
    )

    draft_task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=enrolled_classroom["class_id"],
        title="Draft Laboratory",
    )

    unenrolled_task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=other_classroom["class_id"],
        title="Other Classroom Task",
    )

    publish_task(
        client,
        instructor_token=instructor_token,
        task_id=available_task["task_id"],
    )

    publish_task(
        client,
        instructor_token=instructor_token,
        task_id=unenrolled_task["task_id"],
    )

    list_response = client.get(
        "/activities/",
        headers=bearer_header(student_token),
    )

    assert list_response.status_code == 200

    activities = list_response.json()

    assert len(activities) == 1
    assert activities[0]["task_id"] == available_task["task_id"]
    assert "instructor_id" not in activities[0]

    detail_response = client.get(
        f"/activities/{available_task['task_id']}",
        headers=bearer_header(student_token),
    )

    assert detail_response.status_code == 200
    assert detail_response.json()["task_id"] == available_task["task_id"]
    assert "instructor_id" not in detail_response.json()

    draft_response = client.get(
        f"/activities/{draft_task['task_id']}",
        headers=bearer_header(student_token),
    )

    assert draft_response.status_code == 404

    unenrolled_response = client.get(
        f"/activities/{unenrolled_task['task_id']}",
        headers=bearer_header(student_token),
    )

    assert unenrolled_response.status_code == 404


def test_student_sample_test_cases_exclude_hidden_cases(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="3000000007",
        email="taskfaculty7@pampangastateu.edu.ph",
    )

    student = create_test_user(
        db_session,
        name="Test Student",
        role="student",
        school_id="4000000002",
        email="taskstudent2@pampangastateu.edu.ph",
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

    enroll_student(
        client,
        student_token=student_token,
        class_code=classroom["class_code"],
    )

    task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=classroom["class_id"],
    )

    create_test_case(
        client,
        instructor_token=instructor_token,
        task_id=task["task_id"],
        name="Visible Sample",
        standard_input="2\n",
        expected_output="4\n",
        is_hidden=False,
        display_order=0,
    )

    create_test_case(
        client,
        instructor_token=instructor_token,
        task_id=task["task_id"],
        name="Secret Grading Case",
        standard_input="999\n",
        expected_output="1998\n",
        is_hidden=True,
        display_order=1,
    )

    publish_task(
        client,
        instructor_token=instructor_token,
        task_id=task["task_id"],
    )

    response = client.get(
        f"/activities/{task['task_id']}/sample-test-cases",
        headers=bearer_header(student_token),
    )

    assert response.status_code == 200

    sample_cases = response.json()

    assert len(sample_cases) == 1
    assert sample_cases[0]["name"] == "Visible Sample"
    assert sample_cases[0]["expected_output"] == "4\n"
    assert "is_hidden" not in sample_cases[0]
    assert "task_id" not in sample_cases[0]
    assert "Secret Grading Case" not in str(sample_cases)
    assert "1998" not in str(sample_cases)


def test_disabled_and_removed_enrollment_blocks_task_access(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="3000000008",
        email="taskfaculty8@pampangastateu.edu.ph",
    )

    student = create_test_user(
        db_session,
        name="Test Student",
        role="student",
        school_id="4000000003",
        email="taskstudent3@pampangastateu.edu.ph",
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
    )

    publish_task(
        client,
        instructor_token=instructor_token,
        task_id=task["task_id"],
    )

    disable_response = client.patch(
        (f"/classrooms/enrollments/{enrollment['enrollment_id']}/status"),
        headers=bearer_header(instructor_token),
        json={
            "status": "disabled",
        },
    )

    assert disable_response.status_code == 200

    disabled_list = client.get(
        "/activities/",
        headers=bearer_header(student_token),
    )

    assert disabled_list.status_code == 200
    assert disabled_list.json() == []

    disabled_detail = client.get(
        f"/activities/{task['task_id']}",
        headers=bearer_header(student_token),
    )

    assert disabled_detail.status_code == 404

    reactivate_response = client.patch(
        (f"/classrooms/enrollments/{enrollment['enrollment_id']}/status"),
        headers=bearer_header(instructor_token),
        json={
            "status": "active",
        },
    )

    assert reactivate_response.status_code == 200

    active_list = client.get(
        "/activities/",
        headers=bearer_header(student_token),
    )

    assert active_list.status_code == 200
    assert len(active_list.json()) == 1

    remove_response = client.patch(
        (f"/classrooms/enrollments/{enrollment['enrollment_id']}/status"),
        headers=bearer_header(instructor_token),
        json={
            "status": "removed",
        },
    )

    assert remove_response.status_code == 200

    removed_list = client.get(
        "/activities/",
        headers=bearer_header(student_token),
    )

    assert removed_list.status_code == 200
    assert removed_list.json() == []


def test_inactive_classroom_blocks_student_task_access(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="3000000009",
        email="taskfaculty9@pampangastateu.edu.ph",
    )

    student = create_test_user(
        db_session,
        name="Test Student",
        role="student",
        school_id="4000000004",
        email="taskstudent4@pampangastateu.edu.ph",
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

    enroll_student(
        client,
        student_token=student_token,
        class_code=classroom["class_code"],
    )

    task = create_task(
        client,
        instructor_token=instructor_token,
        class_id=classroom["class_id"],
    )

    publish_task(
        client,
        instructor_token=instructor_token,
        task_id=task["task_id"],
    )

    deactivate_response = client.patch(
        f"/classrooms/{classroom['class_id']}",
        headers=bearer_header(instructor_token),
        json={
            "is_active": False,
        },
    )

    assert deactivate_response.status_code == 200

    list_response = client.get(
        "/activities/",
        headers=bearer_header(student_token),
    )

    assert list_response.status_code == 200
    assert list_response.json() == []

    detail_response = client.get(
        f"/activities/{task['task_id']}",
        headers=bearer_header(student_token),
    )

    assert detail_response.status_code == 404


def test_clients_cannot_supply_backend_task_fields(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="3000000010",
        email="taskfaculty10@pampangastateu.edu.ph",
    )

    token = login_and_get_token(
        client,
        email=instructor.email,
    )

    classroom = create_classroom(
        client,
        instructor_token=token,
    )

    invalid_task_response = client.post(
        "/instructors/tasks/",
        headers=bearer_header(token),
        json={
            "class_ids": [classroom["class_id"]],
            "title": "Invalid Task",
            "activity_type": "laboratory",
            "required_ast_rules": {},
            "starter_code": "",
            "paste_policy": "internal_only",
            "is_graded": True,
            "due_at": None,
            "instructor_id": instructor.user_id,
            "is_published": True,
            "published_at": future_due_at(),
        },
    )

    assert invalid_task_response.status_code == 422
    assert db_session.query(Task).count() == 0

    valid_task = create_task(
        client,
        instructor_token=token,
        class_id=classroom["class_id"],
    )

    invalid_test_case_response = client.post(
        f"/instructors/tasks/{valid_task['task_id']}/test-cases",
        headers=bearer_header(token),
        json={
            "task_id": valid_task["task_id"],
            "name": "Invalid Test Case",
            "standard_input": "",
            "expected_output": "OK\n",
            "is_hidden": False,
            "display_order": 0,
        },
    )

    assert invalid_test_case_response.status_code == 422
    assert db_session.query(TaskTestCase).count() == 0
