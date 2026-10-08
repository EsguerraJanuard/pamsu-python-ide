import os
import re

filepath = "backend/tests/test_schemas.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace user.name with f"{user.first_name} {user.last_name}" or assert user.first_name == "Test" and user.last_name == "Student"
content = re.sub(
    r'assert user\.name == "(.*?)"',
    r'assert user.first_name == "\1".split()[0] and user.last_name == " ".join("\1".split()[1:])',
    content
)

# Also check if it creates the schema with name="..."
content = re.sub(
    r'name="(.*?)"',
    r'first_name="\1".split()[0], last_name=" ".join("\1".split()[1:]) if " " in "\1" else "User"',
    content
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed test_schemas.py")
