from typing import Any, Dict, List, Optional

from app.schemas.execution_schema import MAX_SOURCE_CODE_LENGTH
from pydantic import BaseModel, Field


class PracticeTaskBase(BaseModel):
    task_id: int
    title: str
    instructions: str
    starter_code: Optional[str] = None
    order_index: int
    expected_ast_patterns: Optional[Dict[str, Any]] = None

class PracticeTaskDetail(PracticeTaskBase):
    is_completed: bool = False
    attempts_count: int = 0
    is_locked: bool = False

    class Config:
        from_attributes = True

class PracticeModuleBase(BaseModel):
    module_id: int
    title: str
    description: Optional[str] = None
    order_index: int

class PracticeModuleList(PracticeModuleBase):
    is_completed: bool = False
    is_locked: bool = False
    tasks: List[PracticeTaskDetail] = []

    class Config:
        from_attributes = True

class PracticeSubmissionRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=MAX_SOURCE_CODE_LENGTH)

class PracticeSubmissionResponse(BaseModel):
    # The AI Tutor endpoint (/practice/attempts/{attempt_id}/ai-hint) needs it.
    attempt_id: int
    is_successful: bool
    execution_feedback: Optional[str] = None
    ast_feedback: Optional[List[str]] = None
    message: str

class ModuleBreakdown(BaseModel):
    module_title: str
    total_tasks: int
    completed_tasks: int
    attempts_count: int


class GrowthAnalyticsResponse(BaseModel):
    overall_growth_score: int
    total_tasks: int
    completed_tasks: int
    total_attempts: int
    successful_attempts: int
    module_breakdown: List[ModuleBreakdown] = []

class PracticeModuleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: int = 0
    
    class Config:
        extra = "forbid"

class PracticeModuleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: Optional[int] = None
    
    class Config:
        extra = "forbid"

class PracticeTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    instructions: str = Field(..., min_length=1)
    starter_code: Optional[str] = None
    expected_output: str = Field(..., min_length=1)
    expected_ast_patterns: Optional[Dict[str, Any]] = None
    order_index: int = 0
    
    class Config:
        extra = "forbid"

class PracticeTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    instructions: Optional[str] = Field(None, min_length=1)
    starter_code: Optional[str] = None
    expected_output: Optional[str] = Field(None, min_length=1)
    expected_ast_patterns: Optional[Dict[str, Any]] = None
    order_index: Optional[int] = None
    
    class Config:
        extra = "forbid"



class PracticeAiHintResponse(BaseModel):
    ai_hint: Optional[str] = None
    # "processing" until the hint is ready (poll again), then "completed".
    status: str
