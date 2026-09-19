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
            name="QA Test Instructor",
            school_id="2026-00001",
            email="qa.instructor@pampangastateu.edu.ph",
            role="instructor",
            password_hash=hashed_password,
            email_verified=True,
            is_active=True,
        )

        student = User(
            name="QA Test Student",
            school_id="2026-00002",
            email="qa.student@pampangastateu.edu.ph",
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
            name="QA Automated Testing Classroom",
            section="A",
            class_code="QATEST1",
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
            published_at=datetime.now(timezone.utc),
            paste_policy="internal_only"
        )
        db.add(task)
        db.commit()


        from app.models.domain_models import PracticeModule, PracticeTask
        
        db.execute(text("TRUNCATE TABLE practice_modules CASCADE"))
        db.commit()

        # --- Module 1: Python Basics ---
        mod1 = PracticeModule(
            title="Python Basics",
            description="Learn the basic syntax and structure of Python. Master variables and printing.",
            order_index=1
        )
        db.add(mod1)
        db.commit()

        db.add_all([
            PracticeTask(
                module_id=mod1.module_id, title="Hello World",
                instructions="Print exactly 'Hello, World!' to the console.",
                starter_code="# Write your code below\n",
                expected_output="Hello, World!\n",
                expected_ast_patterns={"require_print_call": True},
                order_index=1
            ),
            PracticeTask(
                module_id=mod1.module_id, title="Variables",
                instructions="Create a variable 'x' assigned to 5. Print 'x'.",
                starter_code="# Create variable x\n",
                expected_output="5\n",
                expected_ast_patterns={"require_print_call": True},
                order_index=2
            )
        ])
        db.commit()

        # --- Module 2: Control Flow ---
        mod2 = PracticeModule(
            title="Control Flow",
            description="Make decisions in your code using if, elif, and else statements.",
            order_index=2
        )
        db.add(mod2)
        db.commit()
        
        db.add_all([
            PracticeTask(
                module_id=mod2.module_id, title="If Statements",
                instructions="Write an if statement that prints 'Positive' if x is greater than 0. x is 10.",
                starter_code="x = 10\n# Write your if statement here\n",
                expected_output="Positive\n",
                expected_ast_patterns={"require_if_statement": True, "require_print_call": True},
                order_index=1
            )
        ])
        db.commit()

        # --- Module 3: Loops ---
        mod3 = PracticeModule(
            title="Loops",
            description="Automate repetitive tasks using for and while loops.",
            order_index=3
        )
        db.add(mod3)
        db.commit()

        db.add_all([
            PracticeTask(
                module_id=mod3.module_id, title="For Loop",
                instructions="Use a for loop to print the numbers 0, 1, 2, 3, 4 each on a new line.",
                starter_code="# Write a for loop\n",
                expected_output="0\n1\n2\n3\n4\n",
                expected_ast_patterns={"require_for_loop": True, "require_print_call": True},
                order_index=1
            ),
            PracticeTask(
                module_id=mod3.module_id, title="While Loop",
                instructions="Use a while loop to print 'Run' exactly 3 times.",
                starter_code="count = 0\n# Write a while loop\n",
                expected_output="Run\nRun\nRun\n",
                expected_ast_patterns={"require_while_loop": True, "require_print_call": True},
                order_index=2
            )
        ])
        db.commit()

        # --- Module 4: Functions ---
        mod4 = PracticeModule(
            title="Functions",
            description="Organize your code with reusable functions.",
            order_index=4
        )
        db.add(mod4)
        db.commit()

        db.add_all([
            PracticeTask(
                module_id=mod4.module_id, title="Defining Functions",
                instructions="Define a function named `greet` that prints 'Hello'. Then call the function.",
                starter_code="# Define greet() here\n",
                expected_output="Hello\n",
                expected_ast_patterns={"require_function_def": True, "require_function_call": True},
                order_index=1
            ),
            PracticeTask(
                module_id=mod4.module_id, title="Return Values",
                instructions="Define a function `add(a, b)` that returns the sum. Print the result of add(2, 3).",
                starter_code="# Define add(a, b) here\n",
                expected_output="5\n",
                expected_ast_patterns={"require_function_def": True, "require_return_statement": True, "require_print_call": True},
                order_index=2
            )
        ])
        db.commit()

        # --- Module 5: Data Structures ---
        mod5 = PracticeModule(
            title="Data Structures",
            description="Store and manipulate collections of data using Lists and Dictionaries.",
            order_index=5
        )
        db.add(mod5)
        db.commit()

        db.add_all([
            PracticeTask(
                module_id=mod5.module_id, title="Lists",
                instructions="Create a list called 'fruits' containing 'apple' and 'banana'. Print the list.",
                starter_code="# Create your list here\n",
                expected_output="['apple', 'banana']\n",
                expected_ast_patterns={"require_print_call": True},
                order_index=1
            ),
            PracticeTask(
                module_id=mod5.module_id, title="List Comprehension",
                instructions="Use a list comprehension to create a list of squares for numbers 1 to 3: [1, 4, 9]. Print the list.",
                starter_code="# Write your list comprehension\n",
                expected_output="[1, 4, 9]\n",
                expected_ast_patterns={"require_list_comprehension": True, "require_print_call": True},
                order_index=2
            )
        ])
        db.commit()

        # --- Module 6: Object-Oriented Programming ---
        mod6 = PracticeModule(
            title="Object-Oriented Programming",
            description="Model real-world concepts using Classes and Objects.",
            order_index=6
        )
        db.add(mod6)
        db.commit()

        db.add_all([
            PracticeTask(
                module_id=mod6.module_id, title="Classes and Objects",
                instructions="Define a class `Dog` with a method `bark` that prints 'Woof!'. Create an instance and call bark().",
                starter_code="# Define your class here\n",
                expected_output="Woof!\n",
                expected_ast_patterns={"require_class_def": True, "require_function_def": True, "require_print_call": True},
                order_index=1
            )
        ])
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
