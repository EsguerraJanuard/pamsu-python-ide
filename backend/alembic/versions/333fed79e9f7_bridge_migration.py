"""bridge_migration

Revision ID: 333fed79e9f7
Revises: 068b56b87330
Create Date: 2026-10-01 05:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '333fed79e9f7'
down_revision: Union[str, Sequence[str], None] = '068b56b87330'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
