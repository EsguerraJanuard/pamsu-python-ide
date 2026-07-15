from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


def normalize_test_case_name(value: str) -> str:
    normalized_value = " ".join(value.strip().split())

    if not normalized_value:
        raise ValueError("Test case name is required.")

    return normalized_value


class TaskTestCaseBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Descriptive test-case name.",
        examples=["Basic positive input"],
    )
    standard_input: str = Field(
        default="",
        max_length=100000,
        description=(
            "Standard input supplied to the isolated execution sandbox. "
            "Whitespace and line breaks are preserved."
        ),
    )
    expected_output: str = Field(
        ...,
        max_length=100000,
        description=(
            "Expected standard output used during execution review. "
            "Hidden expected outputs must never be exposed to students."
        ),
    )
    is_hidden: bool = Field(
        default=False,
        description=("Whether the test case is hidden from student-facing APIs."),
    )
    display_order: int = Field(
        default=0,
        ge=0,
        description="Ordering value within the activity.",
    )

    model_config = ConfigDict(
        extra="forbid",
    )

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str,
    ) -> str:
        return normalize_test_case_name(value)


class TaskTestCaseCreate(TaskTestCaseBase):
    # SECURITY BOUNDARY:
    # task_id is intentionally excluded. It comes from the instructor-owned
    # task identified in the protected route path.
    pass


class TaskTestCaseUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    standard_input: str | None = Field(
        default=None,
        max_length=100000,
    )
    expected_output: str | None = Field(
        default=None,
        max_length=100000,
    )
    is_hidden: bool | None = None
    display_order: int | None = Field(
        default=None,
        ge=0,
    )

    model_config = ConfigDict(
        extra="forbid",
    )

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return normalize_test_case_name(value)

    @model_validator(mode="after")
    def require_at_least_one_field(
        self,
    ) -> "TaskTestCaseUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one test-case field must be provided.")

        return self


class InstructorTaskTestCaseResponse(TaskTestCaseBase):
    test_case_id: int = Field(
        ...,
        gt=0,
    )
    task_id: int = Field(
        ...,
        gt=0,
    )
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class StudentSampleTestCaseResponse(BaseModel):
    test_case_id: int = Field(
        ...,
        gt=0,
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
    )
    standard_input: str
    expected_output: str
    display_order: int = Field(
        ...,
        ge=0,
    )

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    # STUDENT-SAFE BOUNDARY:
    # Only non-hidden sample cases may use this response model.
    # The is_hidden field and every hidden expected output are excluded.
