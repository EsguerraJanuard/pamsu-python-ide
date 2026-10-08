import os

filepath = "backend/app/schemas/user_schema.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

if "academic_integrity_score" not in content:
    content = content.replace("school_id: str", "school_id: str\n    academic_integrity_score: float = 100.0")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated schema")
