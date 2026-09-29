import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# Ensure backend path is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Bypass app config entirely so we don't need JWT_SECRET_KEY locally
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=4)
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_bytes.decode("utf-8")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing in .env")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.models.domain_models import User, Classroom, Enrollment, Task, TaskTestCase, Submission, PracticeModule, PracticeTask, PracticeAttempt

def seed_database():
    db = SessionLocal()
    try:
        # 1. Clean existing records safely
        db.query(PracticeAttempt).delete()
        db.query(PracticeTask).delete()
        db.query(PracticeModule).delete()
        db.query(Submission).delete()
        db.query(TaskTestCase).delete()
        db.query(Task).delete()
        db.query(Enrollment).delete()
        db.query(Classroom).delete()
        
        # Delete users EXCEPT the specified QA accounts
        qa_emails = ['qa.instructor@pampangastateu.edu.ph', 'qa.student@pampangastateu.edu.ph']
        db.query(User).filter(User.email.notin_(qa_emails)).delete(synchronize_session=False)
        db.commit()
        
        # 2. Create 3 Verified Instructors
        instructors = []
        for i in range(1, 4):
            instructor = User(
                name=f"Prof. Instructor {i}",
                school_id=f"20230000{i:02d}",
                email=f"prof{i}@pampangastateu.edu.ph",
                hashed_password=get_password_hash("Password123!"),
                role="instructor",
                is_verified=True,
                is_active=True
            )
            db.add(instructor)
            instructors.append(instructor)
        db.commit()
        
        # 3. Create 15 Students
        students = []
        for i in range(1, 16):
            student = User(
                name=f"Student {i}",
                school_id=f"20240000{i:02d}",
                email=f"student{i}@pampangastateu.edu.ph",
                hashed_password=get_password_hash("Password123!"),
                role="student",
                is_verified=True,
                is_active=True
            )
            db.add(student)
            students.append(student)
        db.commit()
        
        # 4. Create 3 Classes
        classes = []
        class_names = ["CS101: Intro to Python", "CS102: Data Structures", "CS201: Algorithms"]
        for idx, name in enumerate(class_names):
            classroom = Classroom(
                instructor_id=instructors[idx].user_id,
                name=name,
                section=f"Section {chr(65+idx)}",
                class_code=f"CLS{idx}X9",
                is_active=True
            )
            db.add(classroom)
            classes.append(classroom)
        db.commit()
        
        # 5. Bulk Enrollments (Enroll 5 students per class)
        for idx, classroom in enumerate(classes):
            class_students = students[idx*5 : (idx+1)*5]
            for student in class_students:
                enrollment = Enrollment(
                    class_id=classroom.class_id,
                    student_id=student.user_id,
                    status="active"
                )
                db.add(enrollment)
        db.commit()
        
        # 6. Create Practice Modules for Solo Practice Demo
        module = PracticeModule(
            instructor_id=instructors[0].user_id,
            title="Python Fundamentals Bootcamp",
            description="A self-paced, progressive solo practice module.",
            order_index=1
        )
        db.add(module)
        db.commit()
        
        practice_task = PracticeTask(
            module_id=module.module_id,
            title="Variables & Data Types",
            instructions="Print the string 'Python is Awesome!' exactly as shown.",
            expected_output="Python is Awesome!\n",
            expected_ast_patterns={},
            starter_code="# Write your code below\n",
            order_index=1
        )
        db.add(practice_task)
        db.commit()
        
        # 7. Create 5 Activities with Varied AST Requirements & Test Cases
        tasks = []
        ast_configs = [
            {"require_loops": False, "require_functions": False, "desc": "Basic Print Statement"},
            {"require_loops": False, "require_functions": True, "desc": "Basic Function Definition"},
            {"require_loops": True, "require_functions": False, "desc": "Basic For Loop"},
            {"require_loops": True, "require_functions": True, "desc": "Loops inside Functions"},
            {"require_loops": True, "require_functions": True, "desc": "Advanced Nested Logic"}
        ]
        
        target_class = classes[0]
        for idx, config in enumerate(ast_configs):
            diff = "beginner" if idx < 2 else ("intermediate" if idx < 4 else "expert")
            task = Task(
                class_id=target_class.class_id,
                instructor_id=target_class.instructor_id,
                title=f"Activity {idx+1}: {config['desc']}",
                description=f"Demonstrate {config['desc']}.",
                instructions=f"Write a Python script for {config['desc']}.",
                activity_type="laboratory",
                difficulty=diff,
                required_ast_rules=config,
                starter_code="# Write your code here\n",
                is_published=True
            )
            db.add(task)
            db.commit()
            
            # Add a basic test case for each task
            tc = TaskTestCase(
                task_id=task.task_id,
                name="Default Output Check",
                standard_input="",
                expected_output="Success\n",
                is_hidden=False
            )
            db.add(tc)
            tasks.append(task)
        db.commit()
        
        # 8. Create Realistic Submissions
        # Perfect submission
        sub1 = Submission(
            task_id=tasks[0].task_id,
            student_id=students[0].user_id,
            attempt_number=1,
            status="graded",
            raw_code="print('Hello World')",
            grade_score=100.0,
            feedback_text="Perfect execution and structure!"
        )
        
        # AST Flagged submission
        sub2 = Submission(
            task_id=tasks[2].task_id,
            student_id=students[1].user_id,
            attempt_number=1,
            status="rejected",
            raw_code="print('I did not use a loop')",
            grade_score=0.0,
            feedback_text="AST Check Failed: Missing iterative loop structure."
        )
        
        # Pending submission
        sub3 = Submission(
            task_id=tasks[3].task_id,
            student_id=students[2].user_id,
            attempt_number=1,
            status="submitted",
            raw_code="def my_func():\n    for i in range(5):\n        pass",
            grade_score=None
        )
        
        db.add_all([sub1, sub2, sub3])
        db.commit()
        
        print("Database successfully seeded with realistic dummy data!")
        
    finally:
        db.close()
        
if __name__ == "__main__":
    seed_database()
