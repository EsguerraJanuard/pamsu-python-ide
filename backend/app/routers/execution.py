from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.domain_models import Submission, Task, User
from app.schemas.submission_schema import SubmissionCreate, SubmissionResponse

router = APIRouter(
    prefix="/execution",
    tags=["Execution"],
)


@router.post(
    "/submissions",
    response_model=SubmissionCreate,
    status_code=status.HTTP_201_CREATED,
)
def create_submission(
    submission_data: SubmissionCreate,
    db: Session = Depends(get_db),
):
    student = (
        db.query(User)
        .filter(
            User.user_id == submission_data.student_id,
            User.role == "student",
        )
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found.",
        )

    task = db.query(Task).filter(Task.task_id == submission_data.task_id).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    new_submission = Submission(
        student_id=submission_data.student_id,
        task_id=submission_data.task_id,
        raw_code=submission_data.raw_code,
        jaccard_score=None,
        ast_pass_fail=None,
    )

    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    return new_submission


@router.get(
    "/submissions/{sub_id}",
    response_model=SubmissionResponse,
)
def get_submission(
    sub_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    submission = db.query(Submission).filter(Submission.sub_id == sub_id).first()

    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )
    return submission
