from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


def normalize_required_text(
    value: str,
    *,
    field_name: str,
) -> str:
    normalized_value = " ".join(value.strip().split())

    if not normalized_value:
        raise ValueError(f"{field_name} cannot be empty.")

    return normalized_value


class ClassroomBase(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=120,
        description="Descriptive classroom name.",
        examples=["Programming Fundamentals"],
    )
    subject_code: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="Academic subject or course code.",
        examples=["CCS101"],
    )
    section: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Class section or block.",
        examples=["BSIT 1A"],
    )

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str,
    ) -> str:
        return normalize_required_text(
            value,
            field_name="Classroom name",
        )

    @field_validator("subject_code")
    @classmethod
    def validate_subject_code(
        cls,
        value: str,
    ) -> str:
        normalized_value = normalize_required_text(
            value,
            field_name="Subject code",
        )

        return normalized_value.upper()

    @field_validator("section")
    @classmethod
    def validate_section(
        cls,
        value: str,
    ) -> str:
        return normalize_required_text(
            value,
            field_name="Section",
        )


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=120,
    )
    subject_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=30,
    )
    section: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    is_active: bool | None = None

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return normalize_required_text(
            value,
            field_name="Classroom name",
        )

    @field_validator("subject_code")
    @classmethod
    def validate_subject_code(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = normalize_required_text(
            value,
            field_name="Subject code",
        )

        return normalized_value.upper()

    @field_validator("section")
    @classmethod
    def validate_section(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return normalize_required_text(
            value,
            field_name="Section",
        )

    @model_validator(mode="after")
    def require_at_least_one_field(
        self,
    ) -> "ClassroomUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one classroom field must be provided.")

        return self


class ClassroomResponse(ClassroomBase):
    class_id: int = Field(
        ...,
        gt=0,
        description="Unique classroom identifier.",
    )
    instructor_id: int = Field(
        ...,
        gt=0,
        description="Authenticated instructor who owns the classroom.",
    )
    instructor_name: str | None = Field(
        None,
        description="Name of the instructor who owns the classroom.",
    )
    class_code: str = Field(
        ...,
        min_length=6,
        max_length=20,
        pattern=r"^[A-Z0-9]+$",
        description=("Backend-generated code used by students to join the class."),
    )
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class ClassroomCodeResponse(BaseModel):
    class_id: int = Field(
        ...,
        gt=0,
    )
    class_code: str = Field(
        ...,
        min_length=6,
        max_length=20,
        pattern=r"^[A-Z0-9]+$",
    )

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


# SECURITY BOUNDARY:
# ClassroomCreate does not accept instructor_id or class_code.
# The instructor identity comes from the authenticated access token.
# Class codes are generated and validated exclusively by the backend.
