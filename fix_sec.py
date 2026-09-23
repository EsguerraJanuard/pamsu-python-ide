import sys
with open('backend/app/core/security.py', 'r') as f:
    content = f.read()
if 'import redis' not in content:
    content = 'import redis\n' + content
    with open('backend/app/core/security.py', 'w') as f:
        f.write(content)