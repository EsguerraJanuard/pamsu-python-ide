import re
with open('frontend/src/features/dashboard/StudentDashboard.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    'className={dashboard-card rounded-xl border border-l-[3px]',
    'onClick={() => navigate(/student/workspace?activity=)} className={cursor-pointer dashboard-card rounded-xl border border-l-[3px]'
)

with open('frontend/src/features/dashboard/StudentDashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(c)