import re
with open('backend/app/models/domain_models.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Undo User index
c = c.replace(
"""class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_tasks_class_pub", "class_id", "is_published"),
        CheckConstraint(
            "role IN ('student', 'instructor')",
            name="ck_users_role",
        ),
    )""",
"""class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('student', 'instructor')",
            name="ck_users_role",
        ),
    )""")

# Add Task index properly
task_replace = """class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_class_pub", "class_id", "is_published"),
        CheckConstraint(
            "activity_type IN ('laboratory', 'homework')",
            name="ck_tasks_activity_type",
        ),"""

c = c.replace("""class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "activity_type IN ('laboratory', 'homework')",
            name="ck_tasks_activity_type",
        ),""", task_replace)

with open('backend/app/models/domain_models.py', 'w', encoding='utf-8') as f:
    f.write(c)