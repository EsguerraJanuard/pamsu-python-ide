import os

filepath = "backend/app/routers/admin.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix admin seed
content = content.replace(
    'school_id="0000000000"\n    )',
    'school_id="0000000000",\n        email_verified=True\n    )'
)

# Fix instructor provision
content = content.replace(
    'school_id=str(random.randint(1000000000, 9999999999))\n    )',
    'school_id=str(random.randint(1000000000, 9999999999)),\n        email_verified=True\n    )'
)

# Fix student provision
content = content.replace(
    'school_id=str(random.randint(1000000000, 9999999999))\n            )',
    'school_id=str(random.randint(1000000000, 9999999999)),\n                email_verified=True\n            )'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed admin seed logic")
