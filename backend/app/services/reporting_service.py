import csv
from datetime import datetime, timezone
from io import StringIO
from typing import Any

from sqlalchemy import and_, case, exists, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.pagination import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE as GLOBAL_MAX_PAGE_SIZE,
    MIN_PAGE_SIZE as GLOBAL_MIN_PAGE_SIZE,
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
    Enrollment,
    InstructorGrade,
    Submission,
    Task,
    User,
)
from app.schemas.reporting_schema import (
    MissingSubmissionSortField,
    ReportingSortDirection,
)


MIN_REPORT_PAGE_SIZE = GLOBAL_MIN_PAGE_SIZE
MAX_REPORT_PAGE_SIZE = GLOBAL_MAX_PAGE_SIZE

REPORTING_PAGINATION_BOUNDS = PaginationBounds(
    minimum_page=1,
    minimum_page_size=MIN_REPORT_PAGE_SIZE,
    maximum_page_size=MAX_REPORT_PAGE_SIZE,
)

APPROVED_MISSING_SUBMISSION_SORT_FIELDS = {
    "student_name",
    "school_id",
    "activity_title",
    "due_at",
}

CSV_MEDIA_TYPE = "text/csv; charset=utf-8"

GRADE_DISTRIBUTION_BANDS = (
    (
        "0-59.99",
        0.0,
        59.99,
    ),
    (
        "60-69.99",
        60.0,
        69.99,
    ),
    (
        "70-79.99",
        70.0,
        79.99,
    ),
    (
        "80-89.99",
        80.0,
        89.99,
    ),
    (
        "90-100",
        90.0,
        100.0,
    ),
)


class ReportingServiceError(Exception):
    """Base exception for reporting and export operations."""


class ReportingClassroomNotFoundError(
    ReportingServiceError,
):
    """Raised when a selected classroom does not exist."""


class ReportingTaskNotFoundError(
    ReportingServiceError,
):
    """Raised when a selected activity does not exist."""


class ReportingAccessDeniedError(
    ReportingServiceError,
):
    """Raised when an instructor does not own a selected resource."""


class ReportingFilterConflictError(
    ReportingServiceError,
):
    """Raised when report filters describe an invalid hierarchy."""


class ReportingTaskUnavailableError(
    ReportingServiceError,
):
    """Raised when an activity cannot participate in completion reports."""


class ReportingPaginationError(
    ReportingServiceError,
):
    """Raised when report pagination or sorting is invalid."""


class ReportingExportError(
    ReportingServiceError,
):
    """Raised when a privacy-safe CSV export cannot be generated."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _round_percentage(
    value: float,
) -> float:
    return round(
        value,
        2,
    )


def _calculate_percentage(
    *,
    numerator: int,
    denominator: int,
) -> float:
    if denominator <= 0:
        return 0.0

    return _round_percentage(
        numerator * 100.0 / denominator,
    )


def _build_pagination_request(
    *,
    page: int,
    page_size: int,
) -> PaginationRequest:
    try:
        return validate_pagination(
            page=page,
            page_size=page_size,
            bounds=REPORTING_PAGINATION_BOUNDS,
        )
    except PaginationError as error:
        raise ReportingPaginationError(
            str(error)
        ) from error


def _validate_pagination(
    *,
    page: int,
    page_size: int,
) -> None:
    """
    Preserve the existing private validation boundary while delegating
    validation to the shared pagination utility.
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
        raise ReportingClassroomNotFoundError(
            "Classroom not found."
        )

    if classroom.instructor_id != instructor_id:
        raise ReportingAccessDeniedError(
            "You can only access reports "
            "for classrooms that you own."
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
        raise ReportingTaskNotFoundError(
            "Activity not found."
        )

    if task.instructor_id != instructor_id:
        raise ReportingAccessDeniedError(
            "You can only access reports "
            "for activities that you own."
        )

    if task.class_id is None:
        raise ReportingFilterConflictError(
            "The activity is not assigned to a classroom."
        )

    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.class_id == task.class_id,
        )
        .first()
    )

    if (
        classroom is None
        or classroom.instructor_id != instructor_id
    ):
        raise ReportingAccessDeniedError(
            "The activity is not assigned to "
            "a classroom that you own."
        )

    return task


def _validate_owned_filters(
    db: Session,
    *,
    instructor_id: int,
    class_id: int | None,
    task_id: int | None,
) -> tuple[
    Classroom | None,
    Task | None,
]:
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
        raise ReportingFilterConflictError(
            "The selected activity does not belong "
            "to the selected classroom."
        )

    return classroom, task


def _build_classroom_summary(
    classroom: Classroom,
) -> dict[str, Any]:
    return {
        "class_id": classroom.class_id,
        "name": classroom.name,
        "subject_code": classroom.subject_code,
        "section": classroom.section,
    }


def _build_activity_summary(
    task: Task,
) -> dict[str, Any]:
    if task.class_id is None:
        raise ReportingFilterConflictError(
            "The activity is not assigned to a classroom."
        )

    return {
        "task_id": task.task_id,
        "title": task.title,
        "activity_type": task.activity_type,
        "class_id": task.class_id,
        "is_graded": bool(task.is_graded),
        "is_published": bool(task.is_published),
        "due_at": task.due_at,
    }


def _active_student_rows(
    db: Session,
    *,
    class_id: int,
) -> list[Any]:
    return (
        db.query(
            User.user_id.label(
                "student_id"
            ),
            User.name.label(
                "student_name"
            ),
            User.school_id.label(
                "school_id"
            ),
        )
        .join(
            Enrollment,
            Enrollment.student_id
            == User.user_id,
        )
        .filter(
            Enrollment.class_id == class_id,
            Enrollment.status == "active",
            User.role == "student",
            User.is_active.is_(True),
            User.email_verified.is_(True),
        )
        .order_by(
            func.lower(
                User.name
            ).asc(),
            User.school_id.asc(),
            User.user_id.asc(),
        )
        .all()
    )


def _published_graded_tasks(
    db: Session,
    *,
    class_id: int,
) -> list[Task]:
    return (
        db.query(Task)
        .filter(
            Task.class_id == class_id,
            Task.is_published.is_(True),
            Task.is_graded.is_(True),
        )
        .order_by(
            Task.due_at.is_(None),
            Task.due_at.asc(),
            func.lower(
                Task.title
            ).asc(),
            Task.task_id.asc(),
        )
        .all()
    )


def _build_completion_counts(
    *,
    expected_count: int,
    submitted_count: int,
    manually_graded_count: int,
    released_grade_count: int,
) -> dict[str, Any]:
    missing_count = max(
        expected_count - submitted_count,
        0,
    )

    return {
        "expected_count": expected_count,
        "submitted_count": submitted_count,
        "missing_count": missing_count,
        "manually_graded_count": manually_graded_count,
        "released_grade_count": released_grade_count,
        "completion_percentage": _calculate_percentage(
            numerator=submitted_count,
            denominator=expected_count,
        ),
    }


def _load_completion_statistics(
    db: Session,
    *,
    task_ids: list[int],
    student_ids: list[int],
) -> dict[
    int,
    dict[str, int],
]:
    statistics = {
        task_id: {
            "submitted_count": 0,
            "manually_graded_count": 0,
            "released_grade_count": 0,
        }
        for task_id in task_ids
    }

    if not task_ids or not student_ids:
        return statistics

    rows = (
        db.query(
            Submission.task_id.label(
                "task_id"
            ),
            Submission.student_id.label(
                "student_id"
            ),
            Submission.attempt_number.label(
                "attempt_number"
            ),
            InstructorGrade.grade_id.label(
                "grade_id"
            ),
            InstructorGrade.is_released.label(
                "is_released"
            ),
        )
        .outerjoin(
            InstructorGrade,
            InstructorGrade.submission_id
            == Submission.sub_id,
        )
        .filter(
            Submission.task_id.in_(
                task_ids
            ),
            Submission.student_id.in_(
                student_ids
            ),
            Submission.is_official.is_(True),
        )
        .order_by(
            Submission.task_id.asc(),
            Submission.student_id.asc(),
            Submission.attempt_number.desc(),
            Submission.sub_id.desc(),
        )
        .all()
    )

    seen_pairs: set[
        tuple[int, int]
    ] = set()

    for row in rows:
        pair = (
            int(row.task_id),
            int(row.student_id),
        )

        if pair in seen_pairs:
            continue

        seen_pairs.add(
            pair
        )

        task_statistics = statistics[
            int(row.task_id)
        ]

        task_statistics[
            "submitted_count"
        ] += 1

        if row.grade_id is not None:
            task_statistics[
                "manually_graded_count"
            ] += 1

            if bool(row.is_released):
                task_statistics[
                    "released_grade_count"
                ] += 1

    return statistics


def get_activity_completion_summary(
    db: Session,
    *,
    instructor_id: int,
    task_id: int,
) -> dict[str, Any]:
    task = _get_owned_task(
        db,
        instructor_id=instructor_id,
        task_id=task_id,
    )

    if not task.is_published or not task.is_graded:
        raise ReportingTaskUnavailableError(
            "Completion reports require "
            "a published graded activity."
        )

    if task.class_id is None:
        raise ReportingFilterConflictError(
            "The activity is not assigned to a classroom."
        )

    student_rows = _active_student_rows(
        db,
        class_id=task.class_id,
    )

    student_ids = [
        int(row.student_id)
        for row in student_rows
    ]

    statistics = _load_completion_statistics(
        db,
        task_ids=[
            task.task_id,
        ],
        student_ids=student_ids,
    )[task.task_id]

    return {
        "activity": _build_activity_summary(
            task,
        ),
        "active_student_count": len(
            student_ids
        ),
        "completion": _build_completion_counts(
            expected_count=len(
                student_ids
            ),
            submitted_count=statistics[
                "submitted_count"
            ],
            manually_graded_count=statistics[
                "manually_graded_count"
            ],
            released_grade_count=statistics[
                "released_grade_count"
            ],
        ),
        "generated_at": _utc_now(),
    }


def get_classroom_completion_summary(
    db: Session,
    *,
    instructor_id: int,
    class_id: int,
) -> dict[str, Any]:
    classroom = _get_owned_classroom(
        db,
        instructor_id=instructor_id,
        class_id=class_id,
    )

    student_rows = _active_student_rows(
        db,
        class_id=classroom.class_id,
    )

    tasks = _published_graded_tasks(
        db,
        class_id=classroom.class_id,
    )

    student_ids = [
        int(row.student_id)
        for row in student_rows
    ]

    task_ids = [
        task.task_id
        for task in tasks
    ]

    statistics = _load_completion_statistics(
        db,
        task_ids=task_ids,
        student_ids=student_ids,
    )

    active_student_count = len(
        student_ids
    )

    activity_items = []
    total_submitted = 0
    total_manually_graded = 0
    total_released = 0

    for task in tasks:
        task_statistics = statistics[
            task.task_id
        ]

        completion = _build_completion_counts(
            expected_count=active_student_count,
            submitted_count=task_statistics[
                "submitted_count"
            ],
            manually_graded_count=task_statistics[
                "manually_graded_count"
            ],
            released_grade_count=task_statistics[
                "released_grade_count"
            ],
        )

        total_submitted += completion[
            "submitted_count"
        ]

        total_manually_graded += completion[
            "manually_graded_count"
        ]

        total_released += completion[
            "released_grade_count"
        ]

        activity_items.append(
            {
                "activity": (
                    _build_activity_summary(
                        task
                    )
                ),
                "completion": completion,
            }
        )

    expected_count = (
        active_student_count
        * len(tasks)
    )

    return {
        "classroom": _build_classroom_summary(
            classroom,
        ),
        "active_student_count": (
            active_student_count
        ),
        "published_graded_activity_count": len(
            tasks
        ),
        "completion": _build_completion_counts(
            expected_count=expected_count,
            submitted_count=total_submitted,
            manually_graded_count=(
                total_manually_graded
            ),
            released_grade_count=total_released,
        ),
        "activities": activity_items,
        "generated_at": _utc_now(),
    }


def _grade_percentage_expression() -> Any:
    return (
        InstructorGrade.score
        * 100.0
        / InstructorGrade.max_score
    )


def _build_grade_distribution_buckets(
    percentages: list[float],
) -> list[dict[str, Any]]:
    total = len(
        percentages
    )

    buckets = []

    for (
        band,
        minimum,
        maximum,
    ) in GRADE_DISTRIBUTION_BANDS:
        count = sum(
            1
            for percentage in percentages
            if minimum
            <= percentage
            <= maximum
        )

        buckets.append(
            {
                "band": band,
                "minimum_percentage": minimum,
                "maximum_percentage": maximum,
                "count": count,
                "percentage_of_graded": (
                    _calculate_percentage(
                        numerator=count,
                        denominator=total,
                    )
                ),
            }
        )

    return buckets


def get_grade_distribution(
    db: Session,
    *,
    instructor_id: int,
    class_id: int,
    task_id: int | None = None,
) -> dict[str, Any]:
    classroom, task = (
        _validate_owned_filters(
            db,
            instructor_id=instructor_id,
            class_id=class_id,
            task_id=task_id,
        )
    )

    if classroom is None:
        raise ReportingClassroomNotFoundError(
            "Classroom not found."
        )

    percentage_expression = (
        _grade_percentage_expression()
    )

    query = (
        db.query(
            percentage_expression.label(
                "grade_percentage"
            ),
            InstructorGrade.is_released.label(
                "is_released"
            ),
        )
        .join(
            Submission,
            Submission.sub_id
            == InstructorGrade.submission_id,
        )
        .join(
            Task,
            Task.task_id
            == Submission.task_id,
        )
        .filter(
            Task.instructor_id == instructor_id,
            Task.class_id == classroom.class_id,
            Submission.is_official.is_(True),
            InstructorGrade.max_score > 0,
        )
    )

    if task is not None:
        query = query.filter(
            Task.task_id == task.task_id,
        )

    rows = query.all()

    percentages = [
        min(
            max(
                float(
                    row.grade_percentage
                ),
                0.0,
            ),
            100.0,
        )
        for row in rows
    ]

    released_count = sum(
        1
        for row in rows
        if bool(row.is_released)
    )

    average_percentage = None
    minimum_percentage = None
    maximum_percentage = None

    if percentages:
        average_percentage = (
            _round_percentage(
                sum(percentages)
                / len(percentages)
            )
        )

        minimum_percentage = (
            _round_percentage(
                min(percentages)
            )
        )

        maximum_percentage = (
            _round_percentage(
                max(percentages)
            )
        )

    return {
        "classroom": _build_classroom_summary(
            classroom,
        ),
        "activity": (
            _build_activity_summary(
                task,
            )
            if task is not None
            else None
        ),
        "manually_graded_submission_count": len(
            percentages
        ),
        "released_grade_count": (
            released_count
        ),
        "average_percentage": (
            average_percentage
        ),
        "minimum_percentage": (
            minimum_percentage
        ),
        "maximum_percentage": (
            maximum_percentage
        ),
        "buckets": (
            _build_grade_distribution_buckets(
                percentages
            )
        ),
        "generated_at": _utc_now(),
    }


def _apply_missing_submission_ordering(
    query: Any,
    *,
    sort_by: MissingSubmissionSortField,
    sort_direction: ReportingSortDirection,
) -> Any:
    if (
        sort_by
        not in APPROVED_MISSING_SUBMISSION_SORT_FIELDS
    ):
        raise ReportingPaginationError(
            "Unsupported missing-submission sort field."
        )

    try:
        normalized_direction = (
            normalize_sort_direction(
                sort_direction
            )
        )
    except SortConfigurationError as error:
        raise ReportingPaginationError(
            str(error)
        ) from error

    def apply_direction(
        column: Any,
    ) -> Any:
        if normalized_direction == "asc":
            return column.asc()

        return column.desc()

    if sort_by == "student_name":
        return query.order_by(
            apply_direction(
                func.lower(
                    User.name
                )
            ),
            apply_direction(
                User.school_id
            ),
            Task.task_id.asc(),
            User.user_id.asc(),
        )

    if sort_by == "school_id":
        return query.order_by(
            apply_direction(
                User.school_id
            ),
            apply_direction(
                func.lower(
                    User.name
                )
            ),
            Task.task_id.asc(),
            User.user_id.asc(),
        )

    if sort_by == "activity_title":
        return query.order_by(
            apply_direction(
                func.lower(
                    Task.title
                )
            ),
            apply_direction(
                func.lower(
                    User.name
                )
            ),
            User.school_id.asc(),
            Task.task_id.asc(),
            User.user_id.asc(),
        )

    due_at_null_rank = case(
        (
            Task.due_at.is_(None),
            1,
        ),
        else_=0,
    )

    return query.order_by(
        due_at_null_rank.asc(),
        apply_direction(
            Task.due_at
        ),
        func.lower(
            User.name
        ).asc(),
        User.school_id.asc(),
        Task.task_id.asc(),
        User.user_id.asc(),
    )


def list_missing_submissions(
    db: Session,
    *,
    instructor_id: int,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    class_id: int | None = None,
    task_id: int | None = None,
    sort_by: MissingSubmissionSortField = (
        "student_name"
    ),
    sort_direction: ReportingSortDirection = (
        "asc"
    ),
) -> dict[str, Any]:
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

    official_submission_exists = (
        exists().where(
            and_(
                Submission.task_id
                == Task.task_id,
                Submission.student_id
                == User.user_id,
                Submission.is_official.is_(
                    True
                ),
            )
        )
    )

    query = (
        db.query(
            User.user_id.label(
                "student_id"
            ),
            User.name.label(
                "student_name"
            ),
            User.school_id.label(
                "school_id"
            ),
            Task.task_id.label(
                "task_id"
            ),
            Task.title.label(
                "task_title"
            ),
            Task.activity_type.label(
                "activity_type"
            ),
            Task.is_graded.label(
                "is_graded"
            ),
            Task.is_published.label(
                "is_published"
            ),
            Task.due_at.label(
                "due_at"
            ),
            Classroom.class_id.label(
                "class_id"
            ),
        )
        .select_from(
            Enrollment
        )
        .join(
            User,
            User.user_id
            == Enrollment.student_id,
        )
        .join(
            Classroom,
            Classroom.class_id
            == Enrollment.class_id,
        )
        .join(
            Task,
            Task.class_id
            == Classroom.class_id,
        )
        .filter(
            Classroom.instructor_id
            == instructor_id,
            Task.instructor_id
            == instructor_id,
            Enrollment.status == "active",
            User.role == "student",
            User.is_active.is_(True),
            User.email_verified.is_(True),
            Task.is_published.is_(True),
            Task.is_graded.is_(True),
            ~official_submission_exists,
        )
    )

    if class_id is not None:
        query = query.filter(
            Classroom.class_id == class_id,
        )

    if task_id is not None:
        query = query.filter(
            Task.task_id == task_id,
        )

    total_items = int(
        query.order_by(None).count()
    )

    ordered_query = (
        _apply_missing_submission_ordering(
            query,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
    )

    rows = (
        ordered_query
        .offset(
            pagination.offset
        )
        .limit(
            pagination.page_size
        )
        .all()
    )

    metadata = build_pagination_metadata(
        pagination=pagination,
        total_items=total_items,
    )

    items = [
        {
            "student": {
                "student_id": (
                    row.student_id
                ),
                "name": row.student_name,
                "school_id": row.school_id,
            },
            "activity": {
                "task_id": row.task_id,
                "title": row.task_title,
                "activity_type": (
                    row.activity_type
                ),
                "class_id": row.class_id,
                "is_graded": bool(
                    row.is_graded
                ),
                "is_published": bool(
                    row.is_published
                ),
                "due_at": row.due_at,
            },
            "due_at": row.due_at,
            "enrollment_status": "active",
            "submission_state": "missing",
        }
        for row in rows
    ]

    return {
        "items": items,
        "page": metadata.page,
        "page_size": metadata.page_size,
        "total_items": metadata.total_items,
        "total_pages": metadata.total_pages,
        "sort_by": sort_by,
        "sort_direction": sort_direction,
        "generated_at": _utc_now(),
    }


def get_student_progress_summary(
    db: Session,
    *,
    student_id: int,
) -> dict[str, Any]:
    classroom_rows = (
        db.query(
            Classroom.class_id.label(
                "class_id"
            ),
            Classroom.name.label(
                "class_name"
            ),
            Classroom.subject_code.label(
                "subject_code"
            ),
            Classroom.section.label(
                "section"
            ),
        )
        .join(
            Enrollment,
            Enrollment.class_id
            == Classroom.class_id,
        )
        .filter(
            Enrollment.student_id == student_id,
            Enrollment.status == "active",
            Classroom.is_active.is_(True),
        )
        .order_by(
            func.lower(
                Classroom.name
            ).asc(),
            Classroom.class_id.asc(),
        )
        .all()
    )

    class_ids = [
        int(row.class_id)
        for row in classroom_rows
    ]

    task_rows = []

    if class_ids:
        task_rows = (
            db.query(
                Task.task_id.label(
                    "task_id"
                ),
                Task.class_id.label(
                    "class_id"
                ),
            )
            .filter(
                Task.class_id.in_(
                    class_ids
                ),
                Task.is_published.is_(True),
                Task.is_graded.is_(True),
            )
            .all()
        )

    task_ids = [
        int(row.task_id)
        for row in task_rows
    ]

    submission_rows = []

    if task_ids:
        percentage_expression = (
            _grade_percentage_expression()
        )

        submission_rows = (
            db.query(
                Submission.task_id.label(
                    "task_id"
                ),
                Submission.attempt_number.label(
                    "attempt_number"
                ),
                InstructorGrade.grade_id.label(
                    "grade_id"
                ),
                InstructorGrade.is_released.label(
                    "is_released"
                ),
                percentage_expression.label(
                    "grade_percentage"
                ),
            )
            .outerjoin(
                InstructorGrade,
                InstructorGrade.submission_id
                == Submission.sub_id,
            )
            .filter(
                Submission.student_id
                == student_id,
                Submission.task_id.in_(
                    task_ids
                ),
                Submission.is_official.is_(
                    True
                ),
            )
            .order_by(
                Submission.task_id.asc(),
                Submission.attempt_number.desc(),
                Submission.sub_id.desc(),
            )
            .all()
        )

    task_to_class = {
        int(row.task_id): int(row.class_id)
        for row in task_rows
    }

    task_count_by_class = {
        class_id: 0
        for class_id in class_ids
    }

    for class_id in task_to_class.values():
        task_count_by_class[
            class_id
        ] += 1

    submitted_task_ids: set[int] = set()

    released_percentages_by_class: dict[
        int,
        list[float],
    ] = {
        class_id: []
        for class_id in class_ids
    }

    released_grade_count_by_class = {
        class_id: 0
        for class_id in class_ids
    }

    for row in submission_rows:
        task_id = int(
            row.task_id
        )

        if task_id in submitted_task_ids:
            continue

        submitted_task_ids.add(
            task_id
        )

        class_id = task_to_class[
            task_id
        ]

        if (
            row.grade_id is not None
            and bool(row.is_released)
            and row.grade_percentage is not None
        ):
            released_grade_count_by_class[
                class_id
            ] += 1

            released_percentages_by_class[
                class_id
            ].append(
                min(
                    max(
                        float(
                            row.grade_percentage
                        ),
                        0.0,
                    ),
                    100.0,
                )
            )

    submitted_count_by_class = {
        class_id: 0
        for class_id in class_ids
    }

    for task_id in submitted_task_ids:
        submitted_count_by_class[
            task_to_class[task_id]
        ] += 1

    classroom_items = []
    all_released_percentages = []

    for row in classroom_rows:
        class_id = int(
            row.class_id
        )

        expected_count = (
            task_count_by_class[
                class_id
            ]
        )

        submitted_count = (
            submitted_count_by_class[
                class_id
            ]
        )

        missing_count = max(
            expected_count
            - submitted_count,
            0,
        )

        released_percentages = (
            released_percentages_by_class[
                class_id
            ]
        )

        all_released_percentages.extend(
            released_percentages
        )

        classroom_items.append(
            {
                "classroom": {
                    "class_id": class_id,
                    "name": row.class_name,
                    "subject_code": (
                        row.subject_code
                    ),
                    "section": row.section,
                },
                "published_graded_activity_count": (
                    expected_count
                ),
                "submitted_activity_count": (
                    submitted_count
                ),
                "missing_activity_count": (
                    missing_count
                ),
                "released_grade_count": (
                    released_grade_count_by_class[
                        class_id
                    ]
                ),
                "average_released_percentage": (
                    _round_percentage(
                        sum(
                            released_percentages
                        )
                        / len(
                            released_percentages
                        )
                    )
                    if released_percentages
                    else None
                ),
                "completion_percentage": (
                    _calculate_percentage(
                        numerator=submitted_count,
                        denominator=expected_count,
                    )
                ),
            }
        )

    total_expected = sum(
        task_count_by_class.values()
    )

    total_submitted = len(
        submitted_task_ids
    )

    return {
        "student_id": student_id,
        "active_classroom_count": len(
            class_ids
        ),
        "published_graded_activity_count": (
            total_expected
        ),
        "submitted_activity_count": (
            total_submitted
        ),
        "missing_activity_count": max(
            total_expected - total_submitted,
            0,
        ),
        "released_grade_count": sum(
            released_grade_count_by_class.values()
        ),
        "average_released_percentage": (
            _round_percentage(
                sum(
                    all_released_percentages
                )
                / len(
                    all_released_percentages
                )
            )
            if all_released_percentages
            else None
        ),
        "completion_percentage": (
            _calculate_percentage(
                numerator=total_submitted,
                denominator=total_expected,
            )
        ),
        "classrooms": classroom_items,
        "generated_at": _utc_now(),
    }


def _sanitize_csv_cell(
    value: Any,
) -> Any:
    if value is None:
        return ""

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    if isinstance(
        value,
        bool,
    ):
        return (
            "true"
            if value
            else "false"
        )

    if not isinstance(
        value,
        str,
    ):
        return value

    if value and value[0] in (
        "=",
        "+",
        "-",
        "@",
    ):
        return "'" + value

    return value


def build_gradebook_csv_export(
    db: Session,
    *,
    instructor_id: int,
    class_id: int,
    task_id: int | None = None,
) -> dict[str, Any]:
    classroom, task = (
        _validate_owned_filters(
            db,
            instructor_id=instructor_id,
            class_id=class_id,
            task_id=task_id,
        )
    )

    if classroom is None:
        raise ReportingClassroomNotFoundError(
            "Classroom not found."
        )

    percentage_expression = (
        _grade_percentage_expression()
    )

    query = (
        db.query(
            User.name.label(
                "student_name"
            ),
            User.school_id.label(
                "school_id"
            ),
            Classroom.name.label(
                "class_name"
            ),
            Classroom.subject_code.label(
                "subject_code"
            ),
            Classroom.section.label(
                "section"
            ),
            Task.title.label(
                "activity_title"
            ),
            Task.activity_type.label(
                "activity_type"
            ),
            Submission.attempt_number.label(
                "attempt_number"
            ),
            Submission.status.label(
                "submission_status"
            ),
            InstructorGrade.grade_id.label(
                "grade_id"
            ),
            InstructorGrade.score.label(
                "score"
            ),
            InstructorGrade.max_score.label(
                "max_score"
            ),
            InstructorGrade.is_released.label(
                "is_released"
            ),
            InstructorGrade.updated_at.label(
                "grade_updated_at"
            ),
            percentage_expression.label(
                "percentage"
            ),
        )
        .join(
            User,
            User.user_id
            == Submission.student_id,
        )
        .join(
            Task,
            Task.task_id
            == Submission.task_id,
        )
        .join(
            Classroom,
            Classroom.class_id
            == Task.class_id,
        )
        .outerjoin(
            InstructorGrade,
            InstructorGrade.submission_id
            == Submission.sub_id,
        )
        .filter(
            Classroom.class_id
            == classroom.class_id,
            Classroom.instructor_id
            == instructor_id,
            Task.instructor_id
            == instructor_id,
            Submission.is_official.is_(
                True
            ),
            User.role == "student",
        )
    )

    if task is not None:
        query = query.filter(
            Task.task_id == task.task_id,
        )

    rows = (
        query.order_by(
            func.lower(
                User.name
            ).asc(),
            User.school_id.asc(),
            func.lower(
                Task.title
            ).asc(),
            Submission.sub_id.asc(),
        )
        .all()
    )

    output = StringIO(
        newline="",
    )

    writer = csv.writer(
        output,
        lineterminator="\r\n",
    )

    writer.writerow(
        [
            "student_name",
            "school_id",
            "class_name",
            "subject_code",
            "section",
            "activity_title",
            "activity_type",
            "attempt_number",
            "submission_status",
            "has_manual_grade",
            "score",
            "max_score",
            "percentage",
            "grade_is_released",
            "grade_updated_at",
        ]
    )

    for row in rows:
        has_manual_grade = (
            row.grade_id is not None
        )

        writer.writerow(
            [
                _sanitize_csv_cell(
                    row.student_name
                ),
                _sanitize_csv_cell(
                    row.school_id
                ),
                _sanitize_csv_cell(
                    row.class_name
                ),
                _sanitize_csv_cell(
                    row.subject_code
                ),
                _sanitize_csv_cell(
                    row.section
                ),
                _sanitize_csv_cell(
                    row.activity_title
                ),
                _sanitize_csv_cell(
                    row.activity_type
                ),
                row.attempt_number,
                _sanitize_csv_cell(
                    row.submission_status
                ),
                _sanitize_csv_cell(
                    has_manual_grade
                ),
                (
                    float(
                        row.score
                    )
                    if has_manual_grade
                    else ""
                ),
                (
                    float(
                        row.max_score
                    )
                    if has_manual_grade
                    else ""
                ),
                (
                    _round_percentage(
                        float(
                            row.percentage
                        )
                    )
                    if (
                        has_manual_grade
                        and row.percentage
                        is not None
                    )
                    else ""
                ),
                _sanitize_csv_cell(
                    bool(
                        row.is_released
                    )
                    if has_manual_grade
                    else False
                ),
                _sanitize_csv_cell(
                    row.grade_updated_at
                    if has_manual_grade
                    else None
                ),
            ]
        )

    generated_at = _utc_now()

    filename = (
        (
            f"classroom-{classroom.class_id}-"
            f"activity-{task.task_id}-gradebook.csv"
        )
        if task is not None
        else (
            f"classroom-{classroom.class_id}-"
            "gradebook.csv"
        )
    )

    try:
        content = (
            "\ufeff"
            + output.getvalue()
        ).encode(
            "utf-8"
        )

    except (
        UnicodeEncodeError,
        ValueError,
    ) as error:
        raise ReportingExportError(
            "The gradebook CSV export "
            "could not be generated."
        ) from error

    finally:
        output.close()

    return {
        "content": content,
        "media_type": CSV_MEDIA_TYPE,
        "filename": filename,
        "row_count": len(rows),
        "generated_at": generated_at,
        "includes_raw_source": False,
    }


def ensure_reporting_query_available(
    error: Exception,
) -> None:
    """
    Convert unexpected SQLAlchemy failures into one controlled service
    error at router integration boundaries.
    """

    if isinstance(
        error,
        SQLAlchemyError,
    ):
        raise ReportingServiceError(
            "The reporting operation "
            "could not be completed."
        ) from error

    raise error


# PAGINATION BOUNDARY:
# Missing-submission pagination uses the common bounded pagination
# contract. Database offsets are derived internally.

# ORDERING BOUNDARY:
# Missing-submission sort fields are explicitly approved. Every ordering
# includes stable task and user identifiers as deterministic tie-breakers.

# AUTHORIZATION BOUNDARY:
# Instructor completion, grade-distribution, missing-submission, and
# CSV-export operations are scoped to owned classrooms and activities.
# Student progress always uses the authenticated student's identity.

# COMPLETION BOUNDARY:
# Expected completion includes active, verified student accounts with
# active enrollments and published graded activities. Only official
# submission attempts count as submitted.

# GRADING BOUNDARY:
# Grade distributions and CSV grade values come only from manually
# created InstructorGrade records. AST, similarity, execution, and
# session indicators never populate report grades or rankings.

# EXPORT PRIVACY BOUNDARY:
# CSV exports exclude raw source code, standard input, feedback text,
# hidden tests, AST findings, similarity records, execution output,
# coding-session telemetry, clipboard or paste contents, browsing
# history, surveillance data, credentials, OTPs, JWTs, and misconduct
# conclusions.

# CSV FORMULA-INJECTION BOUNDARY:
# Text cells beginning with =, +, -, or @ are prefixed with an apostrophe
# before CSV serialization so spreadsheet applications treat them as
# literal text rather than formulas.

# PERFORMANCE BOUNDARY:
# Report functions use bounded aggregate or bulk queries. They do not
# execute one database query per student, activity, submission, or grade.
