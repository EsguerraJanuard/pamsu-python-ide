import os
import re

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix Faculty Table
content = re.sub(
    r'<th className="px-4 py-3">Name</th>\s*<th className="px-4 py-3">Email</th>\s*<th className="px-4 py-3">Status</th>\s*<th className="px-4 py-3 text-right">Actions</th>',
    '<th className="px-4 py-3 w-[35%]">Name</th>\n                            <th className="px-4 py-3 w-[40%]">Email</th>\n                            <th className="px-4 py-3 w-[15%]">Status</th>\n                            <th className="px-4 py-3 w-[10%] text-right">Actions</th>',
    content
)

# Fix Student Table
content = re.sub(
    r'<th className="px-4 py-3">Name</th>\s*<th className="px-4 py-3">PSU Email</th>\s*<th className="px-4 py-3">Status</th>\s*<th className="px-4 py-3 text-right">Actions</th>',
    '<th className="px-4 py-3 w-[35%]">Name</th>\n                            <th className="px-4 py-3 w-[40%]">PSU Email</th>\n                            <th className="px-4 py-3 w-[15%]">Status</th>\n                            <th className="px-4 py-3 w-[10%] text-right">Actions</th>',
    content
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed tables regex")
