from app.core.database import SessionLocal
from app.models.domain_models import User
from app.core.security import get_password_hash

db = SessionLocal()
admin = db.query(User).filter(User.email == "admin@pampangastateu.edu.ph").first()
if not admin:
    admin = User(
        email="admin@pampangastateu.edu.ph",
        first_name="System",
        last_name="Administrator",
        middle_name="",
        role="admin",
        hashed_password=get_password_hash("Admin@2026")
    )
    db.add(admin)
    db.commit()
    print("Seeded admin account")
else:
    print("Admin already exists")
