import os

files_to_fix = [
    "frontend/src/features/dashboard/Analytics.jsx",
    "frontend/src/features/assignments/Assignments.jsx",
    "frontend/src/features/settings/Settings.jsx",
    "frontend/src/features/submissions/Submissions.jsx",
    "frontend/src/features/submissions/SubmissionDetails.jsx"
]

for filepath in files_to_fix:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "max-w" not in content.split("<main")[1][:200]:
            # Replace <main className="..."> with the main tag + max-w wrapper
            main_tag = content[content.find("<main"):content.find(">", content.find("<main"))+1]
            content = content.replace(main_tag, main_tag + '\n        <div className="max-w-6xl mx-auto w-full">')
            content = content.replace('</main>', '</div>\n      </main>')
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

print("Added max-w-6xl wrappers to Analytics, Assignments, Settings, Submissions")
