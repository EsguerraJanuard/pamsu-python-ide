from datetime import datetime, timezone

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import (
    get_current_instructor,
    get_current_user,
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
def test_instructor(
    db_session: Session,
) -> User:
    user = User(
        name="Test Instructor",
        school_id="1111111111",
        email=("instructor_eval@pampangastateu.edu.ph"),
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
def other_instructor(
    db_session: Session,
) -> User:
    user = User(
        name="Other Instructor",
        school_id="3333333333",
        email=("other_instructor_eval@pampangastateu.edu.ph"),
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
def test_student(
    db_session: Session,
) -> User:
    user = User(
        name="Test Student",
        school_id="2222222222",
        email=("student_eval@pampangastateu.edu.ph"),
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
def other_student(
    db_session: Session,
) -> User:
    user = User(
        name="Other Student",
        school_id="4444444444",
        email=("other_student_eval@pampangastateu.edu.ph"),
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
    db_session: Session,
    test_instructor: User,
    test_student: User,
) -> Submission:
    classroom = Classroom(
        instructor_id=test_instructor.user_id,
        name="Evaluation Class",
        class_code="EVAL0001",
        is_active=True,
    )

    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)

    task = Task(
        instructor_id=test_instructor.user_id,
        class_id=classroom.class_id,
        title="Evaluation Task",
        activity_type="laboratory",
        required_ast_rules={
            "require_print_call": True,
        },
        is_graded=True,
        is_published=True,
    )

    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    submission = Submission(
        student_id=test_student.user_id,
        task_id=task.task_id,
        raw_code=("print('Testing Evaluation')"),
        attempt_number=1,
        status="awaiting_review",
        is_official=True,
        accepted_at=datetime.now(timezone.utc),
    )

    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)

    return submission


@pytest.fixture
def client_instructor(
    client: TestClient,
    test_instructor: User,
):
    app.dependency_overrides[get_current_instructor] = lambda: test_instructor

    app.dependency_overrides[get_current_user] = lambda: test_instructor

    yield client

    app.dependency_overrides.pop(
        get_current_instructor,
        None,
    )

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


@pytest.fixture
def client_student(
    client: TestClient,
    test_student: User,
):
    app.dependency_overrides[get_current_instructor] = lambda: test_student

    app.dependency_overrides[get_current_user] = lambda: test_student

    yield client

    app.dependency_overrides.pop(
        get_current_instructor,
        None,
    )

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


@pytest.fixture
def client_other_instructor(
    client: TestClient,
    other_instructor: User,
):
    app.dependency_overrides[get_current_instructor] = lambda: other_instructor

    app.dependency_overrides[get_current_user] = lambda: other_instructor

    yield client

    app.dependency_overrides.pop(
        get_current_instructor,
        None,
    )

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


@pytest.fixture
def client_other_student(
    client: TestClient,
    other_student: User,
):
    app.dependency_overrides[get_current_instructor] = lambda: other_student

    app.dependency_overrides[get_current_user] = lambda: other_student

    yield client

    app.dependency_overrides.pop(
        get_current_instructor,
        None,
    )

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


def test_student_cannot_run_evaluation(
    client_student: TestClient,
    setup_evaluation_data: Submission,
):
    response = client_student.post(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_missing_submission_is_blocked(
    client_instructor: TestClient,
):
    response = client_instructor.post("/evaluation/submissions/999999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_instructor_can_run_static_evaluation(
    client_instructor: TestClient,
    db_session: Session,
    setup_evaluation_data: Submission,
):
    response = client_instructor.post(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["sub_id"] == setup_evaluation_data.sub_id

    assert data["ast_pass_fail"] is True
    assert "jaccard_score" in data
    assert "ast_details" in data
    assert "jaccard_details" in data
    assert "review_notice" in data

    # REVIEW BOUNDARY:
    # Evaluation must not create an official grade
    # or return an automatic misconduct verdict.
    assert "grade" not in data
    assert "official_grade" not in data
    assert "plagiarism_verdict" not in data
    assert "misconduct_verdict" not in data

    grade_count = (
        db_session.query(InstructorGrade)
        .filter(InstructorGrade.submission_id == setup_evaluation_data.sub_id)
        .count()
    )

    assert grade_count == 0


def test_student_receives_safe_evaluation_view(
    client_student: TestClient,
    setup_evaluation_data: Submission,
):
    response = client_student.get(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["sub_id"] == setup_evaluation_data.sub_id

    assert data["task_id"] == setup_evaluation_data.task_id

    assert data["status"] == "awaiting_review"
    assert data["is_official"] is True
    assert data["instructor_grade"] is None

    # STUDENT VISIBILITY BOUNDARY:
    assert "student_id" not in data
    assert "jaccard_score" not in data
    assert "ast_pass_fail" not in data
    assert "ast_analyses" not in data

    assert "similarity_results_as_source" not in data

    assert "highest_match_sub_id" not in data
    assert "instructor_id" not in data


def test_student_cannot_view_another_students_evaluation(
    client_other_student: TestClient,
    setup_evaluation_data: Submission,
):
    response = client_other_student.get(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_owner_instructor_can_view_full_review_details(
    client_instructor: TestClient,
    setup_evaluation_data: Submission,
):
    evaluation_response = client_instructor.post(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}"
    )

    assert evaluation_response.status_code == status.HTTP_200_OK

    response = client_instructor.get(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["student_id"] == setup_evaluation_data.student_id

    assert "ast_pass_fail" in data
    assert "jaccard_score" in data
    assert "ast_analyses" in data

    assert "similarity_results_as_source" in data

    assert len(data["ast_analyses"]) == 1
    assert data["instructor_grade"] is None


def test_other_instructor_cannot_evaluate_submission(
    client_other_instructor: TestClient,
    setup_evaluation_data: Submission,
):
    response = client_other_instructor.post(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_other_instructor_cannot_view_submission_review(
    client_other_instructor: TestClient,
    setup_evaluation_data: Submission,
):
    response = client_other_instructor.get(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_other_instructor_cannot_grade_submission(
    client_other_instructor: TestClient,
    setup_evaluation_data: Submission,
):
    response = client_other_instructor.put(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 90,
            "max_score": 100,
            "feedback": "Unauthorized.",
            "is_released": True,
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_setting_grade_does_not_change_status(
    client_instructor: TestClient,
    db_session: Session,
    setup_evaluation_data: Submission,
):
    response = client_instructor.put(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 85.5,
            "max_score": 100,
            "feedback": "Good implementation.",
            "is_released": False,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    db_session.refresh(setup_evaluation_data)

    assert setup_evaluation_data.status == "awaiting_review"


def test_unreleased_grade_is_hidden_from_student(
    client_instructor: TestClient,
    test_student: User,
    setup_evaluation_data: Submission,
):
    grade_response = client_instructor.put(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 88,
            "max_score": 100,
            "feedback": "Private draft feedback.",
            "is_released": False,
        },
    )

    assert grade_response.status_code == status.HTTP_200_OK

    app.dependency_overrides[get_current_user] = lambda: test_student

    response = client_instructor.get(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["instructor_grade"] is None
    assert "ast_analyses" not in data

    assert "similarity_results_as_source" not in data


def test_released_grade_is_visible_to_student_safely(
    client_instructor: TestClient,
    test_student: User,
    setup_evaluation_data: Submission,
):
    grade_response = client_instructor.put(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 92,
            "max_score": 100,
            "feedback": "Released feedback.",
            "is_released": True,
        },
    )

    assert grade_response.status_code == status.HTTP_200_OK

    app.dependency_overrides[get_current_user] = lambda: test_student

    response = client_instructor.get(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}"
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    released_grade = data["instructor_grade"]

    assert released_grade is not None
    assert released_grade["score"] == 92
    assert released_grade["max_score"] == 100

    assert released_grade["feedback"] == "Released feedback."

    assert released_grade["is_released"] is True

    # Student response must not reveal internal grade
    # identifiers or instructor identity.
    assert "grade_id" not in released_grade
    assert "submission_id" not in released_grade
    assert "instructor_id" not in released_grade
    assert "created_at" not in released_grade


def test_marking_graded_requires_manual_grade(
    client_instructor: TestClient,
    setup_evaluation_data: Submission,
):
    response = client_instructor.patch(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/status",
        json={
            "status": "graded",
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT


def test_instructor_can_grade_then_explicitly_mark_graded(
    client_instructor: TestClient,
    db_session: Session,
    setup_evaluation_data: Submission,
):
    grade_response = client_instructor.put(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 85.5,
            "max_score": 100,
            "feedback": "Good implementation.",
            "is_released": False,
        },
    )

    assert grade_response.status_code == status.HTTP_200_OK

    grade_data = grade_response.json()

    assert grade_data["score"] == 85.5
    assert grade_data["max_score"] == 100
    assert grade_data["is_released"] is False

    db_session.refresh(setup_evaluation_data)

    assert setup_evaluation_data.status == "awaiting_review"

    patch_response = client_instructor.patch(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 92,
            "is_released": True,
        },
    )

    assert patch_response.status_code == status.HTTP_200_OK

    patched_grade = patch_response.json()

    assert patched_grade["score"] == 92
    assert patched_grade["max_score"] == 100
    assert patched_grade["is_released"] is True

    status_response = client_instructor.patch(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/status",
        json={
            "status": "graded",
        },
    )

    assert status_response.status_code == status.HTTP_200_OK

    assert status_response.json()["status"] == "graded"


def test_unofficial_submission_cannot_receive_grade(
    client_instructor: TestClient,
    db_session: Session,
    setup_evaluation_data: Submission,
):
    setup_evaluation_data.is_official = False

    db_session.commit()
    db_session.refresh(setup_evaluation_data)

    response = client_instructor.put(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 80,
            "max_score": 100,
            "is_released": False,
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT


def test_unaccepted_submission_cannot_receive_grade(
    client_instructor: TestClient,
    db_session: Session,
    setup_evaluation_data: Submission,
):
    setup_evaluation_data.accepted_at = None

    db_session.commit()
    db_session.refresh(setup_evaluation_data)

    response = client_instructor.put(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 80,
            "max_score": 100,
            "is_released": False,
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT


def test_rejected_submission_cannot_receive_grade(
    client_instructor: TestClient,
    db_session: Session,
    setup_evaluation_data: Submission,
):
    setup_evaluation_data.status = "rejected"

    db_session.commit()
    db_session.refresh(setup_evaluation_data)

    response = client_instructor.put(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 80,
            "max_score": 100,
            "is_released": False,
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT


def test_ungraded_activity_cannot_receive_grade(
    client_instructor: TestClient,
    db_session: Session,
    setup_evaluation_data: Submission,
):
    setup_evaluation_data.task.is_graded = False

    db_session.commit()

    response = client_instructor.put(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 80,
            "max_score": 100,
            "is_released": False,
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT


def test_grade_cannot_exceed_maximum_score(
    client_instructor: TestClient,
    setup_evaluation_data: Submission,
):
    response = client_instructor.put(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 105,
            "max_score": 100,
            "feedback": "Invalid score.",
            "is_released": False,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_empty_grade_patch_is_rejected(
    client_instructor: TestClient,
    setup_evaluation_data: Submission,
):
    create_response = client_instructor.put(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 90,
            "max_score": 100,
            "is_released": False,
        },
    )

    assert create_response.status_code == status.HTTP_200_OK

    response = client_instructor.patch(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_grade_patch_cannot_exceed_existing_maximum(
    client_instructor: TestClient,
    setup_evaluation_data: Submission,
):
    create_response = client_instructor.put(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 90,
            "max_score": 100,
            "is_released": False,
        },
    )

    assert create_response.status_code == status.HTTP_200_OK

    response = client_instructor.patch(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 101,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_student_cannot_update_review_status(
    client_student: TestClient,
    setup_evaluation_data: Submission,
):
    response = client_student.patch(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/status",
        json={
            "status": "rejected",
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_student_cannot_create_grade(
    client_student: TestClient,
    setup_evaluation_data: Submission,
):
    response = client_student.put(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/grade",
        json={
            "score": 100,
            "max_score": 100,
            "is_released": True,
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_invalid_review_status_is_rejected(
    client_instructor: TestClient,
    setup_evaluation_data: Submission,
):
    response = client_instructor.patch(
        f"/evaluation/submissions/{setup_evaluation_data.sub_id}/status",
        json={
            "status": "automatically_failed",
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
