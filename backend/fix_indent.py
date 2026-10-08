import os

filepath = "app/schemas/user_schema.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("        @field_validator", "    @field_validator")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed indentation")
