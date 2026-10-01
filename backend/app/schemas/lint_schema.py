from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class LintRequest(BaseModel):
    code: str = Field(..., description="The python code to lint")

class LintMarker(BaseModel):
    line: int
    column: int
    message: str
    severity: Literal["error", "warning", "info"]

class LintResult(BaseModel):
    markers: List[LintMarker] = []
