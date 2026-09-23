"""Merge multiple heads

Revision ID: 068b56b87330
Revises: 2cd5c3a3ee9a, e2b33e751f23
Create Date: 2026-09-22 16:42:38.531934+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '068b56b87330'
down_revision: Union[str, Sequence[str], None] = ('2cd5c3a3ee9a', 'e2b33e751f23')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
