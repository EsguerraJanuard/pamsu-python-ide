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


REVIEW_NOTICE = (
    "Automated AST and similarity results are review indicators only. "
    "They do not independently determine plagiarism, misconduct, "
    "or the official grade."
)


class EvaluationResponse(BaseModel):
    sub_id: int = Field(
        ...,
        gt=0,
        description="Evaluated submission identifier.",
    )
    student_id: int = Field(
        ...,
        gt=0,
        description="Owner of the evaluated submission.",
    )
    task_id: int = Field(
        ...,
        gt=0,
        description="Associated task identifier.",
    )
    ast_pass_fail: bool | None = Field(
        default=None,
        description=(
            "Whether the submission satisfied the configured structural AST rules."
        ),
    )
    jaccard_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description=("Highest source-code similarity score expressed as a percentage."),
    )
    highest_match_sub_id: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Submission identifier with the highest comparison "
            "score, when a comparison exists."
        ),
    )
    ast_details: dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed structural-analysis findings.",
    )
    jaccard_details: dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed similarity-review information.",
    )
    review_notice: str = REVIEW_NOTICE

    model_config = ConfigDict(
        extra="forbid",
    )

    @field_validator("jaccard_score")
    @classmethod
    def validate_jaccard_score(
        cls,
        value: float | None,
    ) -> float | None:
        if value is not None and not 0 <= value <= 100:
            raise ValueError("Jaccard score must be between 0 and 100.")

        return value


def get_submission_or_404(
    *,
    db: Session,
    sub_id: int,
) -> Submission:
    submission = db.query(Submission).filter(Submission.sub_id == sub_id).first()

    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )

    return submission


def get_task_or_404(
    *,
    db: Session,
    task_id: int,
) -> Task:
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found for this submission.",
        )

    return task


def verify_instructor_owns_submission_task(
    *,
    task: Task,
    instructor_id: int,
) -> None:
    if task.instructor_id != instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You can only evaluate submissions belonging "
                "to activities that you own."
            ),
        )


@router.post(
    "/submissions/{sub_id}",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    operation_id="evaluate_submission",
    summary="Evaluate a submission",
    description=(
        "Runs configured AST checks and source-code similarity analysis "
        "for a submission owned by the authenticated instructor. Results "
        "are stored and returned only as review indicators. This endpoint "
        "does not execute student code and does not assign an official grade."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "The submission belongs to a task owned by another instructor."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The submission or its associated task does not exist."),
        },
    },
)
def evaluate_submission(
    sub_id: int = Path(
        ...,
        gt=0,
        description="Submission identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> EvaluationResponse:
    submission = get_submission_or_404(
        db=db,
        sub_id=sub_id,
    )

    task = get_task_or_404(
        db=db,
        task_id=submission.task_id,
    )

    verify_instructor_owns_submission_task(
        task=task,
        instructor_id=current_instructor.user_id,
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

    return EvaluationResponse.model_validate(evaluation_result)


# AUTHORIZATION BOUNDARY:
# Full similarity comparison details are restricted to the instructor who
# owns the activity. Students must not receive another student's source code
# or detailed comparison information.

# EXECUTION BOUNDARY:
# This endpoint performs static structural and similarity analysis only.
# Student code must never execute inside this router or the FastAPI process.

# REVIEW BOUNDARY:
# AST findings and Jaccard similarity results provide review information only.
# They must never automatically assign an official grade, declare plagiarism,
# or determine misconduct.
