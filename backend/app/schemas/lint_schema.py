from typing import List, Literal

from app.schemas.execution_schema import MAX_SOURCE_CODE_LENGTH
from pydantic import BaseModel, Field


class LintRequest(BaseModel):
    code: str = Field(..., max_length=MAX_SOURCE_CODE_LENGTH, description="The python code to lint")

class LintMarker(BaseModel):
    line: int
    column: int
    message: str
    severity: Literal["error", "warning", "info"]

class LintResult(BaseModel):
    markers: List[LintMarker] = []
