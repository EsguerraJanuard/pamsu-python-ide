from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

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
    code: str

class PracticeSubmissionResponse(BaseModel):
    is_successful: bool
    execution_feedback: Optional[str] = None
    ast_feedback: Optional[List[str]] = None
    message: str
