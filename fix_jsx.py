import os

files_to_fix = [
    "frontend/src/features/dashboard/StudentDashboard.jsx",
    "frontend/src/features/classes/MyClasses.jsx",
    "frontend/src/features/classes/ClassDetails.jsx",
    "frontend/src/components/modals/StudentGradebookModal.jsx",
    "frontend/src/features/dashboard/ClassRosterView.jsx"
]

for file in files_to_fix:
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Fix studentName={user?.first_name} {user?.last_name}
        content = content.replace("studentName={user?.first_name} {user?.last_name}", "studentName={`${user?.first_name} ${user?.last_name}`}")
        content = content.replace("studentName={student?.first_name} {student?.last_name}", "studentName={`${student?.first_name} ${student?.last_name}`}")
        content = content.replace("={user?.first_name} {user?.last_name}", "={`${user?.first_name} ${user?.last_name}`}")
        content = content.replace("={student?.first_name} {student?.last_name}", "={`${student?.first_name} ${student?.last_name}`}")

        with open(file, "w", encoding="utf-8") as f:
            f.write(content)

print("Fixed JSX props")
