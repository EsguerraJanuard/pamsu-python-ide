import os

filepath = "frontend/src/components/layout/InstructorLayout.jsx"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace('<main className="flex-1 overflow-y-auto p-8">', '<main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">\n        <div className="max-w-6xl mx-auto w-full">')
    
    # We need to add the closing div for max-w-6xl. Since InstructorLayout probably has <Outlet /> inside main:
    content = content.replace('</main>', '</div>\n      </main>')
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Fixed InstructorLayout")
