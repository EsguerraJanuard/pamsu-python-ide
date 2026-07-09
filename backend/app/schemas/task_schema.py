from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1)
    required_ast_rules: dict[str, Any] = Field(...)

    @field_validator("required_ast_rules")
    @classmethod
    def validate_required_ast_rules(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("required_ast_rules cannot be empty")
        return value


class TaskCreate(TaskBase):
    instructor_id: int = Field(..., gt=0)


class TaskResponse(TaskBase):
    task_id: int
    instructor_id: int

    model_config = ConfigDict(from_attributes=True)
