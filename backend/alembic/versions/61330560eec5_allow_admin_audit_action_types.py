"""allow_admin_audit_action_types

Revision ID: 61330560eec5
Revises: c25114413200
Create Date: 2026-10-18 13:00:00.000000+00:00

DRAFT FOR REVIEW - NOT APPLIED ANYWHERE.
See audit-status.md, "Admin audit logging: investigation and migration
proposal (2026-10-18)".

Admin actions (account creation, activation/deactivation, password reset,
deletion, system settings) write no audit record because the CHECK
constraints on audit_records only allow the action and resource types the
baseline (18d3ef8f020d) listed. This revision widens both constraints:

- ck_audit_records_action_type gains user_created, user_status_changed,
  user_password_reset, user_deleted, system_settings_updated and
  masterlist_imported (one summary event per MIS masterlist upload);
- ck_audit_records_resource_type gains system_setting and masterlist_import.

The new lists are strict supersets of the old ones, so every existing row
stays valid and no row is changed or deleted. Re-adding a CHECK constraint
scans audit_records once to validate it, under the ACCESS EXCLUSIVE lock that
DROP/ADD CONSTRAINT take and hold until the migration transaction commits.
Reads and writes of audit_records (every audited action) wait during that
time; the table is small (37 rows locally), and lock_timeout makes the
migration fail fast instead of queueing behind a long transaction.

Downgrade restores the baseline lists. It refuses (and changes nothing) when
any row already uses one of the new types: audit records are immutable, so
they are never deleted or rewritten to make the downgrade fit.
"""
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61330560eec5'
down_revision: Union[str, Sequence[str], None] = 'c25114413200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Baseline lists (18d3ef8f020d), in the same order.
BASE_ACTION_TYPES = (
    'user_registered',
    'login_succeeded',
    'login_failed',
    'classroom_created',
    'classroom_updated',
    'classroom_archived',
    'classroom_reactivated',
    'student_enrolled',
    'enrollment_status_changed',
    'activity_created',
    'activity_updated',
    'activity_published',
    'activity_unpublished',
    'submission_created',
    'submission_status_changed',
    'grade_created',
    'grade_updated',
    'grade_released',
    'notification_marked_read',
    'notifications_marked_read',
)
BASE_RESOURCE_TYPES = (
    'user',
    'classroom',
    'enrollment',
    'task',
    'submission',
    'grade',
    'notification',
)

NEW_ACTION_TYPES = (
    'user_created',
    'user_status_changed',
    'user_password_reset',
    'user_deleted',
    'system_settings_updated',
    'masterlist_imported',
)
NEW_RESOURCE_TYPES = ('system_setting', 'masterlist_import')

ACTION_CONSTRAINT = 'ck_audit_records_action_type'
RESOURCE_CONSTRAINT = 'ck_audit_records_resource_type'


def _in_list(column: str, values: Sequence[str]) -> str:
    quoted = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({quoted})"


def _replace_check(name: str, condition: str) -> None:
    if op.get_context().dialect.name == 'postgresql':
        # Short lock wait: fail fast instead of queueing behind long writers.
        op.execute("SET LOCAL lock_timeout = '10s'")
        op.drop_constraint(name, 'audit_records', type_='check')
        op.create_check_constraint(name, 'audit_records', condition)
    else:
        with op.batch_alter_table('audit_records') as batch:
            batch.drop_constraint(name, type_='check')
            batch.create_check_constraint(name, condition)


def upgrade() -> None:
    _replace_check(ACTION_CONSTRAINT, _in_list('action_type', BASE_ACTION_TYPES + NEW_ACTION_TYPES))
    _replace_check(RESOURCE_CONSTRAINT, _in_list('resource_type', BASE_RESOURCE_TYPES + NEW_RESOURCE_TYPES))


def downgrade() -> None:
    if context.is_offline_mode():
        raise RuntimeError(
            "61330560eec5 (downgrade) cannot run in offline (--sql) mode: it must "
            "first check that no audit record uses an action or resource type "
            "this revision added."
        )

    bind = op.get_bind()
    in_use = bind.execute(
        sa.text(
            "SELECT count(*) FROM audit_records "
            "WHERE action_type IN :actions OR resource_type IN :resources"
        ).bindparams(
            sa.bindparam('actions', expanding=True),
            sa.bindparam('resources', expanding=True),
        ),
        {'actions': list(NEW_ACTION_TYPES), 'resources': list(NEW_RESOURCE_TYPES)},
    ).scalar_one()

    if in_use:
        raise RuntimeError(
            f"Cannot downgrade 61330560eec5: {in_use} audit record(s) use admin "
            "action or resource types added by this revision. Audit records are "
            "immutable and are not deleted to make a downgrade fit; restore from "
            "a backup taken before the upgrade instead."
        )

    _replace_check(RESOURCE_CONSTRAINT, _in_list('resource_type', BASE_RESOURCE_TYPES))
    _replace_check(ACTION_CONSTRAINT, _in_list('action_type', BASE_ACTION_TYPES))
