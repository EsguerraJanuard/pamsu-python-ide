from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.domain_models import Task, User
from app.schemas.task_schema import TaskCreate, TaskResponse

router = APIRouter(
    prefix="/instructors",
    tags=["Instructors"],
)


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    instructor = (
        db.query(User)
        .filter(User.user_id == task_data.instructor_id, User.role == "instructor")
        .first()
    )

    if instructor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found",
        )

    new_task = Task(
        instructor_id=task_data.instructor_id,
        title=task_data.title,
        required_ast_rules=task_data.required_ast_rules,
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    return task
