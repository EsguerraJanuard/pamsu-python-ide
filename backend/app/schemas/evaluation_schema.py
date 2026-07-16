from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ==========================================
# AST ANALYTICS SCHEMAS
# ==========================================


class ASTFindingResponse(BaseModel):
    finding_id: int
    rule_key: str
    label: str
    passed: Optional[bool] = None
    line_number: Optional[int] = None
    message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ASTAnalysisResponse(BaseModel):
    analysis_id: int
    submission_id: Optional[int] = None
    execution_id: Optional[str] = None
    overall_pass: Optional[bool] = None
    syntax_error: Optional[Dict[str, Any]] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    findings: List[ASTFindingResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# SIMILARITY SCHEMAS
# ==========================================


class SimilarityResultResponse(BaseModel):
    result_id: int
    source_submission_id: int
    compared_submission_id: int
    score: float = Field(ge=0.0, le=100.0)
    algorithm: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# INSTRUCTOR GRADING SCHEMAS
# ==========================================


class InstructorGradeBase(BaseModel):
    score: float = Field(..., ge=0.0, description="The assigned grade.")
    max_score: float = Field(..., gt=0.0, description="The highest possible score.")
    feedback: Optional[str] = Field(None, description="Optional instructor notes.")
    is_released: bool = Field(False, description="Controls visibility to the student.")

    @model_validator(mode="after")
    def check_score_bounds(self) -> "InstructorGradeBase":
        if self.score > self.max_score:
            raise ValueError("score cannot be greater than max_score")
        return self


class InstructorGradeCreate(InstructorGradeBase):
    pass


class InstructorGradeUpdate(BaseModel):
    score: Optional[float] = Field(None, ge=0.0)
    max_score: Optional[float] = Field(None, gt=0.0)
    feedback: Optional[str] = None
    is_released: Optional[bool] = None

    @model_validator(mode="after")
    def check_score_bounds(self) -> "InstructorGradeUpdate":
        if self.score is not None and self.max_score is not None:
            if self.score > self.max_score:
                raise ValueError("score cannot be greater than max_score")
        return self


class InstructorGradeResponse(InstructorGradeBase):
    grade_id: int
    submission_id: int
    instructor_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# EVALUATION WORKFLOW SCHEMAS
# ==========================================


class EvaluationStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(awaiting_review|graded|rejected)$")


class SubmissionEvaluationResponse(BaseModel):
    sub_id: int
    status: str
    jaccard_score: Optional[float] = None
    ast_pass_fail: Optional[bool] = None

    # REVIEW BOUNDARY:
    # Automated indicators below do not determine the official grade.
    ast_analyses: List[ASTAnalysisResponse] = Field(default_factory=list)
    similarity_results_as_source: List[SimilarityResultResponse] = Field(
        default_factory=list
    )

    # GRADING BOUNDARY:
    # The official manual grade explicitly set by the instructor.
    instructor_grade: Optional[InstructorGradeResponse] = None

    model_config = ConfigDict(from_attributes=True)
