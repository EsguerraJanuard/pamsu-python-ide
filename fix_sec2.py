import os

sec_path = 'backend/app/core/security.py'
with open(sec_path, 'r') as f:
    sec_code = f.read()

if 'import redis' not in sec_code:
    sec_code = 'import redis\n' + sec_code

sec_code = sec_code.replace('if current_user.role != "student":', 'if current_user.role.strip() not in ["student", "student_user"]:')

with open(sec_path, 'w') as f:
    f.write(sec_code)

print("done")
