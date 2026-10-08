import os

filepath = "backend/app/routers/auth.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

bad_schema = """class AuthenticatedUserResponse(BaseModel):
    user_id: int
    name: str
    school_id: str
    email: str
    role: str
    email_verified: bool"""
# Wait, let me replace it safely using regex since the role has literal type.

import re
old_schema = r"class AuthenticatedUserResponse\(BaseModel\):\n\s+user_id: int\n\s+name: str\n\s+school_id: str\n\s+email: str\n\s+role: Literal\[\"student\", \"instructor\"\]\n\s+email_verified: bool"
new_schema = """class AuthenticatedUserResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    school_id: str
    email: str
    role: str
    email_verified: bool"""

content = re.sub(old_schema, new_schema, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed AuthenticatedUserResponse")
