from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.schemas.classroom_schema import ClassroomResponse


EnrollmentStatus = Literal[
    "active",
    "disabled",
    "removed",
]


def normalize_class_code(value: str) -> str:
    normalized_value = value.strip().upper()

    if not normalized_value:
        raise ValueError("Class code cannot be empty.")

    if not normalized_value.isalnum():
        raise ValueError("Class code may contain only letters and numbers.")

    return normalized_value


class EnrollmentJoinRequest(BaseModel):
    class_code: str = Field(
        ...,
        min_length=6,
        max_length=20,
        pattern=r"^[A-Za-z0-9]+$",
        description=("Backend-generated class code supplied by the student."),
        examples=["AB12CD34"],
    )

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator("class_code")
    @classmethod
    def validate_class_code(
        cls,
        value: str,
    ) -> str:
        return normalize_class_code(value)


class EnrollmentStatusUpdate(BaseModel):
    status: EnrollmentStatus = Field(
        ...,
        description=(
            "Instructor-controlled enrollment status. "
            "`active` allows class participation, `disabled` temporarily "
            "blocks access, and `removed` indicates removal from the class."
        ),
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class EnrollmentResponse(BaseModel):
    enrollment_id: int = Field(
        ...,
        gt=0,
        description="Unique enrollment identifier.",
    )
    class_id: int = Field(
        ...,
        gt=0,
        description="Enrolled classroom identifier.",
    )
    student_id: int = Field(
        ...,
        gt=0,
        description="Enrolled student identifier.",
    )
    status: EnrollmentStatus

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class ClassMemberResponse(BaseModel):
    enrollment_id: int = Field(
        ...,
        gt=0,
    )
    student_id: int = Field(
        ...,
        gt=0,
    )
    school_id: str = Field(
        ...,
        min_length=10,
        max_length=10,
        pattern=r"^\d{10}$",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=120,
    )
    email: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )
    status: EnrollmentStatus

    model_config = ConfigDict(
        extra="forbid",
    )


class StudentClassroomResponse(BaseModel):
    enrollment_id: int = Field(
        ...,
        gt=0,
    )
    enrollment_status: EnrollmentStatus
    classroom: ClassroomResponse

    model_config = ConfigDict(
        extra="forbid",
    )


# SECURITY BOUNDARY:
# Students join classes using only a backend-generated class code.
# student_id comes from the authenticated access token.
# Clients cannot enroll another student or directly select a class_id.

# AUTHORIZATION BOUNDARY:
# Only the classroom owner may view members or change enrollment status.
# Students may view only their own classroom enrollments.

# STATUS BOUNDARY:
# Classroom availability uses Classroom.is_active.
# Enrollment membership uses active, disabled, or removed.
