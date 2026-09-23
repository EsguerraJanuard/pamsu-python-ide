import os

filepath = 'backend/seed.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

rich_markdown = '''"""
# Welcome to Python!

Python is one of the most popular and versatile programming languages in the world. It is used in everything from **web development** to **artificial intelligence** and **data science**.

One of the reasons Python is so popular is its readability. It reads almost like plain English!

## Your First Program

When learning a new programming language, there is a tradition that dates back to the 1970s: your very first program should be to print the phrase **"Hello, World!"** to the screen.

In Python, we use the `print()` function to display text.

### The `print()` Statement

A **function** is a reusable block of code that performs a specific action. The `print()` function's job is to take whatever you put inside its parentheses and output it to the console.

To print text (which we call a **string**), you must wrap the text in quotes, either single `\'` or double `\"`.

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
"""'''

old_task = '''PracticeTask(
                module_id=mod1.module_id, title="Hello World",
                instructions="Print exactly 'Hello, World!' to the console.",
                starter_code="# Write your code below\\n",
                expected_output="Hello, World!\\n",
                expected_ast_patterns={"require_print_call": True},
                order_index=1
            )'''

new_task = f'''PracticeTask(
                module_id=mod1.module_id, title="Hello World",
                instructions={rich_markdown},
                starter_code="# Write your code below\\n",
                expected_output="Hello, World!\\n",
                expected_ast_patterns={{"require_print_call": True}},
                order_index=1
            )'''

content = content.replace(old_task, new_task)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
