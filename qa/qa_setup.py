"""Create (or, with --reset, recreate) the local QA database and test accounts.

Usage, from the repository folder:
    backend\\venv\\Scripts\\python.exe qa\\qa_setup.py           (first time)
    backend\\venv\\Scripts\\python.exe qa\\qa_setup.py --reset   (start over)

Passwords are random for every setup. They are printed here and saved in
qa/.qa-data/accounts.txt, which git ignores. They only work on this local copy.
"""

import secrets
import sys

import qa_env

ACCOUNTS = [
    # role, email, name, school ID
    ("admin", "qa.admin@pampangastateu.edu.ph", "QA Admin", "0000000001"),
    ("instructor", "qa.instructor@pampangastateu.edu.ph", "QA Instructor", "FAC0000001"),
    ("student", "qa.student1@pampangastateu.edu.ph", "QA Student One", "2026000001"),
    ("student", "qa.student2@pampangastateu.edu.ph", "QA Student Two", "2026000002"),
]


def main() -> int:
    reset = "--reset" in sys.argv[1:]
    if qa_env.DB_PATH.exists():
        if not reset:
            print("The QA database already exists. Your logins are in:")
            print(f"  {qa_env.ACCOUNTS_FILE}")
            print("To start over with an empty database, run this again with --reset")
            return 1
        qa_env.DB_PATH.unlink()
        qa_env.ACCOUNTS_FILE.unlink(missing_ok=True)

    qa_env.apply()

    from app.core.database import Base, SessionLocal, engine
    from app.core.security import get_password_hash
    from app.models import domain_models  # noqa: F401  (registers every table)
    from app.models.domain_models import User

    Base.metadata.create_all(bind=engine)

    lines = []
    db = SessionLocal()
    try:
        for role, email, name, school_id in ACCOUNTS:
            password = secrets.token_urlsafe(9)
            db.add(
                User(
                    email=email,
                    name=name,
                    school_id=school_id,
                    role=role,
                    password_hash=get_password_hash(password),
                    email_verified=True,
                    is_active=True,
                )
            )
            lines.append(f"{role:<11} {email:<40} {password}")
        db.commit()
    finally:
        db.close()

    header = f"{'ROLE':<11} {'EMAIL':<40} PASSWORD"
    text = "\n".join([header, *lines]) + "\n"
    qa_env.ACCOUNTS_FILE.write_text(text, encoding="utf-8")

    print("QA database created.\n")
    print(text)
    print(f"These logins are also saved in: {qa_env.ACCOUNTS_FILE}")
    print("They work only on your local copy, never on the live site.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
