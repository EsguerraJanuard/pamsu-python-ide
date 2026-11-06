"""add_timed_activities

Revision ID: 18a56b9b5fa8
Revises: b7e4c2a91f03
Create Date: 2026-11-06 09:00:00.000000+00:00

Timed activities. An instructor can give an activity a time limit; each
student then has that many minutes from the moment they start, and the
timer cannot be paused.

- tasks.is_timed: NOT NULL with server default false, so every existing
  activity stays untimed, and the previous code (which inserts tasks without
  the column while a deploy switches over) keeps working.
- tasks.time_limit_minutes: NULL unless the activity is timed (1-480).
- timed_attempts: one row per student timer window, written when the student
  chooses "Start Now". The server checks submissions against it, so reloading
  the page or closing the tab never resets the timer.

PostgreSQL 11+ adds a NOT NULL column with a constant default without
rewriting the table. The two CHECK constraints are validated with one scan
of tasks; lock_timeout makes the migration fail fast (and roll back) instead
of queueing behind a long transaction.

Downgrade drops the table and the columns: every timer window is lost and
timed activities become untimed. It refuses while any activity is timed, so
an instructor's settings are not dropped by accident.
"""
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18a56b9b5fa8'
down_revision: Union[str, Sequence[str], None] = 'b7e4c2a91f03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TASKS = 'tasks'
ATTEMPTS = 'timed_attempts'
MATCHES_CONSTRAINT = 'ck_tasks_time_limit_matches_timed'
RANGE_CONSTRAINT = 'ck_tasks_time_limit_range'
MATCHES_CONDITION = (
    "(is_timed AND time_limit_minutes IS NOT NULL) "
    "OR (NOT is_timed AND time_limit_minutes IS NULL)"
)
RANGE_CONDITION = "time_limit_minutes IS NULL OR time_limit_minutes BETWEEN 1 AND 480"


def _task_columns() -> tuple[sa.Column, ...]:
    return (
        sa.Column('is_timed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
    )


def upgrade() -> None:
    if op.get_context().dialect.name == 'postgresql':
        # Short lock wait: fail fast instead of queueing behind long writers.
        op.execute("SET LOCAL lock_timeout = '10s'")
        for column in _task_columns():
            op.add_column(TASKS, column)
        op.create_check_constraint(MATCHES_CONSTRAINT, TASKS, MATCHES_CONDITION)
        op.create_check_constraint(RANGE_CONSTRAINT, TASKS, RANGE_CONDITION)
    else:
        with op.batch_alter_table(TASKS) as batch:
            for column in _task_columns():
                batch.add_column(column)
            batch.create_check_constraint(MATCHES_CONSTRAINT, MATCHES_CONDITION)
            batch.create_check_constraint(RANGE_CONSTRAINT, RANGE_CONDITION)

    op.create_table(
        ATTEMPTS,
        sa.Column('timed_attempt_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('window_number', sa.Integer(), nullable=False),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('opened_with_retake', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.CheckConstraint('window_number > 0', name='ck_timed_attempts_window_number'),
        sa.CheckConstraint('time_limit_minutes BETWEEN 1 AND 480', name='ck_timed_attempts_time_limit'),
        sa.ForeignKeyConstraint(['student_id'], ['users.user_id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.task_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('timed_attempt_id'),
        sa.UniqueConstraint('student_id', 'task_id', 'window_number', name='uq_timed_attempts_window'),
    )
    op.create_index(op.f('ix_timed_attempts_task_id'), ATTEMPTS, ['task_id'], unique=False)
    op.create_index('ix_timed_attempts_student_task', ATTEMPTS, ['student_id', 'task_id'], unique=False)


def downgrade() -> None:
    if context.is_offline_mode():
        raise RuntimeError(
            "18a56b9b5fa8 (downgrade) cannot run in offline (--sql) mode: it must "
            "first check that no activity is timed."
        )

    timed = op.get_bind().execute(
        sa.text(f"SELECT count(*) FROM {TASKS} WHERE is_timed")
    ).scalar_one()

    if timed:
        raise RuntimeError(
            f"Cannot downgrade 18a56b9b5fa8: {timed} activity(ies) are timed. "
            "Downgrading would drop their time limits and every student's timer. "
            "Turn the time limit off on those activities first."
        )

    op.drop_index('ix_timed_attempts_student_task', table_name=ATTEMPTS)
    op.drop_index(op.f('ix_timed_attempts_task_id'), table_name=ATTEMPTS)
    op.drop_table(ATTEMPTS)

    if op.get_context().dialect.name == 'postgresql':
        op.execute("SET LOCAL lock_timeout = '10s'")
        op.drop_constraint(RANGE_CONSTRAINT, TASKS, type_='check')
        op.drop_constraint(MATCHES_CONSTRAINT, TASKS, type_='check')
        op.drop_column(TASKS, 'time_limit_minutes')
        op.drop_column(TASKS, 'is_timed')
    else:
        with op.batch_alter_table(TASKS) as batch:
            batch.drop_constraint(RANGE_CONSTRAINT, type_='check')
            batch.drop_constraint(MATCHES_CONSTRAINT, type_='check')
            batch.drop_column('time_limit_minutes')
            batch.drop_column('is_timed')
