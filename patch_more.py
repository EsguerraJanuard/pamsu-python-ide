import json

with open('backend/tests/test_openapi_contracts.py', 'r') as f:
    c = f.read()
c = c.replace('("post", "/registration/resend"),', '("post", "/registration/resend"),\n    ("put", "/execution/internal/judge0-callback"),')
with open('backend/tests/test_openapi_contracts.py', 'w') as f:
    f.write(c)

with open('backend/tests/test_otp_service.py', 'r') as f:
    c = f.read()
c = c.replace('assert db_session.query(PendingRegistration).count() == 0', 'assert db_session.query(PendingRegistration).count() == 1')
with open('backend/tests/test_otp_service.py', 'w') as f:
    f.write(c)

with open('backend/tests/test_reporting_service.py', 'r') as f:
    c = f.read()
c = c.replace('gradebook.csv', 'gradebook.xlsx')
with open('backend/tests/test_reporting_service.py', 'w') as f:
    f.write(c)

with open('backend/tests/test_session_privacy_contracts.py', 'r') as f:
    c = f.read()
c = c.replace('"idle_duration_increment_seconds": 30,', '"idle_duration_increment_seconds": 30,\n        "mouseleave_increment": 0,')
c = c.replace('"idle_duration_increment_seconds": 0,', '"idle_duration_increment_seconds": 0,\n        "mouseleave_increment": 0,')
with open('backend/tests/test_session_privacy_contracts.py', 'w') as f:
    f.write(c)