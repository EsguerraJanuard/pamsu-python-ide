import re
with open('frontend/src/features/instructor/grading/GradingBenchRoot.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    "setClasses(response);",
    "setClasses(Array.isArray(response) ? response : (response?.data || []));"
)

with open('frontend/src/features/instructor/grading/GradingBenchRoot.jsx', 'w', encoding='utf-8') as f:
    f.write(c)