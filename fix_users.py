import os

filepath = "backend/app/routers/users.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

bad_update = """def update_profile(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    current_user.name = update_data.name
    if update_data.ast_strictness_level:
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
    if update_data.ast_strictness_level:
        current_user.ast_strictness_level = update_data.ast_strictness_level
    db.commit()
    db.refresh(current_user)
    return current_user"""

if bad_update in content:
    content = content.replace(bad_update, fixed_update)
else:
    print("Could not find exact snippet, printing function:")
    import re
    m = re.search(r"def update_profile.*?return current_user", content, re.DOTALL)
    if m: print(m.group(0))

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed users.py")
