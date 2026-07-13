from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_instructor
from app.models.domain_models import Classroom, Task, User
from app.schemas.task_schema import (
    TaskCreate,
    TaskPublishRequest,
    TaskResponse,
    TaskUpdate,
)


router = APIRouter(
    prefix="/instructors",
    tags=["Instructors"],
)


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_owned_classroom(
    *,
    db: Session,
    class_id: int,
    instructor_id: int,
) -> Classroom:
    classroom = db.query(Classroom).filter(Classroom.class_id == class_id).first()

    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found.",
        )

    if classroom.instructor_id != instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage activities in your own classes.",
        )

    if not classroom.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Activities cannot be created in an inactive class.",
        )

    return classroom


def get_owned_task(
    *,
    db: Session,
    task_id: int,
    instructor_id: int,
) -> Task:
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    if task.instructor_id != instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own tasks.",
        )

    return task


@router.post(
    "/tasks/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
):
    get_owned_classroom(
        db=db,
        class_id=task_data.class_id,
        instructor_id=current_instructor.user_id,
    )

    new_task = Task(
        class_id=task_data.class_id,
        instructor_id=current_instructor.user_id,
        title=task_data.title,
        description=task_data.description,
        instructions=task_data.instructions,
        activity_type=task_data.activity_type,
        required_ast_rules=task_data.required_ast_rules,
        starter_code=task_data.starter_code,
        paste_policy=task_data.paste_policy,
        is_graded=task_data.is_graded,
        is_published=False,
        due_at=task_data.due_at,
        published_at=None,
    )

    try:
        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        return new_task
    except Exception:
        db.rollback()
        raise


@router.get(
    "/tasks/",
    response_model=list[TaskResponse],
)
def list_tasks(
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
):
    return (
        db.query(Task)
        .filter(Task.instructor_id == current_instructor.user_id)
        .order_by(Task.created_at.desc())
        .all()
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
):
    return get_owned_task(
        db=db,
        task_id=task_id,
        instructor_id=current_instructor.user_id,
    )


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
def update_task(
    task_data: TaskUpdate,
    task_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
):
    task = get_owned_task(
        db=db,
        task_id=task_id,
        instructor_id=current_instructor.user_id,
    )

    update_data = task_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No task fields were provided for update.",
        )

    for field_name, value in update_data.items():
        setattr(task, field_name, value)

    try:
        db.commit()
        db.refresh(task)

        return task
    except Exception:
        db.rollback()
        raise


@router.patch(
    "/tasks/{task_id}/publication",
    response_model=TaskResponse,
)
def update_task_publication(
    publication_data: TaskPublishRequest,
    task_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
):
    task = get_owned_task(
        db=db,
        task_id=task_id,
        instructor_id=current_instructor.user_id,
    )

    if publication_data.is_published:
        if task.class_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A task must belong to a class before publication.",
            )

        get_owned_classroom(
            db=db,
            class_id=task.class_id,
            instructor_id=current_instructor.user_id,
        )

        if task.due_at is not None:
            due_at = task.due_at

            if due_at.tzinfo is None:
                due_at = due_at.replace(tzinfo=timezone.utc)

            if due_at <= get_utc_now():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="The task due date must be in the future.",
                )

        task.is_published = True
        task.published_at = get_utc_now()
    else:
        task.is_published = False
        task.published_at = None

    try:
        db.commit()
        db.refresh(task)

        return task
    except Exception:
        db.rollback()
        raise


# SECURITY BOUNDARY:
# instructor_id is always taken from the authenticated instructor.
# The frontend must never be allowed to create or modify tasks on behalf
# of another instructor.
