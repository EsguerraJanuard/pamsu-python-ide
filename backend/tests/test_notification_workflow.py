from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.main import app
from app.models.domain_models import (
    AcademicEvent,
    Notification,
    User,
)
from app.schemas.notification_schema import (
    AcademicEventCreate,
)
from app.services.notification_service import (
    AcademicEventConflictError,
    NotificationRecipientUnavailableError,
    create_academic_event_notifications,
)


@pytest.fixture
def notification_student(
    db_session: Session,
) -> User:
    student = User(
        name="Notification Workflow Student",
        school_id="8300000001",
        email=("notification.workflow.student@pampangastateu.edu.ph"),
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
def notification_instructor(
    db_session: Session,
) -> User:
    instructor = User(
        name="Notification Workflow Instructor",
        school_id="8300000002",
        email=("notification.workflow.instructor@pampangastateu.edu.ph"),
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
def other_notification_user(
    db_session: Session,
) -> User:
    user = User(
        name="Other Notification User",
        school_id="8300000003",
        email=("other.notification.user@pampangastateu.edu.ph"),
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
def inactive_notification_user(
    db_session: Session,
) -> User:
    user = User(
        name="Inactive Notification User",
        school_id="8300000004",
        email=("inactive.notification.user@pampangastateu.edu.ph"),
        role="student",
        password_hash="fakehash",
        email_verified=True,
        is_active=False,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def notification_data(
    db_session: Session,
    notification_student: User,
    notification_instructor: User,
    other_notification_user: User,
) -> dict[str, object]:
    now = datetime.now(timezone.utc)

    oldest_event = AcademicEvent(
        event_key="workflow:activity-published:101",
        event_type="activity_published",
        actor_user_id=(notification_instructor.user_id),
        resource_type="task",
        resource_id="101",
        event_data={
            "task_id": 101,
            "title": "Loops Laboratory",
        },
        occurred_at=now - timedelta(days=3),
        created_at=now - timedelta(days=3),
    )

    read_event = AcademicEvent(
        event_key="workflow:submission-created:202",
        event_type="submission_created",
        actor_user_id=notification_student.user_id,
        resource_type="submission",
        resource_id="202",
        event_data={
            "submission_id": 202,
            "attempt_number": 1,
        },
        occurred_at=now - timedelta(days=2),
        created_at=now - timedelta(days=2),
    )

    newest_event = AcademicEvent(
        event_key="workflow:grade-released:303",
        event_type="grade_released",
        actor_user_id=(notification_instructor.user_id),
        resource_type="grade",
        resource_id="303",
        event_data={
            "grade_id": 303,
        },
        occurred_at=now - timedelta(days=1),
        created_at=now - timedelta(days=1),
    )

    other_event = AcademicEvent(
        event_key="workflow:classroom-archived:404",
        event_type="classroom_archived",
        actor_user_id=(notification_instructor.user_id),
        resource_type="classroom",
        resource_id="404",
        event_data={
            "class_id": 404,
        },
        occurred_at=now,
        created_at=now,
    )

    db_session.add_all(
        [
            oldest_event,
            read_event,
            newest_event,
            other_event,
        ]
    )
    db_session.commit()

    oldest_notification = Notification(
        event_id=oldest_event.event_id,
        recipient_id=notification_student.user_id,
        title="New activity published",
        message=("Loops Laboratory is now available."),
        is_read=False,
        read_at=None,
        created_at=now - timedelta(days=3),
        updated_at=now - timedelta(days=3),
    )

    read_notification = Notification(
        event_id=read_event.event_id,
        recipient_id=notification_student.user_id,
        title="Submission received",
        message=("Your submission attempt was received."),
        is_read=True,
        read_at=now - timedelta(days=1),
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=1),
    )

    newest_notification = Notification(
        event_id=newest_event.event_id,
        recipient_id=notification_student.user_id,
        title="Grade released",
        message=("A manual grade is now available."),
        is_read=False,
        read_at=None,
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1),
    )

    other_notification = Notification(
        event_id=other_event.event_id,
        recipient_id=other_notification_user.user_id,
        title="Classroom archived",
        message=("A classroom has been archived."),
        is_read=False,
        read_at=None,
        created_at=now,
        updated_at=now,
    )

    db_session.add_all(
        [
            oldest_notification,
            read_notification,
            newest_notification,
            other_notification,
        ]
    )
    db_session.commit()

    db_session.refresh(oldest_notification)
    db_session.refresh(read_notification)
    db_session.refresh(newest_notification)
    db_session.refresh(other_notification)

    return {
        "oldest_notification": (oldest_notification),
        "read_notification": (read_notification),
        "newest_notification": (newest_notification),
        "other_notification": (other_notification),
    }


@pytest.fixture
def notification_client(
    client: TestClient,
    notification_student: User,
):
    app.dependency_overrides[get_current_user] = lambda: notification_student

    yield client

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


@pytest.fixture
def forbidden_notification_client(
    client: TestClient,
):
    def reject_unauthenticated_user() -> User:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=("Could not validate authentication credentials."),
        )

    app.dependency_overrides[get_current_user] = reject_unauthenticated_user

    yield client

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


def test_user_lists_only_own_safe_notifications(
    notification_client: TestClient,
    notification_data: dict[str, object],
):
    response = notification_client.get("/notifications/")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["total_items"] == 3
    assert data["total_pages"] == 1
    assert data["page"] == 1
    assert data["page_size"] == 25
    assert data["recipient_unread_count"] == 2
    assert data["read_filter"] == "all"
    assert data["sort_direction"] == "desc"

    returned_ids = {item["notification_id"] for item in data["items"]}

    assert notification_data["other_notification"].notification_id not in returned_ids

    prohibited_fields = {
        "recipient_id",
        "actor_user_id",
        "event_key",
        "event_data",
        "raw_code",
        "source_code",
        "standard_input",
        "expected_output",
        "ast_details",
        "jaccard_score",
        "similarity_results",
        "stdout",
        "stderr",
        "coding_session",
        "unreleased_score",
        "unreleased_feedback",
        "risk_score",
        "plagiarism_verdict",
        "misconduct_verdict",
    }

    for item in data["items"]:
        assert prohibited_fields.isdisjoint(item)


def test_notifications_default_to_latest_first(
    notification_client: TestClient,
    notification_data: dict[str, object],
):
    response = notification_client.get("/notifications/")

    assert response.status_code == status.HTTP_200_OK

    returned_ids = [item["notification_id"] for item in response.json()["items"]]

    assert returned_ids == [
        notification_data["newest_notification"].notification_id,
        notification_data["read_notification"].notification_id,
        notification_data["oldest_notification"].notification_id,
    ]


def test_notifications_support_unread_filter(
    notification_client: TestClient,
    notification_data: dict[str, object],
):
    response = notification_client.get(
        "/notifications/",
        params={
            "read_filter": "unread",
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["total_items"] == 2
    assert data["recipient_unread_count"] == 2

    assert all(item["is_read"] is False for item in data["items"])


def test_notifications_support_read_filter(
    notification_client: TestClient,
    notification_data: dict[str, object],
):
    response = notification_client.get(
        "/notifications/",
        params={
            "read_filter": "read",
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["total_items"] == 1
    assert data["recipient_unread_count"] == 2

    assert all(item["is_read"] is True for item in data["items"])


def test_notification_pagination_is_deterministic(
    notification_client: TestClient,
    notification_data: dict[str, object],
):
    first_page = notification_client.get(
        "/notifications/",
        params={
            "page": 1,
            "page_size": 2,
        },
    )

    second_page = notification_client.get(
        "/notifications/",
        params={
            "page": 2,
            "page_size": 2,
        },
    )

    assert first_page.status_code == status.HTTP_200_OK

    assert second_page.status_code == status.HTTP_200_OK

    first_data = first_page.json()
    second_data = second_page.json()

    assert first_data["total_items"] == 3
    assert first_data["total_pages"] == 2
    assert second_data["total_pages"] == 2

    first_ids = {item["notification_id"] for item in first_data["items"]}

    second_ids = {item["notification_id"] for item in second_data["items"]}

    assert len(first_ids) == 2
    assert len(second_ids) == 1
    assert first_ids.isdisjoint(second_ids)


def test_user_reads_own_unread_count(
    notification_client: TestClient,
    notification_data: dict[str, object],
):
    response = notification_client.get("/notifications/unread-count")

    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        "unread_count": 2,
    }


def test_user_gets_one_owned_notification(
    notification_client: TestClient,
    notification_data: dict[str, object],
):
    notification = notification_data["newest_notification"]

    response = notification_client.get(f"/notifications/{notification.notification_id}")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["notification_id"] == (notification.notification_id)

    assert data["event_type"] == ("grade_released")

    assert data["resource_type"] == "grade"
    assert data["resource_id"] == "303"


def test_user_cannot_get_another_users_notification(
    notification_client: TestClient,
    notification_data: dict[str, object],
):
    notification = notification_data["other_notification"]

    response = notification_client.get(f"/notifications/{notification.notification_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_mark_one_notification_read_is_idempotent(
    notification_client: TestClient,
    notification_data: dict[str, object],
):
    notification = notification_data["newest_notification"]

    first_response = notification_client.patch(
        f"/notifications/{notification.notification_id}/read"
    )

    assert first_response.status_code == status.HTTP_200_OK

    first_data = first_response.json()

    assert first_data["is_read"] is True
    assert first_data["read_at"] is not None

    original_read_at = first_data["read_at"]

    second_response = notification_client.patch(
        f"/notifications/{notification.notification_id}/read"
    )

    assert second_response.status_code == status.HTTP_200_OK

    second_data = second_response.json()

    assert second_data["is_read"] is True
    assert second_data["read_at"] == original_read_at


def test_mark_all_notifications_read_is_owner_scoped(
    notification_client: TestClient,
    notification_data: dict[str, object],
    db_session: Session,
):
    response = notification_client.patch("/notifications/read-all")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["marked_read_count"] == 2
    assert data["remaining_unread_count"] == 0
    assert data["marked_at"] is not None

    other_notification = (
        db_session.query(Notification)
        .filter(
            Notification.notification_id
            == notification_data["other_notification"].notification_id,
        )
        .first()
    )

    assert other_notification is not None
    assert other_notification.is_read is False
    assert other_notification.read_at is None


def test_authentication_is_required_for_notifications(
    forbidden_notification_client: TestClient,
):
    response = forbidden_notification_client.get("/notifications/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_notification_page_size_is_bounded(
    notification_client: TestClient,
):
    response = notification_client.get(
        "/notifications/",
        params={
            "page_size": 101,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_event_notification_creation_is_idempotent(
    db_session: Session,
    notification_student: User,
    notification_instructor: User,
    other_notification_user: User,
):
    event_payload = AcademicEventCreate(
        event_key=("service-idempotency:activity-published:500"),
        event_type="activity_published",
        actor_user_id=(notification_instructor.user_id),
        resource_type="task",
        resource_id="500",
        event_data={
            "task_id": 500,
            "title": "Idempotent Activity",
        },
    )

    recipient_ids = [
        notification_student.user_id,
        other_notification_user.user_id,
    ]

    first_result = create_academic_event_notifications(
        db_session,
        event_payload=event_payload,
        recipient_ids=recipient_ids,
        title="New activity published",
        message=("Idempotent Activity is now available."),
    )

    second_result = create_academic_event_notifications(
        db_session,
        event_payload=event_payload,
        recipient_ids=recipient_ids,
        title="New activity published",
        message=("Idempotent Activity is now available."),
    )

    assert first_result["academic_event_created"] is True

    assert first_result["created_notification_count"] == 2

    assert second_result["academic_event_created"] is False

    assert second_result["created_notification_count"] == 0

    event_count = (
        db_session.query(AcademicEvent)
        .filter(
            AcademicEvent.event_key == event_payload.event_key,
        )
        .count()
    )

    notification_count = (
        db_session.query(Notification)
        .join(
            AcademicEvent,
            Notification.event_id == AcademicEvent.event_id,
        )
        .filter(
            AcademicEvent.event_key == event_payload.event_key,
        )
        .count()
    )

    assert event_count == 1
    assert notification_count == 2


def test_event_key_conflict_is_rejected(
    db_session: Session,
    notification_student: User,
    notification_instructor: User,
):
    original_payload = AcademicEventCreate(
        event_key="service-conflict:task:600",
        event_type="activity_published",
        actor_user_id=(notification_instructor.user_id),
        resource_type="task",
        resource_id="600",
        event_data={
            "task_id": 600,
            "title": "Original Activity",
        },
    )

    create_academic_event_notifications(
        db_session,
        event_payload=original_payload,
        recipient_ids=[notification_student.user_id],
        title="Activity published",
        message=("Original Activity is now available."),
    )

    conflicting_payload = AcademicEventCreate(
        event_key="service-conflict:task:600",
        event_type="activity_updated",
        actor_user_id=(notification_instructor.user_id),
        resource_type="task",
        resource_id="600",
        event_data={
            "task_id": 600,
            "title": "Different Activity",
        },
    )

    with pytest.raises(AcademicEventConflictError):
        create_academic_event_notifications(
            db_session,
            event_payload=conflicting_payload,
            recipient_ids=[notification_student.user_id],
            title="Activity updated",
            message=("Different Activity was updated."),
        )

    event_count = (
        db_session.query(AcademicEvent)
        .filter(
            AcademicEvent.event_key == original_payload.event_key,
        )
        .count()
    )

    assert event_count == 1


def test_inactive_notification_recipient_is_rejected(
    db_session: Session,
    notification_instructor: User,
    inactive_notification_user: User,
):
    event_payload = AcademicEventCreate(
        event_key=("inactive-recipient:activity-published:700"),
        event_type="activity_published",
        actor_user_id=(notification_instructor.user_id),
        resource_type="task",
        resource_id="700",
        event_data={
            "task_id": 700,
        },
    )

    with pytest.raises(NotificationRecipientUnavailableError):
        create_academic_event_notifications(
            db_session,
            event_payload=event_payload,
            recipient_ids=[inactive_notification_user.user_id],
            title="Activity published",
            message=("An activity is now available."),
        )

    saved_event = (
        db_session.query(AcademicEvent)
        .filter(
            AcademicEvent.event_key == event_payload.event_key,
        )
        .first()
    )

    assert saved_event is None
