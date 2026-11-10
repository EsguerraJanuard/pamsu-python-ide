"""split_user_name_and_add_admin_role

Revision ID: c5d2f62cc22e
Revises: 9ff2d118b666
Create Date: 2026-10-01 10:51:36.654274+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5d2f62cc22e'
down_revision: Union[str, Sequence[str], None] = '9ff2d118b666'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

