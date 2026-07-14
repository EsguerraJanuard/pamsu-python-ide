from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    get_current_student,
    get_current_user,
)
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


def normalize_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def is_past_due(due_at: datetime | None) -> bool:
    if due_at is None:
        return False

    return get_utc_now() >= normalize_utc_datetime(due_at)


def get_task_or_404(
    *,
    db: Session,
    task_id: int,
) -> Task:
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    return task


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
            detail=("Practice activities do not accept graded submissions."),
        )

    if is_past_due(task.due_at):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("The submission period for this activity has ended."),
        )

    # Transitional compatibility for records created before classroom
    # ownership was introduced. Newly created tasks must belong to a class.
    if task.class_id is None:
        return

    if task.classroom is None or not task.classroom.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=("The class for this activity is no longer active."),
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
        .filter(CodingSession.session_id == coding_session_id)
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
            detail=("You cannot use another student's coding session."),
        )

    if coding_session.task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("The coding session does not belong to this activity."),
        )

    return coding_session


def verify_submission_access(
    *,
    db: Session,
    submission: Submission,
    current_user: User,
) -> None:
    if current_user.role == "student":
        if submission.student_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own submissions.",
            )

        return

    if current_user.role == "instructor":
        task = get_task_or_404(
            db=db,
            task_id=submission.task_id,
        )

        if task.instructor_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=("You can only access submissions for activities that you own."),
            )

        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied.",
    )


@router.post(
    "/submissions/",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_student_submission",
    summary="Create a submission attempt",
    description=(
        "Creates a new immutable code-submission attempt for the "
        "authenticated student. Previous attempts remain stored, while "
        "the newest accepted attempt becomes the official submission. "
        "This endpoint does not execute student code."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "The activity is unpublished, the class is inactive, "
                "the student is not enrolled, or the coding session "
                "belongs to another student."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The task or supplied coding session does not exist."),
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The activity does not accept graded submissions, "
                "the deadline has passed, the coding session belongs "
                "to another activity, or a concurrent attempt conflict "
                "occurred."
            ),
        },
    },
)
def create_submission(
    submission_data: SubmissionCreate,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student),
) -> Submission:
    task = get_task_or_404(
        db=db,
        task_id=submission_data.task_id,
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
            coding_session_id=(submission_data.coding_session_id),
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
    status_code=status.HTTP_200_OK,
    operation_id="get_submission",
    summary="Get an authorized submission",
    description=(
        "Students may retrieve only their own submissions. Instructors "
        "may retrieve submissions only for tasks that they own."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "The authenticated user does not own or manage the "
                "requested submission."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": ("The submission or its associated task does not exist."),
        },
    },
)
def get_submission(
    sub_id: int = Path(
        ...,
        gt=0,
        description="Submission identifier.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Submission:
    submission = get_submission_or_404(
        db=db,
        sub_id=sub_id,
    )

    verify_submission_access(
        db=db,
        submission=submission,
        current_user=current_user,
    )

    return submission


# SECURITY BOUNDARY:
# student_id always comes from the authenticated student.
# Clients cannot create submissions on behalf of another student.

# EXECUTION BOUNDARY:
# This router stores code and submission metadata only. Student code must
# never execute inside FastAPI, the React client, or the host operating
# system. Execution requests must be handled by the isolated sandbox
# integration owned by the execution-service partner.

# IMMUTABILITY BOUNDARY:
# A resubmission creates a new Submission record. Existing source code and
# attempt numbers are not overwritten. Only the official-attempt marker is
# transferred to the latest accepted attempt.
