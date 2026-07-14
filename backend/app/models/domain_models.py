from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('student', 'instructor')",
            name="ck_users_role",
        ),
        CheckConstraint(
            "length(school_id) = 10",
            name="ck_users_school_id_length",
        ),
    )

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    school_id = Column(String(10), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(String(20), nullable=False, default="student")
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # SECURITY BOUNDARY:
    # The backend assigns this role. Registration clients must never be
    # trusted to choose or persist an instructor role directly.
    tasks = relationship(
        "Task",
        back_populates="instructor",
        foreign_keys="Task.instructor_id",
    )
    submissions = relationship(
        "Submission",
        back_populates="student",
        foreign_keys="Submission.student_id",
    )
    owned_classes = relationship(
        "Classroom",
        back_populates="instructor",
        foreign_keys="Classroom.instructor_id",
    )
    enrollments = relationship(
        "Enrollment",
        back_populates="student",
        foreign_keys="Enrollment.student_id",
    )
    coding_sessions = relationship(
        "CodingSession",
        back_populates="student",
        foreign_keys="CodingSession.student_id",
    )
    execution_requests = relationship(
        "ExecutionRequest",
        back_populates="student",
        foreign_keys="ExecutionRequest.student_id",
    )
    grades_given = relationship(
        "InstructorGrade",
        back_populates="instructor",
        foreign_keys="InstructorGrade.instructor_id",
    )


class InstructorAllowlist(Base):
    __tablename__ = "instructor_allowlist"

    allowlist_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class OTPChallenge(Base):
    __tablename__ = "otp_challenges"
    __table_args__ = (
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_otp_attempt_count",
        ),
        CheckConstraint(
            "max_attempts > 0",
            name="ck_otp_max_attempts",
        ),
        CheckConstraint(
            "resend_count >= 0",
            name="ck_otp_resend_count",
        ),
        CheckConstraint(
            "purpose IN ('registration', 'email_change')",
            name="ck_otp_purpose",
        ),
    )

    challenge_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    email = Column(
        String(255),
        nullable=False,
        index=True,
    )
    purpose = Column(
        String(50),
        nullable=False,
        default="registration",
    )
    otp_hash = Column(
        String(255),
        nullable=False,
    )
    attempt_count = Column(
        Integer,
        nullable=False,
        default=0,
    )
    max_attempts = Column(
        Integer,
        nullable=False,
        default=5,
    )
    resend_count = Column(
        Integer,
        nullable=False,
        default=0,
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )
    last_sent_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    consumed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    pending_registration = relationship(
        "PendingRegistration",
        back_populates="challenge",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )

    # PARTNER INTEGRATION:
    # The backend owns OTP generation, hashing, expiration, attempt limits,
    # resend limits, and verification. The partner-owned email adapter only
    # delivers the temporary plaintext OTP to the university email address.


class PendingRegistration(Base):
    __tablename__ = "pending_registrations"
    __table_args__ = (
        CheckConstraint(
            "length(school_id) = 10",
            name="ck_pending_registrations_school_id_length",
        ),
    )

    registration_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    challenge_id = Column(
        String(36),
        ForeignKey(
            "otp_challenges.challenge_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )
    name = Column(
        String(150),
        nullable=False,
    )
    school_id = Column(
        String(10),
        nullable=False,
        index=True,
    )
    email = Column(
        String(255),
        nullable=False,
        index=True,
    )
    password_hash = Column(
        String(255),
        nullable=False,
    )
    data_collection_acknowledged = Column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    challenge = relationship(
        "OTPChallenge",
        back_populates="pending_registration",
    )

    # SECURITY BOUNDARY:
    # This temporary record stores only a password hash, never the plaintext
    # password. It must not contain or accept a client-selected role.
    #
    # REGISTRATION FLOW:
    # Convert this record into a User only after the related OTP challenge is
    # successfully verified and consumed.


class Classroom(Base):
    __tablename__ = "classrooms"

    class_id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name = Column(String(150), nullable=False)
    subject_code = Column(String(50), nullable=True)
    section = Column(String(100), nullable=True)
    class_code = Column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
    )
    is_active = Column(Boolean, nullable=False, default=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    instructor = relationship(
        "User",
        back_populates="owned_classes",
        foreign_keys=[instructor_id],
    )
    enrollments = relationship(
        "Enrollment",
        back_populates="classroom",
    )
    tasks = relationship(
        "Task",
        back_populates="classroom",
    )


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint(
            "class_id",
            "student_id",
            name="uq_enrollment_class_student",
        ),
        CheckConstraint(
            "status IN ('active', 'disabled', 'removed')",
            name="ck_enrollments_status",
        ),
    )

    enrollment_id = Column(Integer, primary_key=True, index=True)
    class_id = Column(
        Integer,
        ForeignKey("classrooms.class_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status = Column(
        String(20),
        nullable=False,
        default="active",
    )
    joined_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    deactivated_at = Column(DateTime(timezone=True), nullable=True)

    classroom = relationship(
        "Classroom",
        back_populates="enrollments",
    )
    student = relationship(
        "User",
        back_populates="enrollments",
        foreign_keys=[student_id],
    )


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "activity_type IN ('laboratory', 'homework')",
            name="ck_tasks_activity_type",
        ),
        CheckConstraint(
            "paste_policy IN ('internal_only', 'disabled')",
            name="ck_tasks_paste_policy",
        ),
    )

    task_id = Column(Integer, primary_key=True, index=True)
    class_id = Column(
        Integer,
        ForeignKey("classrooms.class_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    instructor_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    activity_type = Column(
        String(20),
        nullable=False,
        default="laboratory",
    )
    required_ast_rules = Column(
        JSON,
        nullable=False,
        default=dict,
    )
    starter_code = Column(
        Text,
        nullable=False,
        default="",
    )
    paste_policy = Column(
        String(20),
        nullable=False,
        default="internal_only",
    )
    is_graded = Column(Boolean, nullable=False, default=True)
    is_published = Column(Boolean, nullable=False, default=False)
    due_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # TRANSITIONAL COMPATIBILITY:
    # class_id remains nullable until the classroom router and migration are
    # introduced. New published activities must eventually belong to a class.
    instructor = relationship(
        "User",
        back_populates="tasks",
        foreign_keys=[instructor_id],
    )
    classroom = relationship(
        "Classroom",
        back_populates="tasks",
    )
    test_cases = relationship(
        "TaskTestCase",
        back_populates="task",
    )
    submissions = relationship(
        "Submission",
        back_populates="task",
    )
    coding_sessions = relationship(
        "CodingSession",
        back_populates="task",
    )
    execution_requests = relationship(
        "ExecutionRequest",
        back_populates="task",
    )


class TaskTestCase(Base):
    __tablename__ = "task_test_cases"
    __table_args__ = (
        CheckConstraint(
            "display_order >= 0",
            name="ck_test_cases_display_order",
        ),
    )

    test_case_id = Column(Integer, primary_key=True, index=True)
    task_id = Column(
        Integer,
        ForeignKey("tasks.task_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name = Column(String(150), nullable=False)
    standard_input = Column(
        Text,
        nullable=False,
        default="",
    )
    expected_output = Column(Text, nullable=False)
    is_hidden = Column(Boolean, nullable=False, default=False)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    task = relationship(
        "Task",
        back_populates="test_cases",
    )


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "task_id",
            "attempt_number",
            name="uq_submission_attempt",
        ),
        CheckConstraint(
            "attempt_number > 0",
            name="ck_submission_attempt_number",
        ),
        CheckConstraint(
            "status IN ('submitted', 'awaiting_review', 'graded', 'rejected')",
            name="ck_submissions_status",
        ),
        Index(
            "ix_submissions_student_task",
            "student_id",
            "task_id",
        ),
    )

    sub_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    task_id = Column(
        Integer,
        ForeignKey("tasks.task_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    coding_session_id = Column(
        String(36),
        ForeignKey(
            "coding_sessions.session_id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )
    attempt_number = Column(
        Integer,
        nullable=False,
        default=1,
    )
    raw_code = Column(Text, nullable=False)
    standard_input = Column(
        Text,
        nullable=False,
        default="",
    )
    status = Column(
        String(30),
        nullable=False,
        default="awaiting_review",
    )
    is_official = Column(
        Boolean,
        nullable=False,
        default=True,
    )
    submitted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    # Compatibility fields for the current evaluation endpoints.
    # Detailed results are stored in the related analysis tables.
    jaccard_score = Column(Float, nullable=True)
    ast_pass_fail = Column(Boolean, nullable=True)

    student = relationship(
        "User",
        back_populates="submissions",
        foreign_keys=[student_id],
    )
    task = relationship(
        "Task",
        back_populates="submissions",
    )
    coding_session = relationship(
        "CodingSession",
        back_populates="submissions",
    )
    behavioral_log = relationship(
        "BehavioralLog",
        back_populates="submission",
        uselist=False,
    )
    execution_requests = relationship(
        "ExecutionRequest",
        back_populates="submission",
    )
    ast_analyses = relationship(
        "ASTAnalysis",
        back_populates="submission",
    )
    similarity_results_as_source = relationship(
        "SimilarityResult",
        back_populates="source_submission",
        foreign_keys="SimilarityResult.source_submission_id",
    )
    similarity_results_as_match = relationship(
        "SimilarityResult",
        back_populates="compared_submission",
        foreign_keys="SimilarityResult.compared_submission_id",
    )
    instructor_grade = relationship(
        "InstructorGrade",
        back_populates="submission",
        uselist=False,
    )

    # SUBMISSION RULE:
    # Every row represents an immutable attempt. The service layer must mark
    # only the latest accepted attempt for the student and task as official.


class BehavioralLog(Base):
    __tablename__ = "behavioral_logs"
    __table_args__ = (
        CheckConstraint(
            "tab_switches_count >= 0",
            name="ck_logs_tab_switches",
        ),
        CheckConstraint(
            "blocked_paste_count >= 0",
            name="ck_logs_blocked_paste",
        ),
        CheckConstraint(
            "run_attempt_count >= 0",
            name="ck_logs_run_attempts",
        ),
        CheckConstraint(
            "idle_duration_seconds >= 0",
            name="ck_logs_idle_duration",
        ),
    )

    log_id = Column(Integer, primary_key=True, index=True)
    sub_id = Column(
        Integer,
        ForeignKey("submissions.sub_id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    tab_switches_count = Column(
        Integer,
        default=0,
        nullable=False,
    )
    blocked_paste_count = Column(
        Integer,
        default=0,
        nullable=False,
    )
    run_attempt_count = Column(
        Integer,
        default=0,
        nullable=False,
    )
    idle_duration_seconds = Column(
        Integer,
        default=0,
        nullable=False,
    )
    last_blocked_paste_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    submission = relationship(
        "Submission",
        back_populates="behavioral_log",
    )

    # PRIVACY BOUNDARY:
    # Store summary counts and timestamps only. Never store clipboard text,
    # browsing history, screen/webcam/microphone data, or every keystroke.
    # These indicators must not generate an automatic behavior score.


class CodingSession(Base):
    __tablename__ = "coding_sessions"
    __table_args__ = (
        CheckConstraint(
            "tab_switch_count >= 0",
            name="ck_sessions_tab_switches",
        ),
        CheckConstraint(
            "blocked_paste_count >= 0",
            name="ck_sessions_blocked_paste",
        ),
        CheckConstraint(
            "run_attempt_count >= 0",
            name="ck_sessions_run_attempts",
        ),
        CheckConstraint(
            "idle_duration_seconds >= 0",
            name="ck_sessions_idle_duration",
        ),
    )

    session_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    student_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    task_id = Column(
        Integer,
        ForeignKey("tasks.task_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    ended_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    tab_switch_count = Column(Integer, nullable=False, default=0)
    blocked_paste_count = Column(Integer, nullable=False, default=0)
    run_attempt_count = Column(Integer, nullable=False, default=0)
    idle_duration_seconds = Column(Integer, nullable=False, default=0)
    last_blocked_paste_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    student = relationship(
        "User",
        back_populates="coding_sessions",
        foreign_keys=[student_id],
    )
    task = relationship(
        "Task",
        back_populates="coding_sessions",
    )
    submissions = relationship(
        "Submission",
        back_populates="coding_session",
    )
    execution_requests = relationship(
        "ExecutionRequest",
        back_populates="coding_session",
    )


class ExecutionRequest(Base):
    __tablename__ = "execution_requests"
    __table_args__ = (
        CheckConstraint(
            "request_kind IN ('run', 'check', 'submit')",
            name="ck_execution_request_kind",
        ),
        CheckConstraint(
            "status IN "
            "('queued', 'running', 'completed', 'syntax_error', "
            "'runtime_error', 'timed_out', 'memory_limit', "
            "'output_limit', 'process_limit', 'cancelled', 'failed')",
            name="ck_execution_status",
        ),
    )

    execution_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    student_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    task_id = Column(
        Integer,
        ForeignKey("tasks.task_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    submission_id = Column(
        Integer,
        ForeignKey("submissions.sub_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    coding_session_id = Column(
        String(36),
        ForeignKey(
            "coding_sessions.session_id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )
    request_kind = Column(
        String(20),
        nullable=False,
        default="run",
    )
    status = Column(
        String(30),
        nullable=False,
        default="queued",
        index=True,
    )
    source_code = Column(Text, nullable=False)
    standard_input = Column(
        Text,
        nullable=False,
        default="",
    )
    stdout = Column(
        Text,
        nullable=False,
        default="",
    )
    stderr = Column(
        Text,
        nullable=False,
        default="",
    )
    exit_code = Column(Integer, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    limit_reason = Column(String(100), nullable=True)
    worker_task_id = Column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )
    queued_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship(
        "User",
        back_populates="execution_requests",
        foreign_keys=[student_id],
    )
    task = relationship(
        "Task",
        back_populates="execution_requests",
    )
    submission = relationship(
        "Submission",
        back_populates="execution_requests",
    )
    coding_session = relationship(
        "CodingSession",
        back_populates="execution_requests",
    )
    ast_analyses = relationship(
        "ASTAnalysis",
        back_populates="execution_request",
    )

    # PARTNER INTEGRATION:
    # FastAPI validates authorization and persists this request before the
    # partner-owned Celery/Redis adapter receives execution_id. FastAPI must
    # never execute submitted Python code directly.
    #
    # WORKER UPDATE CONTRACT:
    # The isolated worker may update only lifecycle and result fields such as
    # status, stdout, stderr, exit_code, execution_time_ms, limit_reason,
    # started_at, and completed_at.


class ASTAnalysis(Base):
    __tablename__ = "ast_analyses"

    analysis_id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer,
        ForeignKey("submissions.sub_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    execution_id = Column(
        String(36),
        ForeignKey(
            "execution_requests.execution_id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )
    overall_pass = Column(Boolean, nullable=True)
    syntax_error = Column(JSON, nullable=True)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    submission = relationship(
        "Submission",
        back_populates="ast_analyses",
    )
    execution_request = relationship(
        "ExecutionRequest",
        back_populates="ast_analyses",
    )
    findings = relationship(
        "ASTFinding",
        back_populates="analysis",
    )


class ASTFinding(Base):
    __tablename__ = "ast_findings"

    finding_id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(
        Integer,
        ForeignKey("ast_analyses.analysis_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    rule_key = Column(String(100), nullable=False)
    label = Column(String(150), nullable=False)
    passed = Column(Boolean, nullable=True)
    line_number = Column(Integer, nullable=True)
    message = Column(Text, nullable=True)
    details = Column(JSON, nullable=False, default=dict)

    analysis = relationship(
        "ASTAnalysis",
        back_populates="findings",
    )


class SimilarityResult(Base):
    __tablename__ = "similarity_results"
    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 100",
            name="ck_similarity_score",
        ),
    )

    result_id = Column(Integer, primary_key=True, index=True)
    source_submission_id = Column(
        Integer,
        ForeignKey("submissions.sub_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    compared_submission_id = Column(
        Integer,
        ForeignKey("submissions.sub_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    score = Column(Float, nullable=False)
    algorithm = Column(
        String(100),
        nullable=False,
        default="jaccard",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    source_submission = relationship(
        "Submission",
        back_populates="similarity_results_as_source",
        foreign_keys=[source_submission_id],
    )
    compared_submission = relationship(
        "Submission",
        back_populates="similarity_results_as_match",
        foreign_keys=[compared_submission_id],
    )

    # REVIEW INDICATOR:
    # Similarity supports instructor review only. It must never automatically
    # determine plagiarism, misconduct, or the official grade.


class InstructorGrade(Base):
    __tablename__ = "instructor_grades"
    __table_args__ = (
        CheckConstraint(
            "score >= 0",
            name="ck_grades_score_nonnegative",
        ),
        CheckConstraint(
            "max_score > 0",
            name="ck_grades_max_score_positive",
        ),
        CheckConstraint(
            "score <= max_score",
            name="ck_grades_score_within_max",
        ),
    )

    grade_id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer,
        ForeignKey("submissions.sub_id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    instructor_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)
    is_released = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    submission = relationship(
        "Submission",
        back_populates="instructor_grade",
    )
    instructor = relationship(
        "User",
        back_populates="grades_given",
        foreign_keys=[instructor_id],
    )

    # GRADING BOUNDARY:
    # Only an authorized instructor may set the official grade. AST, tests,
    # similarity, execution, and session indicators must never calculate it.
