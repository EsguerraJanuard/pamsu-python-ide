with open('backend/tests/test_task_openapi_contracts.py', 'r') as f:
    c = f.read()

c = c.replace('"due_at",', '"due_at",\n        "difficulty",')

with open('backend/tests/test_task_openapi_contracts.py', 'w') as f:
    f.write(c)