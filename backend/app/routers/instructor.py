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
    tags=["Instructor"],
)


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


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
            detail=("You can only manage activities in your own classes."),
        )

    if not classroom.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("Activities cannot be managed in an inactive class."),
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


def validate_task_for_publication(
    *,
    db: Session,
    class_id: int | None,
    instructor_id: int,
    due_at: datetime | None,
) -> None:
    if class_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A task must belong to a class before publication.",
        )

    get_owned_classroom(
        db=db,
        class_id=class_id,
        instructor_id=instructor_id,
    )

    if due_at is None:
        return

    normalized_due_at = normalize_utc_datetime(due_at)

    if normalized_due_at <= get_utc_now():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The task due date must be in the future.",
        )


def commit_task(
    *,
    db: Session,
    task: Task,
) -> Task:
    try:
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


@router.post(
    "/tasks/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_instructor_task",
    summary="Create a task",
    description=(
        "Creates a draft laboratory or homework activity inside a class "
        "owned by the authenticated instructor. The instructor identity "
        "is taken from the access token and cannot be supplied by the client."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "The class belongs to another instructor.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The selected class does not exist.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "The selected class is inactive.",
        },
    },
)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Task:
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

    db.add(new_task)

    return commit_task(
        db=db,
        task=new_task,
    )


@router.get(
    "/tasks/",
    response_model=list[TaskResponse],
    status_code=status.HTTP_200_OK,
    operation_id="list_instructor_tasks",
    summary="List instructor tasks",
    description=(
        "Returns tasks created by the authenticated instructor, ordered "
        "from newest to oldest."
    ),
)
def list_tasks(
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> list[Task]:
    return (
        db.query(Task)
        .filter(Task.instructor_id == current_instructor.user_id)
        .order_by(Task.created_at.desc())
        .all()
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_instructor_task",
    summary="Get an instructor task",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "The task belongs to another instructor.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The task does not exist.",
        },
    },
)
def get_task(
    task_id: int = Path(
        ...,
        gt=0,
        description="Task identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Task:
    return get_owned_task(
        db=db,
        task_id=task_id,
        instructor_id=current_instructor.user_id,
    )


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    operation_id="update_instructor_task",
    summary="Update an instructor task",
    description=(
        "Updates selected task fields. Moving a task to another class is "
        "allowed only when the destination class belongs to the authenticated "
        "instructor and remains active."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "No task fields were supplied.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": (
                "The task or selected class belongs to another instructor."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The task or selected class does not exist.",
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The selected class is inactive or the published task "
                "would become invalid."
            ),
        },
    },
)
def update_task(
    task_data: TaskUpdate,
    task_id: int = Path(
        ...,
        gt=0,
        description="Task identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Task:
    task = get_owned_task(
        db=db,
        task_id=task_id,
        instructor_id=current_instructor.user_id,
    )

    update_data = task_data.model_dump(
        exclude_unset=True,
    )

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No task fields were provided for update.",
        )

    candidate_class_id = update_data.get(
        "class_id",
        task.class_id,
    )
    candidate_due_at = update_data.get(
        "due_at",
        task.due_at,
    )

    if "class_id" in update_data:
        if candidate_class_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A task must belong to a class.",
            )

        get_owned_classroom(
            db=db,
            class_id=candidate_class_id,
            instructor_id=current_instructor.user_id,
        )

    if task.is_published:
        validate_task_for_publication(
            db=db,
            class_id=candidate_class_id,
            instructor_id=current_instructor.user_id,
            due_at=candidate_due_at,
        )

    for field_name, value in update_data.items():
        setattr(task, field_name, value)

    return commit_task(
        db=db,
        task=task,
    )


@router.patch(
    "/tasks/{task_id}/publication",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    operation_id="update_task_publication",
    summary="Publish or unpublish a task",
    description=(
        "Publishes a valid task or returns it to draft status. Publishing "
        "requires an active instructor-owned class and a future due date "
        "when a due date is provided."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": ("The task or its class belongs to another instructor."),
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The task or class does not exist.",
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "The task cannot be published because its class or due date is invalid."
            ),
        },
    },
)
def update_task_publication(
    publication_data: TaskPublishRequest,
    task_id: int = Path(
        ...,
        gt=0,
        description="Task identifier.",
    ),
    db: Session = Depends(get_db),
    current_instructor: User = Depends(get_current_instructor),
) -> Task:
    task = get_owned_task(
        db=db,
        task_id=task_id,
        instructor_id=current_instructor.user_id,
    )

    if publication_data.is_published:
        validate_task_for_publication(
            db=db,
            class_id=task.class_id,
            instructor_id=current_instructor.user_id,
            due_at=task.due_at,
        )

        if not task.is_published:
            task.published_at = get_utc_now()

        task.is_published = True
    else:
        task.is_published = False
        task.published_at = None

    return commit_task(
        db=db,
        task=task,
    )


# SECURITY BOUNDARY:
# instructor_id always comes from the authenticated instructor.
# Clients cannot create or update tasks on behalf of another instructor.
# Task ownership and class ownership are checked independently.
