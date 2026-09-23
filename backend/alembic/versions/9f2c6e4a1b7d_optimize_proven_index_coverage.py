"""optimize proven index coverage

Revision ID: 9f2c6e4a1b7d
Revises: 4b3a1d9e7c25
Create Date: 2026-07-22

"""

from collections.abc import Sequence

from alembic import op


revision: str = "9f2c6e4a1b7d"
down_revision: str | Sequence[str] | None = "4b3a1d9e7c25"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Add indexes that match execution-list filtering and deterministic
    ordering, then remove standalone indexes whose leading columns are
    already covered by primary, unique, or composite indexes.
    """

    op.create_index(
        "ix_execution_requests_student_queued",
        "execution_requests",
        [
            "student_id",
            "queued_at",
            "execution_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_execution_requests_task_queued",
        "execution_requests",
        [
            "task_id",
            "queued_at",
            "execution_id",
        ],
        unique=False,
    )

    op.drop_index(
        "ix_execution_requests_correlation_id",
        table_name="execution_requests",
    )
    op.drop_index(
        "ix_execution_requests_dispatch_idempotency_key",
        table_name="execution_requests",
    )
    op.drop_index(
        "ix_execution_requests_status",
        table_name="execution_requests",
    )

    op.drop_index(
        "ix_partner_execution_updates_partner_update_record_id",
        table_name="partner_execution_updates",
    )
    op.drop_index(
        "ix_partner_execution_updates_correlation_id",
        table_name="partner_execution_updates",
    )
    op.drop_index(
        "ix_partner_execution_updates_execution_id",
        table_name="partner_execution_updates",
    )

    op.drop_index(
        "ix_submissions_sub_id",
        table_name="submissions",
    )
    op.drop_index(
        "ix_submissions_student_id",
        table_name="submissions",
    )

    op.drop_index(
        "ix_instructor_grades_grade_id",
        table_name="instructor_grades",
    )

    op.drop_index(
        "ix_notifications_event_id",
        table_name="notifications",
    )
    op.drop_index(
        "ix_notifications_recipient_id",
        table_name="notifications",
    )

    op.drop_index(
        "ix_audit_records_actor_user_id",
        table_name="audit_records",
    )


def downgrade() -> None:
    """
    Restore the previous standalone indexes before removing the Pillar 15
    execution-list pagination indexes.
    """

    op.create_index(
        "ix_execution_requests_correlation_id",
        "execution_requests",
        ["correlation_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_requests_dispatch_idempotency_key",
        "execution_requests",
        ["dispatch_idempotency_key"],
        unique=False,
    )
    op.create_index(
        "ix_execution_requests_status",
        "execution_requests",
        ["status"],
        unique=False,
    )

    op.create_index(
        "ix_partner_execution_updates_partner_update_record_id",
        "partner_execution_updates",
        ["partner_update_record_id"],
        unique=False,
    )
    op.create_index(
        "ix_partner_execution_updates_correlation_id",
        "partner_execution_updates",
        ["correlation_id"],
        unique=False,
    )
    op.create_index(
        "ix_partner_execution_updates_execution_id",
        "partner_execution_updates",
        ["execution_id"],
        unique=False,
    )

    op.create_index(
        "ix_submissions_sub_id",
        "submissions",
        ["sub_id"],
        unique=False,
    )
    op.create_index(
        "ix_submissions_student_id",
        "submissions",
        ["student_id"],
        unique=False,
    )

    op.create_index(
        "ix_instructor_grades_grade_id",
        "instructor_grades",
        ["grade_id"],
        unique=False,
    )

    op.create_index(
        "ix_notifications_event_id",
        "notifications",
        ["event_id"],
        unique=False,
    )
    op.create_index(
        "ix_notifications_recipient_id",
        "notifications",
        ["recipient_id"],
        unique=False,
    )

    op.create_index(
        "ix_audit_records_actor_user_id",
        "audit_records",
        ["actor_user_id"],
        unique=False,
    )

    op.drop_index(
        "ix_execution_requests_task_queued",
        table_name="execution_requests",
    )
    op.drop_index(
        "ix_execution_requests_student_queued",
        table_name="execution_requests",
    )
