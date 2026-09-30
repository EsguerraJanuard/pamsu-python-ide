import os
import re

filepath = "frontend/src/components/layout/Sidebar.jsx"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('rounded-full bg-psu-red text-xs', 'rounded-full bg-psu-maroon text-xs')
content = content.replace('rounded-full bg-psu-red font-semibold', 'rounded-full bg-psu-maroon font-semibold')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Sidebar fixed.")
