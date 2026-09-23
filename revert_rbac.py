import os

filepath = 'backend/app/core/security.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Revert the student role check
old_check = 'if current_user.role.strip() not in ["student", "student_user"]:'
new_check = 'if current_user.role != "student":'
if old_check in content:
    content = content.replace(old_check, new_check)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully reverted student role check in security.py")
else:
    print("Could not find the modified student role check in security.py")
