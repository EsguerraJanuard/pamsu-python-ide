import os
import sys
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from app.core.database import SessionLocal
from app.models.domain_models import User
from app.core.security import get_password_hash

db = SessionLocal()

# Add 3 instructors
instructors = [
    ("alice.smith@pampangastateu.edu.ph", "Alice", "Smith"),
    ("bob.jones@pampangastateu.edu.ph", "Bob", "Jones"),
    ("carol.white@pampangastateu.edu.ph", "Carol", "White")
]

import random

for email, first, last in instructors:
    if not db.query(User).filter(User.email == email).first():
        u = User(
            email=email,
            first_name=first,
            last_name=last,
            role="instructor",
            password_hash=get_password_hash("Pass@123"),
            school_id=str(random.randint(1000000000, 9999999999)),
            email_verified=True
        )
        db.add(u)

# Add 15 students
for i in range(1, 16):
    email = f"student{i}@pampangastateu.edu.ph"
    if not db.query(User).filter(User.email == email).first():
        u = User(
            email=email,
            first_name="Student",
            last_name=str(i),
            role="student",
            password_hash=get_password_hash("Pass@123"),
            school_id=f"1000000{i:03d}",
            email_verified=True
        )
        db.add(u)

db.commit()
print("Dummy data seeded")
db.close()
