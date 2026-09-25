import re
with open('backend/app/routers/classrooms.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('\\n\n@router.delete(', '\n@router.delete(')

with open('backend/app/routers/classrooms.py', 'w', encoding='utf-8') as f:
    f.write(c)