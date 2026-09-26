import re
with open('backend/app/models/domain_models.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Add index to Enrollment
enrollment_args = """__table_args__ = (
        UniqueConstraint(
            "class_id",
            "student_id",
            name="uq_enrollment_class_student",
        ),
        Index("ix_enrollments_class_student", "class_id", "student_id"),"""

c = c.replace("""__table_args__ = (
        UniqueConstraint(
            "class_id",
            "student_id",
            name="uq_enrollment_class_student",
        ),""", enrollment_args)

# Add index to Task
task_args = """__table_args__ = (
        Index("ix_tasks_class_pub", "class_id", "is_published"),
        CheckConstraint("""
c = c.replace("""__table_args__ = (
        CheckConstraint(""", task_args, 1) # Only first one for Task table

# Add index to Submission
sub_args = """__table_args__ = (
        Index("ix_submissions_task_student", "task_id", "student_id"),
        UniqueConstraint("""
c = c.replace("""__table_args__ = (
        UniqueConstraint(
            "student_id",
            "task_id",
            "attempt_number",
            name="uq_submission_attempt",
        ),""", sub_args + """
            "student_id",
            "task_id",
            "attempt_number",
            name="uq_submission_attempt",
        ),""")

with open('backend/app/models/domain_models.py', 'w', encoding='utf-8') as f:
    f.write(c)