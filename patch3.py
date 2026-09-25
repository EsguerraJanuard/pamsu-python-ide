import re
with open('frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    'subsMap[sub.student.student_id] = sub;',
    'if (!subsMap[sub.student.student_id]) { subsMap[sub.student.student_id] = sub; }'
)

with open('frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx', 'w', encoding='utf-8') as f:
    f.write(c)