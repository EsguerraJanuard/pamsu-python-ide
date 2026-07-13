from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ActivityType = Literal["laboratory", "homework"]
PastePolicy = Literal["internal_only", "disabled"]


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    instructions: str | None = None
    activity_type: ActivityType = "laboratory"
    required_ast_rules: dict[str, Any] = Field(default_factory=dict)
    starter_code: str = ""
    paste_policy: PastePolicy = "internal_only"
    is_graded: bool = True
    due_at: datetime | None = None

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        normalized_title = " ".join(value.split())

        if not normalized_title:
            raise ValueError("Task title is required.")

        return normalized_title

    @field_validator("required_ast_rules")
    @classmethod
    def validate_required_ast_rules(
        cls,
        value: dict[str, Any],
    ) -> dict[str, Any]:
        for rule_name in value:
            if not isinstance(rule_name, str) or not rule_name.strip():
                raise ValueError("Each AST rule must have a non-empty string key.")

        return value


class TaskCreate(TaskBase):
    class_id: int = Field(..., gt=0)

    # SECURITY BOUNDARY:
    # instructor_id is intentionally excluded. The backend must obtain the
    # instructor identity from the authenticated JWT user, not the client.


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    instructions: str | None = None
    activity_type: ActivityType | None = None
    required_ast_rules: dict[str, Any] | None = None
    starter_code: str | None = None
    paste_policy: PastePolicy | None = None
    is_graded: bool | None = None
    due_at: datetime | None = None

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized_title = " ".join(value.split())

        if not normalized_title:
            raise ValueError("Task title cannot be empty.")

        return normalized_title

    @field_validator("required_ast_rules")
    @classmethod
    def validate_required_ast_rules(
        cls,
        value: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if value is None:
            return None

        for rule_name in value:
            if not isinstance(rule_name, str) or not rule_name.strip():
                raise ValueError("Each AST rule must have a non-empty string key.")

        return value


class TaskPublishRequest(BaseModel):
    is_published: bool

    model_config = ConfigDict(extra="forbid")


class TaskResponse(TaskBase):
    task_id: int
    class_id: int | None
    instructor_id: int
    is_published: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )
