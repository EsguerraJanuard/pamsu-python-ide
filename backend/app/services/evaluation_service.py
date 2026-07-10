from typing import Any

from sqlalchemy.orm import Session

from app.models.domain_models import Submission, Task
from app.services.ast_evaluator import evaluate_ast_details
from app.services.jaccard import find_highest_similarity


class SubmissionNotFoundError(Exception):
    pass


class TaskNotFoundError(Exception):
    pass


def evaluate_submission_by_id(db: Session, sub_id: int) -> dict[str, Any]:
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

    ast_pass_fail = bool(ast_details["passed"])

    other_submissions = (
        db.query(Submission)
        .filter(
            Submission.task_id == submission.task_id,
            Submission.sub_id != submission.sub_id,
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

    highest_jaccard_score = float(jaccard_details["highest_score"])

    submission.ast_pass_fail = ast_pass_fail
    submission.jaccard_score = highest_jaccard_score

    db.add(submission)
    db.commit()
    db.refresh(submission)

    return {
        "sub_id": submission.sub_id,
        "student_id": submission.student_id,
        "task_id": submission.task_id,
        "ast_pass_fail": submission.ast_pass_fail,
        "jaccard_score": submission.jaccard_score,
        "highest_match_sub_id": jaccard_details["highest_match_sub_id"],
        "ast_details": ast_details,
        "jaccard_details": jaccard_details,
    }
