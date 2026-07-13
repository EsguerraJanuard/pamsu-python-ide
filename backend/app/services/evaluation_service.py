from typing import Any

from sqlalchemy.orm import Session

from app.models.domain_models import (
    ASTAnalysis,
    SimilarityResult,
    Submission,
    Task,
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


# REVIEW BOUNDARY:
# AST and similarity results are automated review indicators only.
# They must never assign the official grade or automatically declare
# plagiarism, copying, cheating, or academic misconduct.

# PARTNER INTEGRATION:
# This service performs static AST and similarity analysis only. It must not
# execute submitted Python source code. The partner-owned isolated worker
# remains responsible for actual Python execution and resource enforcement.
