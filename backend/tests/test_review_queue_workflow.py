from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_current_instructor
from app.main import app
from app.models.domain_models import (
    Classroom,
    InstructorGrade,
    Submission,
    Task,
    User,
)


@pytest.fixture
def review_instructor(
    db_session: Session,
) -> User:
    instructor = User(
        name="Review Queue Instructor",
        school_id="5100000001",
        email=("review.queue.instructor@pampangastateu.edu.ph"),
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
def other_review_instructor(
    db_session: Session,
) -> User:
    instructor = User(
        name="Other Review Instructor",
        school_id="5100000002",
        email=("other.review.instructor@pampangastateu.edu.ph"),
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
def review_student_one(
    db_session: Session,
) -> User:
    student = User(
        name="Alice Student",
        school_id="5200000001",
        email=("alice.review.student@pampangastateu.edu.ph"),
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
def review_student_two(
    db_session: Session,
) -> User:
    student = User(
        name="Bob Student",
        school_id="5200000002",
        email=("bob.review.student@pampangastateu.edu.ph"),
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
def review_queue_data(
    db_session: Session,
    review_instructor: User,
    other_review_instructor: User,
    review_student_one: User,
    review_student_two: User,
) -> dict[str, object]:
    now = datetime.now(timezone.utc)

    class_one = Classroom(
        instructor_id=review_instructor.user_id,
        name="Programming One",
        subject_code="CS101",
        section="A",
        class_code="REVQ1001",
        is_active=True,
    )

    class_two = Classroom(
        instructor_id=review_instructor.user_id,
        name="Programming Two",
        subject_code="CS102",
        section="B",
        class_code="REVQ1002",
        is_active=True,
    )

    other_class = Classroom(
        instructor_id=(other_review_instructor.user_id),
        name="Other Instructor Class",
        subject_code="CS999",
        section="Z",
        class_code="REVQ9999",
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
        instructor_id=review_instructor.user_id,
        class_id=class_one.class_id,
        title="Loops Laboratory",
        activity_type="laboratory",
        required_ast_rules={},
        is_graded=True,
        is_published=True,
    )

    task_two = Task(
        instructor_id=review_instructor.user_id,
        class_id=class_two.class_id,
        title="Functions Homework",
        activity_type="homework",
        required_ast_rules={},
        is_graded=True,
        is_published=True,
    )

    other_task = Task(
        instructor_id=(other_review_instructor.user_id),
        class_id=other_class.class_id,
        title="Private Other Activity",
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

    historical_submission = Submission(
        student_id=review_student_one.user_id,
        task_id=task_one.task_id,
        raw_code="print('historical')",
        attempt_number=1,
        status="submitted",
        is_official=False,
        submitted_at=now - timedelta(days=5),
        accepted_at=now - timedelta(days=5),
    )

    awaiting_submission = Submission(
        student_id=review_student_one.user_id,
        task_id=task_one.task_id,
        raw_code="print('official')",
        attempt_number=2,
        status="awaiting_review",
        is_official=True,
        submitted_at=now - timedelta(days=4),
        accepted_at=now - timedelta(days=4),
    )

    graded_submission = Submission(
        student_id=review_student_two.user_id,
        task_id=task_one.task_id,
        raw_code="print('graded')",
        attempt_number=1,
        status="graded",
        is_official=True,
        submitted_at=now - timedelta(days=3),
        accepted_at=now - timedelta(days=3),
    )

    rejected_submission = Submission(
        student_id=review_student_two.user_id,
        task_id=task_two.task_id,
        raw_code="print('rejected')",
        attempt_number=1,
        status="rejected",
        is_official=True,
        submitted_at=now - timedelta(days=2),
        accepted_at=now - timedelta(days=2),
    )

    unreleased_submission = Submission(
        student_id=review_student_one.user_id,
        task_id=task_two.task_id,
        raw_code="print('unreleased')",
        attempt_number=1,
        status="awaiting_review",
        is_official=True,
        submitted_at=now - timedelta(days=1),
        accepted_at=now - timedelta(days=1),
    )

    other_submission = Submission(
        student_id=review_student_two.user_id,
        task_id=other_task.task_id,
        raw_code="print('other instructor')",
        attempt_number=1,
        status="awaiting_review",
        is_official=True,
        submitted_at=now,
        accepted_at=now,
    )

    db_session.add_all(
        [
            historical_submission,
            awaiting_submission,
            graded_submission,
            rejected_submission,
            unreleased_submission,
            other_submission,
        ]
    )
    db_session.commit()

    released_grade = InstructorGrade(
        submission_id=graded_submission.sub_id,
        instructor_id=review_instructor.user_id,
        score=90,
        max_score=100,
        feedback="Released grade.",
        is_released=True,
    )

    unreleased_grade = InstructorGrade(
        submission_id=unreleased_submission.sub_id,
        instructor_id=review_instructor.user_id,
        score=85,
        max_score=100,
        feedback="Draft grade.",
        is_released=False,
    )

    db_session.add_all(
        [
            released_grade,
            unreleased_grade,
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
        "historical_submission": (historical_submission),
        "awaiting_submission": (awaiting_submission),
        "graded_submission": graded_submission,
        "rejected_submission": (rejected_submission),
        "unreleased_submission": (unreleased_submission),
        "other_submission": other_submission,
    }


@pytest.fixture
def review_queue_client(
    client: TestClient,
    review_instructor: User,
):
    app.dependency_overrides[get_current_instructor] = lambda: review_instructor

    yield client

    app.dependency_overrides.pop(
        get_current_instructor,
        None,
    )


@pytest.fixture
def forbidden_review_queue_client(
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


def test_owner_instructor_lists_safe_review_queue(
    review_queue_client: TestClient,
    review_queue_data: dict[str, object],
):
    response = review_queue_client.get("/instructors/review-queue")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["total_items"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 25
    assert data["total_pages"] == 1

    assert data["counts"] == {
        "total": 5,
        "submitted": 1,
        "awaiting_review": 2,
        "graded": 1,
        "rejected": 1,
        "official": 4,
        "unofficial": 1,
        "unreleased_grades": 1,
    }

    returned_ids = {item["sub_id"] for item in data["items"]}

    assert review_queue_data["other_submission"].sub_id not in returned_ids

    for item in data["items"]:
        assert "raw_code" not in item
        assert "standard_input" not in item
        assert "ast_analyses" not in item
        assert "jaccard_score" not in item
        assert "similarity_results" not in item
        assert "execution_requests" not in item
        assert "coding_session" not in item
        assert "feedback" not in item
        assert "score" not in item


def test_default_order_is_latest_submission_first(
    review_queue_client: TestClient,
    review_queue_data: dict[str, object],
):
    response = review_queue_client.get("/instructors/review-queue")

    assert response.status_code == status.HTTP_200_OK

    returned_ids = [item["sub_id"] for item in response.json()["items"]]

    assert returned_ids[0] == (review_queue_data["unreleased_submission"].sub_id)

    assert returned_ids[-1] == (review_queue_data["historical_submission"].sub_id)


def test_review_queue_supports_owned_filters(
    review_queue_client: TestClient,
    review_queue_data: dict[str, object],
):
    task_one = review_queue_data["task_one"]

    response = review_queue_client.get(
        "/instructors/review-queue",
        params={
            "task_id": task_one.task_id,
            "status": "awaiting_review",
            "official": True,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["total_items"] == 1
    assert len(data["items"]) == 1

    assert data["items"][0]["sub_id"] == (
        review_queue_data["awaiting_submission"].sub_id
    )


def test_review_queue_pagination_is_deterministic(
    review_queue_client: TestClient,
    review_queue_data: dict[str, object],
):
    page_one = review_queue_client.get(
        "/instructors/review-queue",
        params={
            "page": 1,
            "page_size": 2,
        },
    )

    page_two = review_queue_client.get(
        "/instructors/review-queue",
        params={
            "page": 2,
            "page_size": 2,
        },
    )

    assert page_one.status_code == status.HTTP_200_OK

    assert page_two.status_code == status.HTTP_200_OK

    first_data = page_one.json()
    second_data = page_two.json()

    assert first_data["total_items"] == 5
    assert first_data["total_pages"] == 3
    assert second_data["total_pages"] == 3

    first_ids = {item["sub_id"] for item in first_data["items"]}

    second_ids = {item["sub_id"] for item in second_data["items"]}

    assert len(first_ids) == 2
    assert len(second_ids) == 2
    assert first_ids.isdisjoint(second_ids)


def test_review_queue_filters_unreleased_grades(
    review_queue_client: TestClient,
    review_queue_data: dict[str, object],
):
    response = review_queue_client.get(
        "/instructors/review-queue",
        params={
            "grade_released": False,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["total_items"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["sub_id"] == (review_queue_data["unreleased_submission"].sub_id)

    assert item["has_manual_grade"] is True
    assert item["grade_is_released"] is False


def test_review_queue_sorts_by_student_name(
    review_queue_client: TestClient,
    review_queue_data: dict[str, object],
):
    response = review_queue_client.get(
        "/instructors/review-queue",
        params={
            "sort_by": "student_name",
            "sort_direction": "asc",
        },
    )

    assert response.status_code == status.HTTP_200_OK

    names = [item["student"]["name"] for item in response.json()["items"]]

    assert names == sorted(
        names,
        key=str.lower,
    )


def test_missing_classroom_filter_returns_404(
    review_queue_client: TestClient,
):
    response = review_queue_client.get(
        "/instructors/review-queue",
        params={
            "class_id": 999999,
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_other_instructor_classroom_returns_403(
    review_queue_client: TestClient,
    review_queue_data: dict[str, object],
):
    other_class = review_queue_data["other_class"]

    response = review_queue_client.get(
        "/instructors/review-queue",
        params={
            "class_id": other_class.class_id,
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_mismatched_class_and_task_return_409(
    review_queue_client: TestClient,
    review_queue_data: dict[str, object],
):
    class_two = review_queue_data["class_two"]

    task_one = review_queue_data["task_one"]

    response = review_queue_client.get(
        "/instructors/review-queue",
        params={
            "class_id": class_two.class_id,
            "task_id": task_one.task_id,
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT


def test_non_instructor_is_denied(
    forbidden_review_queue_client: TestClient,
):
    response = forbidden_review_queue_client.get("/instructors/review-queue")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_review_queue_rejects_excessive_page_size(
    review_queue_client: TestClient,
):
    response = review_queue_client.get(
        "/instructors/review-queue",
        params={
            "page_size": 101,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
