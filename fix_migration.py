import os

filepath = "backend/alembic/versions/06d1a312becc_add_academic_integrity_score.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "op.add_column('users', sa.Column('academic_integrity_score', sa.Float(), nullable=False))",
    "op.add_column('users', sa.Column('academic_integrity_score', sa.Float(), nullable=False, server_default='100.0'))"
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed migration")
