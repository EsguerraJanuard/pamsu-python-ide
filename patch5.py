import re
with open('frontend/src/features/dashboard/StudentDashboard.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    'className="dashboard-card relative overflow-hidden',
    'onClick={() => navigate(\'/student/assignments\')} className="cursor-pointer dashboard-card relative overflow-hidden'
)

with open('frontend/src/features/dashboard/StudentDashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(c)