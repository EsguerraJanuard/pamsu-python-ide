import re
with open('backend/app/main.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    'allow_methods=[',
    'max_age=86400,\n        allow_methods=['
)

with open('backend/app/main.py', 'w', encoding='utf-8') as f:
    f.write(c)