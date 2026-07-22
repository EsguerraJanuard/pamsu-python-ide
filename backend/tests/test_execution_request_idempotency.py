from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.domain_models import (
    Classroom,
    CodingSession,
    Enrollment,
    ExecutionRequest,
    Task,
    User,
)
from app.schemas.execution_schema import (
    ExecutionRequestCreate,
    StudentExecutionResponse,
)
from app.services.execution_service import (
    ExecutionRequestIdempotencyConflictError,
    ExecutionRequestIdempotencyInvalidError,
    create_student_execution_request,
)


def create_execution_context(
    db_session: Session,
    *,
    suffix: str,
) -> dict:
    instructor = User(
        name=f"Execution Instructor {suffix}",
        school_id=f"91{int(suffix):08d}",
        email=(f"execution.instructor.{suffix}@pampangastateu.edu.ph"),
        role="instructor",
        password_hash="fakehash",
        email_verified=True,
        is_active=True,
    )

    student = User(
        name=f"Execution Student {suffix}",
        school_id=f"92{int(suffix):08d}",
        email=(f"execution.student.{suffix}@pampangastateu.edu.ph"),
        role="student",
        password_hash="fakehash",
        email_verified=True,
        is_active=True,
    )

    db_session.add_all(
        [
            instructor,
            student,
        ]
    )
    db_session.flush()

    classroom = Classroom(
        instructor_id=instructor.user_id,
        name=f"Execution Class {suffix}",
        subject_code="CS-IDEMP",
        section=f"Section {suffix}",
        class_code=f"IDEMP{suffix}",
        is_active=True,
    )

    db_session.add(classroom)
    db_session.flush()

    enrollment = Enrollment(
        class_id=classroom.class_id,
        student_id=student.user_id,
        status="active",
    )

    task = Task(
        class_id=classroom.class_id,
        instructor_id=instructor.user_id,
        title=f"Execution Task {suffix}",
        description="Student execution idempotency test.",
        activity_type="laboratory",
        required_ast_rules={},
        starter_code="",
        paste_policy="internal_only",
        is_graded=True,
        is_published=True,
    )

    db_session.add_all(
        [
            enrollment,
            task,
        ]
    )
    db_session.flush()

    coding_session = CodingSession(
        session_id=str(uuid4()),
        student_id=student.user_id,
        task_id=task.task_id,
        run_attempt_count=0,
    )

    db_session.add(coding_session)
    db_session.commit()

    db_session.refresh(student)
    db_session.refresh(task)
    db_session.refresh(coding_session)

    return {
        "student_id": student.user_id,
        "task_id": task.task_id,
        "coding_session_id": coding_session.session_id,
    }


def create_run_payload(
    context: dict,
    *,
    source_code: str = "print('idempotent execution')\n",
    standard_input: str = "",
) -> ExecutionRequestCreate:
    return ExecutionRequestCreate(
        request_kind="run",
        task_id=context["task_id"],
        coding_session_id=context["coding_session_id"],
        source_code=source_code,
        standard_input=standard_input,
    )


def test_execution_request_without_idempotency_key_creates_new_rows(
    db_session: Session,
) -> None:
    context = create_execution_context(
        db_session,
        suffix="1",
    )

    payload = create_run_payload(context)

    first_request = create_student_execution_request(
        db_session,
        student_id=context["student_id"],
        payload=payload,
    )

    second_request = create_student_execution_request(
        db_session,
        student_id=context["student_id"],
        payload=payload,
    )

    assert first_request.execution_id != second_request.execution_id

    assert first_request.request_idempotency_key is None
    assert first_request.request_payload_digest is None

    assert second_request.request_idempotency_key is None
    assert second_request.request_payload_digest is None

    execution_count = (
        db_session.query(ExecutionRequest)
        .filter(
            ExecutionRequest.student_id == context["student_id"],
        )
        .count()
    )

    coding_session = (
        db_session.query(CodingSession)
        .filter(
            CodingSession.session_id == context["coding_session_id"],
        )
        .one()
    )

    assert execution_count == 2
    assert coding_session.run_attempt_count == 2


def test_same_idempotency_key_and_payload_returns_existing_request(
    db_session: Session,
) -> None:
    context = create_execution_context(
        db_session,
        suffix="2",
    )

    idempotency_key = str(uuid4()).upper()
    normalized_key = str(UUID(idempotency_key))

    payload = create_run_payload(context)

    first_request = create_student_execution_request(
        db_session,
        student_id=context["student_id"],
        payload=payload,
        request_idempotency_key=idempotency_key,
    )

    second_request = create_student_execution_request(
        db_session,
        student_id=context["student_id"],
        payload=payload,
        request_idempotency_key=idempotency_key,
    )

    assert second_request.execution_id == first_request.execution_id

    assert first_request.request_idempotency_key == normalized_key
    assert second_request.request_idempotency_key == normalized_key

    assert first_request.request_payload_digest is not None
    assert len(first_request.request_payload_digest) == 64

    assert second_request.request_payload_digest == first_request.request_payload_digest

    execution_count = (
        db_session.query(ExecutionRequest)
        .filter(
            ExecutionRequest.student_id == context["student_id"],
            ExecutionRequest.request_idempotency_key == normalized_key,
        )
        .count()
    )

    coding_session = (
        db_session.query(CodingSession)
        .filter(
            CodingSession.session_id == context["coding_session_id"],
        )
        .one()
    )

    assert execution_count == 1
    assert coding_session.run_attempt_count == 1


def test_reused_idempotency_key_with_different_source_is_rejected(
    db_session: Session,
) -> None:
    context = create_execution_context(
        db_session,
        suffix="3",
    )

    idempotency_key = str(uuid4())

    first_payload = create_run_payload(
        context,
        source_code="print('first content')\n",
    )

    conflicting_payload = create_run_payload(
        context,
        source_code="print('different content')\n",
    )

    first_request = create_student_execution_request(
        db_session,
        student_id=context["student_id"],
        payload=first_payload,
        request_idempotency_key=idempotency_key,
    )

    with pytest.raises(
        ExecutionRequestIdempotencyConflictError,
        match="already used",
    ):
        create_student_execution_request(
            db_session,
            student_id=context["student_id"],
            payload=conflicting_payload,
            request_idempotency_key=idempotency_key,
        )

    execution_requests = (
        db_session.query(ExecutionRequest)
        .filter(
            ExecutionRequest.student_id == context["student_id"],
            ExecutionRequest.request_idempotency_key == idempotency_key,
        )
        .all()
    )

    coding_session = (
        db_session.query(CodingSession)
        .filter(
            CodingSession.session_id == context["coding_session_id"],
        )
        .one()
    )

    assert len(execution_requests) == 1
    assert execution_requests[0].execution_id == first_request.execution_id
    assert coding_session.run_attempt_count == 1


def test_reused_idempotency_key_with_different_input_is_rejected(
    db_session: Session,
) -> None:
    context = create_execution_context(
        db_session,
        suffix="4",
    )

    idempotency_key = str(uuid4())

    first_payload = create_run_payload(
        context,
        standard_input="first input\n",
    )

    conflicting_payload = create_run_payload(
        context,
        standard_input="different input\n",
    )

    create_student_execution_request(
        db_session,
        student_id=context["student_id"],
        payload=first_payload,
        request_idempotency_key=idempotency_key,
    )

    with pytest.raises(
        ExecutionRequestIdempotencyConflictError,
        match="already used",
    ):
        create_student_execution_request(
            db_session,
            student_id=context["student_id"],
            payload=conflicting_payload,
            request_idempotency_key=idempotency_key,
        )

    execution_count = (
        db_session.query(ExecutionRequest)
        .filter(
            ExecutionRequest.student_id == context["student_id"],
        )
        .count()
    )

    coding_session = (
        db_session.query(CodingSession)
        .filter(
            CodingSession.session_id == context["coding_session_id"],
        )
        .one()
    )

    assert execution_count == 1
    assert coding_session.run_attempt_count == 1


@pytest.mark.parametrize(
    "invalid_key",
    [
        "",
        "not-a-uuid",
        "12345",
        "00000000-0000-0000-0000",
    ],
)
def test_invalid_execution_request_idempotency_key_is_rejected(
    db_session: Session,
    invalid_key: str,
) -> None:
    context = create_execution_context(
        db_session,
        suffix="5",
    )

    with pytest.raises(
        ExecutionRequestIdempotencyInvalidError,
        match="valid UUID",
    ):
        create_student_execution_request(
            db_session,
            student_id=context["student_id"],
            payload=create_run_payload(context),
            request_idempotency_key=invalid_key,
        )

    execution_count = (
        db_session.query(ExecutionRequest)
        .filter(
            ExecutionRequest.student_id == context["student_id"],
        )
        .count()
    )

    coding_session = (
        db_session.query(CodingSession)
        .filter(
            CodingSession.session_id == context["coding_session_id"],
        )
        .one()
    )

    assert execution_count == 0
    assert coding_session.run_attempt_count == 0


def test_same_key_is_scoped_to_authenticated_student(
    db_session: Session,
) -> None:
    first_context = create_execution_context(
        db_session,
        suffix="6",
    )

    second_context = create_execution_context(
        db_session,
        suffix="7",
    )

    shared_key = str(uuid4())

    first_request = create_student_execution_request(
        db_session,
        student_id=first_context["student_id"],
        payload=create_run_payload(first_context),
        request_idempotency_key=shared_key,
    )

    second_request = create_student_execution_request(
        db_session,
        student_id=second_context["student_id"],
        payload=create_run_payload(second_context),
        request_idempotency_key=shared_key,
    )

    assert first_request.execution_id != second_request.execution_id
    assert first_request.student_id != second_request.student_id

    assert first_request.request_idempotency_key == shared_key
    assert second_request.request_idempotency_key == shared_key

    execution_count = (
        db_session.query(ExecutionRequest)
        .filter(
            ExecutionRequest.request_idempotency_key == shared_key,
        )
        .count()
    )

    assert execution_count == 2


def test_student_execution_response_excludes_idempotency_metadata(
    db_session: Session,
) -> None:
    context = create_execution_context(
        db_session,
        suffix="8",
    )

    execution_request = create_student_execution_request(
        db_session,
        student_id=context["student_id"],
        payload=create_run_payload(context),
        request_idempotency_key=str(uuid4()),
    )

    response = StudentExecutionResponse.model_validate(
        execution_request,
    )

    response_data = response.model_dump()

    assert "request_idempotency_key" not in response_data
    assert "request_payload_digest" not in response_data
    assert "dispatch_idempotency_key" not in response_data
    assert "correlation_id" not in response_data
    assert "worker_task_id" not in response_data


# EXECUTION BOUNDARY:
# These tests verify database persistence and retry behavior only.
# They never execute student Python inside FastAPI or the host system.

# IDEMPOTENCY BOUNDARY:
# One student and one UUID key identify one logical execution request.
# Identical retries return the existing row. Conflicting payloads are
# rejected. Different students may independently reuse the same UUID.

# TELEMETRY BOUNDARY:
# Safe retries do not create duplicate execution rows and do not increment
# the coding-session run-attempt counter more than once.

# PRIVACY BOUNDARY:
# Student-facing execution responses exclude request idempotency metadata,
# partner dispatch identifiers, correlation identifiers, and worker IDs.
