import os
import glob

jsx_files = [
    'frontend/src/components/layout/InstructorSidebar.jsx',
    'frontend/src/components/layout/Sidebar.jsx',
    'frontend/src/features/admin/AdminDashboard.jsx',
    'frontend/src/features/auth/Login.jsx'
]

for filepath in jsx_files:
    if not os.path.exists(filepath):
        continue
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "logo-192.png" in content:
        content = content.replace("logo-192.png", "school_logo.png")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Reverted {filepath}")
