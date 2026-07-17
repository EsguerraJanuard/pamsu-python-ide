import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.domain_models import (
    AcademicEvent,
    Notification,
    User,
)


def create_test_user(
    db_session: Session,
    *,
    name: str,
    school_id: str,
    email: str,
    role: str = "student",
) -> User:
    user = User(
        name=name,
        school_id=school_id,
        email=email,
        role=role,
        password_hash="fakehash",
        email_verified=True,
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def create_academic_event(
    db_session: Session,
    *,
    event_key: str,
    actor_user_id: int | None,
    event_type: str = "activity_published",
    resource_type: str = "task",
    resource_id: str = "1",
) -> AcademicEvent:
    academic_event = AcademicEvent(
        event_key=event_key,
        event_type=event_type,
        actor_user_id=actor_user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        event_data={
            "task_id": int(resource_id),
            "title": "Python Activity",
        },
    )

    db_session.add(academic_event)
    db_session.commit()
    db_session.refresh(academic_event)

    return academic_event


def test_notification_tables_are_registered():
    assert AcademicEvent.__tablename__ in Base.metadata.tables

    assert Notification.__tablename__ in Base.metadata.tables


def test_academic_event_and_notification_are_created(
    db_session: Session,
):
    instructor = create_test_user(
        db_session,
        name="Notification Instructor",
        school_id="8100000001",
        email=("notification.instructor@pampangastateu.edu.ph"),
        role="instructor",
    )

    student = create_test_user(
        db_session,
        name="Notification Student",
        school_id="8200000001",
        email=("notification.student@pampangastateu.edu.ph"),
    )

    academic_event = create_academic_event(
        db_session,
        event_key="activity-published:1:v1",
        actor_user_id=instructor.user_id,
    )

    notification = Notification(
        event_id=academic_event.event_id,
        recipient_id=student.user_id,
        title="New activity published",
        message=("Python Activity is now available."),
    )

    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    assert notification.notification_id
    assert notification.event_id == (academic_event.event_id)
    assert notification.recipient_id == (student.user_id)
    assert notification.is_read is False
    assert notification.read_at is None
    assert notification.created_at is not None
    assert notification.updated_at is not None


def test_duplicate_academic_event_key_is_rejected(
    db_session: Session,
):
    instructor = create_test_user(
        db_session,
        name="Duplicate Event Instructor",
        school_id="8100000002",
        email=("duplicate.event.instructor@pampangastateu.edu.ph"),
        role="instructor",
    )

    create_academic_event(
        db_session,
        event_key="activity-published:2:v1",
        actor_user_id=instructor.user_id,
        resource_id="2",
    )

    duplicate_event = AcademicEvent(
        event_key="activity-published:2:v1",
        event_type="activity_published",
        actor_user_id=instructor.user_id,
        resource_type="task",
        resource_id="2",
        event_data={
            "task_id": 2,
            "title": "Duplicate Activity",
        },
    )

    db_session.add(duplicate_event)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_duplicate_notification_for_same_event_and_recipient_is_rejected(
    db_session: Session,
):
    instructor = create_test_user(
        db_session,
        name="Duplicate Notification Instructor",
        school_id="8100000003",
        email=("duplicate.notification.instructor@pampangastateu.edu.ph"),
        role="instructor",
    )

    student = create_test_user(
        db_session,
        name="Duplicate Notification Student",
        school_id="8200000002",
        email=("duplicate.notification.student@pampangastateu.edu.ph"),
    )

    academic_event = create_academic_event(
        db_session,
        event_key="activity-published:3:v1",
        actor_user_id=instructor.user_id,
        resource_id="3",
    )

    first_notification = Notification(
        event_id=academic_event.event_id,
        recipient_id=student.user_id,
        title="Activity published",
        message="An activity is available.",
    )

    db_session.add(first_notification)
    db_session.commit()

    duplicate_notification = Notification(
        event_id=academic_event.event_id,
        recipient_id=student.user_id,
        title="Duplicate notification",
        message="This must not be saved.",
    )

    db_session.add(duplicate_notification)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_same_event_can_notify_multiple_recipients(
    db_session: Session,
):
    instructor = create_test_user(
        db_session,
        name="Multiple Recipient Instructor",
        school_id="8100000004",
        email=("multiple.recipient.instructor@pampangastateu.edu.ph"),
        role="instructor",
    )

    first_student = create_test_user(
        db_session,
        name="First Recipient",
        school_id="8200000003",
        email=("first.notification.recipient@pampangastateu.edu.ph"),
    )

    second_student = create_test_user(
        db_session,
        name="Second Recipient",
        school_id="8200000004",
        email=("second.notification.recipient@pampangastateu.edu.ph"),
    )

    academic_event = create_academic_event(
        db_session,
        event_key="activity-published:4:v1",
        actor_user_id=instructor.user_id,
        resource_id="4",
    )

    notifications = [
        Notification(
            event_id=academic_event.event_id,
            recipient_id=first_student.user_id,
            title="Activity published",
            message="An activity is available.",
        ),
        Notification(
            event_id=academic_event.event_id,
            recipient_id=second_student.user_id,
            title="Activity published",
            message="An activity is available.",
        ),
    ]

    db_session.add_all(notifications)
    db_session.commit()

    saved_notifications = (
        db_session.query(Notification)
        .filter(
            Notification.event_id == academic_event.event_id,
        )
        .all()
    )

    assert len(saved_notifications) == 2

    recipient_ids = {notification.recipient_id for notification in saved_notifications}

    assert recipient_ids == {
        first_student.user_id,
        second_student.user_id,
    }


@pytest.mark.parametrize(
    "invalid_event_type",
    [
        "automatic_misconduct_verdict",
        "source_code_copied",
        "unknown_event",
    ],
)
def test_invalid_academic_event_type_is_rejected(
    db_session: Session,
    invalid_event_type: str,
):
    event = AcademicEvent(
        event_key=(f"invalid-event-type:{invalid_event_type}"),
        event_type=invalid_event_type,
        actor_user_id=None,
        resource_type="task",
        resource_id="5",
        event_data={},
    )

    db_session.add(event)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


@pytest.mark.parametrize(
    "invalid_resource_type",
    [
        "source_code",
        "clipboard",
        "similarity_verdict",
    ],
)
def test_invalid_academic_resource_type_is_rejected(
    db_session: Session,
    invalid_resource_type: str,
):
    event = AcademicEvent(
        event_key=(f"invalid-resource-type:{invalid_resource_type}"),
        event_type="activity_published",
        actor_user_id=None,
        resource_type=invalid_resource_type,
        resource_id="6",
        event_data={},
    )

    db_session.add(event)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_notification_relationships_are_connected(
    db_session: Session,
):
    instructor = create_test_user(
        db_session,
        name="Relationship Instructor",
        school_id="8100000005",
        email=("relationship.instructor@pampangastateu.edu.ph"),
        role="instructor",
    )

    student = create_test_user(
        db_session,
        name="Relationship Student",
        school_id="8200000005",
        email=("relationship.student@pampangastateu.edu.ph"),
    )

    academic_event = create_academic_event(
        db_session,
        event_key="activity-published:7:v1",
        actor_user_id=instructor.user_id,
        resource_id="7",
    )

    notification = Notification(
        event_id=academic_event.event_id,
        recipient_id=student.user_id,
        title="Activity available",
        message="A new activity was published.",
    )

    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    assert academic_event.actor.user_id == (instructor.user_id)

    assert notification.recipient.user_id == (student.user_id)

    assert notification.academic_event.event_id == academic_event.event_id

    assert notification in (student.notifications_received)

    assert notification in (academic_event.notifications)
