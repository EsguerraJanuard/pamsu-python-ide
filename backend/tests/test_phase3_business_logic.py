import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.core.system_settings import (
    DEFAULT_SYSTEM_SETTINGS,
    get_all_system_settings,
    get_system_setting,
    set_system_setting,
)
from app.models.domain_models import Classroom, CodingSession, SystemSetting, Task, User
from app.routers.admin import delete_user, toggle_user_status
from app.schemas.execution_schema import (
    PartnerExecutionResultUpdate,
    is_execution_status_transition_allowed,
)
from app.services.ast_analyzer import analyze_reference_solution
from app.services.ast_evaluator import evaluate_ast
from app.services.coding_session_service import start_or_resume_student_coding_session
from app.services.jaccard import calculate_jaccard_details
from app.services.submission_service import (
    SubmissionTaskUnavailableError,
    create_student_submission,
)
from fastapi import HTTPException


def test_ast_rule_keys_harmonized():
    code = """
def sample_func():
    pass

class SampleClass:
    pass
"""
    analysis = analyze_reference_solution(code)
    suggested = analysis["suggested_ast_rules"]
    assert "require_function_def" in suggested
    assert "require_class_def" in suggested
    assert suggested["require_function_def"]["required"] is True
    assert suggested["require_class_def"]["required"] is True

    # Evaluator backward-compatibility aliases
    assert evaluate_ast(
        raw_code=code,
        rules={"require_function": True, "require_class": True},
    ) is True


def test_execution_status_running_self_transition_allowed():
    assert is_execution_status_transition_allowed(
        current_status="running",
        next_status="running",
    ) is True


def test_execution_completed_with_nonzero_exit_code_allowed():
    now = datetime.now(timezone.utc)
    callback = PartnerExecutionResultUpdate(
        execution_id="11111111-1111-1111-1111-111111111111",
        correlation_id="22222222-2222-2222-2222-222222222222",
        update_id="33333333-3333-3333-3333-333333333333",
        sequence_number=2,
        worker_task_id="task-123",
        status="completed",
        exit_code=1,
        completed_at=now,
    )
    assert callback.status == "completed"
    assert callback.exit_code == 1


def test_jaccard_similarity_symmetric_comparison():
    valid_code = "def add(a, b):\n    return a + b"
    syntax_error_code = "def add(a, b\n    return a + b"

    # Should not crash, and should not compare AST node types to lexical tokens
    result = calculate_jaccard_details(valid_code, syntax_error_code)
    assert isinstance(result["score"], float)
    assert 0.0 <= result["score"] <= 100.0
    # Because both fall back to lexical tokens, similarity is high!
    assert result["score"] > 50.0


def test_system_settings_persistence(db_session):
    # Initial read
    assert get_system_setting(db_session, "maintenance_mode") is False

    # Update setting
    set_system_setting(db_session, "maintenance_mode", True)
    assert get_system_setting(db_session, "maintenance_mode") is True

    # Read all settings
    all_settings = get_all_system_settings(db_session)
    assert all_settings["maintenance_mode"] is True
    assert all_settings["default_ast_strictness"] == "moderate"


def test_admin_cannot_deactivate_or_delete_self(db_session):
    admin_user = User(
        email="admin_self_test@pampangastateu.edu.ph",
        name="Admin Test",
        role="admin",
        password_hash="hash",
        school_id="ADM0000001",
        email_verified=True,
        is_active=True,
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)

    with pytest.raises(HTTPException) as exc_info:
        toggle_user_status(
            user_id=admin_user.user_id,
            db=db_session,
            current_admin=admin_user,
        )
    assert exc_info.value.status_code == 400
    assert "Cannot modify own admin account" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        delete_user(
            user_id=admin_user.user_id,
            db=db_session,
            current_admin=admin_user,
        )
    assert exc_info.value.status_code == 400
    assert "Cannot delete own admin account" in exc_info.value.detail


def test_guest_login_enrolls_into_sandbox(db_session):
    from app.routers.auth import login_guest
    from app.models.domain_models import Enrollment

    instructor = User(
        email="instructor_sandbox@pampangastateu.edu.ph",
        name="Instructor Sandbox",
        role="instructor",
        password_hash="hash",
        school_id="INS0000001",
        email_verified=True,
        is_active=True,
    )
    db_session.add(instructor)
    db_session.commit()

    token_resp = login_guest(db=db_session)
    assert token_resp.user.role == "student"

    sandbox = db_session.query(Classroom).filter(Classroom.class_code == "SANDBOX01").first()
    assert sandbox is not None
    assert sandbox.name == "Guest Sandbox Classroom"


def test_deadline_enforcement_on_submission(db_session):
    from app.models.domain_models import Enrollment
    from app.schemas.submission_schema import SubmissionCreate

    instructor = User(
        email="inst_due@pampangastateu.edu.ph",
        name="Inst Due",
        role="instructor",
        password_hash="hash",
        school_id="INS0000002",
        email_verified=True,
        is_active=True,
    )
    student = User(
        email="stud_due@pampangastateu.edu.ph",
        name="Stud Due",
        role="student",
        password_hash="hash",
        school_id="STU0000002",
        email_verified=True,
        is_active=True,
    )
    db_session.add_all([instructor, student])
    db_session.commit()

    classroom = Classroom(
        name="Due Class",
        subject_code="CS101",
        section="A",
        class_code="DUECLASS01",
        instructor_id=instructor.user_id,
        is_active=True,
    )
    db_session.add(classroom)
    db_session.commit()

    enrollment = Enrollment(
        class_id=classroom.class_id,
        student_id=student.user_id,
        status="active",
    )
    past_due = datetime.now(timezone.utc) - timedelta(hours=2)
    task = Task(
        class_id=classroom.class_id,
        instructor_id=instructor.user_id,
        title="Due Task",
        description="Desc",
        due_at=past_due,
        is_published=True,
        is_graded=True,
    )
    db_session.add_all([enrollment, task])
    db_session.commit()

    with pytest.raises(SubmissionTaskUnavailableError) as exc_info:
        create_student_submission(
            db=db_session,
            student_id=student.user_id,
            payload=SubmissionCreate(
                task_id=task.task_id,
                raw_code="print('hello')",
            ),
        )
    assert "deadline has passed" in str(exc_info.value).lower()
