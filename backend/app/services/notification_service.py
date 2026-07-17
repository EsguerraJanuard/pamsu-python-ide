from datetime import datetime, timezone
from math import ceil
from typing import Any, Sequence

from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.orm import Session

from app.models.domain_models import (
    AcademicEvent,
    Notification,
    User,
)
from app.schemas.notification_schema import (
    AcademicEventCreate,
    MAX_NOTIFICATION_PAGE_SIZE,
    MIN_NOTIFICATION_PAGE_SIZE,
    NotificationCreate,
    NotificationReadFilter,
    NotificationSortDirection,
)


MAX_NOTIFICATION_RECIPIENTS_PER_EVENT = 5_000


class NotificationServiceError(Exception):
    """Base exception for notification workflow errors."""


class NotificationNotFoundError(
    NotificationServiceError,
):
    """Raised when a recipient-owned notification cannot be found."""


class NotificationPaginationError(
    NotificationServiceError,
):
    """Raised when notification pagination values are invalid."""


class NotificationRecipientUnavailableError(
    NotificationServiceError,
):
    """Raised when a notification recipient is unavailable."""


class AcademicEventActorUnavailableError(
    NotificationServiceError,
):
    """Raised when an academic-event actor does not exist."""


class AcademicEventConflictError(
    NotificationServiceError,
):
    """Raised when an event key is reused for different event data."""


class NotificationConflictError(
    NotificationServiceError,
):
    """Raised when an idempotent notification conflicts with saved data."""


class NotificationPersistenceError(
    NotificationServiceError,
):
    """Raised when a notification database operation fails."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_pagination(
    *,
    page: int,
    page_size: int,
) -> None:
    if page < 1:
        raise NotificationPaginationError("page must be greater than or equal to 1.")

    if not (MIN_NOTIFICATION_PAGE_SIZE <= page_size <= MAX_NOTIFICATION_PAGE_SIZE):
        raise NotificationPaginationError(
            "page_size must be between "
            f"{MIN_NOTIFICATION_PAGE_SIZE} and "
            f"{MAX_NOTIFICATION_PAGE_SIZE}."
        )


def _normalize_recipient_ids(
    recipient_ids: Sequence[int],
) -> list[int]:
    normalized_ids: list[int] = []
    seen_ids: set[int] = set()

    for recipient_id in recipient_ids:
        if recipient_id <= 0:
            raise NotificationRecipientUnavailableError(
                "Notification recipient IDs must be positive."
            )

        if recipient_id in seen_ids:
            continue

        seen_ids.add(recipient_id)
        normalized_ids.append(recipient_id)

    if not normalized_ids:
        raise NotificationRecipientUnavailableError(
            "At least one notification recipient is required."
        )

    if len(normalized_ids) > MAX_NOTIFICATION_RECIPIENTS_PER_EVENT:
        raise NotificationRecipientUnavailableError(
            "The academic event has too many notification recipients."
        )

    return normalized_ids


def _validate_event_actor(
    db: Session,
    *,
    actor_user_id: int | None,
) -> None:
    if actor_user_id is None:
        return

    actor_exists = (
        db.query(User.user_id)
        .filter(
            User.user_id == actor_user_id,
        )
        .first()
    )

    if actor_exists is None:
        raise AcademicEventActorUnavailableError(
            "The academic-event actor is unavailable."
        )


def _validate_recipients(
    db: Session,
    *,
    recipient_ids: list[int],
) -> None:
    available_recipient_ids = {
        row.user_id
        for row in (
            db.query(User.user_id)
            .filter(
                User.user_id.in_(recipient_ids),
                User.is_active.is_(True),
            )
            .all()
        )
    }

    unavailable_ids = set(recipient_ids) - available_recipient_ids

    if unavailable_ids:
        raise NotificationRecipientUnavailableError(
            "One or more notification recipients are unavailable."
        )


def _academic_event_matches(
    academic_event: AcademicEvent,
    payload: AcademicEventCreate,
) -> bool:
    return (
        academic_event.event_type == payload.event_type
        and academic_event.actor_user_id == payload.actor_user_id
        and academic_event.resource_type == payload.resource_type
        and academic_event.resource_id == payload.resource_id
        and (academic_event.event_data or {}) == payload.event_data
    )


def _resolve_academic_event(
    db: Session,
    *,
    payload: AcademicEventCreate,
) -> tuple[AcademicEvent, bool]:
    existing_event = (
        db.query(AcademicEvent)
        .filter(
            AcademicEvent.event_key == payload.event_key,
        )
        .first()
    )

    if existing_event is not None:
        if not _academic_event_matches(
            existing_event,
            payload,
        ):
            raise AcademicEventConflictError(
                "The academic-event key is already associated "
                "with different event data."
            )

        return existing_event, False

    academic_event = AcademicEvent(
        event_key=payload.event_key,
        event_type=payload.event_type,
        actor_user_id=payload.actor_user_id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        event_data=payload.event_data,
    )

    db.add(academic_event)
    db.flush()

    return academic_event, True


def _notification_matches(
    notification: Notification,
    *,
    title: str,
    message: str,
) -> bool:
    return notification.title == title and notification.message == message


def _load_event_notifications(
    db: Session,
    *,
    event_id: str,
    recipient_ids: list[int],
) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(
            Notification.event_id == event_id,
            Notification.recipient_id.in_(recipient_ids),
        )
        .order_by(
            Notification.recipient_id.asc(),
            Notification.notification_id.asc(),
        )
        .all()
    )


def _recover_idempotent_event_notifications(
    db: Session,
    *,
    event_payload: AcademicEventCreate,
    recipient_ids: list[int],
    title: str,
    message: str,
) -> dict[str, Any] | None:
    academic_event = (
        db.query(AcademicEvent)
        .filter(
            AcademicEvent.event_key == event_payload.event_key,
        )
        .first()
    )

    if academic_event is None:
        return None

    if not _academic_event_matches(
        academic_event,
        event_payload,
    ):
        raise AcademicEventConflictError(
            "The academic-event key is already associated with different event data."
        )

    notifications = _load_event_notifications(
        db,
        event_id=academic_event.event_id,
        recipient_ids=recipient_ids,
    )

    if len(notifications) != len(recipient_ids):
        return None

    for notification in notifications:
        if not _notification_matches(
            notification,
            title=title,
            message=message,
        ):
            raise NotificationConflictError(
                "The academic event already has a different "
                "notification for one or more recipients."
            )

    return {
        "academic_event": academic_event,
        "notifications": notifications,
        "academic_event_created": False,
        "created_notification_count": 0,
    }


def create_academic_event_notifications(
    db: Session,
    *,
    event_payload: AcademicEventCreate,
    recipient_ids: Sequence[int],
    title: str,
    message: str,
) -> dict[str, Any]:
    """
    Create or reuse an immutable academic event and create one
    recipient-specific notification per active user.

    Repeating the same event key, recipients, title, and message is
    idempotent. Reusing an event key for different event data or
    conflicting notification content is rejected.
    """

    normalized_recipient_ids = _normalize_recipient_ids(recipient_ids)

    _validate_event_actor(
        db,
        actor_user_id=(event_payload.actor_user_id),
    )

    _validate_recipients(
        db,
        recipient_ids=(normalized_recipient_ids),
    )

    try:
        (
            academic_event,
            academic_event_created,
        ) = _resolve_academic_event(
            db,
            payload=event_payload,
        )

        existing_notifications = _load_event_notifications(
            db,
            event_id=academic_event.event_id,
            recipient_ids=(normalized_recipient_ids),
        )

        existing_by_recipient = {
            notification.recipient_id: notification
            for notification in existing_notifications
        }

        notifications_to_create: list[Notification] = []

        for recipient_id in normalized_recipient_ids:
            existing_notification = existing_by_recipient.get(recipient_id)

            if existing_notification is not None:
                if not _notification_matches(
                    existing_notification,
                    title=title,
                    message=message,
                ):
                    raise NotificationConflictError(
                        "The academic event already has a different "
                        "notification for this recipient."
                    )

                continue

            validated_notification = NotificationCreate(
                event_id=academic_event.event_id,
                recipient_id=recipient_id,
                title=title,
                message=message,
            )

            notification = Notification(
                event_id=(validated_notification.event_id),
                recipient_id=(validated_notification.recipient_id),
                title=validated_notification.title,
                message=validated_notification.message,
            )

            db.add(notification)

            notifications_to_create.append(notification)

        db.commit()

    except NotificationServiceError:
        db.rollback()
        raise

    except IntegrityError as error:
        db.rollback()

        recovered_result = _recover_idempotent_event_notifications(
            db,
            event_payload=event_payload,
            recipient_ids=(normalized_recipient_ids),
            title=title.strip(),
            message=message.strip(),
        )

        if recovered_result is not None:
            return recovered_result

        raise NotificationConflictError(
            "The academic event or notification was created "
            "concurrently. Please retry the operation."
        ) from error

    except SQLAlchemyError as error:
        db.rollback()

        raise NotificationPersistenceError(
            "The academic event notifications could not be saved."
        ) from error

    notifications = _load_event_notifications(
        db,
        event_id=academic_event.event_id,
        recipient_ids=(normalized_recipient_ids),
    )

    return {
        "academic_event": academic_event,
        "notifications": notifications,
        "academic_event_created": (academic_event_created),
        "created_notification_count": len(notifications_to_create),
    }


def _build_notification_item(
    row: Any,
) -> dict[str, Any]:
    return {
        "notification_id": (row.notification_id),
        "event_id": row.event_id,
        "event_type": row.event_type,
        "resource_type": (row.resource_type),
        "resource_id": row.resource_id,
        "title": row.title,
        "message": row.message,
        "is_read": row.is_read,
        "read_at": row.read_at,
        "occurred_at": row.occurred_at,
        "created_at": row.created_at,
    }


def _build_recipient_notification_query(
    db: Session,
    *,
    recipient_id: int,
) -> Any:
    return (
        db.query(
            Notification.notification_id.label("notification_id"),
            Notification.event_id.label("event_id"),
            Notification.title.label("title"),
            Notification.message.label("message"),
            Notification.is_read.label("is_read"),
            Notification.read_at.label("read_at"),
            Notification.created_at.label("created_at"),
            AcademicEvent.event_type.label("event_type"),
            AcademicEvent.resource_type.label("resource_type"),
            AcademicEvent.resource_id.label("resource_id"),
            AcademicEvent.occurred_at.label("occurred_at"),
        )
        .join(
            AcademicEvent,
            Notification.event_id == AcademicEvent.event_id,
        )
        .filter(
            Notification.recipient_id == recipient_id,
        )
    )


def _apply_read_filter(
    query: Any,
    *,
    read_filter: NotificationReadFilter,
) -> Any:
    if read_filter == "unread":
        return query.filter(
            Notification.is_read.is_(False),
        )

    if read_filter == "read":
        return query.filter(
            Notification.is_read.is_(True),
        )

    return query


def _apply_notification_ordering(
    query: Any,
    *,
    sort_direction: NotificationSortDirection,
) -> Any:
    if sort_direction == "asc":
        return query.order_by(
            Notification.created_at.asc(),
            Notification.notification_id.asc(),
        )

    return query.order_by(
        Notification.created_at.desc(),
        Notification.notification_id.desc(),
    )


def count_user_unread_notifications(
    db: Session,
    *,
    recipient_id: int,
) -> int:
    return int(
        db.query(Notification)
        .filter(
            Notification.recipient_id == recipient_id,
            Notification.is_read.is_(False),
        )
        .count()
    )


def list_user_notifications(
    db: Session,
    *,
    recipient_id: int,
    page: int = 1,
    page_size: int = 25,
    read_filter: NotificationReadFilter = "all",
    sort_direction: NotificationSortDirection = "desc",
) -> dict[str, Any]:
    """
    Return only notifications belonging to the authenticated recipient.

    Academic-event event_data is intentionally not selected.
    """

    _validate_pagination(
        page=page,
        page_size=page_size,
    )

    query = _build_recipient_notification_query(
        db,
        recipient_id=recipient_id,
    )

    query = _apply_read_filter(
        query,
        read_filter=read_filter,
    )

    total_items = query.order_by(None).count()

    offset = (page - 1) * page_size

    rows = (
        _apply_notification_ordering(
            query,
            sort_direction=sort_direction,
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )

    total_pages = ceil(total_items / page_size) if total_items else 0

    unread_count = count_user_unread_notifications(
        db,
        recipient_id=recipient_id,
    )

    return {
        "items": [_build_notification_item(row) for row in rows],
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "recipient_unread_count": (unread_count),
        "read_filter": read_filter,
        "sort_direction": (sort_direction),
    }


def get_user_notification(
    db: Session,
    *,
    recipient_id: int,
    notification_id: str,
) -> dict[str, Any]:
    row = (
        _build_recipient_notification_query(
            db,
            recipient_id=recipient_id,
        )
        .filter(
            Notification.notification_id == notification_id,
        )
        .first()
    )

    if row is None:
        raise NotificationNotFoundError("Notification not found.")

    return _build_notification_item(row)


def mark_user_notification_read(
    db: Session,
    *,
    recipient_id: int,
    notification_id: str,
) -> dict[str, Any]:
    """
    Mark one recipient-owned notification as read.

    The operation is idempotent. Repeated calls preserve the original
    read timestamp.
    """

    notification = (
        db.query(Notification)
        .filter(
            Notification.notification_id == notification_id,
            Notification.recipient_id == recipient_id,
        )
        .first()
    )

    if notification is None:
        raise NotificationNotFoundError("Notification not found.")

    if not notification.is_read:
        marked_at = _utc_now()

        notification.is_read = True
        notification.read_at = marked_at
        notification.updated_at = marked_at

        try:
            db.commit()
        except SQLAlchemyError as error:
            db.rollback()

            raise NotificationPersistenceError(
                "The notification could not be marked as read."
            ) from error

    return get_user_notification(
        db,
        recipient_id=recipient_id,
        notification_id=notification_id,
    )


def mark_all_user_notifications_read(
    db: Session,
    *,
    recipient_id: int,
) -> dict[str, Any]:
    """
    Mark every unread notification belonging to one recipient as read.

    Other users' notifications are never changed.
    """

    marked_at = _utc_now()

    try:
        marked_read_count = (
            db.query(Notification)
            .filter(
                Notification.recipient_id == recipient_id,
                Notification.is_read.is_(False),
            )
            .update(
                {
                    Notification.is_read: True,
                    Notification.read_at: marked_at,
                    Notification.updated_at: (marked_at),
                },
                synchronize_session=False,
            )
        )

        db.commit()

    except SQLAlchemyError as error:
        db.rollback()

        raise NotificationPersistenceError(
            "The notifications could not be marked as read."
        ) from error

    remaining_unread_count = count_user_unread_notifications(
        db,
        recipient_id=recipient_id,
    )

    return {
        "marked_read_count": int(marked_read_count or 0),
        "remaining_unread_count": (remaining_unread_count),
        "marked_at": marked_at,
    }


# OWNERSHIP BOUNDARY:
# Public read-state operations always filter by both notification ID and
# the authenticated recipient ID. A user cannot read or modify another
# user's notifications.

# IDEMPOTENCY BOUNDARY:
# Academic event keys are unique. Each event-recipient pair is unique.
# Retrying the same event workflow does not create duplicate records.

# PRIVACY BOUNDARY:
# Public notification queries never select or expose academic-event
# event_data, source code, standard input, hidden test cases, AST details,
# similarity records, execution output, coding-session telemetry,
# clipboard contents, pasted text, surveillance information, or
# unreleased grade information.

# CONTENT BOUNDARY:
# Notification title and message values are validated through internal
# schemas and must originate from trusted backend event templates.

# DELIVERY BOUNDARY:
# This service persists in-app notifications only. It does not send
# email, SMS, push notifications, or other external messages.
