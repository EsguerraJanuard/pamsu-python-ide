from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
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
    sub_id: int
    student_id: int
    task_id: int
    ast_pass_fail: Optional[bool]
    jaccard_score: Optional[float]
    highest_match_sub_id: Optional[int]
    ast_details: dict[str, Any]
    jaccard_details: dict[str, Any]


@router.post(
    "/submissions/{sub_id}",
    response_model=EvaluationResponse,
)
def evaluate_submission(
    sub_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.sub_id == sub_id).first()

    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )

    if current_user.role == "student":
        if submission.student_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only evaluate your own submission.",
            )

    elif current_user.role == "instructor":
        task = db.query(Task).filter(Task.task_id == submission.task_id).first()

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found for this submission.",
            )

        if task.instructor_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only evaluate submissions under your own tasks.",
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    try:
        evaluation_result = evaluate_submission_by_id(db=db, sub_id=sub_id)
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
