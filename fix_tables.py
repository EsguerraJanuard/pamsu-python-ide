import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix Faculty Table
content = content.replace(
    '<tr>\n                            <th className="px-4 py-3">Name</th>\n                            <th className="px-4 py-3">Email</th>\n                            <th className="px-4 py-3">Status</th>\n                            <th className="px-4 py-3 text-right">Actions</th>\n                          </tr>',
    '<tr>\n                            <th className="px-4 py-3 w-[35%]">Name</th>\n                            <th className="px-4 py-3 w-[40%]">Email</th>\n                            <th className="px-4 py-3 w-[15%]">Status</th>\n                            <th className="px-4 py-3 w-[10%] text-right">Actions</th>\n                          </tr>'
)

# Fix Student Table
content = content.replace(
    '<tr>\n                            <th className="px-4 py-3">Name</th>\n                            <th className="px-4 py-3">PSU Email</th>\n                            <th className="px-4 py-3">Status</th>\n                            <th className="px-4 py-3 text-right">Actions</th>\n                          </tr>',
    '<tr>\n                            <th className="px-4 py-3 w-[35%]">Name</th>\n                            <th className="px-4 py-3 w-[40%]">PSU Email</th>\n                            <th className="px-4 py-3 w-[15%]">Status</th>\n                            <th className="px-4 py-3 w-[10%] text-right">Actions</th>\n                          </tr>'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed tables")
