import os

filepath = "backend/app/schemas/user_schema.py"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    content = content.replace(
        'role: Literal["student", "instructor"]',
        'role: Literal["student", "instructor", "superadmin", "guest"]'
    )
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed roles in user_schema")
