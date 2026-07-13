from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_student, get_current_user
from app.models.domain_models import (
    CodingSession,
    Enrollment,
    Submission,
    Task,
    User,
)
from app.schemas.submission_schema import (
    SubmissionCreate,
    SubmissionResponse,
)


router = APIRouter(
    prefix="/execution",
    tags=["Execution"],
)


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_past_due(due_at: datetime | None) -> bool:
    if due_at is None:
        return False

    normalized_due_at = due_at

    if normalized_due_at.tzinfo is None:
        normalized_due_at = normalized_due_at.replace(
            tzinfo=timezone.utc,
        )

    return get_utc_now() > normalized_due_at


def verify_student_task_access(
    *,
    db: Session,
    task: Task,
    student_id: int,
) -> None:
    if not task.is_published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This activity is not available for submission.",
        )

    if not task.is_graded:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Practice activities do not accept graded submissions.",
        )

    if is_past_due(task.due_at):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The submission period for this activity has ended.",
        )

    # Transitional compatibility:
    # Existing tasks may temporarily have no classroom until their migration
    # is completed. New published activities should belong to a classroom.
    if task.class_id is None:
        return

    if task.classroom is None or not task.classroom.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The class for this activity is no longer active.",
        )

    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.class_id == task.class_id,
            Enrollment.student_id == student_id,
            Enrollment.status == "active",
        )
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be actively enrolled in the class.",
        )


def verify_coding_session(
    *,
    db: Session,
    coding_session_id: str | None,
    student_id: int,
    task_id: int,
) -> CodingSession | None:
    if coding_session_id is None:
        return None

    coding_session = (
        db.query(CodingSession)
        .filter(
            CodingSession.session_id == coding_session_id,
        )
        .first()
    )

    if coding_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coding session not found.",
        )

    if coding_session.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot use another student's coding session.",
        )

    if coding_session.task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The coding session does not belong to this activity.",
        )

    return coding_session


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
    task = db.query(Task).filter(Task.task_id == submission_data.task_id).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    verify_student_task_access(
        db=db,
        task=task,
        student_id=current_student.user_id,
    )

    verify_coding_session(
        db=db,
        coding_session_id=submission_data.coding_session_id,
        student_id=current_student.user_id,
        task_id=task.task_id,
    )

    try:
        previous_attempts = (
            db.query(Submission)
            .filter(
                Submission.student_id == current_student.user_id,
                Submission.task_id == task.task_id,
            )
            .order_by(Submission.attempt_number.desc())
            .with_for_update()
            .all()
        )

        next_attempt_number = (
            previous_attempts[0].attempt_number + 1 if previous_attempts else 1
        )

        for previous_attempt in previous_attempts:
            if previous_attempt.is_official:
                previous_attempt.is_official = False

        new_submission = Submission(
            student_id=current_student.user_id,
            task_id=task.task_id,
            coding_session_id=submission_data.coding_session_id,
            attempt_number=next_attempt_number,
            raw_code=submission_data.raw_code,
            standard_input=submission_data.standard_input,
            status="awaiting_review",
            is_official=True,
            accepted_at=get_utc_now(),
            jaccard_score=None,
            ast_pass_fail=None,
        )

        db.add(new_submission)
        db.commit()
        db.refresh(new_submission)

        return new_submission

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A submission attempt was created at the same time. "
                "Please retry the submission."
            ),
        ) from exc

    except Exception:
        db.rollback()
        raise


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

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task associated with this submission was not found.",
            )

        if task.instructor_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=("You can only access submissions for activities that you own."),
            )

        return submission

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied.",
    )
