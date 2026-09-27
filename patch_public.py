with open('backend/tests/test_openapi_contracts.py', 'r') as f:
    c = f.read()

c = c.replace('("post", "/registration/resend"),', '("post", "/registration/resend"),\n    ("post", "/users/password-reset/start"),\n    ("post", "/users/password-reset/verify"),\n    ("post", "/users/password-reset/complete"),\n    ("post", "/users/password-reset/resend"),')

with open('backend/tests/test_openapi_contracts.py', 'w') as f:
    f.write(c)