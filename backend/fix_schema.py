import os

filepath = "app/schemas/user_schema.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    '    school_id: str\n    academic_integrity_score: float = 100.0 = Field(..., pattern=r"^(\d{10}|\d{4}-\d{5})$")',
    '    school_id: str = Field(..., pattern=r"^(\d{10}|\d{4}-\d{5})$")\n    academic_integrity_score: float = 100.0'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed user schema syntax")
