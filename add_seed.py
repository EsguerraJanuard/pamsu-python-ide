import os

filepath = "backend/app/routers/admin.py"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    seed_logic = """
@router.get("/seed-production")
def seed_production(db: Session = Depends(get_db)):
    # Temporary seed endpoint for MIS account
    admin_email = "admin@pampangastateu.edu.ph"
    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        return {"msg": "Super Admin already exists."}
    
    admin_user = User(
        email=admin_email,
        first_name="Super",
        last_name="Admin",
        role="superadmin",
        password_hash=get_password_hash("Admin@2026"),
        school_id="ADMIN-0001",
        email_verified=True
    )
    db.add(admin_user)
    db.commit()
    return {"msg": "Super Admin seeded successfully."}
"""
    
    if "@router.get(\"/seed-production\")" not in content:
        content = content + "\n" + seed_logic
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print("Added seed-production endpoint.")
