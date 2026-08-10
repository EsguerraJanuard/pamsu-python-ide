from datetime import datetime, timezone
from typing import Any, TypeVar
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.domain_models import (
    Classroom,
    Enrollment,
    Task,
    TaskTestCase,
    Submission,
    InstructorGrade,
)
from app.schemas.task_schema import (
    TaskCreate,
    TaskUpdate,
)
from app.schemas.task_test_case_schema import (
    TaskTestCaseCreate,
    TaskTestCaseUpdate,
)
from app.services.academic_event_service import (
    AcademicEventWorkflowError,
    notify_activity_published,
)
from app.services.audit_service import (
    AuditServiceError,
    create_audit_record,
)
from app.services.notification_service import (
    NotificationServiceError,
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


class TaskNotificationWorkflowError(
    TaskServiceError,
):
    """
    Raised when publication succeeds but its in-app notification
    workflow cannot be completed.
    """


class TaskAuditWorkflowError(
    TaskServiceError,
):
    """
    Raised when an activity action and its required audit record
    cannot be saved as one accountable transaction.
    """


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


def build_task_audit_key(
    *,
    action_type: str,
    task_id: int,
    repeatable: bool,
) -> str:
    base_key = f"audit:{action_type}:task:{task_id}"

    if not repeatable:
        return base_key

    return f"{base_key}:{uuid4()}"


def record_task_audit(
    *,
    db: Session,
    audit_key: str,
    actor_user_id: int,
    action_type: str,
    task_id: int,
    audit_data: dict[str, Any],
    occurred_at: datetime,
) -> None:
    create_audit_record(
        db,
        {
            "audit_key": audit_key,
            "actor_user_id": actor_user_id,
            "action_type": action_type,
            "resource_type": "task",
            "resource_id": str(task_id),
            "outcome": "succeeded",
            "audit_data": audit_data,
            "occurred_at": occurred_at,
        },
        commit=False,
    )


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

    occurred_at = get_utc_now()

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

    try:
        db.add(task)
        db.flush()

        record_task_audit(
            db=db,
            audit_key=build_task_audit_key(
                action_type="activity_created",
                task_id=task.task_id,
                repeatable=False,
            ),
            actor_user_id=instructor_id,
            action_type="activity_created",
            task_id=task.task_id,
            audit_data={
                "class_id": task.class_id,
                "activity_type": task.activity_type,
                "is_graded": bool(task.is_graded),
                "is_published": False,
                "paste_policy": task.paste_policy,
            },
            occurred_at=occurred_at,
        )

        db.commit()
        db.refresh(task)

        return task
    except AuditServiceError as error:
        db.rollback()

        raise TaskAuditWorkflowError(
            "The activity could not be created because its required "
            "accountability record could not be saved. Please try "
            "again."
        ) from error
    except Exception:
        db.rollback()
        raise


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

    tasks = query.order_by(
        Task.created_at.desc(),
        Task.task_id.desc(),
    ).all()

    if class_id is not None and tasks:
        from sqlalchemy import func

        student_count = db.query(Enrollment).filter(
            Enrollment.class_id == class_id,
            Enrollment.status == "active",
        ).count()

        task_ids = [t.task_id for t in tasks]

        submitted_counts = db.query(
            Submission.task_id,
            func.count(func.distinct(Submission.student_id))
        ).filter(
            Submission.task_id.in_(task_ids),
            Submission.is_official.is_(True)
        ).group_by(Submission.task_id).all()
        submitted_map = {row[0]: row[1] for row in submitted_counts}

        graded_counts = db.query(
            Submission.task_id,
            func.count(func.distinct(Submission.student_id))
        ).join(
            InstructorGrade, InstructorGrade.submission_id == Submission.sub_id
        ).filter(
            Submission.task_id.in_(task_ids),
            Submission.is_official.is_(True)
        ).group_by(Submission.task_id).all()
        graded_map = {row[0]: row[1] for row in graded_counts}

        for task in tasks:
            t_id = task.task_id
            turned_in = submitted_map.get(t_id, 0)
            graded = graded_map.get(t_id, 0)
            
            # Use setattr so Pydantic from_attributes works
            setattr(task, "assigned_count", max(0, student_count - turned_in))
            setattr(task, "turned_in_count", turned_in)
            setattr(task, "graded_count", graded)

    return tasks


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

    changed_fields = sorted(
        field_name
        for field_name, value in update_data.items()
        if getattr(task, field_name) != value
    )

    if not changed_fields:
        return task

    for field_name, value in update_data.items():
        setattr(
            task,
            field_name,
            value,
        )

    occurred_at = get_utc_now()

    try:
        db.flush()

        record_task_audit(
            db=db,
            audit_key=build_task_audit_key(
                action_type="activity_updated",
                task_id=task.task_id,
                repeatable=True,
            ),
            actor_user_id=instructor_id,
            action_type="activity_updated",
            task_id=task.task_id,
            audit_data={
                "class_id": task.class_id,
                "changed_fields": changed_fields,
                "is_published": bool(task.is_published),
            },
            occurred_at=occurred_at,
        )

        db.commit()
        db.refresh(task)

        return task
    except AuditServiceError as error:
        db.rollback()

        raise TaskAuditWorkflowError(
            "The activity could not be updated because its required "
            "accountability record could not be saved. Please try "
            "again."
        ) from error
    except Exception:
        db.rollback()
        raise


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

    was_published = bool(task.is_published)
    state_changed = was_published != is_published

    if is_published:
        validate_task_for_publication(
            db=db,
            class_id=task.class_id,
            instructor_id=instructor_id,
            due_at=task.due_at,
        )

    if state_changed:
        occurred_at = get_utc_now()

        if is_published:
            task.is_published = True
            task.published_at = occurred_at
            action_type = "activity_published"
        else:
            task.is_published = False
            task.published_at = None
            action_type = "activity_unpublished"

        try:
            db.flush()

            record_task_audit(
                db=db,
                audit_key=build_task_audit_key(
                    action_type=action_type,
                    task_id=task.task_id,
                    repeatable=True,
                ),
                actor_user_id=instructor_id,
                action_type=action_type,
                task_id=task.task_id,
                audit_data={
                    "class_id": task.class_id,
                    "previous_state": ("published" if was_published else "draft"),
                    "new_state": ("published" if is_published else "draft"),
                },
                occurred_at=occurred_at,
            )

            db.commit()
            db.refresh(task)
        except AuditServiceError as error:
            db.rollback()

            raise TaskAuditWorkflowError(
                "The activity publication state could not be changed "
                "because its required accountability record could "
                "not be saved. Please try again."
            ) from error
        except Exception:
            db.rollback()
            raise

    if is_published:
        try:
            notify_activity_published(
                db,
                actor_instructor_id=instructor_id,
                task_id=task.task_id,
            )
        except (
            AcademicEventWorkflowError,
            NotificationServiceError,
        ) as error:
            raise TaskNotificationWorkflowError(
                "The activity was published, but its in-app "
                "notification workflow could not be completed. "
                "Publishing the activity again will safely retry "
                "notification creation."
            ) from error

        db.refresh(task)

    return task


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

# NOTIFICATION WORKFLOW BOUNDARY:
# Successful publication triggers the approved activity-published
# in-app notification workflow. Repeated publication requests safely
# reuse the same backend-generated academic event key. Notification
# content excludes starter code, instructions, test cases, AST rules,
# analytics, execution output, and unreleased grades.

# AUDIT WORKFLOW BOUNDARY:
# Activity creation, meaningful activity updates, publication, and
# unpublication create immutable audit records. Activity and audit
# changes are committed together. Repeated no-op publication requests
# do not create misleading duplicate audit rows but may safely retry
# a previously incomplete notification workflow.

# AUDIT PRIVACY BOUNDARY:
# Activity audit metadata contains only approved identifiers, changed
# field names, activity classification, paste-policy classification,
# and publication-state transitions. It excludes titles, descriptions,
# instructions, starter code, AST rules, test cases, source code,
# execution output, analytics details, grades, feedback, clipboard or
# paste contents, surveillance data, and misconduct conclusions.

# REVIEW BOUNDARY:
# Task test cases support execution review but do not independently assign
# an official grade. Official grades remain instructor-controlled.
