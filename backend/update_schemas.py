import os
import re

filepath = "app/schemas/user_schema.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace name with first, middle, last
content = content.replace("    name: str = Field(..., min_length=1, max_length=150)\n", 
"""    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)\n""")

content = content.replace('@field_validator("name")\n    @classmethod\n    def validate_name(cls, value: str) -> str:\n        normalized_name = " ".join(value.split())\n\n        if not normalized_name:\n            raise ValueError("Name is required.")\n\n        return normalized_name',
"""    @field_validator("first_name", "last_name", "middle_name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = " ".join(value.split())
        return normalized""")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

filepath = "app/schemas/auth_schema.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()
if "full_name: str" in content:
    content = content.replace("full_name: str", "first_name: str\n    middle_name: str | None\n    last_name: str")
if "name: str" in content:
    content = content.replace("name: str", "first_name: str\n    middle_name: str | None\n    last_name: str")
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
    
filepath = "app/routers/admin.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace("full_name: str", "first_name: str\n    last_name: str")
content = content.replace("full_name=request.full_name", "first_name=request.first_name, last_name=request.last_name")
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated schemas")
