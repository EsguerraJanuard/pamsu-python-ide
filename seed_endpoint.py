import os
import re

filepath = "backend/app/routers/admin.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

seed_endpoint = """@router.get("/seed-production")
def seed_production_admin(db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == "admin@pampangastateu.edu.ph").first()
    if existing:
        return {"message": "Admin already exists in this database!"}
    
    admin = User(
        email="admin@pampangastateu.edu.ph",
        first_name="System",
        last_name="Administrator",
        middle_name="",
        role="admin",
        password_hash=get_password_hash("Admin@2026"),
        school_id="0000000000"
    )
    db.add(admin)
    db.commit()
    return {"message": "Admin account successfully seeded into production database!"}
"""

if "seed_production_admin" not in content:
    content = content + "\n" + seed_endpoint

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Added seed endpoint")
