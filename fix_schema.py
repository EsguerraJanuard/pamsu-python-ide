import re
with open('backend/app/schemas/task_schema.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'difficulty: ActivityDifficulty\n', 'difficulty: ActivityDifficulty = "beginner"\n', content)
with open('backend/app/schemas/task_schema.py', 'w', encoding='utf-8') as f:
    f.write(content)