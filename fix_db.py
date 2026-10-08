import os
import sys
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from app.core.database import SessionLocal
from app.models.domain_models import User

db = SessionLocal()
admin = db.query(User).filter(User.email == "admin@pampangastateu.edu.ph").first()
if admin:
    admin.email_verified = True
    db.commit()
    print("Admin verified!")
else:
    print("Admin not found.")
db.close()
