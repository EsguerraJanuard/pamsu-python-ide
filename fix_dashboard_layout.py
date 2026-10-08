import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update aside and main
content = content.replace('<div className="flex">', '<div className="flex min-h-[calc(100vh-73px)]">')
content = content.replace('<aside className="w-64 border-r border-border-subtle min-h-[calc(100vh-73px)] p-6 space-y-2">', '<aside className="w-56 lg:w-64 shrink-0 border-r border-border-subtle p-4 lg:p-6 space-y-2 overflow-y-auto">')
content = content.replace('<main className="flex-1 p-8">', '<main className="flex-1 min-w-0 p-4 lg:p-8 overflow-x-hidden">\n          <div className="max-w-6xl mx-auto w-full">')

# 2. Add closing div for the max-w-6xl wrapper
content = content.replace('</main>', '  </div>\n        </main>')

# 3. Add overflow-x-auto to the tables that only have overflow-y-auto
content = content.replace('className="overflow-y-auto flex-1 border border-border-subtle rounded-lg"', 'className="overflow-x-auto overflow-y-auto flex-1 border border-border-subtle rounded-lg"')
content = content.replace('className="overflow-y-auto flex-1"', 'className="overflow-x-auto overflow-y-auto flex-1"')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed AdminDashboard layout")
