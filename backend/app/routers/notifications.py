from typing import NoReturn
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain_models import User
from app.schemas.notification_schema import (
    MarkAllNotificationsReadResponse,
    NotificationListResponse,
    NotificationReadFilter,
    NotificationResponse,
    NotificationSortDirection,
    NotificationUnreadCountResponse,
)
from app.services.notification_service import (
    NotificationNotFoundError,
    NotificationPaginationError,
    NotificationPersistenceError,
    NotificationServiceError,
    count_user_unread_notifications,
    get_user_notification,
    list_user_notifications,
    mark_all_user_notifications_read,
    mark_user_notification_read,
)


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


def raise_notification_http_exception(
    exc: NotificationServiceError,
) -> NoReturn:
    if isinstance(
        exc,
        NotificationNotFoundError,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        NotificationPaginationError,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        NotificationPersistenceError,
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=("The notification operation could not be completed."),
    ) from exc


@router.get(
    "/",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    operation_id="list_my_notifications",
    summary="List my notifications",
    description=(
        "Returns a paginated list containing only notifications "
        "belonging to the authenticated student or instructor. "
        "Academic-event payloads, source code, hidden test cases, "
        "analytics details, execution output, session telemetry, "
        "and unreleased grades are excluded."
    ),
)
def list_notifications_endpoint(
    page: int = Query(
        default=1,
        ge=1,
        description="One-based page number.",
    ),
    page_size: int = Query(
        default=25,
        ge=1,
        le=100,
        description=("Number of notifications returned per page."),
    ),
    read_filter: NotificationReadFilter = Query(
        default="all",
        description=("Return all, unread, or read notifications."),
    ),
    sort_direction: NotificationSortDirection = Query(
        default="desc",
        description=("Sort notifications by creation time."),
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    try:
        result = list_user_notifications(
            db,
            recipient_id=current_user.user_id,
            page=page,
            page_size=page_size,
            read_filter=read_filter,
            sort_direction=sort_direction,
        )
    except NotificationServiceError as exc:
        raise_notification_http_exception(exc)

    return NotificationListResponse.model_validate(result)


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCountResponse,
    status_code=status.HTTP_200_OK,
    operation_id="count_my_unread_notifications",
    summary="Count my unread notifications",
    description=(
        "Returns the unread notification count belonging only "
        "to the authenticated user."
    ),
)
def count_unread_notifications_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationUnreadCountResponse:
    unread_count = count_user_unread_notifications(
        db,
        recipient_id=current_user.user_id,
    )

    return NotificationUnreadCountResponse(
        unread_count=unread_count,
    )


@router.patch(
    "/read-all",
    response_model=MarkAllNotificationsReadResponse,
    status_code=status.HTTP_200_OK,
    operation_id="mark_all_my_notifications_read",
    summary="Mark all my notifications as read",
    description=(
        "Marks every unread notification belonging to the "
        "authenticated user as read. Notifications belonging "
        "to other users are not changed."
    ),
)
def mark_all_notifications_read_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MarkAllNotificationsReadResponse:
    try:
        result = mark_all_user_notifications_read(
            db,
            recipient_id=(current_user.user_id),
        )
    except NotificationServiceError as exc:
        raise_notification_http_exception(exc)

    return MarkAllNotificationsReadResponse.model_validate(result)


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_my_notification",
    summary="Get one of my notifications",
    description=(
        "Returns a notification only when it belongs to the authenticated user."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The notification was not found for the authenticated user."
            ),
        },
    },
)
def get_notification_endpoint(
    notification_id: UUID = Path(
        ...,
        description="Notification UUID.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    try:
        result = get_user_notification(
            db,
            recipient_id=current_user.user_id,
            notification_id=str(notification_id),
        )
    except NotificationServiceError as exc:
        raise_notification_http_exception(exc)

    return NotificationResponse.model_validate(result)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    operation_id="mark_my_notification_read",
    summary="Mark one of my notifications as read",
    description=(
        "Marks a recipient-owned notification as read. "
        "The operation is idempotent and preserves the "
        "original read timestamp when repeated."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The notification was not found for the authenticated user."
            ),
        },
    },
)
def mark_notification_read_endpoint(
    notification_id: UUID = Path(
        ...,
        description="Notification UUID.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    try:
        result = mark_user_notification_read(
            db,
            recipient_id=current_user.user_id,
            notification_id=str(notification_id),
        )
    except NotificationServiceError as exc:
        raise_notification_http_exception(exc)

    return NotificationResponse.model_validate(result)


# AUTHORIZATION BOUNDARY:
# Notification ownership always comes from the authenticated database
# user. Clients cannot select a recipient or access another user's
# notifications.

# PRIVACY BOUNDARY:
# Notification responses exclude academic-event event_data, source code,
# standard input, hidden test cases, AST findings, similarity details,
# execution output, coding-session telemetry, clipboard contents,
# pasted text, surveillance data, and unreleased grades.

# READ-STATE BOUNDARY:
# Mark-one and mark-all operations modify only notifications belonging
# to the authenticated user. Mark-one is idempotent and preserves the
# original read timestamp.

# CREATION BOUNDARY:
# This router does not expose notification or academic-event creation
# endpoints. Notifications are created only by trusted backend domain
# workflows.

# DELIVERY BOUNDARY:
# These endpoints support in-app notifications only. They do not send
# email, SMS, or push notifications.
