import os

filepath = "app/routers/users.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'class IntegrityUpdate(BaseModel):',
    'router = APIRouter(prefix="/users", tags=["users"])\n\nclass IntegrityUpdate(BaseModel):'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed users.py syntax")
