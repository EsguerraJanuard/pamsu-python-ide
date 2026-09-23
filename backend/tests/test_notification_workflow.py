from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.main import app
from app.models.domain_models import (
    AcademicEvent,
    Classroom,
    Enrollment,
    Notification,
    Submission,
    Task,
    User,
)
from app.schemas.classroom_schema import (
    ClassroomUpdate,
)
from app.schemas.evaluation_schema import (
    InstructorGradeCreate,
    InstructorGradeUpdate,
)
from app.schemas.notification_schema import (
    AcademicEventCreate,
)
from app.schemas.submission_schema import (
    SubmissionCreate,
)
import app.services.classroom_service as classroom_service_module
import app.services.submission_service as submission_service_module
import app.services.task_service as task_service_module
from app.services.classroom_service import (
    ClassroomNotificationWorkflowError,
    update_classroom,
)
from app.services.evaluation_service import (
    create_or_update_grade,
    patch_grade,
)
from app.services.submission_service import (
    SubmissionNotificationWorkflowError,
    create_student_submission,
)
from app.services.task_service import (
    TaskNotificationWorkflowError,
    set_task_publication,
)
from app.services.notification_service import (
    AcademicEventConflictError,
    NotificationRecipientUnavailableError,
    NotificationServiceError,
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


@pytest.fixture
def approved_event_context(
    db_session: Session,
    notification_student: User,
    notification_instructor: User,
    other_notification_user: User,
    inactive_notification_user: User,
) -> dict[str, object]:
    """
    Build one privacy-sensitive academic workflow context.

    Only notification_student is both actively enrolled and eligible
    to receive student-facing classroom notifications.
    """

    classroom = Classroom(
        instructor_id=notification_instructor.user_id,
        name="Notification Integration Class",
        subject_code="CS-NOTIFY",
        section="N1",
        class_code="NTFY8001",
        is_active=True,
        archived_at=None,
    )

    db_session.add(classroom)
    db_session.flush()

    active_enrollment = Enrollment(
        class_id=classroom.class_id,
        student_id=notification_student.user_id,
        status="active",
        deactivated_at=None,
    )

    disabled_enrollment = Enrollment(
        class_id=classroom.class_id,
        student_id=other_notification_user.user_id,
        status="disabled",
        deactivated_at=datetime.now(timezone.utc),
    )

    inactive_user_enrollment = Enrollment(
        class_id=classroom.class_id,
        student_id=inactive_notification_user.user_id,
        status="active",
        deactivated_at=None,
    )

    task = Task(
        class_id=classroom.class_id,
        instructor_id=notification_instructor.user_id,
        title="Notification Integration Activity",
        description="PRIVATE DESCRIPTION",
        instructions="PRIVATE INSTRUCTIONS",
        activity_type="laboratory",
        required_ast_rules={
            "required_function": "private_function",
        },
        starter_code="SECRET_STARTER_CODE",
        paste_policy="internal_only",
        is_graded=True,
        is_published=False,
        due_at=(datetime.now(timezone.utc) + timedelta(days=2)),
        published_at=None,
    )

    db_session.add_all(
        [
            active_enrollment,
            disabled_enrollment,
            inactive_user_enrollment,
            task,
        ]
    )
    db_session.commit()

    db_session.refresh(classroom)
    db_session.refresh(task)

    return {
        "classroom": classroom,
        "task": task,
        "active_student": notification_student,
        "instructor": notification_instructor,
        "disabled_student": other_notification_user,
        "inactive_student": inactive_notification_user,
    }


def _event_rows(
    db_session: Session,
    *,
    event_type: str,
) -> list[AcademicEvent]:
    return (
        db_session.query(AcademicEvent)
        .filter(
            AcademicEvent.event_type == event_type,
        )
        .order_by(
            AcademicEvent.created_at.asc(),
            AcademicEvent.event_id.asc(),
        )
        .all()
    )


def _notification_rows_for_event(
    db_session: Session,
    *,
    event_id: str,
) -> list[Notification]:
    return (
        db_session.query(Notification)
        .filter(
            Notification.event_id == event_id,
        )
        .order_by(
            Notification.recipient_id.asc(),
        )
        .all()
    )


def _assert_privacy_safe(
    *,
    event: AcademicEvent,
    notification: Notification,
    prohibited_values: set[str],
) -> None:
    prohibited_event_keys = {
        "raw_code",
        "source_code",
        "starter_code",
        "instructions",
        "standard_input",
        "expected_output",
        "hidden_test_cases",
        "ast_details",
        "required_ast_rules",
        "jaccard_score",
        "similarity_results",
        "stdout",
        "stderr",
        "coding_session",
        "clipboard_text",
        "pasted_text",
        "score",
        "max_score",
        "feedback",
        "unreleased_score",
        "unreleased_feedback",
        "risk_score",
        "plagiarism_verdict",
        "misconduct_verdict",
    }

    assert prohibited_event_keys.isdisjoint(event.event_data)

    rendered_payload = f"{event.event_data} {notification.title} {notification.message}"

    for prohibited_value in prohibited_values:
        assert prohibited_value not in rendered_payload


def test_activity_publication_notifies_only_eligible_students_once(
    db_session: Session,
    approved_event_context: dict[str, object],
):
    task = approved_event_context["task"]
    instructor = approved_event_context["instructor"]
    active_student = approved_event_context["active_student"]

    published_task = set_task_publication(
        db=db_session,
        task_id=task.task_id,
        instructor_id=instructor.user_id,
        is_published=True,
    )

    assert published_task.is_published is True
    assert published_task.published_at is not None

    events = _event_rows(
        db_session,
        event_type="activity_published",
    )

    assert len(events) == 1

    event = events[0]

    assert event.actor_user_id == instructor.user_id
    assert event.resource_type == "task"
    assert event.resource_id == str(task.task_id)
    assert set(event.event_data) == {
        "task_id",
        "class_id",
        "activity_type",
        "published_at",
    }

    notifications = _notification_rows_for_event(
        db_session,
        event_id=event.event_id,
    )

    assert len(notifications) == 1
    assert notifications[0].recipient_id == active_student.user_id

    _assert_privacy_safe(
        event=event,
        notification=notifications[0],
        prohibited_values={
            "SECRET_STARTER_CODE",
            "PRIVATE INSTRUCTIONS",
            "PRIVATE DESCRIPTION",
            "private_function",
        },
    )

    original_published_at = published_task.published_at

    repeated_task = set_task_publication(
        db=db_session,
        task_id=task.task_id,
        instructor_id=instructor.user_id,
        is_published=True,
    )

    assert repeated_task.published_at == original_published_at

    assert (
        db_session.query(AcademicEvent)
        .filter(
            AcademicEvent.event_type == "activity_published",
        )
        .count()
        == 1
    )

    assert (
        db_session.query(Notification)
        .join(
            AcademicEvent,
            Notification.event_id == AcademicEvent.event_id,
        )
        .filter(
            AcademicEvent.event_type == "activity_published",
        )
        .count()
        == 1
    )


def test_activity_notification_failure_preserves_publication_for_retry(
    db_session: Session,
    approved_event_context: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
):
    task = approved_event_context["task"]
    instructor = approved_event_context["instructor"]

    original_notify = task_service_module.notify_activity_published

    def fail_notification(*args, **kwargs):
        raise NotificationServiceError("Forced activity notification failure.")

    monkeypatch.setattr(
        task_service_module,
        "notify_activity_published",
        fail_notification,
    )

    with pytest.raises(TaskNotificationWorkflowError):
        set_task_publication(
            db=db_session,
            task_id=task.task_id,
            instructor_id=instructor.user_id,
            is_published=True,
        )

    persisted_task = (
        db_session.query(Task)
        .filter(
            Task.task_id == task.task_id,
        )
        .first()
    )

    assert persisted_task is not None
    assert persisted_task.is_published is True
    assert persisted_task.published_at is not None

    assert (
        db_session.query(AcademicEvent)
        .filter(
            AcademicEvent.event_type == "activity_published",
        )
        .count()
        == 0
    )

    monkeypatch.setattr(
        task_service_module,
        "notify_activity_published",
        original_notify,
    )

    set_task_publication(
        db=db_session,
        task_id=task.task_id,
        instructor_id=instructor.user_id,
        is_published=True,
    )

    assert (
        db_session.query(AcademicEvent)
        .filter(
            AcademicEvent.event_type == "activity_published",
        )
        .count()
        == 1
    )


def test_submission_creation_notifies_owning_instructor_without_code(
    db_session: Session,
    approved_event_context: dict[str, object],
):
    task = approved_event_context["task"]
    instructor = approved_event_context["instructor"]
    student = approved_event_context["active_student"]

    set_task_publication(
        db=db_session,
        task_id=task.task_id,
        instructor_id=instructor.user_id,
        is_published=True,
    )

    submission = create_student_submission(
        db_session,
        student_id=student.user_id,
        payload=SubmissionCreate.model_construct(
            task_id=task.task_id,
            coding_session_id=None,
            raw_code="SECRET_SUBMISSION_CODE",
            standard_input="SECRET_STANDARD_INPUT",
        ),
    )

    assert submission.student_id == student.user_id
    assert submission.task_id == task.task_id
    assert submission.is_official is True
    assert submission.attempt_number == 1

    events = _event_rows(
        db_session,
        event_type="submission_created",
    )

    assert len(events) == 1

    event = events[0]

    assert event.actor_user_id == student.user_id
    assert event.resource_type == "submission"
    assert event.resource_id == str(submission.sub_id)

    notifications = _notification_rows_for_event(
        db_session,
        event_id=event.event_id,
    )

    assert len(notifications) == 1
    assert notifications[0].recipient_id == instructor.user_id

    _assert_privacy_safe(
        event=event,
        notification=notifications[0],
        prohibited_values={
            "SECRET_SUBMISSION_CODE",
            "SECRET_STANDARD_INPUT",
            "SECRET_STARTER_CODE",
            "PRIVATE INSTRUCTIONS",
        },
    )


def test_submission_notification_failure_rolls_back_new_attempt(
    db_session: Session,
    approved_event_context: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
):
    task = approved_event_context["task"]
    instructor = approved_event_context["instructor"]
    student = approved_event_context["active_student"]

    set_task_publication(
        db=db_session,
        task_id=task.task_id,
        instructor_id=instructor.user_id,
        is_published=True,
    )

    def fail_notification(*args, **kwargs):
        raise NotificationServiceError("Forced submission notification failure.")

    monkeypatch.setattr(
        submission_service_module,
        "notify_submission_created",
        fail_notification,
    )

    with pytest.raises(SubmissionNotificationWorkflowError):
        create_student_submission(
            db_session,
            student_id=student.user_id,
            payload=SubmissionCreate.model_construct(
                task_id=task.task_id,
                coding_session_id=None,
                raw_code="ROLLBACK_SECRET_CODE",
                standard_input="ROLLBACK_SECRET_INPUT",
            ),
        )

    assert (
        db_session.query(Submission)
        .filter(
            Submission.student_id == student.user_id,
            Submission.task_id == task.task_id,
        )
        .count()
        == 0
    )

    assert (
        db_session.query(AcademicEvent)
        .filter(
            AcademicEvent.event_type == "submission_created",
        )
        .count()
        == 0
    )


def test_grade_release_notifies_student_only_on_release_transition(
    db_session: Session,
    approved_event_context: dict[str, object],
):
    task = approved_event_context["task"]
    instructor = approved_event_context["instructor"]
    student = approved_event_context["active_student"]

    set_task_publication(
        db=db_session,
        task_id=task.task_id,
        instructor_id=instructor.user_id,
        is_published=True,
    )

    submission = create_student_submission(
        db_session,
        student_id=student.user_id,
        payload=SubmissionCreate.model_construct(
            task_id=task.task_id,
            coding_session_id=None,
            raw_code="GRADE_SECRET_CODE",
            standard_input="GRADE_SECRET_INPUT",
        ),
    )

    grade = create_or_update_grade(
        db_session,
        sub_id=submission.sub_id,
        grade_in=InstructorGradeCreate.model_construct(
            score=88.0,
            max_score=100.0,
            feedback="PRIVATE GRADE FEEDBACK",
            is_released=False,
        ),
        current_user=instructor,
    )

    assert grade.is_released is False

    assert (
        db_session.query(AcademicEvent)
        .filter(
            AcademicEvent.event_type == "grade_released",
        )
        .count()
        == 0
    )

    released_grade = patch_grade(
        db_session,
        sub_id=submission.sub_id,
        grade_update=InstructorGradeUpdate.model_construct(
            is_released=True,
        ),
        current_user=instructor,
    )

    assert released_grade.is_released is True

    events = _event_rows(
        db_session,
        event_type="grade_released",
    )

    assert len(events) == 1

    event = events[0]

    assert event.actor_user_id == instructor.user_id
    assert event.resource_type == "grade"
    assert event.resource_id == str(released_grade.grade_id)

    notifications = _notification_rows_for_event(
        db_session,
        event_id=event.event_id,
    )

    assert len(notifications) == 1
    assert notifications[0].recipient_id == student.user_id

    _assert_privacy_safe(
        event=event,
        notification=notifications[0],
        prohibited_values={
            "PRIVATE GRADE FEEDBACK",
            "GRADE_SECRET_CODE",
            "GRADE_SECRET_INPUT",
        },
    )

    patch_grade(
        db_session,
        sub_id=submission.sub_id,
        grade_update=InstructorGradeUpdate.model_construct(
            score=90.0,
            feedback="UPDATED PRIVATE FEEDBACK",
        ),
        current_user=instructor,
    )

    patch_grade(
        db_session,
        sub_id=submission.sub_id,
        grade_update=InstructorGradeUpdate.model_construct(
            is_released=True,
        ),
        current_user=instructor,
    )

    assert (
        db_session.query(AcademicEvent)
        .filter(
            AcademicEvent.event_type == "grade_released",
        )
        .count()
        == 1
    )

    assert (
        db_session.query(Notification)
        .filter(
            Notification.event_id == event.event_id,
        )
        .count()
        == 1
    )


def test_classroom_archive_notifies_only_active_eligible_students_once(
    db_session: Session,
    approved_event_context: dict[str, object],
):
    classroom = approved_event_context["classroom"]
    instructor = approved_event_context["instructor"]
    active_student = approved_event_context["active_student"]

    archived_classroom = update_classroom(
        db=db_session,
        class_id=classroom.class_id,
        instructor_id=instructor.user_id,
        classroom_data=ClassroomUpdate.model_construct(
            is_active=False,
        ),
    )

    assert archived_classroom.is_active is False
    assert archived_classroom.archived_at is not None

    events = _event_rows(
        db_session,
        event_type="classroom_archived",
    )

    assert len(events) == 1

    event = events[0]

    assert event.actor_user_id == instructor.user_id
    assert event.resource_type == "classroom"
    assert event.resource_id == str(classroom.class_id)
    assert set(event.event_data) == {
        "class_id",
        "archived_at",
    }

    notifications = _notification_rows_for_event(
        db_session,
        event_id=event.event_id,
    )

    assert len(notifications) == 1
    assert notifications[0].recipient_id == active_student.user_id

    _assert_privacy_safe(
        event=event,
        notification=notifications[0],
        prohibited_values={
            classroom.class_code,
            approved_event_context["disabled_student"].email,
            approved_event_context["inactive_student"].email,
            "SECRET_STARTER_CODE",
            "PRIVATE INSTRUCTIONS",
        },
    )

    original_archived_at = archived_classroom.archived_at

    repeated_archive = update_classroom(
        db=db_session,
        class_id=classroom.class_id,
        instructor_id=instructor.user_id,
        classroom_data=ClassroomUpdate.model_construct(
            is_active=False,
        ),
    )

    assert repeated_archive.archived_at == original_archived_at

    assert (
        db_session.query(AcademicEvent)
        .filter(
            AcademicEvent.event_type == "classroom_archived",
        )
        .count()
        == 1
    )

    assert (
        db_session.query(Notification)
        .filter(
            Notification.event_id == event.event_id,
        )
        .count()
        == 1
    )


def test_classroom_archive_succeeds_without_active_recipients(
    db_session: Session,
    notification_instructor: User,
):
    empty_classroom = Classroom(
        instructor_id=notification_instructor.user_id,
        name="Empty Notification Class",
        subject_code="CS-EMPTY",
        section="E1",
        class_code="EMPTY801",
        is_active=True,
        archived_at=None,
    )

    db_session.add(empty_classroom)
    db_session.commit()
    db_session.refresh(empty_classroom)

    archived_classroom = update_classroom(
        db=db_session,
        class_id=empty_classroom.class_id,
        instructor_id=notification_instructor.user_id,
        classroom_data=ClassroomUpdate.model_construct(
            is_active=False,
        ),
    )

    assert archived_classroom.is_active is False
    assert archived_classroom.archived_at is not None

    assert (
        db_session.query(AcademicEvent)
        .filter(
            AcademicEvent.event_type == "classroom_archived",
        )
        .count()
        == 0
    )

    assert db_session.query(Notification).count() == 0


def test_classroom_notification_failure_rolls_back_archive(
    db_session: Session,
    approved_event_context: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
):
    classroom = approved_event_context["classroom"]
    instructor = approved_event_context["instructor"]

    def fail_notification(*args, **kwargs):
        raise NotificationServiceError("Forced classroom notification failure.")

    monkeypatch.setattr(
        classroom_service_module,
        "notify_classroom_archived",
        fail_notification,
    )

    with pytest.raises(ClassroomNotificationWorkflowError):
        update_classroom(
            db=db_session,
            class_id=classroom.class_id,
            instructor_id=instructor.user_id,
            classroom_data=ClassroomUpdate.model_construct(
                is_active=False,
            ),
        )

    persisted_classroom = (
        db_session.query(Classroom)
        .filter(
            Classroom.class_id == classroom.class_id,
        )
        .first()
    )

    assert persisted_classroom is not None
    assert persisted_classroom.is_active is True
    assert persisted_classroom.archived_at is None

    assert (
        db_session.query(AcademicEvent)
        .filter(
            AcademicEvent.event_type == "classroom_archived",
        )
        .count()
        == 0
    )
