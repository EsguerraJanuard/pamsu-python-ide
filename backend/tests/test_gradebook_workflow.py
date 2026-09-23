from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import (
    get_current_instructor,
    get_current_student,
)
from app.main import app
from app.models.domain_models import (
    Classroom,
    InstructorGrade,
    Submission,
    Task,
    User,
)


@pytest.fixture
def gradebook_instructor(
    db_session: Session,
) -> User:
    instructor = User(
        name="Gradebook Instructor",
        school_id="6100000001",
        email=("gradebook.instructor@pampangastateu.edu.ph"),
        role="instructor",
        password_hash="fakehash",
        email_verified=True,
        is_active=True,
    )

    db_session.add(instructor)
    db_session.commit()
    db_session.refresh(instructor)

    return instructor


@pytest.fixture
def other_gradebook_instructor(
    db_session: Session,
) -> User:
    instructor = User(
        name="Other Gradebook Instructor",
        school_id="6100000002",
        email=("other.gradebook.instructor@pampangastateu.edu.ph"),
        role="instructor",
        password_hash="fakehash",
        email_verified=True,
        is_active=True,
    )

    db_session.add(instructor)
    db_session.commit()
    db_session.refresh(instructor)

    return instructor


@pytest.fixture
def gradebook_student_one(
    db_session: Session,
) -> User:
    student = User(
        name="Alice Gradebook Student",
        school_id="6200000001",
        email=("alice.gradebook.student@pampangastateu.edu.ph"),
        role="student",
        password_hash="fakehash",
        email_verified=True,
        is_active=True,
    )

    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    return student


@pytest.fixture
def gradebook_student_two(
    db_session: Session,
) -> User:
    student = User(
        name="Bob Gradebook Student",
        school_id="6200000002",
        email=("bob.gradebook.student@pampangastateu.edu.ph"),
        role="student",
        password_hash="fakehash",
        email_verified=True,
        is_active=True,
    )

    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    return student


@pytest.fixture
def gradebook_data(
    db_session: Session,
    gradebook_instructor: User,
    other_gradebook_instructor: User,
    gradebook_student_one: User,
    gradebook_student_two: User,
) -> dict[str, object]:
    now = datetime.now(timezone.utc)

    class_one = Classroom(
        instructor_id=gradebook_instructor.user_id,
        name="Gradebook Programming One",
        subject_code="GB101",
        section="A",
        class_code="GRADE001",
        is_active=True,
    )

    class_two = Classroom(
        instructor_id=gradebook_instructor.user_id,
        name="Gradebook Programming Two",
        subject_code="GB102",
        section="B",
        class_code="GRADE002",
        is_active=True,
    )

    other_class = Classroom(
        instructor_id=(other_gradebook_instructor.user_id),
        name="Other Gradebook Class",
        subject_code="GB999",
        section="Z",
        class_code="GRADE999",
        is_active=True,
    )

    db_session.add_all(
        [
            class_one,
            class_two,
            other_class,
        ]
    )
    db_session.commit()

    task_one = Task(
        instructor_id=gradebook_instructor.user_id,
        class_id=class_one.class_id,
        title="Gradebook Loops Laboratory",
        activity_type="laboratory",
        required_ast_rules={},
        is_graded=True,
        is_published=True,
    )

    task_two = Task(
        instructor_id=gradebook_instructor.user_id,
        class_id=class_two.class_id,
        title="Gradebook Functions Homework",
        activity_type="homework",
        required_ast_rules={},
        is_graded=True,
        is_published=True,
    )

    other_task = Task(
        instructor_id=(other_gradebook_instructor.user_id),
        class_id=other_class.class_id,
        title="Other Instructor Gradebook Task",
        activity_type="laboratory",
        required_ast_rules={},
        is_graded=True,
        is_published=True,
    )

    db_session.add_all(
        [
            task_one,
            task_two,
            other_task,
        ]
    )
    db_session.commit()

    released_submission = Submission(
        student_id=gradebook_student_one.user_id,
        task_id=task_one.task_id,
        raw_code="print('released official')",
        attempt_number=2,
        status="graded",
        is_official=True,
        submitted_at=now - timedelta(days=4),
        accepted_at=now - timedelta(days=4),
    )

    unreleased_submission = Submission(
        student_id=gradebook_student_two.user_id,
        task_id=task_one.task_id,
        raw_code="print('unreleased official')",
        attempt_number=1,
        status="awaiting_review",
        is_official=True,
        submitted_at=now - timedelta(days=3),
        accepted_at=now - timedelta(days=3),
    )

    ungraded_submission = Submission(
        student_id=gradebook_student_one.user_id,
        task_id=task_two.task_id,
        raw_code="print('no grade')",
        attempt_number=1,
        status="submitted",
        is_official=True,
        submitted_at=now - timedelta(days=2),
        accepted_at=now - timedelta(days=2),
    )

    historical_submission = Submission(
        student_id=gradebook_student_one.user_id,
        task_id=task_one.task_id,
        raw_code="print('historical released')",
        attempt_number=1,
        status="graded",
        is_official=False,
        submitted_at=now - timedelta(days=5),
        accepted_at=now - timedelta(days=5),
    )

    other_submission = Submission(
        student_id=gradebook_student_two.user_id,
        task_id=other_task.task_id,
        raw_code="print('other instructor')",
        attempt_number=1,
        status="graded",
        is_official=True,
        submitted_at=now - timedelta(days=1),
        accepted_at=now - timedelta(days=1),
    )

    db_session.add_all(
        [
            released_submission,
            unreleased_submission,
            ungraded_submission,
            historical_submission,
            other_submission,
        ]
    )
    db_session.commit()

    released_grade = InstructorGrade(
        submission_id=released_submission.sub_id,
        instructor_id=gradebook_instructor.user_id,
        score=90,
        max_score=100,
        feedback="Released official feedback.",
        is_released=True,
    )

    unreleased_grade = InstructorGrade(
        submission_id=unreleased_submission.sub_id,
        instructor_id=gradebook_instructor.user_id,
        score=80,
        max_score=100,
        feedback="Private draft feedback.",
        is_released=False,
    )

    historical_grade = InstructorGrade(
        submission_id=historical_submission.sub_id,
        instructor_id=gradebook_instructor.user_id,
        score=70,
        max_score=100,
        feedback="Historical released feedback.",
        is_released=True,
    )

    other_grade = InstructorGrade(
        submission_id=other_submission.sub_id,
        instructor_id=(other_gradebook_instructor.user_id),
        score=95,
        max_score=100,
        feedback="Other instructor feedback.",
        is_released=True,
    )

    db_session.add_all(
        [
            released_grade,
            unreleased_grade,
            historical_grade,
            other_grade,
        ]
    )
    db_session.commit()

    return {
        "class_one": class_one,
        "class_two": class_two,
        "other_class": other_class,
        "task_one": task_one,
        "task_two": task_two,
        "other_task": other_task,
        "released_submission": released_submission,
        "unreleased_submission": (unreleased_submission),
        "ungraded_submission": ungraded_submission,
        "historical_submission": (historical_submission),
        "other_submission": other_submission,
    }


@pytest.fixture
def gradebook_client(
    client: TestClient,
    gradebook_instructor: User,
):
    app.dependency_overrides[get_current_instructor] = lambda: gradebook_instructor

    yield client

    app.dependency_overrides.pop(
        get_current_instructor,
        None,
    )


@pytest.fixture
def student_grade_client(
    client: TestClient,
    gradebook_student_one: User,
):
    app.dependency_overrides[get_current_student] = lambda: gradebook_student_one

    yield client

    app.dependency_overrides.pop(
        get_current_student,
        None,
    )


@pytest.fixture
def second_student_grade_client(
    client: TestClient,
    gradebook_student_two: User,
):
    app.dependency_overrides[get_current_student] = lambda: gradebook_student_two

    yield client

    app.dependency_overrides.pop(
        get_current_student,
        None,
    )


@pytest.fixture
def forbidden_gradebook_client(
    client: TestClient,
):
    def reject_non_instructor() -> User:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor access required.",
        )

    app.dependency_overrides[get_current_instructor] = reject_non_instructor

    yield client

    app.dependency_overrides.pop(
        get_current_instructor,
        None,
    )


@pytest.fixture
def forbidden_student_grade_client(
    client: TestClient,
):
    def reject_non_student() -> User:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required.",
        )

    app.dependency_overrides[get_current_student] = reject_non_student

    yield client

    app.dependency_overrides.pop(
        get_current_student,
        None,
    )


def test_owner_instructor_lists_safe_gradebook(
    gradebook_client: TestClient,
    gradebook_data: dict[str, object],
):
    response = gradebook_client.get("/instructors/gradebook")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["total_items"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 25
    assert data["total_pages"] == 1

    assert data["counts"] == {
        "total": 3,
        "with_manual_grade": 2,
        "without_manual_grade": 1,
        "released": 1,
        "unreleased": 1,
        "graded_status": 1,
        "awaiting_review_status": 1,
    }

    returned_ids = {item["sub_id"] for item in data["items"]}

    assert gradebook_data["historical_submission"].sub_id not in returned_ids

    assert gradebook_data["other_submission"].sub_id not in returned_ids

    for item in data["items"]:
        assert "raw_code" not in item
        assert "standard_input" not in item
        assert "ast_analyses" not in item
        assert "jaccard_score" not in item
        assert "similarity_results" not in item
        assert "execution_requests" not in item
        assert "coding_session" not in item


def test_gradebook_defaults_to_official_attempts(
    gradebook_client: TestClient,
    gradebook_data: dict[str, object],
):
    response = gradebook_client.get("/instructors/gradebook")

    assert response.status_code == status.HTTP_200_OK

    returned_ids = {item["sub_id"] for item in response.json()["items"]}

    assert gradebook_data["historical_submission"].sub_id not in returned_ids

    assert gradebook_data["released_submission"].sub_id in returned_ids


def test_gradebook_supports_filters(
    gradebook_client: TestClient,
    gradebook_data: dict[str, object],
):
    task_one = gradebook_data["task_one"]

    response = gradebook_client.get(
        "/instructors/gradebook",
        params={
            "task_id": task_one.task_id,
            "has_manual_grade": True,
            "grade_released": False,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["total_items"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["sub_id"] == (gradebook_data["unreleased_submission"].sub_id)

    assert item["score"] == 80
    assert item["max_score"] == 100
    assert item["percentage"] == 80
    assert item["grade_is_released"] is False


def test_gradebook_pagination_is_deterministic(
    gradebook_client: TestClient,
    gradebook_data: dict[str, object],
):
    page_one = gradebook_client.get(
        "/instructors/gradebook",
        params={
            "page": 1,
            "page_size": 2,
        },
    )

    page_two = gradebook_client.get(
        "/instructors/gradebook",
        params={
            "page": 2,
            "page_size": 2,
        },
    )

    assert page_one.status_code == status.HTTP_200_OK

    assert page_two.status_code == status.HTTP_200_OK

    first_data = page_one.json()
    second_data = page_two.json()

    assert first_data["total_items"] == 3
    assert first_data["total_pages"] == 2
    assert second_data["total_pages"] == 2

    first_ids = {item["sub_id"] for item in first_data["items"]}

    second_ids = {item["sub_id"] for item in second_data["items"]}

    assert first_ids.isdisjoint(second_ids)


def test_gradebook_sorts_by_score_with_missing_grades_last(
    gradebook_client: TestClient,
    gradebook_data: dict[str, object],
):
    response = gradebook_client.get(
        "/instructors/gradebook",
        params={
            "sort_by": "score",
            "sort_direction": "desc",
        },
    )

    assert response.status_code == status.HTTP_200_OK

    items = response.json()["items"]

    assert items[0]["score"] == 90
    assert items[1]["score"] == 80
    assert items[2]["score"] is None
    assert items[2]["has_manual_grade"] is False


def test_missing_task_filter_returns_404(
    gradebook_client: TestClient,
):
    response = gradebook_client.get(
        "/instructors/gradebook",
        params={
            "task_id": 999999,
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_other_instructor_classroom_returns_403(
    gradebook_client: TestClient,
    gradebook_data: dict[str, object],
):
    other_class = gradebook_data["other_class"]

    response = gradebook_client.get(
        "/instructors/gradebook",
        params={
            "class_id": other_class.class_id,
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_mismatched_class_and_task_return_409(
    gradebook_client: TestClient,
    gradebook_data: dict[str, object],
):
    class_two = gradebook_data["class_two"]

    task_one = gradebook_data["task_one"]

    response = gradebook_client.get(
        "/instructors/gradebook",
        params={
            "class_id": class_two.class_id,
            "task_id": task_one.task_id,
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT


def test_conflicting_grade_filters_return_409(
    gradebook_client: TestClient,
):
    response = gradebook_client.get(
        "/instructors/gradebook",
        params={
            "has_manual_grade": False,
            "grade_released": True,
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT


def test_non_instructor_is_denied_gradebook_access(
    forbidden_gradebook_client: TestClient,
):
    response = forbidden_gradebook_client.get("/instructors/gradebook")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_gradebook_rejects_excessive_page_size(
    gradebook_client: TestClient,
):
    response = gradebook_client.get(
        "/instructors/gradebook",
        params={
            "page_size": 101,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_student_sees_only_own_released_official_grade(
    student_grade_client: TestClient,
    gradebook_data: dict[str, object],
):
    response = student_grade_client.get("/activities/released-grades")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["total_items"] == 1
    assert data["total_pages"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["sub_id"] == (gradebook_data["released_submission"].sub_id)

    assert item["score"] == 90
    assert item["max_score"] == 100
    assert item["percentage"] == 90

    assert item["feedback"] == "Released official feedback."

    assert item["is_released"] is True

    assert "grade_id" not in item
    assert "instructor_id" not in item
    assert "student_id" not in item
    assert "raw_code" not in item
    assert "standard_input" not in item
    assert "ast_analyses" not in item
    assert "jaccard_score" not in item


def test_unreleased_grade_is_hidden_from_student(
    second_student_grade_client: TestClient,
):
    response = second_student_grade_client.get("/activities/released-grades")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["total_items"] == 0
    assert data["total_pages"] == 0
    assert data["items"] == []


def test_student_released_grade_filters_are_scoped_to_owner(
    student_grade_client: TestClient,
    gradebook_data: dict[str, object],
):
    task_two = gradebook_data["task_two"]

    response = student_grade_client.get(
        "/activities/released-grades",
        params={
            "task_id": task_two.task_id,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["total_items"] == 0
    assert data["items"] == []


def test_non_student_is_denied_released_grade_access(
    forbidden_student_grade_client: TestClient,
):
    response = forbidden_student_grade_client.get("/activities/released-grades")

    assert response.status_code == status.HTTP_403_FORBIDDEN
