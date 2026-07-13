from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_instructor, get_current_student
from app.models.domain_models import BehavioralLog, Submission, Task, User
from app.schemas.log_schema import (
    BehavioralLogCreate,
    BehavioralLogResponse,
    BehavioralLogUpdate,
)


router = APIRouter(
    prefix="/logs",
    tags=["Session Indicators"],
)


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


def get_behavioral_log_or_404(
    *,
    db: Session,
    log_id: int,
) -> BehavioralLog:
    behavioral_log = (
        db.query(BehavioralLog).filter(BehavioralLog.log_id == log_id).first()
    )

    if behavioral_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session indicator log not found.",
        )

    return behavioral_log


def verify_student_submission_ownership(
    *,
    submission: Submission,
    student_id: int,
) -> None:
    if submission.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage indicators for your own submission.",
        )


def verify_instructor_submission_access(
    *,
    db: Session,
    submission: Submission,
    instructor_id: int,
) -> None:
    task = db.query(Task).filter(Task.task_id == submission.task_id).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task associated with this submission was not found.",
        )

    if task.instructor_id != instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You can only view session indicators for activities that you own."
            ),
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
    submission = get_submission_or_404(
        db=db,
        sub_id=log_data.sub_id,
    )

    verify_student_submission_ownership(
        submission=submission,
        student_id=current_student.user_id,
    )

    existing_log = (
        db.query(BehavioralLog).filter(BehavioralLog.sub_id == log_data.sub_id).first()
    )

    if existing_log is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A session indicator log already exists for this submission.",
        )

    new_log = BehavioralLog(
        sub_id=log_data.sub_id,
        tab_switches_count=log_data.tab_switches_count,
        blocked_paste_count=log_data.blocked_paste_count,
        run_attempt_count=log_data.run_attempt_count,
        idle_duration_seconds=log_data.idle_duration_seconds,
        last_blocked_paste_at=log_data.last_blocked_paste_at,
    )

    try:
        db.add(new_log)
        db.commit()
        db.refresh(new_log)

        return new_log

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A session indicator log already exists for this submission.",
        ) from exc

    except Exception:
        db.rollback()
        raise


@router.patch(
    "/behavioral/{log_id}",
    response_model=BehavioralLogResponse,
)
def update_behavioral_log(
    log_data: BehavioralLogUpdate,
    log_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
):
    behavioral_log = get_behavioral_log_or_404(
        db=db,
        log_id=log_id,
    )

    submission = get_submission_or_404(
        db=db,
        sub_id=behavioral_log.sub_id,
    )

    verify_student_submission_ownership(
        submission=submission,
        student_id=current_student.user_id,
    )

    update_data = log_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No session indicator fields were provided.",
        )

    monotonic_fields = {
        "tab_switches_count",
        "blocked_paste_count",
        "run_attempt_count",
        "idle_duration_seconds",
    }

    for field_name, value in update_data.items():
        if (
            field_name in monotonic_fields
            and value is not None
            and value < getattr(behavioral_log, field_name)
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{field_name} cannot be decreased.",
            )

        setattr(behavioral_log, field_name, value)

    try:
        db.commit()
        db.refresh(behavioral_log)

        return behavioral_log

    except Exception:
        db.rollback()
        raise


@router.get(
    "/behavioral/{log_id}",
    response_model=BehavioralLogResponse,
)
def get_behavioral_log(
    log_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
):
    behavioral_log = get_behavioral_log_or_404(
        db=db,
        log_id=log_id,
    )

    submission = get_submission_or_404(
        db=db,
        sub_id=behavioral_log.sub_id,
    )

    verify_instructor_submission_access(
        db=db,
        submission=submission,
        instructor_id=current_instructor.user_id,
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
    submission = get_submission_or_404(
        db=db,
        sub_id=sub_id,
    )

    verify_instructor_submission_access(
        db=db,
        submission=submission,
        instructor_id=current_instructor.user_id,
    )

    behavioral_log = (
        db.query(BehavioralLog).filter(BehavioralLog.sub_id == sub_id).first()
    )

    if behavioral_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No session indicator log exists for this submission.",
        )

    return behavioral_log


# PRIVACY BOUNDARY:
# These endpoints accept and return summarized counts and timestamps only.
# Clipboard text, browsing history, screen recordings, webcam or microphone
# data, and complete keystroke histories must never be stored.

# REVIEW BOUNDARY:
# Session indicators provide context for authorized instructor review only.
# They must not produce a behavior score or automatically prove misconduct.

# TRANSITIONAL NOTE:
# This router preserves the existing submission-linked BehavioralLog workflow.
# Future live-session updates should use CodingSession before a submission
# exists, while this record may remain as the finalized submission snapshot.
