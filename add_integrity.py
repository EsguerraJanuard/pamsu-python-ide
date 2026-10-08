import os
import re

filepath = "backend/app/models/domain_models.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add academic_integrity_score
if "academic_integrity_score" not in content:
    content = content.replace("    password_hash = Column(", "    academic_integrity_score = Column(Float, default=100.0, nullable=False)\n    password_hash = Column(", 1)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated User model")
