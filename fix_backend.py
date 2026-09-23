import os

# 1. Fix OTP Service ImportError
otp_path = 'backend/app/services/otp_service.py'
with open(otp_path, 'r') as f:
    otp_code = f.read()

otp_code = otp_code.replace('from app.core.request_context import get_utc_now\n', '')
otp_code = otp_code.replace('get_utc_now()', 'utc_now()')

with open(otp_path, 'w') as f:
    f.write(otp_code)

# 2. Fix Redis NameError in security.py
sec_path = 'backend/app/core/security.py'
with open(sec_path, 'r') as f:
    sec_code = f.read()

if 'import redis' not in sec_code:
    sec_code = 'import redis\n' + sec_code
    with open(sec_path, 'w') as f:
        f.write(sec_code)

# 3. Fix Student access required in security.py
# If current_user.role != 'student':
# We'll allow 'student' and 'student_user' and also handle potential trailing spaces
sec_code = sec_code.replace('if current_user.role != \"student\":', 'if current_user.role.strip() not in [\"student\", \"student_user\"]:')
with open(sec_path, 'w') as f:
    f.write(sec_code)

print('Done fixing.')
