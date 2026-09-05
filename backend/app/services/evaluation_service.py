from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.domain_models import (
    ASTAnalysis,
    InstructorGrade,
    SimilarityResult,
    Submission,
    Task,
    User,
)
from app.schemas.evaluation_schema import (
    EvaluationStatusUpdate,
    InstructorGradeCreate,
    InstructorGradeUpdate,
)
from app.services.academic_event_service import (
    AcademicEventWorkflowError,
    notify_grade_released,
)
from app.services.ast_evaluator import evaluate_ast_details
from app.services.audit_service import (
    AuditServiceError,
    create_audit_record,
)
from app.services.jaccard import find_highest_similarity
from app.services.notification_service import NotificationServiceError


class EvaluationServiceError(Exception):
    """Base exception for evaluation and grading workflow errors."""


class SubmissionNotFoundError(
    EvaluationServiceError,
):
    """Raised when the requested submission does not exist."""


class TaskNotFoundError(
    EvaluationServiceError,
):
    """Raised when the submission's activity does not exist."""


class EvaluationAccessDeniedError(
    EvaluationServiceError,
):
    """Raised when a user cannot access an evaluation operation."""


class OfficialSubmissionRequiredError(
    EvaluationServiceError,
):
    """Raised when a manual grade targets an unofficial attempt."""


class GradeUnavailableError(
    EvaluationServiceError,
):
    """Raised when an activity does not accept an official grade."""


class GradeNotFoundError(
    EvaluationServiceError,
):
    """Raised when a manual instructor grade does not exist."""


class GradeValidationError(
    EvaluationServiceError,
):
    """Raised when final grade values violate the grading contract."""


class EvaluationStateConflictError(
    EvaluationServiceError,
):
    """Raised when a requested review-state change is inconsistent."""


class InvalidEvaluationResultError(
    EvaluationServiceError,
):
    """Raised when an automated evaluator returns invalid data."""


class EvaluationPersistenceConflictError(
    EvaluationServiceError,
):
    """Raised when evaluation data conflicts with another transaction."""


class EvaluationPersistenceError(
    EvaluationServiceError,
):
    """Raised when evaluation data cannot be persisted."""


class GradeNotificationWorkflowError(
    EvaluationServiceError,
):
    """
    Raised when a released grade and its required student notification
    cannot be saved as one transaction.
    """


class GradeAuditWorkflowError(
    EvaluationServiceError,
):
    """
    Raised when a manual-grade write and its required accountability
    record cannot be saved as one transaction.
    """


def _commit_evaluation_transaction(
    db: Session,
) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()

        raise EvaluationPersistenceConflictError(
            "The evaluation operation conflicted with another database operation."
        ) from error
    except SQLAlchemyError as error:
        db.rollback()

        raise EvaluationPersistenceError(
            "The evaluation operation could not be saved."
        ) from error


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _flush_grade_write_transaction(
    db: Session,
) -> None:
    """
    Flush a manual grade before creating its required audit records
    and optional release notification workflow.
    """

    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()

        raise EvaluationPersistenceConflictError(
            "The grade write conflicted with another database operation."
        ) from error
    except SQLAlchemyError as error:
        db.rollback()

        raise EvaluationPersistenceError(
            "The grade write could not be saved."
        ) from error


def _build_grade_audit_key(
    *,
    action_type: str,
    grade_id: int,
    repeatable: bool,
) -> str:
    base_key = f"audit:{action_type}:grade:{grade_id}"

    if not repeatable:
        return base_key

    return f"{base_key}:{uuid4()}"


def _record_grade_audit(
    *,
    db: Session,
    audit_key: str,
    actor_user_id: int,
    action_type: str,
    grade_id: int,
    audit_data: dict[str, Any],
    occurred_at: datetime,
) -> None:
    create_audit_record(
        db,
        {
            "audit_key": audit_key,
            "actor_user_id": actor_user_id,
            "action_type": action_type,
            "resource_type": "grade",
            "resource_id": str(grade_id),
            "outcome": "succeeded",
            "audit_data": audit_data,
            "occurred_at": occurred_at,
        },
        commit=False,
    )


def _complete_grade_write(
    db: Session,
    *,
    grade: InstructorGrade,
    submission: Submission,
    task: Task,
    was_created: bool,
    was_released: bool,
    changed_fields: list[str],
    actor_instructor_id: int,
) -> InstructorGrade:
    """
    Save one manual-grade write with immutable accountability records.

    A grade-created audit record is created for the initial write.
    Later meaningful edits create grade-updated records. A separate
    grade-released record and student notification are created only on
    an unreleased-to-released transition.
    """

    release_transition = not was_released and bool(grade.is_released)
    occurred_at = _utc_now()

    _flush_grade_write_transaction(db)

    base_audit_data = {
        "submission_id": submission.sub_id,
        "task_id": task.task_id,
        "class_id": task.class_id,
        "previous_release_state": ("released" if was_released else "unreleased"),
        "new_release_state": ("released" if grade.is_released else "unreleased"),
    }

    try:
        if was_created:
            _record_grade_audit(
                db=db,
                audit_key=_build_grade_audit_key(
                    action_type="grade_created",
                    grade_id=grade.grade_id,
                    repeatable=False,
                ),
                actor_user_id=actor_instructor_id,
                action_type="grade_created",
                grade_id=grade.grade_id,
                audit_data={
                    **base_audit_data,
                    "created_fields": sorted(changed_fields),
                },
                occurred_at=occurred_at,
            )
        else:
            _record_grade_audit(
                db=db,
                audit_key=_build_grade_audit_key(
                    action_type="grade_updated",
                    grade_id=grade.grade_id,
                    repeatable=True,
                ),
                actor_user_id=actor_instructor_id,
                action_type="grade_updated",
                grade_id=grade.grade_id,
                audit_data={
                    **base_audit_data,
                    "changed_fields": sorted(changed_fields),
                },
                occurred_at=occurred_at,
            )

        if release_transition:
            _record_grade_audit(
                db=db,
                audit_key=_build_grade_audit_key(
                    action_type="grade_released",
                    grade_id=grade.grade_id,
                    repeatable=True,
                ),
                actor_user_id=actor_instructor_id,
                action_type="grade_released",
                grade_id=grade.grade_id,
                audit_data=base_audit_data,
                occurred_at=occurred_at,
            )
    except (
        AuditServiceError,
        ValidationError,
        SQLAlchemyError,
    ) as error:
        db.rollback()

        raise GradeAuditWorkflowError(
            "The manual grade and its required accountability record "
            "could not be saved. No grade change was completed. "
            "Please try again."
        ) from error

    if not release_transition:
        _commit_evaluation_transaction(db)
        db.refresh(grade)

        return grade

    try:
        notify_grade_released(
            db,
            actor_instructor_id=actor_instructor_id,
            grade_id=grade.grade_id,
        )
    except (
        AcademicEventWorkflowError,
        NotificationServiceError,
        SQLAlchemyError,
    ) as error:
        db.rollback()

        raise GradeNotificationWorkflowError(
            "The grade release and its in-app notification could not "
            "be saved. The grade remains unreleased. Please try again."
        ) from error

    db.refresh(grade)

    return grade


def _get_submission(
    db: Session,
    *,
    sub_id: int,
    lock_for_update: bool = False,
) -> Submission:
    query = db.query(Submission).filter(
        Submission.sub_id == sub_id,
    )

    if lock_for_update:
        query = query.with_for_update()

    submission = query.first()

    if submission is None:
        raise SubmissionNotFoundError("Submission not found.")

    return submission


def _get_submission_with_review_data(
    db: Session,
    *,
    sub_id: int,
) -> Submission:
    submission = (
        db.query(Submission)
        .options(
            selectinload(Submission.ast_analyses).selectinload(ASTAnalysis.findings),
            selectinload(Submission.similarity_results_as_source),
            selectinload(Submission.instructor_grade),
            selectinload(Submission.task),
        )
        .filter(
            Submission.sub_id == sub_id,
        )
        .first()
    )

    if submission is None:
        raise SubmissionNotFoundError("Submission not found.")

    return submission


def _get_task(
    db: Session,
    *,
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
        raise TaskNotFoundError("Task not found for this submission.")

    return task


def _verify_instructor_owns_submission(
    *,
    submission: Submission,
    instructor_id: int,
) -> Task:
    task = submission.task

    if task is None:
        raise TaskNotFoundError("Task not found for this submission.")

    if task.instructor_id != instructor_id:
        raise EvaluationAccessDeniedError(
            "You can only review submissions for activities that you own."
        )

    return task


def _verify_instructor_user(
    *,
    submission: Submission,
    current_user: User,
) -> Task:
    if current_user.role != "instructor":
        raise EvaluationAccessDeniedError(
            "Only instructors may perform this evaluation operation."
        )

    return _verify_instructor_owns_submission(
        submission=submission,
        instructor_id=current_user.user_id,
    )


def _require_gradable_official_submission(
    *,
    submission: Submission,
    task: Task,
) -> None:
    if not task.is_graded:
        raise GradeUnavailableError(
            "This activity does not accept an official instructor grade."
        )

    if not submission.is_official or submission.accepted_at is None:
        raise OfficialSubmissionRequiredError(
            "Official grades may be assigned only "
            "to the latest accepted official submission."
        )

    if submission.status == "rejected":
        raise EvaluationStateConflictError(
            "A rejected submission cannot receive an official instructor grade."
        )


def _validate_similarity_score(
    value: Any,
) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise InvalidEvaluationResultError(
            "The similarity evaluator returned an invalid score."
        ) from exc

    if not 0 <= score <= 100:
        raise InvalidEvaluationResultError(
            "The similarity score must be between 0 and 100."
        )

    return score


def _validate_highest_match_submission_id(
    *,
    value: Any,
    comparison_submissions: dict[int, str],
) -> int | None:
    if value is None:
        return None

    if isinstance(value, bool):
        raise InvalidEvaluationResultError(
            "The similarity evaluator returned an invalid matched submission."
        )

    try:
        matched_submission_id = int(value)
    except (TypeError, ValueError) as exc:
        raise InvalidEvaluationResultError(
            "The similarity evaluator returned an invalid matched submission."
        ) from exc

    if matched_submission_id not in comparison_submissions:
        raise InvalidEvaluationResultError(
            "The similarity evaluator returned an unknown submission."
        )

    return matched_submission_id


def evaluate_submission_by_id(
    db: Session,
    sub_id: int,
    *,
    instructor_id: int | None = None,
) -> dict[str, Any]:
    """
    Perform static AST and source-similarity analysis.

    When instructor_id is supplied, ownership is verified inside the
    service. The function does not execute student Python and does not
    create or modify an official instructor grade.
    """

    submission = _get_submission_with_review_data(
        db,
        sub_id=sub_id,
    )

    task = submission.task

    if task is None:
        task = _get_task(
            db,
            task_id=submission.task_id,
        )

    if instructor_id is not None:
        _verify_instructor_owns_submission(
            submission=submission,
            instructor_id=instructor_id,
        )

    ast_details = evaluate_ast_details(
        raw_code=submission.raw_code,
        rules=task.required_ast_rules,
    )

    if not isinstance(ast_details, dict):
        raise InvalidEvaluationResultError(
            "The AST evaluator returned an invalid result."
        )

    ast_pass_fail = bool(
        ast_details.get(
            "passed",
            False,
        )
    )

    # Compare only against another student's current official attempt.
    # Previous attempts from the same student must not inflate similarity.
    other_submissions = (
        db.query(Submission)
        .filter(
            Submission.task_id == submission.task_id,
            Submission.sub_id != submission.sub_id,
            Submission.student_id != submission.student_id,
            Submission.is_official.is_(True),
            Submission.status.in_(
                (
                    "submitted",
                    "awaiting_review",
                    "graded",
                )
            ),
        )
        .all()
    )

    comparison_submissions = {
        candidate.sub_id: candidate.raw_code for candidate in other_submissions
    }

    jaccard_details = find_highest_similarity(
        target_code=submission.raw_code,
        comparison_submissions=(comparison_submissions),
    )

    if not isinstance(jaccard_details, dict):
        raise InvalidEvaluationResultError(
            "The similarity evaluator returned an invalid result."
        )

    highest_jaccard_score = _validate_similarity_score(
        jaccard_details.get(
            "highest_score",
            0.0,
        )
    )

    highest_match_sub_id = _validate_highest_match_submission_id(
        value=jaccard_details.get("highest_match_sub_id"),
        comparison_submissions=(comparison_submissions),
    )

    ast_analysis = ASTAnalysis(
        submission_id=submission.sub_id,
        execution_id=None,
        overall_pass=ast_pass_fail,
        syntax_error=ast_details.get("syntax_error"),
        details=ast_details,
    )

    submission.ast_pass_fail = ast_pass_fail
    submission.jaccard_score = highest_jaccard_score

    db.add(ast_analysis)

    if highest_match_sub_id is not None:
        similarity_result = SimilarityResult(
            source_submission_id=(submission.sub_id),
            compared_submission_id=(highest_match_sub_id),
            score=highest_jaccard_score,
            algorithm="jaccard",
        )

        db.add(similarity_result)

    _commit_evaluation_transaction(db)

    db.refresh(submission)

    return {
        "sub_id": submission.sub_id,
        "student_id": submission.student_id,
        "task_id": submission.task_id,
        "ast_pass_fail": (submission.ast_pass_fail),
        "jaccard_score": (submission.jaccard_score),
        "highest_match_sub_id": (highest_match_sub_id),
        "ast_details": ast_details,
        "jaccard_details": jaccard_details,
    }


def get_student_evaluation_details(
    db: Session,
    *,
    sub_id: int,
    student_id: int,
) -> dict[str, Any]:
    """
    Return a student-safe evaluation view.

    Full AST findings, similarity comparison records, comparison IDs,
    instructor identity, and unreleased grade information are excluded.
    """

    submission = (
        db.query(Submission)
        .options(
            selectinload(Submission.instructor_grade),
        )
        .filter(
            Submission.sub_id == sub_id,
        )
        .first()
    )

    if submission is None:
        raise SubmissionNotFoundError("Submission not found.")

    if submission.student_id != student_id:
        raise EvaluationAccessDeniedError(
            "You can only view evaluation information for your own submissions."
        )

    released_grade: dict[str, Any] | None = None

    grade = submission.instructor_grade

    if grade is not None and grade.is_released:
        released_grade = {
            "score": grade.score,
            "max_score": grade.max_score,
            "feedback": grade.feedback,
            "is_released": True,
            "released_at": grade.updated_at,
        }

    return {
        "sub_id": submission.sub_id,
        "task_id": submission.task_id,
        "status": submission.status,
        "is_official": submission.is_official,
        "submitted_at": submission.submitted_at,
        "accepted_at": submission.accepted_at,
        "instructor_grade": released_grade,
    }


def get_instructor_evaluation_details(
    db: Session,
    *,
    sub_id: int,
    instructor_id: int,
) -> Submission:
    """
    Return the complete review view only to the activity owner.
    """

    submission = _get_submission_with_review_data(
        db,
        sub_id=sub_id,
    )

    _verify_instructor_owns_submission(
        submission=submission,
        instructor_id=instructor_id,
    )

    return submission


def get_evaluation_details(
    db: Session,
    sub_id: int,
    current_user: User,
) -> Submission | dict[str, Any]:
    """
    Compatibility dispatcher for older router imports.

    New routes should call the role-specific student or instructor
    functions directly so their response schemas remain separate.
    """

    if current_user.role == "student":
        return get_student_evaluation_details(
            db,
            sub_id=sub_id,
            student_id=current_user.user_id,
        )

    if current_user.role == "instructor":
        return get_instructor_evaluation_details(
            db,
            sub_id=sub_id,
            instructor_id=current_user.user_id,
        )

    raise EvaluationAccessDeniedError(
        "Evaluation access is unavailable for this account."
    )


def update_submission_status(
    db: Session,
    sub_id: int,
    status_update: EvaluationStatusUpdate,
    current_user: User,
) -> Submission:
    """
    Apply an explicit instructor-controlled review-status update.

    Manual grade creation and modification do not silently change the
    submission status.
    """

    submission = _get_submission(
        db,
        sub_id=sub_id,
        lock_for_update=True,
    )

    task = _verify_instructor_user(
        submission=submission,
        current_user=current_user,
    )

    if status_update.status == "graded":
        grade = (
            db.query(InstructorGrade)
            .filter(
                InstructorGrade.submission_id == submission.sub_id,
            )
            .first()
        )

        if grade is None:
            db.rollback()

            raise EvaluationStateConflictError(
                "A manual instructor grade must be set "
                "before marking the submission as graded."
            )

        _require_gradable_official_submission(
            submission=submission,
            task=task,
        )

    submission.status = status_update.status

    _commit_evaluation_transaction(db)

    db.refresh(submission)

    return submission


def create_or_update_grade(
    db: Session,
    sub_id: int,
    grade_in: InstructorGradeCreate,
    current_user: User,
) -> InstructorGrade:
    """
    Create or fully replace a manual instructor grade.

    Automated AST, similarity, execution, and session indicators are
    never used to populate the manual grade. Every meaningful write
    creates a privacy-safe immutable audit record. A student
    notification is created only when the grade transitions from
    unreleased to released.
    """

    submission = _get_submission(
        db,
        sub_id=sub_id,
        lock_for_update=True,
    )

    task = _verify_instructor_user(
        submission=submission,
        current_user=current_user,
    )

    _require_gradable_official_submission(
        submission=submission,
        task=task,
    )

    grade = (
        db.query(InstructorGrade)
        .filter(
            InstructorGrade.submission_id == submission.sub_id,
        )
        .with_for_update()
        .first()
    )

    was_created = grade is None
    was_released = False

    incoming_values = {
        "score": grade_in.score,
        "max_score": grade_in.max_score,
        "feedback": grade_in.feedback,
        "is_released": grade_in.is_released,
    }

    if grade is None:
        changed_fields = sorted(incoming_values)

        grade = InstructorGrade(
            submission_id=submission.sub_id,
            instructor_id=current_user.user_id,
            **incoming_values,
        )

        db.add(grade)
    else:
        if grade.instructor_id != current_user.user_id:
            db.rollback()

            raise EvaluationAccessDeniedError(
                "The existing grade belongs to another instructor."
            )

        was_released = bool(grade.is_released)

        changed_fields = sorted(
            field_name
            for field_name, value in incoming_values.items()
            if getattr(grade, field_name) != value
        )

        if not changed_fields:
            return grade

        for field_name, value in incoming_values.items():
            setattr(
                grade,
                field_name,
                value,
            )

    # Intentionally do not change submission.status here.
    return _complete_grade_write(
        db,
        grade=grade,
        submission=submission,
        task=task,
        was_created=was_created,
        was_released=was_released,
        changed_fields=changed_fields,
        actor_instructor_id=current_user.user_id,
    )


def patch_grade(
    db: Session,
    sub_id: int,
    grade_update: InstructorGradeUpdate,
    current_user: User,
) -> InstructorGrade:
    """
    Partially modify an existing manual instructor grade.

    The service validates the final score and maximum after combining
    supplied fields with the current database values. Every meaningful
    edit creates a privacy-safe immutable audit record. A student
    notification is created only on an unreleased-to-released
    transition.
    """

    submission = _get_submission(
        db,
        sub_id=sub_id,
        lock_for_update=True,
    )

    task = _verify_instructor_user(
        submission=submission,
        current_user=current_user,
    )

    _require_gradable_official_submission(
        submission=submission,
        task=task,
    )

    grade = (
        db.query(InstructorGrade)
        .filter(
            InstructorGrade.submission_id == submission.sub_id,
        )
        .with_for_update()
        .first()
    )

    if grade is None:
        db.rollback()

        raise GradeNotFoundError("Grade not found for this submission.")

    if grade.instructor_id != current_user.user_id:
        db.rollback()

        raise EvaluationAccessDeniedError(
            "The existing grade belongs to another instructor."
        )

    update_data = grade_update.model_dump(
        exclude_unset=True,
    )

    if not update_data:
        db.rollback()

        raise GradeValidationError("At least one grade field must be supplied.")

    new_score = update_data.get(
        "score",
        grade.score,
    )

    new_max_score = update_data.get(
        "max_score",
        grade.max_score,
    )

    if new_score > new_max_score:
        db.rollback()

        raise GradeValidationError("score cannot be greater than max_score")

    changed_fields = sorted(
        field_name
        for field_name, value in update_data.items()
        if getattr(grade, field_name) != value
    )

    if not changed_fields:
        return grade

    was_released = bool(grade.is_released)

    for field_name, value in update_data.items():
        setattr(
            grade,
            field_name,
            value,
        )

    # Intentionally do not change submission.status here.
    return _complete_grade_write(
        db,
        grade=grade,
        submission=submission,
        task=task,
        was_created=False,
        was_released=was_released,
        changed_fields=changed_fields,
        actor_instructor_id=current_user.user_id,
    )


# SECURITY BOUNDARY:
# Students may view only their own student-safe evaluation response.
# Full AST findings, similarity comparisons, and unreleased grades remain
# restricted to the instructor who owns the associated activity.

# GRADING BOUNDARY:
# Only an authorized instructor may create or modify a manual grade for
# the latest accepted official submission of a graded activity. Manual
# grading does not silently change the submission's review status.

# GRADE AUDIT WORKFLOW BOUNDARY:
# Manual grade creation and every meaningful later edit create immutable
# backend-owned audit records. An unreleased-to-released transition also
# creates a separate grade-released record. Grade writes and their audit
# records are committed together. Audit failure rolls back the grade
# change so the instructor may retry safely.

# GRADE AUDIT PRIVACY BOUNDARY:
# Grade audit metadata contains only grade, submission, task, and
# classroom identifiers, changed field names, and release-state
# transitions. It never contains score values, maximum-score values,
# feedback text, source code, standard input, hidden test data, AST or
# similarity details, execution output, behavioral telemetry, clipboard
# or paste contents, surveillance data, or misconduct conclusions.

# GRADE-RELEASE NOTIFICATION BOUNDARY:
# A student notification is created only when an instructor-controlled
# grade transitions from unreleased to released. Ordinary grade edits,
# repeated writes to an already released grade, and unrelease operations
# do not create duplicate release notifications.

# NOTIFICATION TRANSACTION BOUNDARY:
# A grade release, its audit records, academic event, and student
# notification are committed as one transaction. A workflow failure
# rolls back the release so the instructor may retry safely.

# NOTIFICATION PRIVACY BOUNDARY:
# Grade-release notifications exclude the score, maximum score, feedback,
# source code, standard input, AST details, similarity results, execution
# output, hidden test cases, behavioral telemetry, and misconduct claims.

# REVIEW BOUNDARY:
# AST and source-similarity results are automated review indicators only.
# They never assign the official grade or automatically declare copying,
# plagiarism, cheating, or academic misconduct.

# EXECUTION BOUNDARY:
# This service performs static AST parsing and token-based similarity
# analysis only. It never executes submitted Python source code.
