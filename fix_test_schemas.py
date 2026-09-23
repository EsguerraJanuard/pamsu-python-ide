import re
with open('backend/tests/test_schemas.py', 'r') as f:
    content = f.read()
content = content.replace('"class_id": 1,', '"class_ids": [1], "difficulty": "beginner",')
with open('backend/tests/test_schemas.py', 'w') as f:
    f.write(content)