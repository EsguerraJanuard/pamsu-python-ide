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
from app.schemas.gradebook_schema import (
    GradebookSortDirection,
    GradebookSortField,
    MAX_GRADEBOOK_PAGE_SIZE,
    MIN_GRADEBOOK_PAGE_SIZE,
)
from app.schemas.submission_schema import SubmissionStatus


GRADEBOOK_PAGINATION_BOUNDS = PaginationBounds(
    minimum_page=1,
    minimum_page_size=MIN_GRADEBOOK_PAGE_SIZE,
    maximum_page_size=MAX_GRADEBOOK_PAGE_SIZE,
)

APPROVED_GRADEBOOK_SORT_FIELDS = {
    "student_name",
    "school_id",
    "score",
    "percentage",
    "submitted_at",
}


class GradebookServiceError(Exception):
    """Base exception for gradebook operations."""


class GradebookClassNotFoundError(
    GradebookServiceError,
):
    """Raised when the selected classroom does not exist."""


class GradebookTaskNotFoundError(
    GradebookServiceError,
):
    """Raised when the selected activity does not exist."""


class GradebookAccessDeniedError(
    GradebookServiceError,
):
    """Raised when an instructor does not own a selected resource."""


class GradebookFilterConflictError(
    GradebookServiceError,
):
    """Raised when supplied filters are inconsistent."""


class GradebookPaginationError(
    GradebookServiceError,
):
    """Raised when pagination or sorting values are invalid."""


def _build_pagination_request(
    *,
    page: int,
    page_size: int,
) -> PaginationRequest:
    try:
        return validate_pagination(
            page=page,
            page_size=page_size,
            bounds=GRADEBOOK_PAGINATION_BOUNDS,
        )
    except PaginationError as error:
        raise GradebookPaginationError(str(error)) from error


def _validate_pagination(
    *,
    page: int,
    page_size: int,
) -> None:
    """
    Preserve the existing private validation boundary while delegating
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
        raise GradebookClassNotFoundError("Classroom not found.")

    if classroom.instructor_id != instructor_id:
        raise GradebookAccessDeniedError(
            "You can only access gradebooks for classrooms that you own."
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
        raise GradebookTaskNotFoundError("Activity not found.")

    if task.instructor_id != instructor_id:
        raise GradebookAccessDeniedError(
            "You can only access gradebooks for activities that you own."
        )

    if task.class_id is None:
        raise GradebookFilterConflictError(
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
        raise GradebookAccessDeniedError(
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
        raise GradebookFilterConflictError(
            "The selected activity does not belong to the selected classroom."
        )


def _validate_grade_filters(
    *,
    has_manual_grade: bool | None,
    grade_released: bool | None,
) -> None:
    if has_manual_grade is False and grade_released is not None:
        raise GradebookFilterConflictError(
            "grade_released cannot be filtered when has_manual_grade is false."
        )


def _apply_instructor_filters(
    query: Any,
    *,
    class_id: int | None,
    task_id: int | None,
    student_id: int | None,
    submission_status: SubmissionStatus | None,
    official: bool | None,
    has_manual_grade: bool | None,
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

    if has_manual_grade is True:
        query = query.filter(
            InstructorGrade.grade_id.is_not(None),
        )

    if has_manual_grade is False:
        query = query.filter(
            InstructorGrade.grade_id.is_(None),
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


def _build_instructor_item_query(
    db: Session,
    *,
    instructor_id: int,
) -> Any:
    percentage_expression = InstructorGrade.score * 100.0 / InstructorGrade.max_score

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
            InstructorGrade.score.label("grade_score"),
            InstructorGrade.max_score.label("grade_max_score"),
            InstructorGrade.is_released.label("grade_is_released"),
            InstructorGrade.updated_at.label("grade_updated_at"),
            percentage_expression.label("grade_percentage"),
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


def _build_instructor_count_query(
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
                            InstructorGrade.grade_id.is_not(None),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("with_manual_grade"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            InstructorGrade.grade_id.is_(None),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("without_manual_grade"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            and_(
                                InstructorGrade.grade_id.is_not(None),
                                InstructorGrade.is_released.is_(True),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("released"),
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
            ).label("unreleased"),
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
            ).label("graded_status"),
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
            ).label("awaiting_review_status"),
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


def _apply_instructor_ordering(
    query: Any,
    *,
    sort_by: GradebookSortField,
    sort_direction: GradebookSortDirection,
) -> Any:
    if sort_by not in APPROVED_GRADEBOOK_SORT_FIELDS:
        raise GradebookPaginationError("Unsupported gradebook sort field.")

    try:
        normalized_direction = normalize_sort_direction(sort_direction)
    except SortConfigurationError as error:
        raise GradebookPaginationError(str(error)) from error

    def apply_direction(
        column: Any,
    ) -> Any:
        if normalized_direction == "asc":
            return column.asc()

        return column.desc()

    if sort_by == "student_name":
        return query.order_by(
            apply_direction(func.lower(User.name)),
            apply_direction(User.school_id),
            Submission.sub_id.desc(),
        )

    if sort_by == "school_id":
        return query.order_by(
            apply_direction(User.school_id),
            apply_direction(func.lower(User.name)),
            Submission.sub_id.desc(),
        )

    if sort_by == "score":
        null_rank = case(
            (
                InstructorGrade.grade_id.is_(None),
                1,
            ),
            else_=0,
        )

        return query.order_by(
            null_rank.asc(),
            apply_direction(InstructorGrade.score),
            Submission.sub_id.desc(),
        )

    if sort_by == "percentage":
        null_rank = case(
            (
                InstructorGrade.grade_id.is_(None),
                1,
            ),
            else_=0,
        )

        percentage_expression = (
            InstructorGrade.score * 100.0 / InstructorGrade.max_score
        )

        return query.order_by(
            null_rank.asc(),
            apply_direction(percentage_expression),
            Submission.sub_id.desc(),
        )

    return query.order_by(
        apply_direction(Submission.submitted_at),
        Submission.sub_id.desc(),
    )


def _build_activity_summary(
    row: Any,
) -> dict[str, Any]:
    return {
        "task_id": row.task_id,
        "title": row.task_title,
        "activity_type": row.activity_type,
        "class_id": row.class_id,
        "class_name": row.class_name,
        "subject_code": row.subject_code,
        "section": row.section,
    }


def _build_instructor_gradebook_item(
    row: Any,
) -> dict[str, Any]:
    has_manual_grade = row.grade_id is not None

    score: float | None = None
    max_score: float | None = None
    percentage: float | None = None
    grade_updated_at = None

    if has_manual_grade:
        score = float(row.grade_score)

        max_score = float(row.grade_max_score)

        percentage = float(row.grade_percentage)

        grade_updated_at = row.grade_updated_at

    return {
        "sub_id": row.sub_id,
        "student": {
            "student_id": row.student_id,
            "name": row.student_name,
            "school_id": (row.student_school_id),
        },
        "activity": (_build_activity_summary(row)),
        "attempt_number": (row.attempt_number),
        "submission_status": (row.submission_status),
        "is_official": row.is_official,
        "submitted_at": row.submitted_at,
        "accepted_at": row.accepted_at,
        "has_manual_grade": (has_manual_grade),
        "score": score,
        "max_score": max_score,
        "percentage": percentage,
        "grade_is_released": (
            bool(row.grade_is_released) if has_manual_grade else False
        ),
        "grade_updated_at": (grade_updated_at),
    }


def list_instructor_gradebook(
    db: Session,
    *,
    instructor_id: int,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    class_id: int | None = None,
    task_id: int | None = None,
    student_id: int | None = None,
    submission_status: SubmissionStatus | None = None,
    official: bool | None = True,
    has_manual_grade: bool | None = None,
    grade_released: bool | None = None,
    sort_by: GradebookSortField = "student_name",
    sort_direction: GradebookSortDirection = "asc",
) -> dict[str, Any]:
    """
    Return a paginated instructor-owned gradebook.

    Summary rows exclude source code, standard input, AST details,
    similarity records, execution output, and session telemetry.
    """

    pagination = _build_pagination_request(
        page=page,
        page_size=page_size,
    )

    _validate_grade_filters(
        has_manual_grade=has_manual_grade,
        grade_released=grade_released,
    )

    _validate_owned_filters(
        db,
        instructor_id=instructor_id,
        class_id=class_id,
        task_id=task_id,
    )

    item_query = _build_instructor_item_query(
        db,
        instructor_id=instructor_id,
    )

    item_query = _apply_instructor_filters(
        item_query,
        class_id=class_id,
        task_id=task_id,
        student_id=student_id,
        submission_status=submission_status,
        official=official,
        has_manual_grade=has_manual_grade,
        grade_released=grade_released,
    )

    total_items = int(item_query.order_by(None).count())

    count_query = _build_instructor_count_query(
        db,
        instructor_id=instructor_id,
    )

    count_query = _apply_instructor_filters(
        count_query,
        class_id=class_id,
        task_id=task_id,
        student_id=student_id,
        submission_status=submission_status,
        official=official,
        has_manual_grade=has_manual_grade,
        grade_released=grade_released,
    )

    count_row = count_query.one()

    ordered_query = _apply_instructor_ordering(
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
        "items": [_build_instructor_gradebook_item(row) for row in rows],
        "page": metadata.page,
        "page_size": metadata.page_size,
        "total_items": metadata.total_items,
        "total_pages": metadata.total_pages,
        "sort_by": sort_by,
        "sort_direction": sort_direction,
        "counts": {
            "total": int(count_row.total or 0),
            "with_manual_grade": int(count_row.with_manual_grade or 0),
            "without_manual_grade": int(count_row.without_manual_grade or 0),
            "released": int(count_row.released or 0),
            "unreleased": int(count_row.unreleased or 0),
            "graded_status": int(count_row.graded_status or 0),
            "awaiting_review_status": int(count_row.awaiting_review_status or 0),
        },
    }


def _apply_student_released_grade_filters(
    query: Any,
    *,
    class_id: int | None,
    task_id: int | None,
) -> Any:
    if class_id is not None:
        query = query.filter(
            Classroom.class_id == class_id,
        )

    if task_id is not None:
        query = query.filter(
            Task.task_id == task_id,
        )

    return query


def _build_student_released_grade_query(
    db: Session,
    *,
    student_id: int,
) -> Any:
    percentage_expression = InstructorGrade.score * 100.0 / InstructorGrade.max_score

    return (
        db.query(
            Submission.sub_id.label("sub_id"),
            Submission.attempt_number.label("attempt_number"),
            Submission.status.label("submission_status"),
            Task.task_id.label("task_id"),
            Task.title.label("task_title"),
            Task.activity_type.label("activity_type"),
            Classroom.class_id.label("class_id"),
            Classroom.name.label("class_name"),
            Classroom.subject_code.label("subject_code"),
            Classroom.section.label("section"),
            InstructorGrade.score.label("grade_score"),
            InstructorGrade.max_score.label("grade_max_score"),
            InstructorGrade.feedback.label("grade_feedback"),
            InstructorGrade.updated_at.label("released_at"),
            percentage_expression.label("grade_percentage"),
        )
        .join(
            Task,
            Submission.task_id == Task.task_id,
        )
        .outerjoin(
            Classroom,
            Task.class_id == Classroom.class_id,
        )
        .join(
            InstructorGrade,
            InstructorGrade.submission_id == Submission.sub_id,
        )
        .filter(
            Submission.student_id == student_id,
            Submission.is_official.is_(True),
            InstructorGrade.is_released.is_(True),
        )
    )


def _build_student_released_grade_item(
    row: Any,
) -> dict[str, Any]:
    return {
        "sub_id": row.sub_id,
        "activity": (_build_activity_summary(row)),
        "attempt_number": (row.attempt_number),
        "submission_status": (row.submission_status),
        "score": float(row.grade_score),
        "max_score": float(row.grade_max_score),
        "percentage": float(row.grade_percentage),
        "feedback": row.grade_feedback,
        "is_released": True,
        "released_at": row.released_at,
    }


def list_student_released_grades(
    db: Session,
    *,
    student_id: int,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    class_id: int | None = None,
    task_id: int | None = None,
) -> dict[str, Any]:
    """
    Return only released grades belonging to the authenticated student.

    Unreleased grades, instructor identity, internal grade IDs, and
    instructor-only evaluation information are excluded.
    """

    pagination = _build_pagination_request(
        page=page,
        page_size=page_size,
    )

    query = _build_student_released_grade_query(
        db,
        student_id=student_id,
    )

    query = _apply_student_released_grade_filters(
        query,
        class_id=class_id,
        task_id=task_id,
    )

    total_items = int(query.order_by(None).count())

    rows = (
        query.order_by(
            InstructorGrade.updated_at.desc(),
            Submission.sub_id.desc(),
        )
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )

    metadata = build_pagination_metadata(
        pagination=pagination,
        total_items=total_items,
    )

    return {
        "items": [_build_student_released_grade_item(row) for row in rows],
        "page": metadata.page,
        "page_size": metadata.page_size,
        "total_items": metadata.total_items,
        "total_pages": metadata.total_pages,
    }


# PAGINATION BOUNDARY:
# Instructor and student gradebook pagination use the common bounded
# pagination contract. Database offsets are derived internally.

# ORDERING BOUNDARY:
# Instructor gradebook ordering uses approved sort fields and ends with
# Submission.sub_id as a stable unique tie-breaker. Student released
# grades use grade update time followed by Submission.sub_id.

# AUTHORIZATION BOUNDARY:
# Instructor gradebook queries are restricted to activities and
# classrooms owned by the authenticated instructor. Student grade
# queries are restricted to the authenticated student's own submissions.

# PRIVACY BOUNDARY:
# Gradebook summary queries exclude source code, standard input, hidden
# test cases, AST details, similarity comparison records, execution
# output, session telemetry, clipboard contents, pasted text, and
# surveillance data.

# GRADING BOUNDARY:
# Scores, maximum scores, percentages, release state, and feedback come
# only from manually created InstructorGrade records. Automated
# indicators never populate official academic grades.

# STUDENT VISIBILITY BOUNDARY:
# Students receive only released grades for their own official
# submissions. Internal grade IDs and instructor identity are excluded.
