import os
import re

files_to_fix = [
    ("backend/tests/test_schemas.py", '"name": "Test Student",', '"first_name": "Test", "last_name": "Student",'),
    ("backend/tests/test_security.py", '"name": "Test Instructor",', '"first_name": "Test", "last_name": "Instructor",'),
    ("backend/tests/test_pillar10_privacy_contracts.py", '"name": "Privacy Contract Student",', '"first_name": "Privacy Contract", "last_name": "Student",')
]

for filepath, old, new in files_to_fix:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace(old, new)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Fixed dictionary keys")
