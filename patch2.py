import re
with open('frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('/instructors/review-queue?task_id= + ""', '/instructors/review-queue?task_id=&page_size=100')
c = c.replace('/instructors/review-queue?task_id={taskId}', '/instructors/review-queue?task_id={taskId}&page_size=100')
with open('frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx', 'w', encoding='utf-8') as f:
    f.write(c)