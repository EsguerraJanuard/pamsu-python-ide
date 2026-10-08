import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("import { useAuth } from '../auth/AuthContext';", "import { useAuth } from '../auth/AuthContext';\nimport { useInView } from 'react-intersection-observer';")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed imports")
