from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


AcademicEventType = Literal[
    "student_enrolled",
    "enrollment_status_changed",
    "activity_published",
    "activity_updated",
    "submission_created",
    "submission_status_changed",
    "grade_released",
    "classroom_archived",
]

AcademicResourceType = Literal[
    "classroom",
    "enrollment",
    "task",
    "submission",
    "grade",
]

NotificationReadFilter = Literal[
    "all",
    "unread",
    "read",
]

NotificationSortDirection = Literal[
    "asc",
    "desc",
]

AcademicEventDataValue = str | int | float | bool | None

MIN_NOTIFICATION_PAGE_SIZE = 1
MAX_NOTIFICATION_PAGE_SIZE = 100

MAX_EVENT_KEY_LENGTH = 255
MAX_RESOURCE_ID_LENGTH = 100
MAX_NOTIFICATION_TITLE_LENGTH = 200
MAX_NOTIFICATION_MESSAGE_LENGTH = 2_000
MAX_EVENT_DATA_FIELDS = 25
MAX_EVENT_DATA_KEY_LENGTH = 100
MAX_EVENT_DATA_STRING_LENGTH = 500

PROHIBITED_EVENT_DATA_KEYS = {
    "raw_code",
    "source_code",
    "standard_input",
    "expected_output",
    "hidden_test_case",
    "hidden_test_cases",
    "ast_details",
    "ast_findings",
    "jaccard_score",
    "similarity_score",
    "similarity_results",
    "stdout",
    "stderr",
    "execution_output",
    "clipboard_content",
    "clipboard_text",
    "pasted_text",
    "keystrokes",
    "browsing_history",
    "screen_recording",
    "webcam_data",
    "microphone_data",
    "unreleased_score",
    "unreleased_feedback",
    "risk_score",
    "behavior_score",
    "plagiarism_verdict",
    "cheating_verdict",
    "misconduct_verdict",
}


def normalize_uuid_string(
    value: str,
    *,
    field_name: str,
) -> str:
    try:
        parsed_value = UUID(value)
    except (
        TypeError,
        ValueError,
        AttributeError,
    ) as error:
        raise ValueError(f"{field_name} must be a valid UUID.") from error

    return str(parsed_value)


def normalize_notification_datetime(
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(
            tzinfo=timezone.utc,
        )

    return value.astimezone(
        timezone.utc,
    )


def validate_nonblank_text(
    value: str,
    *,
    field_name: str,
) -> str:
    normalized_value = value.strip()

    if not normalized_value:
        raise ValueError(f"{field_name} cannot be empty.")

    if "\x00" in normalized_value:
        raise ValueError(f"{field_name} cannot contain null bytes.")

    return normalized_value


def validate_event_data(
    value: dict[
        str,
        AcademicEventDataValue,
    ],
) -> dict[
    str,
    AcademicEventDataValue,
]:
    if len(value) > MAX_EVENT_DATA_FIELDS:
        raise ValueError("Academic event data contains too many fields.")

    validated_data: dict[
        str,
        AcademicEventDataValue,
    ] = {}

    for key, item_value in value.items():
        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError("Academic event data keys cannot be empty.")

        if "\x00" in normalized_key:
            raise ValueError("Academic event data keys cannot contain null bytes.")

        if len(normalized_key) > MAX_EVENT_DATA_KEY_LENGTH:
            raise ValueError("Academic event data keys are too long.")

        if normalized_key.lower() in PROHIBITED_EVENT_DATA_KEYS:
            raise ValueError("Academic event data contains a prohibited field.")

        if isinstance(
            item_value,
            str,
        ):
            if "\x00" in item_value:
                raise ValueError("Academic event data cannot contain null bytes.")

            if len(item_value) > MAX_EVENT_DATA_STRING_LENGTH:
                raise ValueError("Academic event data text is too long.")

        validated_data[normalized_key] = item_value

    return validated_data


class AcademicEventCreate(BaseModel):
    """
    Internal service-layer contract for creating an immutable
    academic event.

    This schema is not intended as a client request body.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    event_key: str = Field(
        ...,
        min_length=1,
        max_length=MAX_EVENT_KEY_LENGTH,
    )

    event_type: AcademicEventType

    actor_user_id: int | None = Field(
        default=None,
        gt=0,
    )

    resource_type: AcademicResourceType

    resource_id: str = Field(
        ...,
        min_length=1,
        max_length=MAX_RESOURCE_ID_LENGTH,
    )

    event_data: dict[
        str,
        AcademicEventDataValue,
    ] = Field(
        default_factory=dict,
    )

    @field_validator(
        "event_key",
        "resource_id",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
        info,
    ) -> str:
        field_name = "Event key" if info.field_name == "event_key" else "Resource ID"

        return validate_nonblank_text(
            value,
            field_name=field_name,
        )

    @field_validator(
        "event_data",
    )
    @classmethod
    def validate_safe_event_data(
        cls,
        value: dict[
            str,
            AcademicEventDataValue,
        ],
    ) -> dict[
        str,
        AcademicEventDataValue,
    ]:
        return validate_event_data(value)


class NotificationCreate(BaseModel):
    """
    Internal service-layer contract for creating one recipient-specific
    in-app notification.

    Recipients and text must come from trusted backend domain logic.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    event_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
    )

    recipient_id: int = Field(
        ...,
        gt=0,
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=MAX_NOTIFICATION_TITLE_LENGTH,
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=MAX_NOTIFICATION_MESSAGE_LENGTH,
    )

    @field_validator(
        "event_id",
    )
    @classmethod
    def validate_event_id(
        cls,
        value: str,
    ) -> str:
        return normalize_uuid_string(
            value,
            field_name="Event ID",
        )

    @field_validator(
        "title",
        "message",
    )
    @classmethod
    def validate_notification_text(
        cls,
        value: str,
        info,
    ) -> str:
        field_name = (
            "Notification title"
            if info.field_name == "title"
            else "Notification message"
        )

        return validate_nonblank_text(
            value,
            field_name=field_name,
        )


class NotificationResponse(BaseModel):
    """
    Recipient-safe in-app notification response.

    The academic event's internal event_data payload is intentionally
    excluded.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    notification_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
    )

    event_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
    )

    event_type: AcademicEventType

    resource_type: AcademicResourceType

    resource_id: str = Field(
        ...,
        min_length=1,
        max_length=MAX_RESOURCE_ID_LENGTH,
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=MAX_NOTIFICATION_TITLE_LENGTH,
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=MAX_NOTIFICATION_MESSAGE_LENGTH,
    )

    is_read: bool

    read_at: datetime | None = None

    occurred_at: datetime

    created_at: datetime

    @field_validator(
        "notification_id",
    )
    @classmethod
    def validate_notification_id(
        cls,
        value: str,
    ) -> str:
        return normalize_uuid_string(
            value,
            field_name="Notification ID",
        )

    @field_validator(
        "event_id",
    )
    @classmethod
    def validate_response_event_id(
        cls,
        value: str,
    ) -> str:
        return normalize_uuid_string(
            value,
            field_name="Event ID",
        )

    @field_validator(
        "read_at",
        "occurred_at",
        "created_at",
        mode="after",
    )
    @classmethod
    def normalize_datetime_fields(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return normalize_notification_datetime(value)

    @model_validator(
        mode="after",
    )
    def validate_read_state(
        self,
    ) -> "NotificationResponse":
        if self.is_read and self.read_at is None:
            raise ValueError("A read notification requires read_at.")

        if not self.is_read and self.read_at is not None:
            raise ValueError("An unread notification cannot have read_at.")

        return self


class NotificationListResponse(BaseModel):
    """
    Paginated notifications belonging only to the authenticated user.

    recipient_unread_count represents the authenticated recipient's
    total unread count, independent of the current page.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[NotificationResponse] = Field(
        default_factory=list,
    )

    page: int = Field(
        ...,
        ge=1,
    )

    page_size: int = Field(
        ...,
        ge=MIN_NOTIFICATION_PAGE_SIZE,
        le=MAX_NOTIFICATION_PAGE_SIZE,
    )

    total_items: int = Field(
        ...,
        ge=0,
    )

    total_pages: int = Field(
        ...,
        ge=0,
    )

    recipient_unread_count: int = Field(
        ...,
        ge=0,
    )

    read_filter: NotificationReadFilter

    sort_direction: NotificationSortDirection

    @model_validator(
        mode="after",
    )
    def validate_pagination(
        self,
    ) -> "NotificationListResponse":
        expected_total_pages = (
            0
            if self.total_items == 0
            else (self.total_items + self.page_size - 1) // self.page_size
        )

        if self.total_pages != expected_total_pages:
            raise ValueError("total_pages does not match total_items and page_size.")

        if len(self.items) > self.page_size:
            raise ValueError("Notification items cannot exceed page_size.")

        return self


class NotificationUnreadCountResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    unread_count: int = Field(
        ...,
        ge=0,
    )


class MarkAllNotificationsReadResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    marked_read_count: int = Field(
        ...,
        ge=0,
    )

    remaining_unread_count: int = Field(
        ...,
        ge=0,
    )

    marked_at: datetime

    @field_validator(
        "marked_at",
        mode="after",
    )
    @classmethod
    def normalize_marked_at(
        cls,
        value: datetime,
    ) -> datetime:
        normalized_value = normalize_notification_datetime(value)

        assert normalized_value is not None

        return normalized_value


# OWNERSHIP BOUNDARY:
# Public notification endpoints derive recipient ownership exclusively
# from the authenticated user. Clients cannot create notifications or
# select a recipient.

# PRIVACY BOUNDARY:
# Public schemas exclude academic-event event_data, source code, standard
# input, hidden test cases, AST findings, similarity details, execution
# output, coding-session telemetry, clipboard contents, pasted text,
# surveillance data, and unreleased grade information.

# CONTENT BOUNDARY:
# Notification title and message values must be generated by trusted
# backend templates for approved academic events.

# DELIVERY BOUNDARY:
# These schemas represent in-app notifications only. External email,
# SMS, and push-delivery adapters are outside Pillar 11.
