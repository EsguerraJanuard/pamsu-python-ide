import os
import re

filepath = "backend/app/services/classroom_service.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("User.name.asc()", "User.last_name.asc(), User.first_name.asc()")
content = content.replace('"name": user.name,', '"name": f"{user.first_name} {user.last_name}",')
content = content.replace('"name": instructor.name', '"name": f"{instructor.first_name} {instructor.last_name}"')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)


filepath = "backend/app/services/coding_session_service.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# .label("student_name")
content = content.replace('User.name.label("student_name"),', '(User.first_name + " " + User.last_name).label("student_name"),')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed service references")
