import os
import re

filepath = "backend/app/core/security.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

rbac_code = """
class RequireRole:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of: {', '.join(self.allowed_roles)}"
            )
        return current_user

get_current_admin = RequireRole(["admin"])
get_current_instructor = RequireRole(["instructor", "admin"])
"""

pattern = r"def get_current_admin\(.*?return current_user\n"
content = re.sub(pattern, rbac_code.strip() + "\n", content, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Implemented RBAC in security.py")
