from datetime import datetime, timezone
from typing import TypeVar

from sqlalchemy.orm import Session

from app.models.domain_models import (
    Classroom,
    Enrollment,
    Task,
    TaskTestCase,
)
from app.schemas.task_schema import (
    TaskCreate,
    TaskUpdate,
)
from app.schemas.task_test_case_schema import (
    TaskTestCaseCreate,
    TaskTestCaseUpdate,
)


ModelType = TypeVar(
    "ModelType",
    Task,
    TaskTestCase,
)


class TaskServiceError(Exception):
    """Base exception for activity and test-case operations."""


class TaskNotFoundError(TaskServiceError):
    pass


class TaskAccessDeniedError(TaskServiceError):
    pass


class TaskClassNotFoundError(TaskServiceError):
    pass


class TaskClassAccessDeniedError(TaskServiceError):
    pass


class TaskClassInactiveError(TaskServiceError):
    pass


class TaskUpdateEmptyError(TaskServiceError):
    pass


class TaskPublicationError(TaskServiceError):
    pass


class TaskTestCaseNotFoundError(TaskServiceError):
    pass


class StudentTaskUnavailableError(TaskServiceError):
    pass


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_utc_datetime(
    value: datetime,
) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def commit_and_refresh(
    *,
    db: Session,
    instance: ModelType,
) -> ModelType:
    try:
        db.commit()
        db.refresh(instance)

        return instance
    except Exception:
        db.rollback()
        raise


def get_classroom_by_id(
    *,
    db: Session,
    class_id: int,
) -> Classroom:
    classroom = db.query(Classroom).filter(Classroom.class_id == class_id).first()

    if classroom is None:
        raise TaskClassNotFoundError("Classroom not found.")

    return classroom


def get_instructor_classroom(
    *,
    db: Session,
    class_id: int,
    instructor_id: int,
    require_active: bool = False,
) -> Classroom:
    classroom = get_classroom_by_id(
        db=db,
        class_id=class_id,
    )

    if classroom.instructor_id != instructor_id:
        raise TaskClassAccessDeniedError(
            "You can only manage activities in your own classrooms."
        )

    if require_active and not classroom.is_active:
        raise TaskClassInactiveError(
            "Activities cannot be created or published inside an inactive classroom."
        )

    return classroom


def get_task_by_id(
    *,
    db: Session,
    task_id: int,
) -> Task:
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if task is None:
        raise TaskNotFoundError("Task not found.")

    return task


def get_instructor_task(
    *,
    db: Session,
    task_id: int,
    instructor_id: int,
) -> Task:
    task = get_task_by_id(
        db=db,
        task_id=task_id,
    )

    if task.instructor_id != instructor_id:
        raise TaskAccessDeniedError("You can only manage your own tasks.")

    return task


def validate_task_for_publication(
    *,
    db: Session,
    class_id: int | None,
    instructor_id: int,
    due_at: datetime | None,
) -> Classroom:
    if class_id is None:
        raise TaskPublicationError(
            "A task must belong to a classroom before publication."
        )

    classroom = get_instructor_classroom(
        db=db,
        class_id=class_id,
        instructor_id=instructor_id,
        require_active=True,
    )

    if due_at is not None:
        normalized_due_at = normalize_utc_datetime(due_at)

        if normalized_due_at <= get_utc_now():
            raise TaskPublicationError("The task due date must be in the future.")

    return classroom


def create_task(
    *,
    db: Session,
    instructor_id: int,
    task_data: TaskCreate,
) -> Task:
    get_instructor_classroom(
        db=db,
        class_id=task_data.class_id,
        instructor_id=instructor_id,
        require_active=True,
    )

    task = Task(
        class_id=task_data.class_id,
        instructor_id=instructor_id,
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

    db.add(task)

    return commit_and_refresh(
        db=db,
        instance=task,
    )


def list_instructor_tasks(
    *,
    db: Session,
    instructor_id: int,
    class_id: int | None = None,
) -> list[Task]:
    query = db.query(Task).filter(Task.instructor_id == instructor_id)

    if class_id is not None:
        get_instructor_classroom(
            db=db,
            class_id=class_id,
            instructor_id=instructor_id,
        )

        query = query.filter(Task.class_id == class_id)

    return query.order_by(
        Task.created_at.desc(),
        Task.task_id.desc(),
    ).all()


def update_task(
    *,
    db: Session,
    task_id: int,
    instructor_id: int,
    task_data: TaskUpdate,
) -> Task:
    task = get_instructor_task(
        db=db,
        task_id=task_id,
        instructor_id=instructor_id,
    )

    update_data = task_data.model_dump(
        exclude_unset=True,
    )

    if not update_data:
        raise TaskUpdateEmptyError("No task fields were provided for update.")

    if "class_id" in update_data and update_data["class_id"] is None:
        raise TaskPublicationError("A task must belong to a classroom.")

    candidate_class_id = update_data.get(
        "class_id",
        task.class_id,
    )
    candidate_due_at = update_data.get(
        "due_at",
        task.due_at,
    )

    if "class_id" in update_data:
        get_instructor_classroom(
            db=db,
            class_id=candidate_class_id,
            instructor_id=instructor_id,
            require_active=True,
        )

    if task.is_published and ("class_id" in update_data or "due_at" in update_data):
        validate_task_for_publication(
            db=db,
            class_id=candidate_class_id,
            instructor_id=instructor_id,
            due_at=candidate_due_at,
        )

    for field_name, value in update_data.items():
        setattr(
            task,
            field_name,
            value,
        )

    return commit_and_refresh(
        db=db,
        instance=task,
    )


def set_task_publication(
    *,
    db: Session,
    task_id: int,
    instructor_id: int,
    is_published: bool,
) -> Task:
    task = get_instructor_task(
        db=db,
        task_id=task_id,
        instructor_id=instructor_id,
    )

    if is_published:
        validate_task_for_publication(
            db=db,
            class_id=task.class_id,
            instructor_id=instructor_id,
            due_at=task.due_at,
        )

        if not task.is_published:
            task.published_at = get_utc_now()

        task.is_published = True
    else:
        task.is_published = False
        task.published_at = None

    return commit_and_refresh(
        db=db,
        instance=task,
    )


def get_test_case_by_id(
    *,
    db: Session,
    test_case_id: int,
) -> TaskTestCase:
    test_case = (
        db.query(TaskTestCase).filter(TaskTestCase.test_case_id == test_case_id).first()
    )

    if test_case is None:
        raise TaskTestCaseNotFoundError("Task test case not found.")

    return test_case


def get_instructor_test_case(
    *,
    db: Session,
    test_case_id: int,
    instructor_id: int,
) -> TaskTestCase:
    test_case = get_test_case_by_id(
        db=db,
        test_case_id=test_case_id,
    )

    get_instructor_task(
        db=db,
        task_id=test_case.task_id,
        instructor_id=instructor_id,
    )

    return test_case


def create_task_test_case(
    *,
    db: Session,
    task_id: int,
    instructor_id: int,
    test_case_data: TaskTestCaseCreate,
) -> TaskTestCase:
    get_instructor_task(
        db=db,
        task_id=task_id,
        instructor_id=instructor_id,
    )

    test_case = TaskTestCase(
        task_id=task_id,
        name=test_case_data.name,
        standard_input=test_case_data.standard_input,
        expected_output=test_case_data.expected_output,
        is_hidden=test_case_data.is_hidden,
        display_order=test_case_data.display_order,
    )

    db.add(test_case)

    return commit_and_refresh(
        db=db,
        instance=test_case,
    )


def list_instructor_test_cases(
    *,
    db: Session,
    task_id: int,
    instructor_id: int,
) -> list[TaskTestCase]:
    get_instructor_task(
        db=db,
        task_id=task_id,
        instructor_id=instructor_id,
    )

    return (
        db.query(TaskTestCase)
        .filter(TaskTestCase.task_id == task_id)
        .order_by(
            TaskTestCase.display_order.asc(),
            TaskTestCase.test_case_id.asc(),
        )
        .all()
    )


def update_task_test_case(
    *,
    db: Session,
    test_case_id: int,
    instructor_id: int,
    test_case_data: TaskTestCaseUpdate,
) -> TaskTestCase:
    test_case = get_instructor_test_case(
        db=db,
        test_case_id=test_case_id,
        instructor_id=instructor_id,
    )

    update_data = test_case_data.model_dump(
        exclude_unset=True,
    )

    if not update_data:
        raise TaskUpdateEmptyError("No test-case fields were provided for update.")

    for field_name, value in update_data.items():
        setattr(
            test_case,
            field_name,
            value,
        )

    return commit_and_refresh(
        db=db,
        instance=test_case,
    )


def delete_task_test_case(
    *,
    db: Session,
    test_case_id: int,
    instructor_id: int,
) -> int:
    test_case = get_instructor_test_case(
        db=db,
        test_case_id=test_case_id,
        instructor_id=instructor_id,
    )

    deleted_test_case_id = test_case.test_case_id

    try:
        db.delete(test_case)
        db.commit()

        return deleted_test_case_id
    except Exception:
        db.rollback()
        raise


def get_student_task_query(
    *,
    db: Session,
    student_id: int,
):
    return (
        db.query(Task)
        .join(
            Classroom,
            Classroom.class_id == Task.class_id,
        )
        .join(
            Enrollment,
            Enrollment.class_id == Classroom.class_id,
        )
        .filter(
            Enrollment.student_id == student_id,
            Enrollment.status == "active",
            Classroom.is_active.is_(True),
            Task.is_published.is_(True),
        )
    )


def list_student_tasks(
    *,
    db: Session,
    student_id: int,
    class_id: int | None = None,
    activity_type: str | None = None,
) -> list[Task]:
    query = get_student_task_query(
        db=db,
        student_id=student_id,
    )

    if class_id is not None:
        query = query.filter(Task.class_id == class_id)

    if activity_type is not None:
        query = query.filter(Task.activity_type == activity_type)

    return query.order_by(
        Task.due_at.is_(None),
        Task.due_at.asc(),
        Task.created_at.desc(),
    ).all()


def get_student_task(
    *,
    db: Session,
    task_id: int,
    student_id: int,
) -> Task:
    task = (
        get_student_task_query(
            db=db,
            student_id=student_id,
        )
        .filter(Task.task_id == task_id)
        .first()
    )

    if task is None:
        raise StudentTaskUnavailableError("Activity not found or unavailable.")

    return task


def list_student_sample_test_cases(
    *,
    db: Session,
    task_id: int,
    student_id: int,
) -> list[TaskTestCase]:
    get_student_task(
        db=db,
        task_id=task_id,
        student_id=student_id,
    )

    return (
        db.query(TaskTestCase)
        .filter(
            TaskTestCase.task_id == task_id,
            TaskTestCase.is_hidden.is_(False),
        )
        .order_by(
            TaskTestCase.display_order.asc(),
            TaskTestCase.test_case_id.asc(),
        )
        .all()
    )


# SECURITY BOUNDARY:
# instructor_id and student_id always come from authenticated users.
# Clients cannot create tasks or test cases on behalf of another account.

# TEST-CASE PRIVACY BOUNDARY:
# Instructors may access all test cases for their own tasks.
# Student-facing queries return only records where is_hidden is false.
# Hidden inputs and expected outputs must never reach student APIs.

# PUBLICATION BOUNDARY:
# Published tasks require an active instructor-owned classroom and a future
# deadline when a deadline is configured. Draft tasks may be prepared before
# all publication requirements are satisfied.

# REVIEW BOUNDARY:
# Task test cases support execution review but do not independently assign
# an official grade. Official grades remain instructor-controlled.
