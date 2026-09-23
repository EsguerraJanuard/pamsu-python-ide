import csv
from datetime import datetime, timezone
from io import StringIO

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.models.domain_models import (
    Classroom,
    Enrollment,
    InstructorGrade,
    Submission,
    Task,
    User,
)
from app.services.reporting_service import (
    MAX_REPORT_PAGE_SIZE,
    ReportingAccessDeniedError,
    ReportingPaginationError,
    ReportingTaskUnavailableError,
    build_gradebook_csv_export,
    get_activity_completion_summary,
    get_classroom_completion_summary,
    get_grade_distribution,
    get_student_progress_summary,
    list_missing_submissions,
)


def _create_user(
    db: Session,
    *,
    name: str,
    school_id: str,
    email: str,
    role: str,
    email_verified: bool = True,
    is_active: bool = True,
) -> User:
    user = User(
        name=name,
        school_id=school_id,
        email=email,
        role=role,
        password_hash="fakehash",
        email_verified=email_verified,
        is_active=is_active,
    )

    db.add(user)
    db.flush()

    return user


def _create_classroom(
    db: Session,
    *,
    instructor_id: int,
    name: str,
    class_code: str,
) -> Classroom:
    classroom = Classroom(
        instructor_id=instructor_id,
        name=name,
        subject_code="REP-101",
        section="A",
        class_code=class_code,
        is_active=True,
        archived_at=None,
    )

    db.add(classroom)
    db.flush()

    return classroom


def _create_enrollment(
    db: Session,
    *,
    class_id: int,
    student_id: int,
    status: str = "active",
) -> Enrollment:
    enrollment = Enrollment(
        class_id=class_id,
        student_id=student_id,
        status=status,
        deactivated_at=None,
    )

    db.add(enrollment)
    db.flush()

    return enrollment


def _create_task(
    db: Session,
    *,
    class_id: int,
    instructor_id: int,
    title: str,
    is_published: bool = True,
    is_graded: bool = True,
) -> Task:
    task = Task(
        class_id=class_id,
        instructor_id=instructor_id,
        title=title,
        description="PRIVATE TASK DESCRIPTION",
        instructions="PRIVATE TASK INSTRUCTIONS",
        activity_type="laboratory",
        required_ast_rules={
            "require_for_loop": True,
        },
        starter_code="PRIVATE STARTER CODE",
        paste_policy="internal_only",
        is_graded=is_graded,
        is_published=is_published,
        due_at=None,
        published_at=(datetime.now(timezone.utc) if is_published else None),
    )

    db.add(task)
    db.flush()

    return task


def _create_submission(
    db: Session,
    *,
    student_id: int,
    task_id: int,
    attempt_number: int,
    raw_code: str,
    is_official: bool = True,
    status: str = "submitted",
) -> Submission:
    submission = Submission(
        student_id=student_id,
        task_id=task_id,
        coding_session_id=None,
        attempt_number=attempt_number,
        raw_code=raw_code,
        standard_input="PRIVATE STANDARD INPUT",
        status=status,
        is_official=is_official,
        accepted_at=datetime.now(timezone.utc),
    )

    db.add(submission)
    db.flush()

    return submission


def _create_grade(
    db: Session,
    *,
    submission_id: int,
    instructor_id: int,
    score: float,
    max_score: float = 100.0,
    is_released: bool,
    feedback: str,
) -> InstructorGrade:
    grade = InstructorGrade(
        submission_id=submission_id,
        instructor_id=instructor_id,
        score=score,
        max_score=max_score,
        feedback=feedback,
        is_released=is_released,
    )

    db.add(grade)
    db.flush()

    return grade


def _create_reporting_context(
    db: Session,
) -> dict[str, object]:
    owner = _create_user(
        db,
        name="Reporting Owner",
        school_id="9300000001",
        email="reporting.owner@pampangastateu.edu.ph",
        role="instructor",
    )

    other_instructor = _create_user(
        db,
        name="Other Instructor",
        school_id="9300000002",
        email="reporting.other@pampangastateu.edu.ph",
        role="instructor",
    )

    student_alpha = _create_user(
        db,
        name="Alpha Student",
        school_id="9400000001",
        email="reporting.alpha@pampangastateu.edu.ph",
        role="student",
    )

    student_formula = _create_user(
        db,
        name="=Formula Student",
        school_id="9400000002",
        email="reporting.formula@pampangastateu.edu.ph",
        role="student",
    )

    inactive_student = _create_user(
        db,
        name="Inactive Student",
        school_id="9400000003",
        email="reporting.inactive@pampangastateu.edu.ph",
        role="student",
        is_active=False,
    )

    unverified_student = _create_user(
        db,
        name="Unverified Student",
        school_id="9400000004",
        email="reporting.unverified@pampangastateu.edu.ph",
        role="student",
        email_verified=False,
    )

    removed_student = _create_user(
        db,
        name="Removed Student",
        school_id="9400000005",
        email="reporting.removed@pampangastateu.edu.ph",
        role="student",
    )

    classroom = _create_classroom(
        db,
        instructor_id=owner.user_id,
        name="Reporting Classroom",
        class_code="REPCLASS01",
    )

    other_classroom = _create_classroom(
        db,
        instructor_id=other_instructor.user_id,
        name="Other Classroom",
        class_code="REPCLASS02",
    )

    for student in (
        student_alpha,
        student_formula,
        inactive_student,
        unverified_student,
    ):
        _create_enrollment(
            db,
            class_id=classroom.class_id,
            student_id=student.user_id,
        )

    _create_enrollment(
        db,
        class_id=classroom.class_id,
        student_id=removed_student.user_id,
        status="removed",
    )

    task_one = _create_task(
        db,
        class_id=classroom.class_id,
        instructor_id=owner.user_id,
        title="Activity One",
    )

    task_two = _create_task(
        db,
        class_id=classroom.class_id,
        instructor_id=owner.user_id,
        title="@Activity Two",
    )

    unpublished_task = _create_task(
        db,
        class_id=classroom.class_id,
        instructor_id=owner.user_id,
        title="Unpublished Activity",
        is_published=False,
    )

    practice_task = _create_task(
        db,
        class_id=classroom.class_id,
        instructor_id=owner.user_id,
        title="Practice Activity",
        is_graded=False,
    )

    other_task = _create_task(
        db,
        class_id=other_classroom.class_id,
        instructor_id=other_instructor.user_id,
        title="Other Instructor Activity",
    )

    unofficial_attempt = _create_submission(
        db,
        student_id=student_alpha.user_id,
        task_id=task_one.task_id,
        attempt_number=1,
        raw_code="PRIVATE UNOFFICIAL SOURCE",
        is_official=False,
    )

    official_alpha_one = _create_submission(
        db,
        student_id=student_alpha.user_id,
        task_id=task_one.task_id,
        attempt_number=2,
        raw_code="PRIVATE ALPHA ONE SOURCE",
    )

    official_alpha_two = _create_submission(
        db,
        student_id=student_alpha.user_id,
        task_id=task_two.task_id,
        attempt_number=1,
        raw_code="PRIVATE ALPHA TWO SOURCE",
        status="graded",
    )

    official_formula_two = _create_submission(
        db,
        student_id=student_formula.user_id,
        task_id=task_two.task_id,
        attempt_number=1,
        raw_code="PRIVATE FORMULA SOURCE",
        status="graded",
    )

    _create_grade(
        db,
        submission_id=unofficial_attempt.sub_id,
        instructor_id=owner.user_id,
        score=10.0,
        is_released=True,
        feedback="PRIVATE UNOFFICIAL FEEDBACK",
    )

    unreleased_grade = _create_grade(
        db,
        submission_id=official_alpha_one.sub_id,
        instructor_id=owner.user_id,
        score=85.0,
        is_released=False,
        feedback="PRIVATE UNRELEASED FEEDBACK",
    )

    released_alpha_grade = _create_grade(
        db,
        submission_id=official_alpha_two.sub_id,
        instructor_id=owner.user_id,
        score=95.0,
        is_released=True,
        feedback="PRIVATE RELEASED ALPHA FEEDBACK",
    )

    released_formula_grade = _create_grade(
        db,
        submission_id=official_formula_two.sub_id,
        instructor_id=owner.user_id,
        score=50.0,
        is_released=True,
        feedback="PRIVATE RELEASED FORMULA FEEDBACK",
    )

    db.commit()

    return {
        "owner": owner,
        "other_instructor": other_instructor,
        "student_alpha": student_alpha,
        "student_formula": student_formula,
        "classroom": classroom,
        "other_classroom": other_classroom,
        "task_one": task_one,
        "task_two": task_two,
        "unpublished_task": unpublished_task,
        "practice_task": practice_task,
        "other_task": other_task,
        "unreleased_grade": unreleased_grade,
        "released_alpha_grade": released_alpha_grade,
        "released_formula_grade": released_formula_grade,
    }


def test_classroom_completion_uses_active_verified_students_and_official_attempts(
    db_session: Session,
):
    context = _create_reporting_context(
        db_session,
    )

    response = get_classroom_completion_summary(
        db_session,
        instructor_id=context["owner"].user_id,
        class_id=context["classroom"].class_id,
    )

    assert response["active_student_count"] == 2
    assert response["published_graded_activity_count"] == 2

    completion = response["completion"]

    assert completion == {
        "expected_count": 4,
        "submitted_count": 3,
        "missing_count": 1,
        "manually_graded_count": 3,
        "released_grade_count": 2,
        "completion_percentage": 75.0,
    }

    activity_counts = {
        item["activity"]["task_id"]: item["completion"]
        for item in response["activities"]
    }

    assert activity_counts[context["task_one"].task_id]["submitted_count"] == 1

    assert activity_counts[context["task_one"].task_id]["released_grade_count"] == 0

    assert activity_counts[context["task_two"].task_id]["submitted_count"] == 2


def test_activity_completion_excludes_unofficial_attempt_and_unreleased_grade(
    db_session: Session,
):
    context = _create_reporting_context(
        db_session,
    )

    response = get_activity_completion_summary(
        db_session,
        instructor_id=context["owner"].user_id,
        task_id=context["task_one"].task_id,
    )

    assert response["active_student_count"] == 2
    assert response["completion"] == {
        "expected_count": 2,
        "submitted_count": 1,
        "missing_count": 1,
        "manually_graded_count": 1,
        "released_grade_count": 0,
        "completion_percentage": 50.0,
    }


@pytest.mark.parametrize(
    "task_key",
    [
        "unpublished_task",
        "practice_task",
    ],
)
def test_activity_completion_requires_published_graded_activity(
    db_session: Session,
    task_key: str,
):
    context = _create_reporting_context(
        db_session,
    )

    with pytest.raises(
        ReportingTaskUnavailableError,
        match="published graded activity",
    ):
        get_activity_completion_summary(
            db_session,
            instructor_id=context["owner"].user_id,
            task_id=context[task_key].task_id,
        )


def test_instructor_reports_deny_cross_owner_classroom_and_task(
    db_session: Session,
):
    context = _create_reporting_context(
        db_session,
    )

    with pytest.raises(
        ReportingAccessDeniedError,
    ):
        get_classroom_completion_summary(
            db_session,
            instructor_id=context["other_instructor"].user_id,
            class_id=context["classroom"].class_id,
        )

    with pytest.raises(
        ReportingAccessDeniedError,
    ):
        get_activity_completion_summary(
            db_session,
            instructor_id=context["other_instructor"].user_id,
            task_id=context["task_one"].task_id,
        )


def test_grade_distribution_uses_only_official_manual_grades(
    db_session: Session,
):
    context = _create_reporting_context(
        db_session,
    )

    response = get_grade_distribution(
        db_session,
        instructor_id=context["owner"].user_id,
        class_id=context["classroom"].class_id,
    )

    assert response["manually_graded_submission_count"] == 3
    assert response["released_grade_count"] == 2
    assert response["average_percentage"] == 76.67
    assert response["minimum_percentage"] == 50.0
    assert response["maximum_percentage"] == 95.0

    buckets = {bucket["band"]: bucket["count"] for bucket in response["buckets"]}

    assert buckets == {
        "0-59.99": 1,
        "60-69.99": 0,
        "70-79.99": 0,
        "80-89.99": 1,
        "90-100": 1,
    }


def test_grade_distribution_supports_owned_activity_filter(
    db_session: Session,
):
    context = _create_reporting_context(
        db_session,
    )

    response = get_grade_distribution(
        db_session,
        instructor_id=context["owner"].user_id,
        class_id=context["classroom"].class_id,
        task_id=context["task_one"].task_id,
    )

    assert response["activity"]["task_id"] == context["task_one"].task_id
    assert response["manually_graded_submission_count"] == 1
    assert response["released_grade_count"] == 0
    assert response["average_percentage"] == 85.0


def test_grade_distribution_denies_activity_owned_by_another_instructor(
    db_session: Session,
):
    context = _create_reporting_context(
        db_session,
    )

    with pytest.raises(
        ReportingAccessDeniedError,
        match="activities that you own",
    ):
        get_grade_distribution(
            db_session,
            instructor_id=context["other_instructor"].user_id,
            class_id=context["other_classroom"].class_id,
            task_id=context["task_one"].task_id,
        )


def test_missing_submission_report_returns_only_expected_missing_pair(
    db_session: Session,
):
    context = _create_reporting_context(
        db_session,
    )

    response = list_missing_submissions(
        db_session,
        instructor_id=context["owner"].user_id,
        class_id=context["classroom"].class_id,
        page=1,
        page_size=25,
        sort_by="student_name",
        sort_direction="asc",
    )

    assert response["total_items"] == 1
    assert response["total_pages"] == 1
    assert len(response["items"]) == 1

    item = response["items"][0]

    assert item["student"]["student_id"] == context["student_formula"].user_id
    assert item["activity"]["task_id"] == context["task_one"].task_id
    assert item["submission_state"] == "missing"
    assert item["enrollment_status"] == "active"


def test_missing_submission_report_has_bounded_pagination(
    db_session: Session,
):
    context = _create_reporting_context(
        db_session,
    )

    with pytest.raises(
        ReportingPaginationError,
    ):
        list_missing_submissions(
            db_session,
            instructor_id=context["owner"].user_id,
            page=0,
        )

    with pytest.raises(
        ReportingPaginationError,
    ):
        list_missing_submissions(
            db_session,
            instructor_id=context["owner"].user_id,
            page_size=MAX_REPORT_PAGE_SIZE + 1,
        )


def test_student_progress_uses_only_authenticated_students_own_released_grades(
    db_session: Session,
):
    context = _create_reporting_context(
        db_session,
    )

    alpha_response = get_student_progress_summary(
        db_session,
        student_id=context["student_alpha"].user_id,
    )

    assert alpha_response["student_id"] == context["student_alpha"].user_id
    assert alpha_response["active_classroom_count"] == 1
    assert alpha_response["published_graded_activity_count"] == 2
    assert alpha_response["submitted_activity_count"] == 2
    assert alpha_response["missing_activity_count"] == 0
    assert alpha_response["released_grade_count"] == 1
    assert alpha_response["average_released_percentage"] == 95.0
    assert alpha_response["completion_percentage"] == 100.0

    formula_response = get_student_progress_summary(
        db_session,
        student_id=context["student_formula"].user_id,
    )

    assert formula_response["submitted_activity_count"] == 1
    assert formula_response["missing_activity_count"] == 1
    assert formula_response["released_grade_count"] == 1
    assert formula_response["average_released_percentage"] == 50.0
    assert formula_response["completion_percentage"] == 50.0


def test_gradebook_csv_export_is_owner_scoped_and_privacy_safe(
    db_session: Session,
):
    context = _create_reporting_context(
        db_session,
    )

    export = build_gradebook_csv_export(
        db_session,
        instructor_id=context["owner"].user_id,
        class_id=context["classroom"].class_id,
    )

    assert export["filename"] == (
        f"classroom-{context['classroom'].class_id}-gradebook.csv"
    )
    assert export["media_type"] == "text/csv; charset=utf-8"
    assert export["row_count"] == 3
    assert export["includes_raw_source"] is False

    decoded = export["content"].decode(
        "utf-8-sig",
    )

    prohibited_values = {
        "PRIVATE UNOFFICIAL SOURCE",
        "PRIVATE ALPHA ONE SOURCE",
        "PRIVATE ALPHA TWO SOURCE",
        "PRIVATE FORMULA SOURCE",
        "PRIVATE STANDARD INPUT",
        "PRIVATE UNRELEASED FEEDBACK",
        "PRIVATE RELEASED ALPHA FEEDBACK",
        "PRIVATE RELEASED FORMULA FEEDBACK",
        "PRIVATE TASK DESCRIPTION",
        "PRIVATE TASK INSTRUCTIONS",
        "PRIVATE STARTER CODE",
    }

    for prohibited_value in prohibited_values:
        assert prohibited_value not in decoded

    reader = csv.DictReader(
        StringIO(decoded),
    )

    rows = list(reader)

    assert len(rows) == 3
    assert "raw_code" not in reader.fieldnames
    assert "standard_input" not in reader.fieldnames
    assert "feedback" not in reader.fieldnames
    assert "risk_score" not in reader.fieldnames
    assert "plagiarism_verdict" not in reader.fieldnames

    formula_row = next(
        row for row in rows if row["school_id"] == context["student_formula"].school_id
    )

    assert formula_row["student_name"] == "'=Formula Student"
    assert formula_row["activity_title"] == "'@Activity Two"


def test_gradebook_csv_export_denies_another_instructor(
    db_session: Session,
):
    context = _create_reporting_context(
        db_session,
    )

    with pytest.raises(
        ReportingAccessDeniedError,
    ):
        build_gradebook_csv_export(
            db_session,
            instructor_id=context["other_instructor"].user_id,
            class_id=context["classroom"].class_id,
        )


def test_classroom_completion_uses_constant_query_count(
    db_session: Session,
):
    context = _create_reporting_context(
        db_session,
    )

    instructor_id = context["owner"].user_id
    class_id = context["classroom"].class_id

    statement_count = 0

    def count_selects(
        _connection,
        _cursor,
        statement,
        _parameters,
        _context,
        _executemany,
    ):
        nonlocal statement_count

        if statement.lstrip().upper().startswith("SELECT"):
            statement_count += 1

    event.listen(
        db_session.bind,
        "before_cursor_execute",
        count_selects,
    )

    try:
        get_classroom_completion_summary(
            db_session,
            instructor_id=instructor_id,
            class_id=class_id,
        )
    finally:
        event.remove(
            db_session.bind,
            "before_cursor_execute",
            count_selects,
        )

    assert statement_count <= 4
