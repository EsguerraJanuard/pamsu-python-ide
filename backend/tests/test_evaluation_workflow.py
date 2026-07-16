import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.security import get_current_instructor, get_current_user
from app.models.domain_models import Classroom, Submission, Task, User


@pytest.fixture
def test_instructor(db_session: Session) -> User:
    user = User(
        name="Test Instructor",
        school_id="1111111111",
        email="instructor_eval@pampangastateu.edu.ph",
        role="instructor",
        password_hash="fakehash",
        email_verified=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_student(db_session: Session) -> User:
    user = User(
        name="Test Student",
        school_id="2222222222",
        email="student_eval@pampangastateu.edu.ph",
        role="student",
        password_hash="fakehash",
        email_verified=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def setup_evaluation_data(
    db_session: Session, test_instructor: User, test_student: User
) -> Submission:
    classroom = Classroom(
        instructor_id=test_instructor.user_id,
        name="Evaluation Class",
        class_code="EVAL0001",
        is_active=True,
    )
    db_session.add(classroom)
    db_session.commit()

    task = Task(
        instructor_id=test_instructor.user_id,
        class_id=classroom.class_id,
        title="Evaluation Task",
        activity_type="laboratory",
        required_ast_rules={},
        is_graded=True,
        is_published=True,
    )
    db_session.add(task)
    db_session.commit()

    submission = Submission(
        student_id=test_student.user_id,
        task_id=task.task_id,
        raw_code="print('Testing Evaluation')",
        attempt_number=1,
        status="awaiting_review",
        is_official=True,
    )
    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)

    return submission


@pytest.fixture
def client_instructor(client: TestClient, test_instructor: User):
    app.dependency_overrides[get_current_instructor] = lambda: test_instructor
    app.dependency_overrides[get_current_user] = lambda: test_instructor
    yield client
    app.dependency_overrides.pop(get_current_instructor, None)
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def client_student(client: TestClient, test_student: User):
    app.dependency_overrides[get_current_instructor] = lambda: test_student
    app.dependency_overrides[get_current_user] = lambda: test_student
    yield client
    app.dependency_overrides.pop(get_current_instructor, None)
    app.dependency_overrides.pop(get_current_user, None)


def test_student_cannot_evaluate_submission(
    client_student: TestClient, setup_evaluation_data: Submission
):
    sub_id = setup_evaluation_data.sub_id
    response = client_student.post(f"/evaluation/submissions/{sub_id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_invalid_submission_blocked(client_instructor: TestClient):
    response = client_instructor.post("/evaluation/submissions/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_instructor_can_evaluate_submission(
    client_instructor: TestClient, setup_evaluation_data: Submission
):
    sub_id = setup_evaluation_data.sub_id
    response = client_instructor.post(f"/evaluation/submissions/{sub_id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["sub_id"] == sub_id
    assert "ast_pass_fail" in data
    assert "jaccard_score" in data
    assert "review_notice" in data

    # REVIEW BOUNDARY: Ensure there's no automatic grade or plagiarism field returned here.
    assert "grade" not in data
    assert "plagiarism_verdict" not in data


def test_student_can_view_own_evaluation(
    client_student: TestClient, setup_evaluation_data: Submission
):
    sub_id = setup_evaluation_data.sub_id
    response = client_student.get(f"/evaluation/submissions/{sub_id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["sub_id"] == sub_id
    assert data["status"] == "awaiting_review"
    assert "instructor_grade" in data


def test_instructor_can_update_status(
    client_instructor: TestClient, setup_evaluation_data: Submission
):
    sub_id = setup_evaluation_data.sub_id
    payload = {"status": "graded"}
    response = client_instructor.patch(
        f"/evaluation/submissions/{sub_id}/status", json=payload
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "graded"


def test_instructor_can_set_and_patch_grade(
    client_instructor: TestClient, setup_evaluation_data: Submission
):
    sub_id = setup_evaluation_data.sub_id

    # 1. SET Grade
    put_payload = {
        "score": 85.5,
        "max_score": 100.0,
        "feedback": "Good implementation.",
        "is_released": False,
    }
    put_res = client_instructor.put(
        f"/evaluation/submissions/{sub_id}/grade", json=put_payload
    )
    assert put_res.status_code == status.HTTP_200_OK

    put_data = put_res.json()
    assert put_data["score"] == 85.5
    assert put_data["max_score"] == 100.0

    # 2. PATCH Grade
    patch_payload = {
        "score": 92.0,
        "is_released": True,
    }
    patch_res = client_instructor.patch(
        f"/evaluation/submissions/{sub_id}/grade", json=patch_payload
    )
    assert patch_res.status_code == status.HTTP_200_OK

    patch_data = patch_res.json()
    assert patch_data["score"] == 92.0
    assert patch_data["max_score"] == 100.0  # max score remains unchanged
    assert patch_data["is_released"] is True


def test_grade_cannot_exceed_max_score(
    client_instructor: TestClient, setup_evaluation_data: Submission
):
    sub_id = setup_evaluation_data.sub_id
    payload = {
        "score": 105.0,
        "max_score": 100.0,
        "feedback": "Invalid score",
        "is_released": False,
    }
    response = client_instructor.put(
        f"/evaluation/submissions/{sub_id}/grade", json=payload
    )
    # Expected to fail due to Pydantic validation
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
