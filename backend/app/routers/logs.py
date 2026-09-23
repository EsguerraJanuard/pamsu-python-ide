from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    get_current_instructor,
    get_current_student,
)
from app.models.domain_models import (
    BehavioralLog,
    Submission,
    Task,
    User,
)
from app.schemas.log_schema import (
    BehavioralLogCreate,
    BehavioralLogResponse,
    BehavioralLogUpdate,
)


router = APIRouter(
    prefix="/logs",
    tags=["Behavioral Logs"],
)


MONOTONIC_INDICATOR_FIELDS = {
    "tab_switches_count",
    "blocked_paste_count",
    "mouseleave_count",
    "run_attempt_count",
    "idle_duration_seconds",
}


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


def get_behavioral_log_by_submission_or_404(
    *,
    db: Session,
    sub_id: int,
) -> BehavioralLog:
    behavioral_log = (
        db.query(BehavioralLog).filter(BehavioralLog.sub_id == sub_id).first()
    )

    if behavioral_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=("No session indicator log exists for this submission."),
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
            detail=("You can only manage indicators for your own submission."),
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
            detail=("Task associated with this submission was not found."),
        )

    if task.instructor_id != instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You can only view session indicators for activities that you own."
            ),
        )


def validate_monotonic_updates(
    *,
    behavioral_log: BehavioralLog,
    update_data: dict[str, object],
) -> None:
    for field_name in MONOTONIC_INDICATOR_FIELDS:
        if field_name not in update_data:
            continue

        new_value = update_data[field_name]

        if new_value is None:
            continue

        current_value = getattr(
            behavioral_log,
            field_name,
        )

        if new_value < current_value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{field_name} cannot be decreased.",
            )


def commit_behavioral_log(
    *,
    db: Session,
    behavioral_log: BehavioralLog,
) -> BehavioralLog:
    try:
        db.commit()
        db.refresh(behavioral_log)
        return behavioral_log
    except Exception:
        db.rollback()
        raise


@router.post(
    "/behavioral/",
    response_model=BehavioralLogResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_submission_behavioral_log",
    summary="Create submission session indicators",
    description=(
        "Creates one summarized session-indicator record for a submission "
        "owned by the authenticated student. Only counts and timestamps are "
        "accepted. Clipboard contents, screen recordings, browsing history, "
        "webcam data, microphone data, and complete keystroke histories are "
        "not collected."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": ("The submission belongs to another student."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The submission does not exist.",
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "A session-indicator record already exists for the submission."
            ),
        },
    },
)
def create_behavioral_log(
    log_data: BehavioralLogCreate,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> BehavioralLog:
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
            detail=("A session indicator log already exists for this submission."),
        )

    new_log = BehavioralLog(
        sub_id=log_data.sub_id,
        tab_switches_count=log_data.tab_switches_count,
        blocked_paste_count=log_data.blocked_paste_count,
        mouseleave_count=log_data.mouseleave_count,
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
            detail=("A session indicator log already exists for this submission."),
        ) from exc

    except Exception:
        db.rollback()
        raise


@router.get(
    "/behavioral/submission/{sub_id}",
    response_model=BehavioralLogResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_behavioral_log_by_submission",
    summary="Get indicators by submission",
    description=(
        "Returns the summarized session indicators for a submission "
        "belonging to an activity owned by the authenticated instructor."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": ("The submission belongs to another instructor's activity."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The submission, associated task, or indicator record does not exist."
            ),
        },
    },
)
def get_behavioral_log_by_submission(
    sub_id: int = Path(
        ...,
        gt=0,
        description="Submission identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> BehavioralLog:
    submission = get_submission_or_404(
        db=db,
        sub_id=sub_id,
    )

    verify_instructor_submission_access(
        db=db,
        submission=submission,
        instructor_id=current_instructor.user_id,
    )

    return get_behavioral_log_by_submission_or_404(
        db=db,
        sub_id=sub_id,
    )


@router.patch(
    "/behavioral/{log_id}",
    response_model=BehavioralLogResponse,
    status_code=status.HTTP_200_OK,
    operation_id="update_submission_behavioral_log",
    summary="Update submission session indicators",
    description=(
        "Updates summarized indicators for a submission owned by the "
        "authenticated student. Count and duration values are monotonic "
        "and cannot be decreased."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "No indicator fields were supplied.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": ("The associated submission belongs to another student."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The indicator record or associated submission does not exist."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "description": ("A count or duration value attempted to decrease."),
        },
    },
)
def update_behavioral_log(
    log_data: BehavioralLogUpdate,
    log_id: int = Path(
        ...,
        gt=0,
        description="Session indicator log identifier.",
    ),
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> BehavioralLog:
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

    update_data = log_data.model_dump(
        exclude_unset=True,
    )

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No session indicator fields were provided.",
        )

    validate_monotonic_updates(
        behavioral_log=behavioral_log,
        update_data=update_data,
    )

    for field_name, value in update_data.items():
        setattr(
            behavioral_log,
            field_name,
            value,
        )

    return commit_behavioral_log(
        db=db,
        behavioral_log=behavioral_log,
    )


@router.get(
    "/behavioral/{log_id}",
    response_model=BehavioralLogResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_behavioral_log",
    summary="Get a session-indicator record",
    description=(
        "Returns a summarized session-indicator record when its submission "
        "belongs to an activity owned by the authenticated instructor."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": ("The associated activity belongs to another instructor."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The indicator record, submission, or associated task does not exist."
            ),
        },
    },
)
def get_behavioral_log(
    log_id: int = Path(
        ...,
        gt=0,
        description="Session indicator log identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> BehavioralLog:
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


# PRIVACY BOUNDARY:
# These endpoints accept and return summarized counts and timestamps only.
# Clipboard contents, browsing history, screen recordings, webcam or
# microphone data, and complete keystroke histories must never be stored.

# PASTE-POLICY BOUNDARY:
# Only blocked external-paste counts and the latest blocked-paste timestamp
# are stored. The pasted text itself must never be transmitted or persisted.

# REVIEW BOUNDARY:
# Session indicators provide context for authorized instructor review only.
# They must not produce a behavior score or automatically prove misconduct.

# TRANSITIONAL NOTE:
# BehavioralLog remains the finalized submission-linked snapshot. Future
# live-session updates may use CodingSession before a submission exists.
