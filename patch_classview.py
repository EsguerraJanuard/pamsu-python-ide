import re

filepath = 'frontend/src/features/instructor/grading/GradingClassView.jsx'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('<main className="p-8 bg-transparent min-h-screen text-text-main">', '<main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8 text-text-main">')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
