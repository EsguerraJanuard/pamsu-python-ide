import os
import re

filepath = "app/models/domain_models.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Update User model
old_name = "    name = Column(String(150), nullable=False)"
new_names = """    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)"""

content = content.replace(old_name, new_names)

# Update check constraint
content = content.replace("'student', 'instructor'", "'student', 'instructor', 'admin'")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated domain_models.py")
