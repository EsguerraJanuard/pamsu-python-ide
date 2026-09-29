import os
from datetime import datetime, timezone
import sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=4)
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_bytes.decode("utf-8")

from app.models.domain_models import (
    User, Classroom, Enrollment, Task, TaskTestCase, Submission, 
    PracticeModule, PracticeTask, PracticeAttempt, PracticeProgress,
    BehavioralLog, ExecutionRequest, PartnerExecutionUpdateRecord, 
    ASTAnalysis, ASTFinding, SimilarityResult, InstructorGrade, 
    AcademicEvent, AuditRecord, Notification, CodingSession
)

def seed_database():
    db = SessionLocal()
    try:
        # 1. Clean existing records safely (DO NOT wipe Users or PracticeModules)
        db.query(Notification).delete()
        db.query(AuditRecord).delete()
        db.query(AcademicEvent).delete()
        db.query(InstructorGrade).delete()
        db.query(SimilarityResult).delete()
        db.query(ASTFinding).delete()
        db.query(ASTAnalysis).delete()
        db.query(PartnerExecutionUpdateRecord).delete()
        db.query(ExecutionRequest).delete()
        db.query(BehavioralLog).delete()
        
        db.query(PracticeAttempt).delete()
        db.query(PracticeProgress).delete()
        db.query(Submission).delete()
        db.query(CodingSession).delete()
        db.query(TaskTestCase).delete()
        db.query(Task).delete()
        db.query(Enrollment).delete()
        db.query(Classroom).delete()
        
        # Delete old dummy users to prevent unique constraint violation
        db.query(User).filter(User.email.notin_(["qa.instructor@pampangastateu.edu.ph", "qa.student@pampangastateu.edu.ph"])).delete(synchronize_session=False)
        db.commit()

        # We will NOT delete QA Users. We assume the QA users exist!
        qa_instructor = db.query(User).filter_by(email="qa.instructor@pampangastateu.edu.ph").first()
        qa_student = db.query(User).filter_by(email="qa.student@pampangastateu.edu.ph").first()
        
        if not qa_instructor or not qa_student:
            print("ERROR: Run seed.py first to create the QA accounts!")
            return

        print("Creating Dummy Users...")
        # Create Dummy Instructors
        instructors = [qa_instructor]
        for i in range(1, 3):
            instructor = User(
                name=f"Prof. Instructor {i}",
                school_id=f"20230000{i:02d}",
                email=f"prof{i}@pampangastateu.edu.ph",
                password_hash=get_password_hash("Password123!"),
                role="instructor",
                email_verified=True,
                is_active=True
            )
            db.add(instructor)
            instructors.append(instructor)
            
        # Create Dummy Students
        students = [qa_student]
        for i in range(1, 15):
            student = User(
                name=f"Dummy Student {i}",
                school_id=f"20240000{i:02d}",
                email=f"student{i}@pampangastateu.edu.ph",
                password_hash=get_password_hash("Password123!"),
                role="student",
                email_verified=True,
                is_active=True
            )
            db.add(student)
            students.append(student)
        db.commit()

        print("Creating Classes...")
        classes = []
        class_names = ["CS101: Intro to Python", "CS102: Data Structures", "CS201: Algorithms"]
        for idx, name in enumerate(class_names):
            classroom = Classroom(
                instructor_id=instructors[0 if idx < 2 else 1].user_id,
                name=name,
                section=f"Section {chr(65+idx)}",
                class_code=f"QA{idx}X9Z",
                is_active=True
            )
            db.add(classroom)
            classes.append(classroom)
        db.commit()

        print("Enrolling Students...")
        for student in students:
            enrollment = Enrollment(
                class_id=classes[0].class_id,
                student_id=student.user_id,
                status="active"
            )
            db.add(enrollment)
        db.commit()

        print("Creating Tasks...")
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
                instructions=f"Write a Python script for {config['desc']}. Make sure your output says 'Success'.",
                activity_type="laboratory",
                difficulty=diff,
                required_ast_rules=config,
                starter_code="# Write your code here\n",
                is_published=True,
                published_at=datetime.now(timezone.utc)
            )
            db.add(task)
            db.commit()
            
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

        print("Creating Submissions...")
        sub1 = Submission(
            task_id=tasks[0].task_id,
            student_id=students[1].user_id,
            attempt_number=1,
            status="graded",
            accepted_at=datetime.now(timezone.utc),
            raw_code="print('Success')",
        )
        
        sub2 = Submission(
            task_id=tasks[2].task_id,
            student_id=students[2].user_id,
            attempt_number=1,
            status="rejected",
            raw_code="print('I did not use a loop')",
        )
        
        sub3 = Submission(
            task_id=tasks[3].task_id,
            student_id=qa_student.user_id,
            attempt_number=1,
            status="submitted",
            accepted_at=datetime.now(timezone.utc),
            raw_code="def my_func():\n    for i in range(5):\n        pass",
        )
        
        db.add_all([sub1, sub2, sub3])
        db.commit()

        print("Finished injecting realistic panelist demo data to QA accounts!")
        
    finally:
        db.close()
        
if __name__ == "__main__":
    seed_database()
