"""activity guidance fields and deadline reminders

Revision ID: 5e8a1c7d9b42
Revises: c25114413200
Create Date: 2026-10-20 16:00:00.000000+00:00

Panel recommendations (oral defense, 2026-09-30):
- tasks.scenario: real-world context shown with the problem;
- tasks.solution_explanation: why the solution works, shown to a student
  only after that student's grade is released;
- academic_events.event_type accepts 'deadline_reminder', used for the
  in-app reminder sent when a published activity is due within 24 hours.

Both columns are nullable, so existing rows need no backfill.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e8a1c7d9b42'
down_revision: Union[str, Sequence[str], None] = 'c25114413200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PREVIOUS_EVENT_TYPES = (
    "'student_enrolled', 'enrollment_status_changed', 'activity_published', "
    "'activity_updated', 'submission_created', 'submission_status_changed', "
    "'grade_released', 'classroom_archived'"
)
EVENT_TYPES = PREVIOUS_EVENT_TYPES + ", 'deadline_reminder'"


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tasks', sa.Column('scenario', sa.Text(), nullable=True))
    op.add_column('tasks', sa.Column('solution_explanation', sa.Text(), nullable=True))

    with op.batch_alter_table('academic_events') as batch_op:
        batch_op.drop_constraint('ck_academic_events_type', type_='check')
        batch_op.create_check_constraint(
            'ck_academic_events_type',
            f"event_type IN ({EVENT_TYPES})",
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Reminder rows cannot satisfy the old constraint, so they are removed
    # together with their notifications.
    op.execute(
        "DELETE FROM notifications WHERE event_id IN "
        "(SELECT event_id FROM academic_events WHERE event_type = 'deadline_reminder')"
    )
    op.execute("DELETE FROM academic_events WHERE event_type = 'deadline_reminder'")

    with op.batch_alter_table('academic_events') as batch_op:
        batch_op.drop_constraint('ck_academic_events_type', type_='check')
        batch_op.create_check_constraint(
            'ck_academic_events_type',
            f"event_type IN ({PREVIOUS_EVENT_TYPES})",
        )

    op.drop_column('tasks', 'solution_explanation')
    op.drop_column('tasks', 'scenario')
