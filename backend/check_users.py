import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from app.models.domain_models import User
db = SessionLocal()
users = db.query(User).all()
for u in users:
    print(f"{u.email} - {u.role}")
db.close()
