from typing import Any

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.core.pagination import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    PaginationBounds,
    PaginationError,
    PaginationRequest,
    SortConfigurationError,
    build_pagination_metadata,
    normalize_sort_direction,
    validate_pagination,
)
from app.models.domain_models import (
    Classroom,
    InstructorGrade,
    Submission,
    Task,
    User,
)
from app.schemas.review_queue_schema import (
    MAX_PAGE_SIZE,
    MIN_PAGE_SIZE,
    ReviewQueueSortField,
    SortDirection,
)
from app.schemas.submission_schema import SubmissionStatus


REVIEW_QUEUE_PAGINATION_BOUNDS = PaginationBounds(
    minimum_page=1,
    minimum_page_size=MIN_PAGE_SIZE,
    maximum_page_size=MAX_PAGE_SIZE,
)

APPROVED_REVIEW_QUEUE_SORT_FIELDS = {
    "submitted_at",
    "accepted_at",
    "student_name",
    "attempt_number",
}


class ReviewQueueServiceError(Exception):
    """Base exception for instructor review-queue operations."""


class ReviewQueueClassNotFoundError(
    ReviewQueueServiceError,
):
    """Raised when a selected classroom does not exist."""


class ReviewQueueTaskNotFoundError(
    ReviewQueueServiceError,
):
    """Raised when a selected activity does not exist."""


class ReviewQueueAccessDeniedError(
    ReviewQueueServiceError,
):
    """Raised when an instructor does not own a selected resource."""


class ReviewQueueFilterConflictError(
    ReviewQueueServiceError,
):
    """Raised when supplied filters refer to unrelated resources."""


class ReviewQueuePaginationError(
    ReviewQueueServiceError,
):
    """Raised when pagination or ordering values are invalid."""


def _build_pagination_request(
    *,
    page: int,
    page_size: int,
) -> PaginationRequest:
    try:
        return validate_pagination(
            page=page,
            page_size=page_size,
            bounds=REVIEW_QUEUE_PAGINATION_BOUNDS,
        )
    except PaginationError as error:
        raise ReviewQueuePaginationError(str(error)) from error


def _validate_pagination(
    *,
    page: int,
    page_size: int,
) -> None:
    """
    Preserve the existing private service boundary while delegating
    validation to the common pagination utility.
    """

    _build_pagination_request(
        page=page,
        page_size=page_size,
    )


def _get_owned_classroom(
    db: Session,
    *,
    instructor_id: int,
    class_id: int,
) -> Classroom:
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.class_id == class_id,
        )
        .first()
    )

    if classroom is None:
        raise ReviewQueueClassNotFoundError("Classroom not found.")

    if classroom.instructor_id != instructor_id:
        raise ReviewQueueAccessDeniedError(
            "You can only access review queues for classrooms that you own."
        )

    return classroom


def _get_owned_task(
    db: Session,
    *,
    instructor_id: int,
    task_id: int,
) -> Task:
    task = (
        db.query(Task)
        .filter(
            Task.task_id == task_id,
        )
        .first()
    )

    if task is None:
        raise ReviewQueueTaskNotFoundError("Activity not found.")

    if task.instructor_id != instructor_id:
        raise ReviewQueueAccessDeniedError(
            "You can only access review queues for activities that you own."
        )

    if task.class_id is None:
        raise ReviewQueueFilterConflictError(
            "The activity is not assigned to a classroom."
        )

    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.class_id == task.class_id,
        )
        .first()
    )

    if classroom is None or classroom.instructor_id != instructor_id:
        raise ReviewQueueAccessDeniedError(
            "The activity is not assigned to a classroom that you own."
        )

    return task


def _validate_owned_filters(
    db: Session,
    *,
    instructor_id: int,
    class_id: int | None,
    task_id: int | None,
) -> None:
    classroom: Classroom | None = None
    task: Task | None = None

    if class_id is not None:
        classroom = _get_owned_classroom(
            db,
            instructor_id=instructor_id,
            class_id=class_id,
        )

    if task_id is not None:
        task = _get_owned_task(
            db,
            instructor_id=instructor_id,
            task_id=task_id,
        )

    if (
        classroom is not None
        and task is not None
        and task.class_id != classroom.class_id
    ):
        raise ReviewQueueFilterConflictError(
            "The selected activity does not belong to the selected classroom."
        )


def _apply_review_queue_filters(
    query: Any,
    *,
    class_id: int | None,
    task_id: int | None,
    student_id: int | None,
    submission_status: SubmissionStatus | None,
    official: bool | None,
    grade_released: bool | None,
) -> Any:
    if class_id is not None:
        query = query.filter(
            Classroom.class_id == class_id,
        )

    if task_id is not None:
        query = query.filter(
            Task.task_id == task_id,
        )

    if student_id is not None:
        query = query.filter(
            Submission.student_id == student_id,
        )

    if submission_status is not None:
        query = query.filter(
            Submission.status == submission_status,
        )

    if official is not None:
        query = query.filter(
            Submission.is_official.is_(official),
        )

    if grade_released is True:
        query = query.filter(
            InstructorGrade.grade_id.is_not(None),
            InstructorGrade.is_released.is_(True),
        )

    if grade_released is False:
        query = query.filter(
            InstructorGrade.grade_id.is_not(None),
            InstructorGrade.is_released.is_(False),
        )

    return query


def _build_authorized_item_query(
    db: Session,
    *,
    instructor_id: int,
) -> Any:
    return (
        db.query(
            Submission.sub_id.label("sub_id"),
            Submission.student_id.label("student_id"),
            Submission.attempt_number.label("attempt_number"),
            Submission.status.label("submission_status"),
            Submission.is_official.label("is_official"),
            Submission.submitted_at.label("submitted_at"),
            Submission.accepted_at.label("accepted_at"),
            User.name.label("student_name"),
            User.school_id.label("student_school_id"),
            Task.task_id.label("task_id"),
            Task.title.label("task_title"),
            Task.activity_type.label("activity_type"),
            Classroom.class_id.label("class_id"),
            Classroom.name.label("class_name"),
            Classroom.subject_code.label("subject_code"),
            Classroom.section.label("section"),
            InstructorGrade.grade_id.label("grade_id"),
            InstructorGrade.is_released.label("grade_is_released"),
        )
        .join(
            User,
            Submission.student_id == User.user_id,
        )
        .join(
            Task,
            Submission.task_id == Task.task_id,
        )
        .join(
            Classroom,
            Task.class_id == Classroom.class_id,
        )
        .outerjoin(
            InstructorGrade,
            InstructorGrade.submission_id == Submission.sub_id,
        )
        .filter(
            Task.instructor_id == instructor_id,
            Classroom.instructor_id == instructor_id,
            User.role == "student",
        )
    )


def _build_authorized_count_query(
    db: Session,
    *,
    instructor_id: int,
) -> Any:
    return (
        db.query(
            func.count(Submission.sub_id).label("total"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            Submission.status == "submitted",
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("submitted"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            Submission.status == "awaiting_review",
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("awaiting_review"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            Submission.status == "graded",
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("graded"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            Submission.status == "rejected",
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("rejected"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            Submission.is_official.is_(True),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("official"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            Submission.is_official.is_(False),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("unofficial"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            and_(
                                InstructorGrade.grade_id.is_not(None),
                                InstructorGrade.is_released.is_(False),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("unreleased_grades"),
        )
        .join(
            User,
            Submission.student_id == User.user_id,
        )
        .join(
            Task,
            Submission.task_id == Task.task_id,
        )
        .join(
            Classroom,
            Task.class_id == Classroom.class_id,
        )
        .outerjoin(
            InstructorGrade,
            InstructorGrade.submission_id == Submission.sub_id,
        )
        .filter(
            Task.instructor_id == instructor_id,
            Classroom.instructor_id == instructor_id,
            User.role == "student",
        )
    )


def _apply_review_queue_ordering(
    query: Any,
    *,
    sort_by: ReviewQueueSortField,
    sort_direction: SortDirection,
) -> Any:
    if sort_by not in APPROVED_REVIEW_QUEUE_SORT_FIELDS:
        raise ReviewQueuePaginationError("Unsupported review-queue sort field.")

    try:
        normalized_direction = normalize_sort_direction(sort_direction)
    except SortConfigurationError as error:
        raise ReviewQueuePaginationError(str(error)) from error

    def apply_direction(
        column: Any,
    ) -> Any:
        if normalized_direction == "asc":
            return column.asc()

        return column.desc()

    if sort_by == "accepted_at":
        null_rank = case(
            (
                Submission.accepted_at.is_(None),
                1,
            ),
            else_=0,
        )

        return query.order_by(
            null_rank.asc(),
            apply_direction(Submission.accepted_at),
            Submission.sub_id.desc(),
        )

    if sort_by == "student_name":
        return query.order_by(
            apply_direction(func.lower(User.name)),
            apply_direction(User.school_id),
            Submission.sub_id.desc(),
        )

    if sort_by == "attempt_number":
        return query.order_by(
            apply_direction(Submission.attempt_number),
            Submission.sub_id.desc(),
        )

    return query.order_by(
        apply_direction(Submission.submitted_at),
        Submission.sub_id.desc(),
    )


def _build_review_queue_item(
    row: Any,
) -> dict[str, Any]:
    has_manual_grade = row.grade_id is not None

    grade_is_released = bool(row.grade_is_released) if has_manual_grade else False

    return {
        "sub_id": row.sub_id,
        "student": {
            "student_id": row.student_id,
            "name": row.student_name,
            "school_id": (row.student_school_id),
        },
        "activity": {
            "task_id": row.task_id,
            "title": row.task_title,
            "activity_type": (row.activity_type),
            "class_id": row.class_id,
            "class_name": row.class_name,
            "subject_code": (row.subject_code),
            "section": row.section,
        },
        "attempt_number": (row.attempt_number),
        "status": row.submission_status,
        "is_official": (row.is_official),
        "submitted_at": (row.submitted_at),
        "accepted_at": (row.accepted_at),
        "has_manual_grade": (has_manual_grade),
        "grade_is_released": (grade_is_released),
    }


def list_instructor_review_queue(
    db: Session,
    *,
    instructor_id: int,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    class_id: int | None = None,
    task_id: int | None = None,
    student_id: int | None = None,
    submission_status: SubmissionStatus | None = None,
    official: bool | None = None,
    grade_released: bool | None = None,
    sort_by: ReviewQueueSortField = ("submitted_at"),
    sort_direction: SortDirection = "desc",
) -> dict[str, Any]:
    """
    Return a paginated instructor-owned review queue.

    The query selects summary columns only. Raw source code, standard
    input, AST findings, similarity details, execution output, hidden
    test-case data, and session telemetry are not loaded or returned.
    """

    pagination = _build_pagination_request(
        page=page,
        page_size=page_size,
    )

    _validate_owned_filters(
        db,
        instructor_id=instructor_id,
        class_id=class_id,
        task_id=task_id,
    )

    item_query = _build_authorized_item_query(
        db,
        instructor_id=instructor_id,
    )

    item_query = _apply_review_queue_filters(
        item_query,
        class_id=class_id,
        task_id=task_id,
        student_id=student_id,
        submission_status=(submission_status),
        official=official,
        grade_released=(grade_released),
    )

    total_items = int(item_query.order_by(None).count())

    count_query = _build_authorized_count_query(
        db,
        instructor_id=instructor_id,
    )

    count_query = _apply_review_queue_filters(
        count_query,
        class_id=class_id,
        task_id=task_id,
        student_id=student_id,
        submission_status=(submission_status),
        official=official,
        grade_released=(grade_released),
    )

    count_row = count_query.one()

    ordered_query = _apply_review_queue_ordering(
        item_query,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )

    rows = ordered_query.offset(pagination.offset).limit(pagination.page_size).all()

    metadata = build_pagination_metadata(
        pagination=pagination,
        total_items=total_items,
    )

    return {
        "items": [_build_review_queue_item(row) for row in rows],
        "page": metadata.page,
        "page_size": metadata.page_size,
        "total_items": metadata.total_items,
        "total_pages": metadata.total_pages,
        "sort_by": sort_by,
        "sort_direction": sort_direction,
        "counts": {
            "total": int(count_row.total or 0),
            "submitted": int(count_row.submitted or 0),
            "awaiting_review": int(count_row.awaiting_review or 0),
            "graded": int(count_row.graded or 0),
            "rejected": int(count_row.rejected or 0),
            "official": int(count_row.official or 0),
            "unofficial": int(count_row.unofficial or 0),
            "unreleased_grades": int(count_row.unreleased_grades or 0),
        },
    }


# PAGINATION BOUNDARY:
# Review-queue pagination uses the common bounded pagination contract.
# Database offsets are derived internally rather than accepted directly.

# ORDERING BOUNDARY:
# Every review-queue ordering ends with Submission.sub_id as the stable
# unique tie-breaker. Sort fields are selected only from an approved map.

# AUTHORIZATION BOUNDARY:
# Every queue query is restricted to activities and classrooms owned by
# the authenticated instructor.

# PRIVACY BOUNDARY:
# Review-queue queries select summary columns only. They do not load or
# expose raw source code, standard input, hidden test cases, AST details,
# similarity comparison details, execution output, session telemetry,
# clipboard contents, pasted text, or surveillance data.

# REVIEW BOUNDARY:
# Queue membership and ordering use explicit academic workflow fields.
# They never use an automated plagiarism, cheating, misconduct, copying,
# behavioral-risk, or similarity-risk score.
