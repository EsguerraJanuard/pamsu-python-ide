import os

filepath = "backend/app/models/domain_models.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "return self.instructor.name if self.instructor else None",
    'return f"{self.instructor.first_name} {self.instructor.last_name}" if self.instructor else None'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed domain_models")
