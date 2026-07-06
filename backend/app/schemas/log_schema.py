from pydantic import BaseModel, ConfigDict, Field


class BehavioralLogBase(BaseModel):
    tab_switches_count: int = Field(default=0, ge=0)


class BehavioralLogCreate(BehavioralLogBase):
    sub_id: int = Field(..., gt=0)


class BehavioralLogResponse(BehavioralLogBase):
    log_id: int
    sub_id: int

    model_config = ConfigDict(from_attributes=True)
