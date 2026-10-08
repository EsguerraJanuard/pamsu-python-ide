import os

filepath = "backend/tests/test_review_queue_workflow.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('item["student"]["name"]', 'f\'{item["student"]["first_name"]} {item["student"]["last_name"]}\'')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

filepath = "backend/tests/test_security.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('payload["name"] == "Test Instructor"', 'payload["first_name"] == "Test" and payload["last_name"] == "Instructor"')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed assertions")
