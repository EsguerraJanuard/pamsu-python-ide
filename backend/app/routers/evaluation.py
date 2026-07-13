from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_instructor
from app.models.domain_models import Submission, Task, User
from app.services.evaluation_service import (
    SubmissionNotFoundError,
    TaskNotFoundError,
    evaluate_submission_by_id,
)


router = APIRouter(
    prefix="/evaluation",
    tags=["Evaluation"],
)


class EvaluationResponse(BaseModel):
    sub_id: int = Field(..., gt=0)
    student_id: int = Field(..., gt=0)
    task_id: int = Field(..., gt=0)
    ast_pass_fail: bool | None = None
    jaccard_score: float | None = None
    highest_match_sub_id: int | None = None
    ast_details: dict[str, Any] = Field(default_factory=dict)
    jaccard_details: dict[str, Any] = Field(default_factory=dict)
    review_notice: str = (
        "Automated AST and similarity results are review indicators only. "
        "They do not independently determine plagiarism, misconduct, "
        "or the official grade."
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("jaccard_score")
    @classmethod
    def validate_jaccard_score(
        cls,
        value: float | None,
    ) -> float | None:
        if value is not None and not 0 <= value <= 100:
            raise ValueError("Jaccard score must be between 0 and 100.")

        return value


@router.post(
    "/submissions/{sub_id}",
    response_model=EvaluationResponse,
)
def evaluate_submission(
    sub_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
):
    submission = db.query(Submission).filter(Submission.sub_id == sub_id).first()

    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )

    task = db.query(Task).filter(Task.task_id == submission.task_id).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found for this submission.",
        )

    if task.instructor_id != current_instructor.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You can only evaluate submissions belonging "
                "to activities that you own."
            ),
        )

    try:
        evaluation_result = evaluate_submission_by_id(
            db=db,
            sub_id=sub_id,
        )
    except SubmissionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        ) from exc
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found for this submission.",
        ) from exc

    return evaluation_result


# AUTHORIZATION BOUNDARY:
# Full similarity comparison details are restricted to the instructor who
# owns the activity. Students should receive their AST learning feedback
# through a separate student-safe structure-check endpoint.

# REVIEW BOUNDARY:
# AST findings and Jaccard similarity results provide review information only.
# They must never automatically assign an official grade or declare misconduct.
