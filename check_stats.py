import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from app.models.domain_models import User
db = SessionLocal()
print("Students:", db.query(User).filter(User.role == 'student').count())
print("Instructors:", db.query(User).filter(User.role == 'instructor').count())
db.close()
