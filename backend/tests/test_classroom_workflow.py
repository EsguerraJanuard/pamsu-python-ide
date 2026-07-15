from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.domain_models import (
    Classroom,
    Enrollment,
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


def create_classroom_through_api(
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


def test_instructor_can_manage_own_classroom(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="1000000001",
        email="faculty1@pampangastateu.edu.ph",
    )

    token = login_and_get_token(
        client,
        email=instructor.email,
    )

    classroom_data = create_classroom_through_api(
        client,
        instructor_token=token,
    )

    class_id = classroom_data["class_id"]
    original_code = classroom_data["class_code"]

    assert classroom_data["instructor_id"] == instructor.user_id
    assert classroom_data["name"] == "Programming Fundamentals"
    assert classroom_data["subject_code"] == "CCS101"
    assert classroom_data["section"] == "BSIT 1A"
    assert classroom_data["is_active"] is True
    assert len(original_code) == 8
    assert original_code.isalnum()
    assert original_code == original_code.upper()

    list_response = client.get(
        "/classrooms/",
        headers=bearer_header(token),
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["class_id"] == class_id

    get_response = client.get(
        f"/classrooms/{class_id}",
        headers=bearer_header(token),
    )

    assert get_response.status_code == 200
    assert get_response.json()["class_code"] == original_code

    update_response = client.patch(
        f"/classrooms/{class_id}",
        headers=bearer_header(token),
        json={
            "name": "Advanced Programming",
            "section": "BSIT 1B",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Advanced Programming"
    assert update_response.json()["section"] == "BSIT 1B"
    assert update_response.json()["class_code"] == original_code

    regenerate_response = client.post(
        f"/classrooms/{class_id}/regenerate-code",
        headers=bearer_header(token),
    )

    assert regenerate_response.status_code == 200

    replacement_code = regenerate_response.json()["class_code"]

    assert replacement_code != original_code
    assert len(replacement_code) == 8

    stored_classroom = db_session.get(
        Classroom,
        class_id,
    )

    assert stored_classroom is not None
    assert stored_classroom.class_code == replacement_code


def test_student_can_join_and_view_classroom(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="1000000002",
        email="faculty2@pampangastateu.edu.ph",
    )

    student = create_test_user(
        db_session,
        name="Test Student",
        role="student",
        school_id="2000000001",
        email="student1@pampangastateu.edu.ph",
    )

    instructor_token = login_and_get_token(
        client,
        email=instructor.email,
    )

    student_token = login_and_get_token(
        client,
        email=student.email,
    )

    classroom_data = create_classroom_through_api(
        client,
        instructor_token=instructor_token,
    )

    join_response = client.post(
        "/classrooms/join",
        headers=bearer_header(student_token),
        json={
            "class_code": classroom_data["class_code"].lower(),
        },
    )

    assert join_response.status_code == 201

    enrollment_data = join_response.json()

    assert enrollment_data["class_id"] == classroom_data["class_id"]
    assert enrollment_data["student_id"] == student.user_id
    assert enrollment_data["status"] == "active"

    mine_response = client.get(
        "/classrooms/mine",
        headers=bearer_header(student_token),
    )

    assert mine_response.status_code == 200

    student_classrooms = mine_response.json()

    assert len(student_classrooms) == 1
    assert student_classrooms[0]["enrollment_id"] == enrollment_data["enrollment_id"]
    assert student_classrooms[0]["enrollment_status"] == "active"
    assert student_classrooms[0]["classroom"]["class_id"] == classroom_data["class_id"]

    members_response = client.get(
        f"/classrooms/{classroom_data['class_id']}/members",
        headers=bearer_header(instructor_token),
    )

    assert members_response.status_code == 200

    members = members_response.json()

    assert len(members) == 1
    assert members[0]["student_id"] == student.user_id
    assert members[0]["school_id"] == student.school_id
    assert members[0]["email"] == student.email
    assert members[0]["status"] == "active"


def test_duplicate_enrollment_is_rejected(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="1000000003",
        email="faculty3@pampangastateu.edu.ph",
    )

    student = create_test_user(
        db_session,
        name="Test Student",
        role="student",
        school_id="2000000002",
        email="student2@pampangastateu.edu.ph",
    )

    instructor_token = login_and_get_token(
        client,
        email=instructor.email,
    )

    student_token = login_and_get_token(
        client,
        email=student.email,
    )

    classroom_data = create_classroom_through_api(
        client,
        instructor_token=instructor_token,
    )

    payload = {
        "class_code": classroom_data["class_code"],
    }

    first_response = client.post(
        "/classrooms/join",
        headers=bearer_header(student_token),
        json=payload,
    )

    assert first_response.status_code == 201

    duplicate_response = client.post(
        "/classrooms/join",
        headers=bearer_header(student_token),
        json=payload,
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == (
        "You already have an enrollment record in this classroom."
    )


def test_inactive_classroom_rejects_new_enrollment(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="1000000004",
        email="faculty4@pampangastateu.edu.ph",
    )

    student = create_test_user(
        db_session,
        name="Test Student",
        role="student",
        school_id="2000000003",
        email="student3@pampangastateu.edu.ph",
    )

    instructor_token = login_and_get_token(
        client,
        email=instructor.email,
    )

    student_token = login_and_get_token(
        client,
        email=student.email,
    )

    classroom_data = create_classroom_through_api(
        client,
        instructor_token=instructor_token,
    )

    deactivate_response = client.patch(
        f"/classrooms/{classroom_data['class_id']}",
        headers=bearer_header(instructor_token),
        json={
            "is_active": False,
        },
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False

    join_response = client.post(
        "/classrooms/join",
        headers=bearer_header(student_token),
        json={
            "class_code": classroom_data["class_code"],
        },
    )

    assert join_response.status_code == 409
    assert join_response.json()["detail"] == (
        "This classroom is inactive and cannot accept new enrollments."
    )


def test_instructor_can_change_enrollment_status(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="1000000005",
        email="faculty5@pampangastateu.edu.ph",
    )

    student = create_test_user(
        db_session,
        name="Test Student",
        role="student",
        school_id="2000000004",
        email="student4@pampangastateu.edu.ph",
    )

    instructor_token = login_and_get_token(
        client,
        email=instructor.email,
    )

    student_token = login_and_get_token(
        client,
        email=student.email,
    )

    classroom_data = create_classroom_through_api(
        client,
        instructor_token=instructor_token,
    )

    join_response = client.post(
        "/classrooms/join",
        headers=bearer_header(student_token),
        json={
            "class_code": classroom_data["class_code"],
        },
    )

    assert join_response.status_code == 201

    enrollment_id = join_response.json()["enrollment_id"]

    disable_response = client.patch(
        f"/classrooms/enrollments/{enrollment_id}/status",
        headers=bearer_header(instructor_token),
        json={
            "status": "disabled",
        },
    )

    assert disable_response.status_code == 200
    assert disable_response.json()["status"] == "disabled"

    db_session.expire_all()

    stored_enrollment = db_session.get(
        Enrollment,
        enrollment_id,
    )

    assert stored_enrollment is not None
    assert stored_enrollment.status == "disabled"
    assert stored_enrollment.deactivated_at is not None

    mine_response = client.get(
        "/classrooms/mine",
        headers=bearer_header(student_token),
    )

    assert mine_response.status_code == 200
    assert mine_response.json()[0]["enrollment_status"] == "disabled"

    reactivate_response = client.patch(
        f"/classrooms/enrollments/{enrollment_id}/status",
        headers=bearer_header(instructor_token),
        json={
            "status": "active",
        },
    )

    assert reactivate_response.status_code == 200
    assert reactivate_response.json()["status"] == "active"

    db_session.expire_all()

    reactivated_enrollment = db_session.get(
        Enrollment,
        enrollment_id,
    )

    assert reactivated_enrollment is not None
    assert reactivated_enrollment.status == "active"
    assert reactivated_enrollment.deactivated_at is None

    remove_response = client.patch(
        f"/classrooms/enrollments/{enrollment_id}/status",
        headers=bearer_header(instructor_token),
        json={
            "status": "removed",
        },
    )

    assert remove_response.status_code == 200
    assert remove_response.json()["status"] == "removed"

    db_session.expire_all()

    removed_enrollment = db_session.get(
        Enrollment,
        enrollment_id,
    )

    assert removed_enrollment is not None
    assert removed_enrollment.status == "removed"
    assert removed_enrollment.deactivated_at is not None


def test_instructor_cannot_manage_another_instructors_class(
    client,
    db_session,
):
    owner = create_test_user(
        db_session,
        name="Class Owner",
        role="instructor",
        school_id="1000000006",
        email="faculty6@pampangastateu.edu.ph",
    )

    other_instructor = create_test_user(
        db_session,
        name="Other Instructor",
        role="instructor",
        school_id="1000000007",
        email="faculty7@pampangastateu.edu.ph",
    )

    owner_token = login_and_get_token(
        client,
        email=owner.email,
    )

    other_token = login_and_get_token(
        client,
        email=other_instructor.email,
    )

    classroom_data = create_classroom_through_api(
        client,
        instructor_token=owner_token,
    )

    class_id = classroom_data["class_id"]

    get_response = client.get(
        f"/classrooms/{class_id}",
        headers=bearer_header(other_token),
    )

    assert get_response.status_code == 403

    update_response = client.patch(
        f"/classrooms/{class_id}",
        headers=bearer_header(other_token),
        json={
            "name": "Unauthorized Update",
        },
    )

    assert update_response.status_code == 403

    members_response = client.get(
        f"/classrooms/{class_id}/members",
        headers=bearer_header(other_token),
    )

    assert members_response.status_code == 403

    regenerate_response = client.post(
        f"/classrooms/{class_id}/regenerate-code",
        headers=bearer_header(other_token),
    )

    assert regenerate_response.status_code == 403


def test_client_cannot_supply_classroom_owner_or_code(
    client,
    db_session,
):
    instructor = create_test_user(
        db_session,
        name="Test Instructor",
        role="instructor",
        school_id="1000000008",
        email="faculty8@pampangastateu.edu.ph",
    )

    token = login_and_get_token(
        client,
        email=instructor.email,
    )

    response = client.post(
        "/classrooms/",
        headers=bearer_header(token),
        json={
            "name": "Invalid Classroom",
            "subject_code": "CCS102",
            "section": "BSIT 2A",
            "instructor_id": instructor.user_id,
            "class_code": "MANUAL01",
        },
    )

    assert response.status_code == 422
    assert db_session.query(Classroom).count() == 0
