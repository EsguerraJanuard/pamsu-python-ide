from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_student, get_current_user
from app.models.domain_models import Submission, Task, User
from app.schemas.submission_schema import SubmissionCreate, SubmissionResponse


router = APIRouter(
    prefix="/execution",
    tags=["Execution"],
)


@router.post(
    "/submissions/",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_submission(
    submission_data: SubmissionCreate,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
):
    if submission_data.student_id != current_student.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create submissions using your own student ID.",
        )

    task = db.query(Task).filter(Task.task_id == submission_data.task_id).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    new_submission = Submission(
        student_id=current_student.user_id,
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
                detail="You can only access your own submissions.",
            )

        return submission

    if current_user.role == "instructor":
        task = db.query(Task).filter(Task.task_id == submission.task_id).first()

        if task is None or task.instructor_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access submissions for your own tasks.",
            )

        return submission

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied.",
    )
