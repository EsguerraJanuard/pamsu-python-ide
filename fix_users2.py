import os
import re

filepath = "backend/app/routers/users.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

bad_update = """def update_profile(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    current_user.name = update_data.name
    if update_data.ast_strictness_level is not None:
        current_user.ast_strictness_level = update_data.ast_strictness_level
    db.commit()
    db.refresh(current_user)
    return current_user"""

fixed_update = """def update_profile(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    current_user.first_name = update_data.first_name
    current_user.middle_name = update_data.middle_name
    current_user.last_name = update_data.last_name
    if update_data.ast_strictness_level is not None:
        current_user.ast_strictness_level = update_data.ast_strictness_level
    db.commit()
    db.refresh(current_user)
    return current_user"""

content = content.replace(bad_update, fixed_update)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed users.py properly")
