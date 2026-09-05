from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BehavioralLogBase(BaseModel):
    tab_switches_count: int = Field(default=0, ge=0)
    blocked_paste_count: int = Field(default=0, ge=0)
    mouseleave_count: int = Field(default=0, ge=0)
    run_attempt_count: int = Field(default=0, ge=0)
    idle_duration_seconds: int = Field(default=0, ge=0)
    last_blocked_paste_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")


class BehavioralLogCreate(BehavioralLogBase):
    sub_id: int = Field(..., gt=0)

    # SECURITY BOUNDARY:
    # The backend must verify that the authenticated student owns this
    # submission before creating or updating its behavioral summary.


class BehavioralLogUpdate(BaseModel):
    tab_switches_count: int | None = Field(default=None, ge=0)
    blocked_paste_count: int | None = Field(default=None, ge=0)
    mouseleave_count: int | None = Field(default=None, ge=0)
    run_attempt_count: int | None = Field(default=None, ge=0)
    idle_duration_seconds: int | None = Field(default=None, ge=0)
    last_blocked_paste_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")

    # PRIVACY BOUNDARY:
    # Store summarized counts and timestamps only. Never accept or store
    # clipboard contents, browsing history, screen data, webcam or microphone
    # data, or a complete keystroke history.


class BehavioralLogResponse(BehavioralLogBase):
    log_id: int
    sub_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )
