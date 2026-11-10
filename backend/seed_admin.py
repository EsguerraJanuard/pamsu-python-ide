"""
Create the first MIS administrator account.

Usage (values come from the environment, never from source code):

    ADMIN_EMAIL=mis.admin@pampangastateu.edu.ph \
    ADMIN_NAME="MIS Administrator" \
    ADMIN_SCHOOL_ID=0000000001 \
    ADMIN_PASSWORD='<a strong password>' \
    python seed_admin.py

The script does nothing if an account with that email already exists.
"""

import os
import sys

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.domain_models import User
from app.schemas.user_schema import UserBase
from pydantic import ValidationError
from sqlalchemy import func


def main() -> int:
    password = os.getenv("ADMIN_PASSWORD", "")

    if len(password) < 12:
        print("ADMIN_PASSWORD must be set and at least 12 characters long.")
        return 1

    try:
        identity = UserBase(
            name=os.getenv("ADMIN_NAME", ""),
            school_id=os.getenv("ADMIN_SCHOOL_ID", ""),
            email=os.getenv("ADMIN_EMAIL", ""),
        )
    except ValidationError as error:
        print(f"Invalid ADMIN_EMAIL, ADMIN_NAME or ADMIN_SCHOOL_ID: {error.errors()[0]['msg']}")
        return 1

    db = SessionLocal()

    try:
        if db.query(User).filter(func.lower(User.email) == identity.email).first():
            print("An account with this email already exists; nothing changed.")
            return 0

        db.add(
            User(
                email=identity.email,
                name=identity.name,
                school_id=identity.school_id,
                role="admin",
                password_hash=get_password_hash(password),
                email_verified=True,
                is_active=True,
            )
        )
        db.commit()
        print("Administrator account created.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
