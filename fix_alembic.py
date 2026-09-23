import re
with open('backend/tests/test_alembic_migrations.py', 'r', encoding='utf-8') as f:
    content = f.read()
block = """'practice_tasks', 'pending_enrollments', 'practice_modules', 'practice_progress', 'practice_attempts', 'practice_test_cases',"""
if 'practice_tasks' not in content:
    content = content.replace('EXPECTED_APPLICATION_TABLES = {', 'EXPECTED_APPLICATION_TABLES = {\n    ' + block)
    with open('backend/tests/test_alembic_migrations.py', 'w', encoding='utf-8') as f:
        f.write(content)