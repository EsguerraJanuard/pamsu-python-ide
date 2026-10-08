import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from app.models.domain_models import User
from app.core.security import verify_password
db = SessionLocal()
admin = db.query(User).filter(User.email == "admin@pampangastateu.edu.ph").first()
if admin:
    print(f"Admin found. Active: {admin.is_active}, Verified: {admin.email_verified}")
    print(f"Password match 'Admin@2026': {verify_password('Admin@2026', admin.password_hash)}")
else:
    print("Admin not found!")
db.close()
