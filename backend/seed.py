from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.domain_models import User

def seed_database():
    db = SessionLocal()
    try:
        # Clear any old placeholder users
        db.query(User).delete()
        db.commit()

        hashed_password = get_password_hash("Password123!")

        instructor = User(
            name="Prof. Juan Dela Cruz",
            school_id="2026-00001",
            email="instructor@pampangastateu.edu.ph",
            role="instructor",
            password_hash=hashed_password,
            email_verified=True,
            is_active=True,
        )

        student = User(
            name="Miguel Santos",
            school_id="2026-00002",
            email="student@pampangastateu.edu.ph",
            role="student",
            password_hash=hashed_password,
            email_verified=True,
            is_active=True,
        )

        db.add(instructor)
        db.add(student)
        db.commit()
        print("Successfully updated test accounts with official @pampangastateu.edu.ph domain!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
