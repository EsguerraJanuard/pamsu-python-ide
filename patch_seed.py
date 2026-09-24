import re

with open("backend/seed.py", "r") as f:
    content = f.read()

variables_lesson = """# Variables in Python

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
"""
content = re.sub(r'instructions="Create a variable \'x\' assigned to 5\. Print \'x\'\."', f'instructions="""{variables_lesson}"""', content)

if_lesson = """# Control Flow: If Statements

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
"""
content = re.sub(r'instructions="Write an if statement that prints \'Positive\' if x is greater than 0\. x is 10\."', f'instructions="""{if_lesson}"""', content)

for_lesson = """# Loops: The For Loop

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
"""
content = re.sub(r'instructions="Use a for loop to print the numbers 0, 1, 2, 3, 4 each on a new line\."', f'instructions="""{for_lesson}"""', content)

while_lesson = """# Loops: The While Loop

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
"""
content = re.sub(r'instructions="Use a while loop to print \'Run\' exactly 3 times\."', f'instructions="""{while_lesson}"""', content)

func_lesson = """# Functions: Defining reusable code

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
"""
content = re.sub(r'instructions="Define a function named `greet` that prints \'Hello\'\. Then call the function\."', f'instructions="""{func_lesson}"""', content)

return_lesson = """# Functions: Return Values

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
"""
content = re.sub(r'instructions="Define a function `add\(a, b\)` that returns the sum\. Print the result of add\(2, 3\)\."', f'instructions="""{return_lesson}"""', content)

list_lesson = """# Data Structures: Lists

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
"""
content = re.sub(r'instructions="Create a list called \'fruits\' containing \'apple\' and \'banana\'\. Print the list\."', f'instructions="""{list_lesson}"""', content)

listcomp_lesson = """# Data Structures: List Comprehensions

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
"""
content = re.sub(r'instructions="Use a list comprehension to create a list of squares for numbers 1 to 3: \[1, 4, 9\]\. Print the list\."', f'instructions="""{listcomp_lesson}"""', content)

class_lesson = """# Object-Oriented Programming: Classes

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
"""
content = re.sub(r'instructions="Define a class `Dog` with a method `bark` that prints \'Woof!\'\. Create an instance and call bark\(\)\."', f'instructions="""{class_lesson}"""', content)


with open("backend/seed.py", "w") as f:
    f.write(content)

print("done")
