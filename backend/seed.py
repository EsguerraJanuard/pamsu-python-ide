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
            instructor_id=instructor.user_id,
            title="Load Test Execution",
            description="Stress testing the execution engine",
            instructions="Run this code.",
            required_ast_rules={},
            is_published=True,
            paste_policy="internal_only"
        )
        db.add(task)
        db.commit()


        from app.models.domain_models import PracticeModule, PracticeTask
        
        db.execute(text("TRUNCATE TABLE practice_modules CASCADE"))
        db.commit()

        # Module 1: Python Basics
        mod1 = PracticeModule(
            title="Python Basics",
            description="Learn the basic syntax and structure of Python.",
            order_index=1
        )
        db.add(mod1)
        db.commit()

        task1_1 = PracticeTask(
            module_id=mod1.module_id,
            title="Hello World",
            instructions="Print 'Hello, World!' to the console.",
            starter_code="# Write your code here\n",
            expected_output="Hello, World!\n",
            expected_ast_patterns={
                "require_print_call": True
            },
            order_index=1
        )
        task1_2 = PracticeTask(
            module_id=mod1.module_id,
            title="Variables",
            instructions="Create a variable named 'x' and assign the value 5 to it. Print 'x'.",
            starter_code="# Create variable x\n",
            expected_output="5\n",
            expected_ast_patterns={
                "require_print_call": True
            },
            order_index=2
        )
        db.add_all([task1_1, task1_2])

        # Module 2: Control Flow
        mod2 = PracticeModule(
            title="Control Flow",
            description="Learn how to make decisions in your code using if statements and loops.",
            order_index=2
        )
        db.add(mod2)
        db.commit()
        
        task2_1 = PracticeTask(
            module_id=mod2.module_id,
            title="If Statements",
            instructions="Write an if statement that prints 'Positive' if x is greater than 0. x is already defined for you as 10.",
            starter_code="x = 10\n# Write your if statement here\n",
            expected_output="Positive\n",
            expected_ast_patterns={
                "require_if_statement": True,
                "require_print_call": True
            },
            order_index=1
        )
        db.add(task2_1)
        db.commit()
        
        print("Successfully seeded Practice Modules and Tasks!")

        print("Successfully updated test accounts, classroom, and task!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
