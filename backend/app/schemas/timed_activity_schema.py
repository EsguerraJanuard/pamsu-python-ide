from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.task_schema import normalize_response_datetime

TimerState = Literal[
    "not_started",
    "running",
    "expired",
    "closed",
]


class StudentActivityTimerResponse(BaseModel):
    """
    The authenticated student's timer on a timed activity.

    The workspace counts down from ends_at using server_now to correct for
    the device clock; the server enforces submit_until on its own.
    """

    task_id: int = Field(..., gt=0)
    state: TimerState = Field(
        ...,
        description=(
            "not_started: a timer can be started. running: open until ends_at. "
            "expired: the student's time has ended. closed: the deadline passed "
            "before the student started."
        ),
    )
    time_limit_minutes: int = Field(..., ge=1)
    server_now: datetime
    window_number: int | None = None
    started_at: datetime | None = None
    ends_at: datetime | None = Field(
        default=None,
        description="When the time is up: the time limit, or the deadline if sooner.",
    )
    submit_until: datetime | None = Field(
        default=None,
        description="Last moment a submission is accepted (ends_at plus a short grace).",
    )
    opened_with_retake: bool = False
    retake_available: bool = Field(
        default=False,
        description="The instructor allowed another attempt: starting opens a new timer.",
    )
    submitted_in_window: bool = False

    model_config = ConfigDict(extra="forbid")

    @field_validator("server_now", "started_at", "ends_at", "submit_until", mode="before")
    @classmethod
    def normalize_datetimes(cls, value: Any) -> Any:
        return normalize_response_datetime(value)
