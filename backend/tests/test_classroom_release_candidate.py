from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.domain_models import Classroom, Enrollment, User


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
            "name": "Release Candidate Classroom",
            "subject_code": "RC101",
            "section": "BSIT RC",
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


def test_non_owner_cannot_archive_classroom(
    client,
    db_session: Session,
) -> None:
    owner = create_test_user(
        db_session,
        name="Classroom Owner",
        role="instructor",
        school_id="3100000001",
        email="rc-owner@pampangastateu.edu.ph",
    )

    other_instructor = create_test_user(
        db_session,
        name="Other Instructor",
        role="instructor",
        school_id="3100000002",
        email="rc-other@pampangastateu.edu.ph",
    )

    owner_token = login_and_get_token(
        client,
        email=owner.email,
    )

    other_token = login_and_get_token(
        client,
        email=other_instructor.email,
    )

    classroom_data = create_classroom(
        client,
        instructor_token=owner_token,
    )

    response = client.patch(
        f"/classrooms/{classroom_data['class_id']}",
        headers=bearer_header(other_token),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 403

    db_session.expire_all()

    classroom = db_session.get(
        Classroom,
        classroom_data["class_id"],
    )

    assert classroom is not None
    assert classroom.instructor_id == owner.user_id
    assert classroom.is_active is True
    assert classroom.archived_at is None


def test_non_owner_cannot_change_enrollment_status(
    client,
    db_session: Session,
) -> None:
    owner = create_test_user(
        db_session,
        name="Classroom Owner",
        role="instructor",
        school_id="3100000003",
        email="rc-owner-two@pampangastateu.edu.ph",
    )

    other_instructor = create_test_user(
        db_session,
        name="Other Instructor",
        role="instructor",
        school_id="3100000004",
        email="rc-other-two@pampangastateu.edu.ph",
    )

    student = create_test_user(
        db_session,
        name="Release Candidate Student",
        role="student",
        school_id="3200000001",
        email="rc-student@pampangastateu.edu.ph",
    )

    owner_token = login_and_get_token(
        client,
        email=owner.email,
    )

    other_token = login_and_get_token(
        client,
        email=other_instructor.email,
    )

    student_token = login_and_get_token(
        client,
        email=student.email,
    )

    classroom_data = create_classroom(
        client,
        instructor_token=owner_token,
    )

    enrollment_data = enroll_student(
        client,
        student_token=student_token,
        class_code=classroom_data["class_code"],
    )

    response = client.patch(
        (f"/classrooms/enrollments/{enrollment_data['enrollment_id']}/status"),
        headers=bearer_header(other_token),
        json={
            "status": "disabled",
        },
    )

    assert response.status_code == 403

    db_session.expire_all()

    enrollment = db_session.get(
        Enrollment,
        enrollment_data["enrollment_id"],
    )

    assert enrollment is not None
    assert enrollment.class_id == classroom_data["class_id"]
    assert enrollment.student_id == student.user_id
    assert enrollment.status == "active"
    assert enrollment.deactivated_at is None
