from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.evaluation_schema import (
    InstructorGradeUpdate,
    ReleasedInstructorGradeResponse,
    StudentSubmissionEvaluationResponse,
)
from app.services.ast_evaluator import (
    evaluate_ast_details,
)


def test_ast_evaluator_catches_syntax_errors():
    """
    Static analysis must return a structured syntax-error result
    instead of crashing the API process.
    """

    raw_code = "print('missing closing quote)"
    rules = {
        "require_print_call": True,
    }

    result = evaluate_ast_details(
        raw_code,
        rules,
    )

    assert result["passed"] is False
    assert result["syntax_error"] is not None
    assert result["syntax_error"]["line"] is not None


def test_ast_evaluator_validates_required_rules():
    """
    Static analysis must detect configured Python structures.
    """

    raw_code = "for i in range(5):\n    print(i)"

    rules = {
        "require_for_loop": {
            "required": True,
            "min_count": 1,
        },
        "require_print_call": True,
    }

    result = evaluate_ast_details(
        raw_code,
        rules,
    )

    assert result["passed"] is True
    assert result["missing_requirements"] == []

    assert result["detected_nodes"]["require_for_loop"] >= 1


def test_ast_evaluator_never_executes_source_code(
    tmp_path,
):
    """
    Static AST analysis must never execute submitted Python.

    The submitted source would create a sentinel file if executed.
    Parsing and AST inspection must leave the file system unchanged.
    """

    sentinel_file = tmp_path / "ast-evaluator-executed.txt"

    raw_code = (
        "from pathlib import Path\n"
        f"Path({str(sentinel_file)!r}).write_text("
        "'executed', encoding='utf-8')\n"
    )

    rules = {
        "require_import": True,
    }

    result = evaluate_ast_details(
        raw_code,
        rules,
    )

    assert result["passed"] is True
    assert result["syntax_error"] is None
    assert sentinel_file.exists() is False


def test_ast_evaluator_handles_configuration_errors():
    """
    Invalid AST-rule configuration must be reported safely.
    """

    raw_code = "print('hello')"

    rules = {
        "require_print_call": ("invalid_config"),
    }

    result = evaluate_ast_details(
        raw_code,
        rules,
    )

    assert result["passed"] is False

    assert len(result["configuration_errors"]) > 0


def test_student_response_rejects_instructor_only_analytics():
    """
    Student-facing schemas must reject full AST and similarity data.
    """

    payload = {
        "sub_id": 1,
        "task_id": 10,
        "status": "awaiting_review",
        "is_official": True,
        "submitted_at": datetime.now(timezone.utc),
        "accepted_at": datetime.now(timezone.utc),
        "instructor_grade": None,
        "ast_analyses": [],
        "similarity_results_as_source": [],
    }

    with pytest.raises(ValidationError):
        StudentSubmissionEvaluationResponse.model_validate(payload)


def test_student_grade_schema_requires_released_grade():
    """
    A student-grade response must never represent an unreleased grade.
    """

    payload = {
        "score": 90,
        "max_score": 100,
        "feedback": "Draft feedback.",
        "is_released": False,
        "released_at": datetime.now(timezone.utc),
    }

    with pytest.raises(ValidationError):
        ReleasedInstructorGradeResponse.model_validate(payload)


def test_empty_grade_patch_is_rejected_by_schema():
    """
    Manual-grade PATCH requests must contain at least one field.
    """

    with pytest.raises(ValidationError):
        InstructorGradeUpdate()
