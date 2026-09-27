with open('backend/tests/test_session_privacy_contracts.py', 'r') as f:
    c = f.read()

c = c.replace('"idle_duration_seconds",', '"idle_duration_seconds",\n        "mouseleave_count",')
c = c.replace('"idle_duration_increment_seconds",', '"idle_duration_increment_seconds",\n        "mouseleave_increment",')

with open('backend/tests/test_session_privacy_contracts.py', 'w') as f:
    f.write(c)

with open('backend/tests/test_openapi_contracts.py', 'r') as f:
    d = f.read()

d = d.replace('"idle_duration_increment_seconds",', '"idle_duration_increment_seconds",\n        "mouseleave_increment",')
d = d.replace('("POST", "/users/login"),', '("POST", "/users/login"),\n    ("POST", "/users/password-reset/start"),\n    ("POST", "/users/password-reset/complete"),')

with open('backend/tests/test_openapi_contracts.py', 'w') as f:
    f.write(d)