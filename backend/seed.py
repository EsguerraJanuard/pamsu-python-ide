from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.domain_models import User
from sqlalchemy import text

def seed_database():
    db = SessionLocal()
    try:
        # Clear any old placeholder users using CASCADE to handle foreign keys
        db.execute(text("TRUNCATE TABLE users CASCADE"))
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

        from app.models.domain_models import Classroom, Task, Enrollment

        db.add(instructor)
        db.add(student)
        db.commit()

        # Create a test classroom
        classroom = Classroom(
            name="Load Testing Class",
            section="A",
            class_code="LOAD101",
            instructor_id=instructor.user_id,
            is_active=True
        )
        db.add(classroom)
        db.commit()

        # Enroll the student
        enrollment = Enrollment(
            student_id=student.user_id,
            class_id=classroom.class_id,
            status="active"
        )
        db.add(enrollment)

        # Create a test task
        task = Task(
            class_id=classroom.class_id,
            title="Load Test Execution",
            description="Stress testing the execution engine",
            instructions="Run this code.",
            expected_output="Hello World",
            required_ast_rules={},
            is_published=True,
            allow_paste=True
        )
        db.add(task)
        db.commit()

        print("Successfully updated test accounts, classroom, and task!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
