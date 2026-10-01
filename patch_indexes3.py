import re
with open('backend/app/models/domain_models.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Use regex to strip it from User only
user_match = re.search(r'class User\(Base\):.*?__table_args__ = \([\s]*Index\("ix_tasks_class_pub", "class_id", "is_published"\),', c, re.DOTALL)
if user_match:
    c = c.replace(user_match.group(0), 'class User(Base):\n    __tablename__ = "users"\n    __table_args__ = (')

with open('backend/app/models/domain_models.py', 'w', encoding='utf-8') as f:
    f.write(c)