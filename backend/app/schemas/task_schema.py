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


def normalize_due_at(
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Task due date must include a timezone.")

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
            "`internal_only` permits copying inside the editor while "
            "blocking external paste. `disabled` blocks paste operations."
        ),
    )
    is_graded: bool = Field(
        default=True,
        description=("Whether the activity accepts official graded submissions."),
    )
    due_at: datetime | None = Field(
        default=None,
        description=("Optional timezone-aware deadline normalized to UTC."),
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
    def validate_optional_text(
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

    @field_validator("due_at")
    @classmethod
    def validate_due_at(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return normalize_due_at(value)


class TaskCreate(TaskBase):
    class_id: int = Field(
        ...,
        gt=0,
        description=("Classroom owned by the authenticated instructor."),
    )

    # SECURITY BOUNDARY:
    # instructor_id, is_published, and published_at are intentionally
    # excluded. These values are controlled by the backend.


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
    due_at: datetime | None = None

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
    def validate_optional_text(
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
        return normalize_due_at(value)


class TaskPublishRequest(BaseModel):
    is_published: bool = Field(
        ...,
        description="Publish or return the activity to draft status.",
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class TaskResponse(TaskBase):
    task_id: int = Field(
        ...,
        gt=0,
    )
    class_id: int | None = Field(
        default=None,
        gt=0,
    )
    instructor_id: int = Field(
        ...,
        gt=0,
    )
    is_published: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class StudentTaskResponse(TaskBase):
    task_id: int = Field(
        ...,
        gt=0,
    )
    class_id: int = Field(
        ...,
        gt=0,
    )
    is_published: bool
    published_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    # STUDENT-SAFE BOUNDARY:
    # This response excludes instructor ownership internals and all
    # task-test-case records. Hidden expected outputs must never be
    # included in student activity responses.
