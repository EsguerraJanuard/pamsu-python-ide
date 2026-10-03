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
    # 1. Add new columns
    op.add_column('users', sa.Column('first_name', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('middle_name', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(length=100), nullable=True))

    # 2. Data migration using Python for DB compatibility
    connection = op.get_bind()
    from sqlalchemy.sql import text
    users = connection.execute(text("SELECT user_id, name FROM users")).fetchall()
    
    for user_id, name in users:
        parts = name.split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        middle_name = ""
        connection.execute(
            text("UPDATE users SET first_name = :f, last_name = :l, middle_name = :m WHERE user_id = :id"),
            {"f": first_name, "l": last_name, "m": middle_name, "id": user_id}
        )

    # 3. Make columns not nullable
    op.alter_column('users', 'first_name', nullable=False)
    op.alter_column('users', 'last_name', nullable=False)

    # 4. Drop old name column
    op.drop_column('users', 'name')

    # 5. Update Check Constraint for role
    op.drop_constraint('ck_users_role', 'users', type_='check')
    op.create_check_constraint(
        'ck_users_role',
        'users',
        "role IN ('student', 'instructor', 'admin')"
    )

def downgrade() -> None:
    # Reverse of upgrade
    op.add_column('users', sa.Column('name', sa.String(length=150), nullable=True))
    
    connection = op.get_bind()
    from sqlalchemy.sql import text
    users = connection.execute(text("SELECT user_id, first_name, middle_name, last_name FROM users")).fetchall()
    
    for user_id, f, m, l in users:
        parts = [p for p in (f, m, l) if p]
        name = " ".join(parts)
        connection.execute(
            text("UPDATE users SET name = :n WHERE user_id = :id"),
            {"n": name, "id": user_id}
        )
        
    op.alter_column('users', 'name', nullable=False)
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'middle_name')
    op.drop_column('users', 'last_name')
    
    op.drop_constraint('ck_users_role', 'users', type_='check')
    op.create_check_constraint(
        'ck_users_role',
        'users',
        "role IN ('student', 'instructor')"
    )

