from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.domain_models import User
from sqlalchemy import text
from datetime import datetime, timezone

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
                instructions="""
# Welcome to Python!

Python is one of the most popular and versatile programming languages in the world. It is used in everything from **web development** to **artificial intelligence** and **data science**.

One of the reasons Python is so popular is its readability. It reads almost like plain English!

## Your First Program

When learning a new programming language, there is a tradition that dates back to the 1970s: your very first program should be to print the phrase **"Hello, World!"** to the screen.

In Python, we use the `print()` function to display text.

### The `print()` Statement

A **function** is a reusable block of code that performs a specific action. The `print()` function's job is to take whatever you put inside its parentheses and output it to the console.

To print text (which we call a **string**), you must wrap the text in quotes, either single `'` or double `"`.

**Example:**
```python
print("Welcome to PAMSU IDE!")
```

---

### Activity Instructions
Now it's your turn! Try writing your very first Python program.

1. Use the `print()` function.
2. Output exactly: `Hello, World!`
3. Be careful with spelling, capitalization, and punctuation!
""",
                starter_code="# Write your code below\n",
                expected_output="Hello, World!\n",
                expected_ast_patterns={"require_print_call": True},
                order_index=1
            ),
            PracticeTask(
                module_id=mod1.module_id, title="Variables",
                instructions="""# Variables in Python

A **variable** is like a labeled box where you can store data. Just like you can put a pair of shoes in a box labeled "Shoes", you can store the number `5` in a variable named `x`.

In Python, creating a variable is simple. You just choose a name, use the equals sign `=`, and write the value you want to store.

### Example:
```python
age = 20
name = "Juan"
```

Once a variable is created, you can use its name to retrieve its value! For example, `print(age)` will print `20`.

---

### Activity Instructions
1. Create a variable named `x`.
2. Assign the value `5` to it.
3. Use the `print()` function to display the value of `x`.
""",
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
                instructions="""# Control Flow: If Statements

By default, Python runs your code line by line from top to bottom. But what if you only want to run a piece of code **sometimes**? 

An `if` statement allows your program to make decisions. It checks a condition, and if that condition is true, it executes a block of code.

### Example:
```python
score = 85

if score >= 75:
    print("You passed!")
```
Notice the **colon (`:`)** at the end of the `if` line, and the **indentation (spaces)** on the next line. Python uses indentation to know which code belongs inside the `if` block.

---

### Activity Instructions
We have already created a variable `x = 10` for you.
1. Write an `if` statement that checks if `x` is greater than `0`.
2. Inside the `if` block, print exactly: `Positive`
""",
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
                instructions="""# Loops: The For Loop

A `for` loop is used to repeat a block of code a specific number of times. 

In Python, we often use `for` loops with the `range()` function to count numbers. `range(5)` generates the numbers 0, 1, 2, 3, and 4. 

### Example:
```python
for i in range(3):
    print("Hello!")
```
This will print "Hello!" exactly 3 times. The variable `i` keeps track of the current number (0, 1, then 2).

---

### Activity Instructions
1. Write a `for` loop using `range(5)`.
2. Inside the loop, print the loop variable so it outputs `0`, `1`, `2`, `3`, and `4` on separate lines.
""",
                starter_code="# Write a for loop\n",
                expected_output="0\n1\n2\n3\n4\n",
                expected_ast_patterns={"require_for_loop": True, "require_print_call": True},
                order_index=1
            ),
            PracticeTask(
                module_id=mod3.module_id, title="While Loop",
                instructions="""# Loops: The While Loop

A `while` loop keeps repeating a block of code **as long as a condition remains true**. 

You have to be careful with `while` loops! If the condition never becomes false, the loop will run forever (an infinite loop). To prevent this, we usually update a variable inside the loop.

### Example:
```python
count = 0
while count < 2:
    print("Looping...")
    count = count + 1
```

---

### Activity Instructions
We have created a variable `count = 0` for you.
1. Write a `while` loop that runs as long as `count` is less than `3`.
2. Inside the loop, print exactly: `Run`
3. Don't forget to increase `count` by 1 inside the loop, or it will run forever!
""",
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
                instructions="""# Functions: Defining reusable code

A **function** is a block of organized, reusable code that is used to perform a single, related action. You've already used built-in functions like `print()`. Now you'll learn how to create your own!

In Python, you define a function using the `def` keyword, followed by the function name, parentheses `()`, and a colon `:`.

### Example:
```python
def say_hello():
    print("Hello from a function!")

# To run the function, you "call" it like this:
say_hello()
```

---

### Activity Instructions
1. Define a function named `greet`.
2. Inside the function, print exactly: `Hello`
3. After defining the function, call it so that it actually runs.
""",
                starter_code="# Define greet() here\n",
                expected_output="Hello\n",
                expected_ast_patterns={"require_function_def": True, "require_function_call": True},
                order_index=1
            ),
            PracticeTask(
                module_id=mod4.module_id, title="Return Values",
                instructions="""# Functions: Return Values

Functions can do more than just print things to the screen. They can also perform calculations and **return** a result back to whoever called the function.

We use the `return` keyword to send a value back.

### Example:
```python
def multiply(x, y):
    result = x * y
    return result

answer = multiply(4, 5)
print(answer) # Prints 20
```

---

### Activity Instructions
1. Define a function named `add(a, b)` that takes two parameters.
2. Inside the function, return the sum of `a` and `b`.
3. Outside the function, call `add(2, 3)` and `print()` the returned result.
""",
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
                instructions="""# Data Structures: Lists

A **list** is a data structure in Python that is a mutable, or changeable, ordered sequence of elements. 

You can think of a list like a shopping list. You can put multiple items inside a single variable using square brackets `[]`.

### Example:
```python
colors = ["red", "green", "blue"]
print(colors)
```

---

### Activity Instructions
1. Create a list called `fruits`.
2. Put the strings `'apple'` and `'banana'` inside the list.
3. Print the `fruits` list.
""",
                starter_code="# Create your list here\n",
                expected_output="['apple', 'banana']\n",
                expected_ast_patterns={"require_print_call": True},
                order_index=1
            ),
            PracticeTask(
                module_id=mod5.module_id, title="List Comprehension",
                instructions="""# Data Structures: List Comprehensions

List comprehensions provide a concise way to create lists. It consists of brackets containing an expression followed by a `for` clause.

It allows you to build a new list from an existing sequence in just a single line of code!

### Example:
```python
# Create a list of doubled numbers
doubled = [x * 2 for x in range(3)] 
# Result: [0, 2, 4]
```

---

### Activity Instructions
1. Use a list comprehension to create a list of squares (x multiplied by x) for the numbers `1`, `2`, and `3`. (Hint: use `range(1, 4)`).
2. Assign the result to a variable and print it. It should output `[1, 4, 9]`.
""",
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
                instructions="""# Object-Oriented Programming: Classes

Python is an object-oriented programming language. Almost everything in Python is an object, with its properties and methods.

A **Class** is like an object constructor, or a "blueprint" for creating objects.

### Example:
```python
class Cat:
    def meow(self):
        print("Meow!")

# Create an object (instance) of Cat
my_cat = Cat()
# Call the method
my_cat.meow()
```

---

### Activity Instructions
1. Define a class named `Dog`.
2. Inside the class, define a method named `bark(self)` that prints exactly: `Woof!`
3. Create an instance of the `Dog` class and call its `bark()` method.
""",
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
