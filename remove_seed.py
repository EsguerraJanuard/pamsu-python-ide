import os
import re

filepath = "backend/app/routers/admin.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern to remove the seed-production endpoint
pattern = r"@router\.get\(\"/seed-production\"\).*?return \{\"message\": \"Admin account successfully seeded into production database!\"\}\n"
content = re.sub(pattern, "", content, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Removed seed-production route")
