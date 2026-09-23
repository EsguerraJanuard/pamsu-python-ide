import sys
with open('backend/app/core/security.py', 'r') as f:
    content = f.read()
if 'import redis' not in content:
    content = 'import redis\n' + content
    with open('backend/app/core/security.py', 'w') as f:
        f.write(content)

with open('backend/tests/test_alembic_migrations.py', 'r') as f:
    content = f.read()
new_tables = '"practice_tasks", "pending_enrollments", "practice_modules", "practice_progress", "practice_attempts", "practice_test_cases"'
if 'practice_tasks' not in content:
    content = content.replace('EXPECTED_APPLICATION_TABLES = {', 'EXPECTED_APPLICATION_TABLES = {\n    ' + new_tables + ',')
    with open('backend/tests/test_alembic_migrations.py', 'w') as f:
        f.write(content)