"""Add mouseleave_count to logs and sessions

Revision ID: 8d2f5e3c7a1b
Revises: 49950d8efb8d
Create Date: 2026-08-20 23:51:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d2f5e3c7a1b'
down_revision: Union[str, Sequence[str], None] = '49950d8efb8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('behavioral_logs', sa.Column('mouseleave_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('coding_sessions', sa.Column('mouseleave_count', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('coding_sessions', 'mouseleave_count')
    op.drop_column('behavioral_logs', 'mouseleave_count')
