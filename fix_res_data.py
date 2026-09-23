import os

filepath = 'frontend/src/features/practice/PracticeWorkspace.jsx'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('setFeedback(res.data);', 'setFeedback(res);')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
