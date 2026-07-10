from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_instructor, get_current_student
from app.models.domain_models import BehavioralLog, Submission, User
from app.schemas.log_schema import BehavioralLogCreate, BehavioralLogResponse


router = APIRouter(
    prefix="/logs",
    tags=["Behavioral Logs"],
)


@router.post(
    "/behavioral/",
    response_model=BehavioralLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_behavioral_log(
    log_data: BehavioralLogCreate,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
):
    submission = (
        db.query(Submission).filter(Submission.sub_id == log_data.sub_id).first()
    )

    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )

    if submission.student_id != current_student.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create logs for your own submissions.",
        )

    existing_log = (
        db.query(BehavioralLog).filter(BehavioralLog.sub_id == log_data.sub_id).first()
    )

    if existing_log is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Behavioral log already exists for this submission.",
        )

    new_log = BehavioralLog(
        sub_id=log_data.sub_id,
        tab_switches_count=log_data.tab_switches_count,
    )

    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return new_log


@router.get(
    "/behavioral/{log_id}",
    response_model=BehavioralLogResponse,
)
def get_behavioral_log(
    log_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
):
    behavioral_log = (
        db.query(BehavioralLog).filter(BehavioralLog.log_id == log_id).first()
    )

    if behavioral_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Behavioral log not found.",
        )

    submission = (
        db.query(Submission).filter(Submission.sub_id == behavioral_log.sub_id).first()
    )

    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Related submission not found.",
        )

    return behavioral_log


@router.get(
    "/behavioral/submission/{sub_id}",
    response_model=BehavioralLogResponse,
)
def get_behavioral_log_by_submission(
    sub_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
):
    behavioral_log = (
        db.query(BehavioralLog).filter(BehavioralLog.sub_id == sub_id).first()
    )

    if behavioral_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Behavioral log not found for this submission.",
        )

    submission = db.query(Submission).filter(Submission.sub_id == sub_id).first()

    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Related submission not found.",
        )

    return behavioral_log
