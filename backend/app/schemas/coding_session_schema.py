from datetime import datetime, timezone
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


MAX_TAB_SWITCH_INCREMENT = 100
MAX_BLOCKED_PASTE_INCREMENT = 100
MAX_MOUSELEAVE_INCREMENT = 500
MAX_IDLE_INCREMENT_SECONDS = 3600


class CodingSessionStartRequest(BaseModel):
    """
    Request for starting or resuming a student's coding session.

    Student identity, session ID, lifecycle timestamps, and telemetry
    counters are controlled by the backend.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    task_id: int = Field(
        ...,
        gt=0,
        description=(
            "Published activity for which the authenticated student "
            "is starting or resuming a coding session."
        ),
    )


class CodingSessionActivityUpdate(BaseModel):
    """
    Privacy-safe aggregate session activity update.

    The client submits count increments only. It cannot replace total
    counters, modify run-attempt totals, assign timestamps, or send
    clipboard and surveillance content.

    Sending all zero values is allowed and acts as a heartbeat that
    updates last_activity_at in the service layer.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    tab_switch_increment: int = Field(
        default=0,
        ge=0,
        le=MAX_TAB_SWITCH_INCREMENT,
        description=(
            "Number of newly observed tab switches since the previous "
            "successful session update."
        ),
    )

    blocked_paste_increment: int = Field(
        default=0,
        ge=0,
        le=MAX_BLOCKED_PASTE_INCREMENT,
        description=(
            "Number of newly blocked external-paste attempts. "
            "Clipboard or pasted content must never be included."
        ),
    )

    mouseleave_increment: int = Field(
        default=0,
        ge=0,
        le=MAX_MOUSELEAVE_INCREMENT,
        description=(
            "Number of times the mouse left the browser viewport since the "
            "previous successful session update."
        ),
    )

    idle_duration_increment_seconds: int = Field(
        default=0,
        ge=0,
        le=MAX_IDLE_INCREMENT_SECONDS,
        description=(
            "Additional aggregate idle duration since the previous "
            "successful session update."
        ),
    )


class CodingSessionResponseBase(BaseModel):
    """
    Shared coding-session response.

    These fields are review indicators only. They do not calculate
    grades, behavior scores, cheating findings, or misconduct verdicts.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    session_id: UUID = Field(
        ...,
        description="Backend-generated coding-session UUID.",
    )

    task_id: int = Field(
        ...,
        gt=0,
        description="Activity linked to the coding session.",
    )

    started_at: datetime = Field(
        ...,
        description="Backend-controlled session start time.",
    )

    ended_at: datetime | None = Field(
        default=None,
        description=(
            "Backend-controlled session end time, or null while "
            "the session remains active."
        ),
    )

    last_activity_at: datetime = Field(
        ...,
        description=(
            "Backend-controlled timestamp of the latest accepted "
            "session activity or heartbeat."
        ),
    )

    tab_switch_count: int = Field(
        ...,
        ge=0,
        description=(
            "Aggregate number of tab-switch events recorded during the session."
        ),
    )

    blocked_paste_count: int = Field(
        ...,
        ge=0,
        description=(
            "Aggregate number of blocked external-paste attempts. "
            "No clipboard content is stored."
        ),
    )

    mouseleave_count: int = Field(
        ...,
        ge=0,
        description=(
            "Aggregate number of times the mouse left the browser viewport "
            "during the session."
        ),
    )

    run_attempt_count: int = Field(
        ...,
        ge=0,
        description=(
            "Backend-maintained number of execution requests linked "
            "to the coding session."
        ),
    )

    idle_duration_seconds: int = Field(
        ...,
        ge=0,
        description=("Aggregate idle duration recorded for the session."),
    )

    last_blocked_paste_at: datetime | None = Field(
        default=None,
        description=(
            "Backend timestamp of the latest blocked-paste attempt. "
            "The blocked content itself is never collected."
        ),
    )

    @field_validator(
        "started_at",
        "ended_at",
        "last_activity_at",
        "last_blocked_paste_at",
        mode="after",
    )
    @classmethod
    def normalize_response_datetime(
        cls,
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


class StudentCodingSessionResponse(CodingSessionResponseBase):
    """
    Student-safe session response.

    student_id is intentionally excluded because ownership comes from
    the authenticated access token.
    """


class InstructorCodingSessionResponse(CodingSessionResponseBase):
    """
    Instructor review response for an owned activity.

    This response exposes the student identifier for authorized review
    but contains no automatic grade or misconduct decision.
    """

    student_id: int = Field(
        ...,
        gt=0,
        description=("Student who owns the coding session."),
    )

class GlobalCodingSessionResponse(InstructorCodingSessionResponse):
    """
    Global instructor review response for all active sessions.

    Includes additional contextual information to identify where the
    student is working.
    """
    student_name: str | None = Field(
        default=None,
        description="Name of the student owning the session.",
    )
    task_title: str | None = Field(
        default=None,
        description="Title of the activity being worked on.",
    )
    classroom_name: str | None = Field(
        default=None,
        description="Name of the classroom the task belongs to.",
    )


# Compatibility aliases for concise imports and future adapters.
CodingSessionCreate = CodingSessionStartRequest
CodingSessionUpdate = CodingSessionActivityUpdate
CodingSessionResponse = StudentCodingSessionResponse
CodingSessionTelemetryUpdate = CodingSessionActivityUpdate
