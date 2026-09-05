from app.core.database import SessionLocal
from app.models.domain_models import User, Classroom, Task, Enrollment

def seed_task():
    db = SessionLocal()
    try:
        instructor = db.query(User).filter_by(role="instructor").first()
        student = db.query(User).filter_by(role="student").first()

        if not instructor or not student:
            print("Users not found.")
            return

        classroom = db.query(Classroom).filter_by(name="Load Testing 101").first()
        if not classroom:
            classroom = Classroom(
                name="Load Testing 101",
                section="A",
                class_code="LOAD101",
                instructor_id=instructor.user_id,
                is_active=True
            )
            db.add(classroom)
            db.commit()

        enrollment = db.query(Enrollment).filter_by(student_id=student.user_id, class_id=classroom.class_id).first()
        if not enrollment:
            enrollment = Enrollment(
                student_id=student.user_id,
                class_id=classroom.class_id,
                status="active"
            )
            db.add(enrollment)
            db.commit()

        task = db.query(Task).filter_by(title="Load Test Execution").first()
        if not task:
            task = Task(
                class_id=classroom.class_id,
                instructor_id=instructor.user_id,
                title="Load Test Execution",
                description="Stress testing the execution engine",
                instructions="Run this code.",
                required_ast_rules={},
                is_published=True,
                paste_policy="internal_only",
                is_graded=False
            )
            db.add(task)
            db.commit()

        print("Successfully ensured test classroom and task exist!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_task()
