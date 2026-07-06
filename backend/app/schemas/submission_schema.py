from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SubmissionBase(BaseModel):
    raw_code: str = Field(..., min_length=1)


class SubmissionCreate(SubmissionBase):
    student_id: int = Field(..., gt=0)
    task_id: int = Field(..., gt=0)


class SubmissionResponse(SubmissionBase):
    sub_id: int
    student_id: int
    task_id: int
    jaccard_score: Optional[float] = None
    ast_pass_fail: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)

    @field_validator("jaccard_score")
    @classmethod
    def validate_jaccard_score(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and not 0 <= value <= 100:
            raise ValueError("jaccard_score must be between 0 and 100")
        return value
