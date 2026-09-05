from collections import Counter
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

import app.services.classroom_service as classroom_service_module
import app.services.evaluation_service as evaluation_service_module
import app.services.submission_service as submission_service_module
from app.models.domain_models import (
    AuditRecord,
    Classroom,
    Enrollment,
    InstructorGrade,
    Submission,
    Task,
    User,
)
from app.schemas.classroom_schema import (
    ClassroomCreate,
    ClassroomUpdate,
)
from app.schemas.enrollment_schema import EnrollmentJoinRequest
from app.schemas.evaluation_schema import (
    InstructorGradeCreate,
    InstructorGradeUpdate,
)
from app.schemas.submission_schema import SubmissionCreate
from app.schemas.task_schema import (
    TaskCreate,
    TaskUpdate,
)
from app.services.audit_service import AuditServiceError
from app.services.classroom_service import (
    ClassroomAuditWorkflowError,
    create_classroom,
    join_classroom,
    update_classroom,
    update_enrollment_status,
)
from app.services.evaluation_service import (
    GradeAuditWorkflowError,
    create_or_update_grade,
    patch_grade,
)
from app.services.submission_service import (
    SubmissionAuditWorkflowError,
    create_student_submission,
)
from app.services.task_service import (
    create_task,
    set_task_publication,
    update_task,
)


PROHIBITED_AUDIT_KEYS = {
    "password",
    "password_hash",
    "otp",
    "otp_code",
    "raw_code",
    "source_code",
    "starter_code",
    "standard_input",
    "stdin",
    "hidden_test",
    "hidden_tests",
    "hidden_test_case",
    "hidden_test_cases",
    "expected_output",
    "stdout",
    "stderr",
    "execution_output",
    "ast",
    "ast_details",
    "ast_findings",
    "required_ast_rules",
    "similarity",
    "similarity_score",
    "similarity_details",
    "clipboard",
    "clipboard_content",
    "paste_content",
    "pasted_text",
    "keystrokes",
    "browsing_history",
    "screen_recording",
    "webcam",
    "microphone",
    "misconduct_verdict",
    "cheating_verdict",
    "plagiarism_verdict",
    "score",
    "max_score",
    "feedback",
}


def _create_user(
    db: Session,
    *,
    name: str,
    school_id: str,
    email: str,
    role: str,
) -> User:
    user = User(
        name=name,
        school_id=school_id,
        email=email,
        role=role,
        password_hash="fakehash",
        email_verified=True,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _assert_privacy_safe(value) -> None:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            assert _normalize_key(key) not in PROHIBITED_AUDIT_KEYS
            _assert_privacy_safe(nested_value)
        return

    if isinstance(value, list):
        for item in value:
            _assert_privacy_safe(item)


def _audit_rows(
    db: Session,
    *,
    resource_type: str | None = None,
    resource_id: int | str | None = None,
) -> list[AuditRecord]:
    query = db.query(AuditRecord)

    if resource_type is not None:
        query = query.filter(
            AuditRecord.resource_type == resource_type,
        )

    if resource_id is not None:
        query = query.filter(
            AuditRecord.resource_id == str(resource_id),
        )

    return query.order_by(
        AuditRecord.created_at.asc(),
        AuditRecord.audit_id.asc(),
    ).all()


def _create_direct_submission_context(
    db: Session,
    *,
    prefix: str,
) -> dict[str, object]:
    instructor = _create_user(
        db,
        name=f"{prefix} Instructor",
        school_id=f"91{prefix[-1]}0000001",
        email=(f"{prefix.lower()}.instructor@pampangastateu.edu.ph"),
        role="instructor",
    )

    student = _create_user(
        db,
        name=f"{prefix} Student",
        school_id=f"92{prefix[-1]}0000001",
        email=(f"{prefix.lower()}.student@pampangastateu.edu.ph"),
        role="student",
    )

    classroom = Classroom(
        instructor_id=instructor.user_id,
        name=f"{prefix} Classroom",
        subject_code="AUD-101",
        section=prefix,
        class_code=f"AUD{prefix[-1]}0001",
        is_active=True,
        archived_at=None,
    )

    db.add(classroom)
    db.flush()

    enrollment = Enrollment(
        class_id=classroom.class_id,
        student_id=student.user_id,
        status="active",
        deactivated_at=None,
    )

    task = Task(
        class_id=classroom.class_id,
        instructor_id=instructor.user_id,
        title=f"{prefix} Activity",
        description="Private activity description",
        instructions="Private activity instructions",
        activity_type="laboratory",
        required_ast_rules={
            "require_print_call": True,
        },
        starter_code="PRIVATE_STARTER_CODE",
        paste_policy="internal_only",
        is_graded=True,
        is_published=True,
        due_at=None,
        published_at=datetime.now(timezone.utc),
    )

    db.add_all(
        [
            enrollment,
            task,
        ]
    )
    db.commit()
    db.refresh(classroom)
    db.refresh(enrollment)
    db.refresh(task)

    return {
        "instructor": instructor,
        "student": student,
        "classroom": classroom,
        "enrollment": enrollment,
        "task": task,
    }


def test_classroom_and_enrollment_actions_create_audit_records(
    db_session: Session,
):
    instructor = _create_user(
        db_session,
        name="Audit Classroom Instructor",
        school_id="9010000001",
        email=("audit.classroom.instructor@pampangastateu.edu.ph"),
        role="instructor",
    )

    student = _create_user(
        db_session,
        name="Audit Classroom Student",
        school_id="9020000001",
        email=("audit.classroom.student@pampangastateu.edu.ph"),
        role="student",
    )

    classroom = create_classroom(
        db=db_session,
        instructor_id=instructor.user_id,
        classroom_data=ClassroomCreate(
            name="Audit Trail Classroom",
            subject_code="AUD-201",
            section="A1",
        ),
    )

    enrollment = join_classroom(
        db=db_session,
        student_id=student.user_id,
        enrollment_data=EnrollmentJoinRequest(
            class_code=classroom.class_code,
        ),
    )

    update_enrollment_status(
        db=db_session,
        enrollment_id=enrollment.enrollment_id,
        instructor_id=instructor.user_id,
        new_status="disabled",
    )

    classroom_audits = _audit_rows(
        db_session,
        resource_type="classroom",
        resource_id=classroom.class_id,
    )

    enrollment_audits = _audit_rows(
        db_session,
        resource_type="enrollment",
        resource_id=enrollment.enrollment_id,
    )

    assert [record.action_type for record in classroom_audits] == [
        "classroom_created",
    ]

    assert Counter(record.action_type for record in enrollment_audits) == Counter(
        {
            "student_enrolled": 1,
            "enrollment_status_changed": 1,
        }
    )

    enrollment_audit_by_action = {
        record.action_type: record for record in enrollment_audits
    }

    student_enrolled_audit = enrollment_audit_by_action["student_enrolled"]

    enrollment_status_audit = enrollment_audit_by_action["enrollment_status_changed"]

    assert classroom_audits[0].actor_user_id == instructor.user_id
    assert student_enrolled_audit.actor_user_id == student.user_id
    assert enrollment_status_audit.actor_user_id == instructor.user_id

    assert "class_code" not in classroom_audits[0].audit_data
    assert enrollment_status_audit.audit_data == {
        "class_id": classroom.class_id,
        "student_id": student.user_id,
        "previous_status": "active",
        "new_status": "disabled",
    }

    for record in classroom_audits + enrollment_audits:
        _assert_privacy_safe(record.audit_data)


def test_classroom_lifecycle_audits_only_meaningful_transitions(
    db_session: Session,
):
    instructor = _create_user(
        db_session,
        name="Audit Lifecycle Instructor",
        school_id="9010000002",
        email=("audit.lifecycle.instructor@pampangastateu.edu.ph"),
        role="instructor",
    )

    classroom = create_classroom(
        db=db_session,
        instructor_id=instructor.user_id,
        classroom_data=ClassroomCreate(
            name="Original Classroom",
            subject_code="AUD-202",
            section="A2",
        ),
    )

    update_classroom(
        db=db_session,
        class_id=classroom.class_id,
        instructor_id=instructor.user_id,
        classroom_data=ClassroomUpdate(
            name="Renamed Classroom",
        ),
    )

    count_after_update = len(
        _audit_rows(
            db_session,
            resource_type="classroom",
            resource_id=classroom.class_id,
        )
    )

    update_classroom(
        db=db_session,
        class_id=classroom.class_id,
        instructor_id=instructor.user_id,
        classroom_data=ClassroomUpdate(
            name="Renamed Classroom",
        ),
    )

    assert (
        len(
            _audit_rows(
                db_session,
                resource_type="classroom",
                resource_id=classroom.class_id,
            )
        )
        == count_after_update
    )

    archived = update_classroom(
        db=db_session,
        class_id=classroom.class_id,
        instructor_id=instructor.user_id,
        classroom_data=ClassroomUpdate(
            is_active=False,
        ),
    )

    assert archived.is_active is False
    assert archived.archived_at is not None

    count_after_archive = len(
        _audit_rows(
            db_session,
            resource_type="classroom",
            resource_id=classroom.class_id,
        )
    )

    repeated_archive = update_classroom(
        db=db_session,
        class_id=classroom.class_id,
        instructor_id=instructor.user_id,
        classroom_data=ClassroomUpdate(
            is_active=False,
        ),
    )

    assert repeated_archive.archived_at == archived.archived_at

    assert (
        len(
            _audit_rows(
                db_session,
                resource_type="classroom",
                resource_id=classroom.class_id,
            )
        )
        == count_after_archive
    )

    reactivated = update_classroom(
        db=db_session,
        class_id=classroom.class_id,
        instructor_id=instructor.user_id,
        classroom_data=ClassroomUpdate(
            is_active=True,
        ),
    )

    assert reactivated.is_active is True
    assert reactivated.archived_at is None

    actions = [
        record.action_type
        for record in _audit_rows(
            db_session,
            resource_type="classroom",
            resource_id=classroom.class_id,
        )
    ]

    assert Counter(actions) == Counter(
        {
            "classroom_created": 1,
            "classroom_updated": 1,
            "classroom_archived": 1,
            "classroom_reactivated": 1,
        }
    )


def test_activity_lifecycle_creates_privacy_safe_audits(
    db_session: Session,
):
    instructor = _create_user(
        db_session,
        name="Audit Activity Instructor",
        school_id="9010000003",
        email=("audit.activity.instructor@pampangastateu.edu.ph"),
        role="instructor",
    )

    classroom = create_classroom(
        db=db_session,
        instructor_id=instructor.user_id,
        classroom_data=ClassroomCreate(
            name="Audit Activity Classroom",
            subject_code="AUD-203",
            section="A3",
        ),
    )

    task = create_task(
        db=db_session,
        instructor_id=instructor.user_id,
        target_class_id=classroom.class_id,
        task_data=TaskCreate.model_construct(
            class_ids=[classroom.class_id],
            title="Private Activity Title",
            description="PRIVATE DESCRIPTION",
            instructions="PRIVATE INSTRUCTIONS",
            activity_type="laboratory",
            required_ast_rules={
                "require_for_loop": True,
            },
            starter_code="PRIVATE_STARTER_CODE",
            paste_policy="internal_only",
            is_graded=True,
            due_at=None,
        ),
    )

    update_task(
        db=db_session,
        task_id=task.task_id,
        instructor_id=instructor.user_id,
        task_data=TaskUpdate.model_construct(
            title="Updated Private Activity Title",
        ),
    )

    count_after_update = len(
        _audit_rows(
            db_session,
            resource_type="task",
            resource_id=task.task_id,
        )
    )

    update_task(
        db=db_session,
        task_id=task.task_id,
        instructor_id=instructor.user_id,
        task_data=TaskUpdate.model_construct(
            title="Updated Private Activity Title",
        ),
    )

    assert (
        len(
            _audit_rows(
                db_session,
                resource_type="task",
                resource_id=task.task_id,
            )
        )
        == count_after_update
    )

    set_task_publication(
        db=db_session,
        task_id=task.task_id,
        instructor_id=instructor.user_id,
        is_published=True,
    )

    count_after_publish = len(
        _audit_rows(
            db_session,
            resource_type="task",
            resource_id=task.task_id,
        )
    )

    set_task_publication(
        db=db_session,
        task_id=task.task_id,
        instructor_id=instructor.user_id,
        is_published=True,
    )

    assert (
        len(
            _audit_rows(
                db_session,
                resource_type="task",
                resource_id=task.task_id,
            )
        )
        == count_after_publish
    )

    set_task_publication(
        db=db_session,
        task_id=task.task_id,
        instructor_id=instructor.user_id,
        is_published=False,
    )

    audits = _audit_rows(
        db_session,
        resource_type="task",
        resource_id=task.task_id,
    )

    assert Counter(record.action_type for record in audits) == Counter(
        {
            "activity_created": 1,
            "activity_updated": 1,
            "activity_published": 1,
            "activity_unpublished": 1,
        }
    )

    serialized_metadata = repr([record.audit_data for record in audits])

    assert "PRIVATE DESCRIPTION" not in serialized_metadata
    assert "PRIVATE INSTRUCTIONS" not in serialized_metadata
    assert "PRIVATE_STARTER_CODE" not in serialized_metadata
    assert "Private Activity Title" not in serialized_metadata

    for record in audits:
        _assert_privacy_safe(record.audit_data)


def test_submission_creation_creates_one_privacy_safe_audit(
    db_session: Session,
):
    context = _create_direct_submission_context(
        db_session,
        prefix="Submission1",
    )

    student = context["student"]
    task = context["task"]

    submission = create_student_submission(
        db_session,
        student_id=student.user_id,
        payload=SubmissionCreate.model_construct(
            task_id=task.task_id,
            coding_session_id=None,
            raw_code="PRIVATE SUBMITTED SOURCE",
            standard_input="PRIVATE STANDARD INPUT",
        ),
    )

    audits = _audit_rows(
        db_session,
        resource_type="submission",
        resource_id=submission.sub_id,
    )

    assert len(audits) == 1
    assert audits[0].action_type == "submission_created"
    assert audits[0].actor_user_id == student.user_id
    assert audits[0].audit_data == {
        "task_id": task.task_id,
        "class_id": task.class_id,
        "attempt_number": 1,
        "submission_status": "submitted",
        "is_official": True,
    }

    serialized_metadata = repr(audits[0].audit_data)

    assert "PRIVATE SUBMITTED SOURCE" not in serialized_metadata
    assert "PRIVATE STANDARD INPUT" not in serialized_metadata

    _assert_privacy_safe(audits[0].audit_data)


def test_grade_lifecycle_creates_separate_accountability_records(
    db_session: Session,
):
    context = _create_direct_submission_context(
        db_session,
        prefix="Grade2",
    )

    instructor = context["instructor"]
    student = context["student"]
    task = context["task"]

    submission = Submission(
        student_id=student.user_id,
        task_id=task.task_id,
        coding_session_id=None,
        attempt_number=1,
        raw_code="PRIVATE GRADE SOURCE",
        standard_input="PRIVATE GRADE INPUT",
        status="submitted",
        is_official=True,
        accepted_at=datetime.now(timezone.utc),
    )

    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)

    grade = create_or_update_grade(
        db_session,
        sub_id=submission.sub_id,
        grade_in=InstructorGradeCreate.model_construct(
            score=80.0,
            max_score=100.0,
            feedback="PRIVATE INITIAL FEEDBACK",
            is_released=False,
        ),
        current_user=instructor,
    )

    patch_grade(
        db_session,
        sub_id=submission.sub_id,
        grade_update=InstructorGradeUpdate.model_construct(
            feedback="PRIVATE UPDATED FEEDBACK",
        ),
        current_user=instructor,
    )

    count_before_release = len(
        _audit_rows(
            db_session,
            resource_type="grade",
            resource_id=grade.grade_id,
        )
    )

    released_grade = patch_grade(
        db_session,
        sub_id=submission.sub_id,
        grade_update=InstructorGradeUpdate.model_construct(
            is_released=True,
        ),
        current_user=instructor,
    )

    assert released_grade.is_released is True

    count_after_release = len(
        _audit_rows(
            db_session,
            resource_type="grade",
            resource_id=grade.grade_id,
        )
    )

    assert count_after_release == count_before_release + 2

    patch_grade(
        db_session,
        sub_id=submission.sub_id,
        grade_update=InstructorGradeUpdate.model_construct(
            is_released=True,
        ),
        current_user=instructor,
    )

    audits = _audit_rows(
        db_session,
        resource_type="grade",
        resource_id=grade.grade_id,
    )

    assert Counter(record.action_type for record in audits) == Counter(
        {
            "grade_created": 1,
            "grade_updated": 2,
            "grade_released": 1,
        }
    )

    serialized_metadata = repr([record.audit_data for record in audits])

    assert "80.0" not in serialized_metadata
    assert "100.0" not in serialized_metadata
    assert "PRIVATE INITIAL FEEDBACK" not in serialized_metadata
    assert "PRIVATE UPDATED FEEDBACK" not in serialized_metadata

    for record in audits:
        _assert_privacy_safe(record.audit_data)


def test_classroom_creation_rolls_back_when_audit_fails(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    instructor = _create_user(
        db_session,
        name="Rollback Classroom Instructor",
        school_id="9010000004",
        email=("rollback.classroom.instructor@pampangastateu.edu.ph"),
        role="instructor",
    )

    def fail_audit(*args, **kwargs):
        raise AuditServiceError("Forced audit failure.")

    monkeypatch.setattr(
        classroom_service_module,
        "create_audit_record",
        fail_audit,
    )

    with pytest.raises(
        ClassroomAuditWorkflowError,
        match="accountability record",
    ):
        create_classroom(
            db=db_session,
            instructor_id=instructor.user_id,
            classroom_data=ClassroomCreate(
                name="Rolled Back Classroom",
                subject_code="AUD-204",
                section="A4",
            ),
        )

    assert (
        db_session.query(Classroom)
        .filter(
            Classroom.name == "Rolled Back Classroom",
        )
        .count()
        == 0
    )

    assert db_session.query(AuditRecord).count() == 0


def test_submission_audit_failure_restores_previous_official_attempt(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    context = _create_direct_submission_context(
        db_session,
        prefix="Rollback3",
    )

    student = context["student"]
    task = context["task"]

    previous_submission = Submission(
        student_id=student.user_id,
        task_id=task.task_id,
        coding_session_id=None,
        attempt_number=1,
        raw_code="PREVIOUS PRIVATE SOURCE",
        standard_input=None,
        status="submitted",
        is_official=True,
        accepted_at=datetime.now(timezone.utc),
    )

    db_session.add(previous_submission)
    db_session.commit()
    db_session.refresh(previous_submission)

    def fail_audit(*args, **kwargs):
        raise AuditServiceError("Forced submission audit failure.")

    monkeypatch.setattr(
        submission_service_module,
        "create_audit_record",
        fail_audit,
    )

    with pytest.raises(
        SubmissionAuditWorkflowError,
        match="accountability record",
    ):
        create_student_submission(
            db_session,
            student_id=student.user_id,
            payload=SubmissionCreate.model_construct(
                task_id=task.task_id,
                coding_session_id=None,
                raw_code="FAILED PRIVATE SOURCE",
                standard_input=None,
            ),
        )

    db_session.expire_all()

    saved_submissions = (
        db_session.query(Submission)
        .filter(
            Submission.student_id == student.user_id,
            Submission.task_id == task.task_id,
        )
        .order_by(
            Submission.attempt_number.asc(),
        )
        .all()
    )

    assert len(saved_submissions) == 1
    assert saved_submissions[0].sub_id == previous_submission.sub_id
    assert saved_submissions[0].is_official is True

    assert (
        db_session.query(AuditRecord)
        .filter(
            AuditRecord.resource_type == "submission",
        )
        .count()
        == 0
    )


def test_grade_audit_failure_rolls_back_manual_grade_change(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    context = _create_direct_submission_context(
        db_session,
        prefix="Rollback4",
    )

    instructor = context["instructor"]
    student = context["student"]
    task = context["task"]

    submission = Submission(
        student_id=student.user_id,
        task_id=task.task_id,
        coding_session_id=None,
        attempt_number=1,
        raw_code="PRIVATE ROLLBACK SOURCE",
        standard_input=None,
        status="submitted",
        is_official=True,
        accepted_at=datetime.now(timezone.utc),
    )

    grade = InstructorGrade(
        submission=submission,
        instructor_id=instructor.user_id,
        score=75.0,
        max_score=100.0,
        feedback="ORIGINAL PRIVATE FEEDBACK",
        is_released=False,
    )

    db_session.add_all(
        [
            submission,
            grade,
        ]
    )
    db_session.commit()
    db_session.refresh(submission)
    db_session.refresh(grade)

    grade_id = grade.grade_id

    def fail_audit(*args, **kwargs):
        raise AuditServiceError("Forced grade audit failure.")

    monkeypatch.setattr(
        evaluation_service_module,
        "create_audit_record",
        fail_audit,
    )

    with pytest.raises(
        GradeAuditWorkflowError,
        match="accountability record",
    ):
        patch_grade(
            db_session,
            sub_id=submission.sub_id,
            grade_update=InstructorGradeUpdate.model_construct(
                feedback="FAILED PRIVATE FEEDBACK",
            ),
            current_user=instructor,
        )

    db_session.expire_all()

    saved_grade = (
        db_session.query(InstructorGrade)
        .filter(
            InstructorGrade.grade_id == grade_id,
        )
        .one()
    )

    assert saved_grade.feedback == "ORIGINAL PRIVATE FEEDBACK"
    assert saved_grade.is_released is False

    assert (
        db_session.query(AuditRecord)
        .filter(
            AuditRecord.resource_type == "grade",
            AuditRecord.resource_id == str(grade_id),
        )
        .count()
        == 0
    )
