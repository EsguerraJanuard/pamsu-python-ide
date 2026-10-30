"""track_practice_attempt_status

Revision ID: b7e4c2a91f03
Revises: 61330560eec5
Create Date: 2026-10-22 09:00:00.000000+00:00

Practice submissions no longer wait on Judge0 inside the request ("Full
backend audit" item 5 in audit-status.md: the 3-second rule). The attempt is
saved first, Judge0 runs it in the background and calls back, and the page
polls. An attempt therefore needs a state of its own:

- status: 'pending' while Judge0 runs, 'completed' once judged, 'failed' when
  the code could not be run (queue or Judge0 unavailable, no answer in time).
  NOT NULL with server default 'completed': every existing row was judged
  synchronously, and the previous code, which may still be serving while a
  deploy switches over, inserts rows without the column.
- correlation_id: a random UUID that only the server and Judge0 see (it is in
  the callback URL). The callback must present it. Unique; NULL for old rows.
- completed_at: when the verdict (or the failure) was recorded.

is_successful keeps its meaning. Pending and failed attempts are stored with
is_successful = false and are left out of the practice statistics, which
count only completed attempts.

PostgreSQL 11+ adds a NOT NULL column with a constant default without
rewriting the table. The CHECK constraint is validated with one scan of
practice_attempts, and the unique constraint builds one index; both hold the
ACCESS EXCLUSIVE lock until the migration commits. lock_timeout makes the
migration fail fast (and roll back) instead of queueing behind a long
transaction.

Downgrade drops the three columns. It refuses while any attempt is pending or
failed: without the status column those rows would read as judged, failed
attempts by the student.
"""
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e4c2a91f03'
down_revision: Union[str, Sequence[str], None] = '61330560eec5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE = 'practice_attempts'
STATUS_CONSTRAINT = 'ck_practice_attempts_status'
CORRELATION_CONSTRAINT = 'uq_practice_attempts_correlation_id'
STATUSES = ('pending', 'completed', 'failed')


def _status_condition() -> str:
    quoted = ", ".join(f"'{value}'" for value in STATUSES)
    return f"status IN ({quoted})"


def upgrade() -> None:
    columns = (
        sa.Column('status', sa.String(length=20), nullable=False, server_default='completed'),
        sa.Column('correlation_id', sa.String(length=36), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    if op.get_context().dialect.name == 'postgresql':
        # Short lock wait: fail fast instead of queueing behind long writers.
        op.execute("SET LOCAL lock_timeout = '10s'")
        for column in columns:
            op.add_column(TABLE, column)
        op.create_check_constraint(STATUS_CONSTRAINT, TABLE, _status_condition())
        op.create_unique_constraint(CORRELATION_CONSTRAINT, TABLE, ['correlation_id'])
    else:
        with op.batch_alter_table(TABLE) as batch:
            for column in columns:
                batch.add_column(column)
            batch.create_check_constraint(STATUS_CONSTRAINT, _status_condition())
            batch.create_unique_constraint(CORRELATION_CONSTRAINT, ['correlation_id'])


def downgrade() -> None:
    if context.is_offline_mode():
        raise RuntimeError(
            "b7e4c2a91f03 (downgrade) cannot run in offline (--sql) mode: it must "
            "first check that no practice attempt is pending or failed."
        )

    unjudged = op.get_bind().execute(
        sa.text(f"SELECT count(*) FROM {TABLE} WHERE status <> 'completed'")
    ).scalar_one()

    if unjudged:
        raise RuntimeError(
            f"Cannot downgrade b7e4c2a91f03: {unjudged} practice attempt(s) are "
            "pending or failed. Without the status column they would read as "
            "judged attempts that the student failed. Wait for pending attempts "
            "to finish, then review and remove the failed ones (they are system "
            "failures, not student work) before downgrading."
        )

    if op.get_context().dialect.name == 'postgresql':
        op.execute("SET LOCAL lock_timeout = '10s'")
        op.drop_constraint(CORRELATION_CONSTRAINT, TABLE, type_='unique')
        op.drop_constraint(STATUS_CONSTRAINT, TABLE, type_='check')
        op.drop_column(TABLE, 'completed_at')
        op.drop_column(TABLE, 'correlation_id')
        op.drop_column(TABLE, 'status')
    else:
        with op.batch_alter_table(TABLE) as batch:
            batch.drop_constraint(CORRELATION_CONSTRAINT, type_='unique')
            batch.drop_constraint(STATUS_CONSTRAINT, type_='check')
            batch.drop_column('completed_at')
            batch.drop_column('correlation_id')
            batch.drop_column('status')
