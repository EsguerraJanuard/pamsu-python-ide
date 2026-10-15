"""phase3_business_logic_and_settings

Revision ID: 7a1b8c2d3e4f
Revises: 06d1a312becc
Create Date: 2026-10-15 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a1b8c2d3e4f'
down_revision: Union[str, Sequence[str], None] = '06d1a312becc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create system_settings table
    system_settings_table = op.create_table(
        'system_settings',
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )

    # Seed initial system settings
    op.bulk_insert(
        system_settings_table,
        [
            {'key': 'maintenance_mode', 'value': 'false'},
            {'key': 'default_ast_strictness', 'value': 'moderate'},
            {'key': 'registration_enabled', 'value': 'false'},
        ]
    )

    # 2. Update ck_otp_purpose constraint
    with op.batch_alter_table('otp_challenges', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('ck_otp_purpose', type_='check')
        except Exception:
            pass
        batch_op.create_check_constraint(
            'ck_otp_purpose',
            "purpose IN ('registration', 'email_change', 'password_reset')"
        )

    # 3. Update ck_users_role constraint
    with op.batch_alter_table('users', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('ck_users_role', type_='check')
        except Exception:
            pass
        batch_op.create_check_constraint(
            'ck_users_role',
            "role IN ('student', 'instructor', 'admin')"
        )


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('ck_users_role', type_='check')
        except Exception:
            pass
        batch_op.create_check_constraint(
            'ck_users_role',
            "role IN ('student', 'instructor')"
        )

    with op.batch_alter_table('otp_challenges', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('ck_otp_purpose', type_='check')
        except Exception:
            pass
        batch_op.create_check_constraint(
            'ck_otp_purpose',
            "purpose IN ('registration', 'email_change')"
        )

    op.drop_table('system_settings')
