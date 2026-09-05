from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


ActivityType = Literal[
    "laboratory",
    "homework",
]

PastePolicy = Literal[
    "internal_only",
    "disabled",
]


def normalize_title(value: str) -> str:
    normalized_value = " ".join(value.strip().split())

    if not normalized_value:
        raise ValueError("Task title is required.")

    return normalized_value


def normalize_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized_value = value.strip()

    return normalized_value or None


def validate_request_due_at(
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Task due date must include a timezone.")

    return value.astimezone(timezone.utc)


def normalize_response_datetime(
    value: Any,
) -> Any:
    if value is None:
        return None

    # Non-datetime inputs are left for Pydantic to parse.
    if not isinstance(value, datetime):
        return value

    # SQLite may return DateTime(timezone=True) values without tzinfo.
    # Persisted task datetimes are interpreted as UTC.
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def validate_ast_rules(
    value: dict[str, Any],
) -> dict[str, Any]:
    if len(value) > 50:
        raise ValueError("A task may contain at most 50 AST rules.")

    for rule_name in value:
        if not isinstance(rule_name, str):
            raise ValueError("Each AST rule must use a string key.")

        if not rule_name.strip():
            raise ValueError("Each AST rule must have a non-empty key.")

        if rule_name != rule_name.strip():
            raise ValueError("AST rule keys cannot begin or end with whitespace.")

    return value


class TaskBase(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Activity title.",
        examples=["Loops and Functions Laboratory"],
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Optional activity overview.",
    )
    instructions: str | None = Field(
        default=None,
        max_length=10000,
        description="Detailed student instructions.",
    )
    activity_type: ActivityType = Field(
        default="laboratory",
        description="Laboratory or homework activity.",
    )
    required_ast_rules: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Optional structural-analysis rules. An empty dictionary is allowed."
        ),
    )
    starter_code: str = Field(
        default="",
        max_length=50000,
        description=(
            "Initial Python source shown to students. "
            "Whitespace and indentation are preserved."
        ),
    )
    paste_policy: PastePolicy = Field(
        default="internal_only",
        description=(
            "`internal_only` permits internal editor paste. "
            "`disabled` blocks paste operations."
        ),
    )
    is_graded: bool = Field(
        default=True,
        description=("Whether the activity accepts official graded submissions."),
    )

    model_config = ConfigDict(
        extra="forbid",
    )

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str,
    ) -> str:
        return normalize_title(value)

    @field_validator(
        "description",
        "instructions",
    )
    @classmethod
    def validate_optional_text_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_optional_text(value)

    @field_validator("required_ast_rules")
    @classmethod
    def validate_required_ast_rules(
        cls,
        value: dict[str, Any],
    ) -> dict[str, Any]:
        return validate_ast_rules(value)


class TaskCreate(TaskBase):
    class_ids: list[int] = Field(
        ...,
        min_length=1,
        description=("List of classroom IDs owned by the authenticated instructor."),
    )
    due_at: datetime | None = Field(
        default=None,
        description=("Optional timezone-aware deadline normalized to UTC."),
    )
    scheduled_publish_at: datetime | None = Field(
        default=None,
        description=("Optional timezone-aware scheduled publish time normalized to UTC."),
    )

    @field_validator("due_at", "scheduled_publish_at")
    @classmethod
    def validate_due_at(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return validate_request_due_at(value)

    from pydantic import model_validator
    
    @model_validator(mode="after")
    def validate_scheduling(self):
        if len(self.class_ids) > 1 and self.scheduled_publish_at is not None:
            raise ValueError("You cannot schedule an activity for a future date when selecting multiple classrooms.")
        return self

    # Backend-controlled fields intentionally excluded:
    # instructor_id, is_published, and published_at.


class TaskUpdate(BaseModel):
    class_id: int | None = Field(
        default=None,
        gt=0,
        description="Optional destination classroom.",
    )
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )
    instructions: str | None = Field(
        default=None,
        max_length=10000,
    )
    activity_type: ActivityType | None = None
    required_ast_rules: dict[str, Any] | None = None
    starter_code: str | None = Field(
        default=None,
        max_length=50000,
    )
    paste_policy: PastePolicy | None = None
    is_graded: bool | None = None
    due_at: datetime | None = Field(
        default=None,
        description=("Optional timezone-aware deadline normalized to UTC."),
    )
    scheduled_publish_at: datetime | None = Field(
        default=None,
        description=("Optional timezone-aware scheduled publish time normalized to UTC."),
    )

    model_config = ConfigDict(
        extra="forbid",
    )

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return normalize_title(value)

    @field_validator(
        "description",
        "instructions",
    )
    @classmethod
    def validate_optional_text_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_optional_text(value)

    @field_validator("required_ast_rules")
    @classmethod
    def validate_required_ast_rules(
        cls,
        value: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if value is None:
            return None

        return validate_ast_rules(value)

    @field_validator("due_at")
    @classmethod
    def validate_due_at(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return validate_request_due_at(value)


class TaskPublishRequest(BaseModel):
    is_published: bool = Field(
        ...,
        description=("Publish or return the activity to draft status."),
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class TaskResponseBase(BaseModel):
    task_id: int = Field(
        ...,
        gt=0,
    )
    class_id: int | None = Field(
        default=None,
        gt=0,
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )
    instructions: str | None = Field(
        default=None,
        max_length=10000,
    )
    activity_type: ActivityType
    required_ast_rules: dict[str, Any] = Field(
        default_factory=dict,
    )
    starter_code: str = Field(
        default="",
        max_length=50000,
    )
    paste_policy: PastePolicy
    is_graded: bool
    due_at: datetime | None = None
    is_published: bool
    published_at: datetime | None = None
    scheduled_publish_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    assigned_count: int | None = None
    turned_in_count: int | None = None
    graded_count: int | None = None

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    @field_validator(
        "due_at",
        "published_at",
        "scheduled_publish_at",
        "created_at",
        "updated_at",
        mode="before",
    )
    @classmethod
    def normalize_database_datetime(
        cls,
        value: Any,
    ) -> Any:
        return normalize_response_datetime(value)


class TaskResponse(TaskResponseBase):
    instructor_id: int = Field(
        ...,
        gt=0,
    )


class StudentTaskResponse(TaskResponseBase):
    class_id: int = Field(
        ...,
        gt=0,
    )
    published_at: datetime

    # Student-safe boundary:
    # instructor_id and task-test-case records are excluded.
