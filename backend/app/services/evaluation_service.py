from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

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
from app.services.ast_evaluator import evaluate_ast_details
from app.services.jaccard import find_highest_similarity


class SubmissionNotFoundError(Exception):
    pass


class TaskNotFoundError(Exception):
    pass


class InvalidEvaluationResultError(Exception):
    pass


def _validate_similarity_score(value: Any) -> float:
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


def evaluate_submission_by_id(
    db: Session,
    sub_id: int,
) -> dict[str, Any]:
    submission = db.query(Submission).filter(Submission.sub_id == sub_id).first()

    if submission is None:
        raise SubmissionNotFoundError("Submission not found.")

    task = db.query(Task).filter(Task.task_id == submission.task_id).first()

    if task is None:
        raise TaskNotFoundError("Task not found for this submission.")

    ast_details = evaluate_ast_details(
        raw_code=submission.raw_code,
        rules=task.required_ast_rules,
    )

    ast_pass_fail = bool(ast_details.get("passed", False))

    # Compare only against another student's latest official attempt.
    # A student's previous attempts must not inflate the similarity result.
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
        other_submission.sub_id: other_submission.raw_code
        for other_submission in other_submissions
    }

    jaccard_details = find_highest_similarity(
        target_code=submission.raw_code,
        comparison_submissions=comparison_submissions,
    )

    highest_jaccard_score = _validate_similarity_score(
        jaccard_details.get("highest_score", 0.0)
    )

    highest_match_sub_id = jaccard_details.get("highest_match_sub_id")

    if (
        highest_match_sub_id is not None
        and highest_match_sub_id not in comparison_submissions
    ):
        raise InvalidEvaluationResultError(
            "The similarity evaluator returned an unknown submission."
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

    try:
        db.add(ast_analysis)
        db.add(submission)

        if highest_match_sub_id is not None:
            similarity_result = SimilarityResult(
                source_submission_id=submission.sub_id,
                compared_submission_id=highest_match_sub_id,
                score=highest_jaccard_score,
                algorithm="jaccard",
            )
            db.add(similarity_result)

        db.commit()
        db.refresh(submission)

    except Exception:
        db.rollback()
        raise

    return {
        "sub_id": submission.sub_id,
        "student_id": submission.student_id,
        "task_id": submission.task_id,
        "ast_pass_fail": submission.ast_pass_fail,
        "jaccard_score": submission.jaccard_score,
        "highest_match_sub_id": highest_match_sub_id,
        "ast_details": ast_details,
        "jaccard_details": jaccard_details,
    }


def _verify_evaluator_permission(submission: Submission, user: User) -> None:
    """
    SECURITY BOUNDARY:
    Only the instructor who owns the task can evaluate its submissions.
    """
    if user.role != "instructor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can evaluate submissions.",
        )

    if not submission.task or submission.task.instructor_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to evaluate this submission.",
        )


def get_evaluation_details(db: Session, sub_id: int, current_user: User) -> Submission:
    """
    Fetches the submission and its related review data (AST, Similarity, Grade).
    Enforces student and instructor boundaries.
    """
    submission = db.query(Submission).filter(Submission.sub_id == sub_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )

    if current_user.role == "student":
        # Student boundary: can only access their own submissions
        if submission.student_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this submission.",
            )
    else:
        # Instructor boundary: can only access submissions for their own tasks
        _verify_evaluator_permission(submission, current_user)

    return submission


def update_submission_status(
    db: Session, sub_id: int, status_update: EvaluationStatusUpdate, current_user: User
) -> Submission:
    submission = db.query(Submission).filter(Submission.sub_id == sub_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )

    _verify_evaluator_permission(submission, current_user)

    submission.status = status_update.status
    db.commit()
    db.refresh(submission)
    return submission


def create_or_update_grade(
    db: Session, sub_id: int, grade_in: InstructorGradeCreate, current_user: User
) -> InstructorGrade:
    """
    GRADING BOUNDARY:
    Explicitly assigns a manual instructor grade without relying on auto-grading.
    """
    submission = db.query(Submission).filter(Submission.sub_id == sub_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )

    _verify_evaluator_permission(submission, current_user)

    grade = (
        db.query(InstructorGrade)
        .filter(InstructorGrade.submission_id == sub_id)
        .first()
    )

    if grade:
        # Update existing
        grade.score = grade_in.score
        grade.max_score = grade_in.max_score
        grade.feedback = grade_in.feedback
        grade.is_released = grade_in.is_released
    else:
        # Create new
        grade = InstructorGrade(
            submission_id=sub_id,
            instructor_id=current_user.user_id,
            score=grade_in.score,
            max_score=grade_in.max_score,
            feedback=grade_in.feedback,
            is_released=grade_in.is_released,
        )
        db.add(grade)

    # Automatically transition submission to graded
    if submission.status != "graded":
        submission.status = "graded"

    db.commit()
    db.refresh(grade)
    return grade


def patch_grade(
    db: Session, sub_id: int, grade_update: InstructorGradeUpdate, current_user: User
) -> InstructorGrade:
    submission = db.query(Submission).filter(Submission.sub_id == sub_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )

    _verify_evaluator_permission(submission, current_user)

    grade = (
        db.query(InstructorGrade)
        .filter(InstructorGrade.submission_id == sub_id)
        .first()
    )
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade not found for this submission.",
        )

    update_data = grade_update.model_dump(exclude_unset=True)

    # Prevent score > max_score logically during a patch update
    new_score = update_data.get("score", grade.score)
    new_max = update_data.get("max_score", grade.max_score)
    if new_score > new_max:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="score cannot be greater than max_score",
        )

    for key, value in update_data.items():
        setattr(grade, key, value)

    db.commit()
    db.refresh(grade)
    return grade


# REVIEW BOUNDARY:
# AST and similarity results are automated review indicators only.
# They must never assign the official grade or automatically declare
# plagiarism, copying, cheating, or academic misconduct.

# PARTNER INTEGRATION:
# This service performs static AST and similarity analysis only. It must not
# execute submitted Python source code. The partner-owned isolated worker
# remains responsible for actual Python execution and resource enforcement.
