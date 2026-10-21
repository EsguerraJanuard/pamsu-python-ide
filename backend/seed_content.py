"""
Content for seed.py: the people, classes, activities and practice lessons of
a demo semester at Pampanga State University.

Everything here is fictional. Names are common Kapampangan and Filipino
names put together at random; they are not real students or faculty.

Activity code variants use @@NAME@@ placeholders that seed.py fills per
student (a header comment, a variable or function name), so submissions
differ the way real class submissions do. Every "correct" variant prints the
activity's expected output exactly (checked by seed.py --self-check).
"""

from dataclasses import dataclass, field

UNIVERSITY = "Pampanga State University"
COLLEGE = "College of Computing Studies"

FIRST_NAMES = (
    "Aaron", "Abigail", "Adrian", "Aira", "Aldrin", "Alyssa", "Andrea", "Angelica", "Angelo", "Anne",
    "Arvin", "Bea", "Benedict", "Bianca", "Brent", "Camille", "Carl", "Carlo", "Cedric", "Charisse",
    "Christian", "Clarisse", "Daniel", "Danica", "Darwin", "Denise", "Dominic", "Edward", "Elaine", "Ella",
    "Emmanuel", "Erica", "Francis", "Gabriel", "Gelo", "Hannah", "Ivan", "Jamaica", "Janine", "Jasmine",
    "Jericho", "Jerome", "Jessa", "Joanna", "John Carlo", "John Paul", "Joshua", "Joy", "Justine", "Karen",
    "Kenneth", "Kevin", "Kim", "Kristine", "Kyla", "Lance", "Leah", "Lorraine", "Mae", "Mark",
    "Marvin", "Mary Grace", "Matthew", "Michelle", "Miguel", "Nathaniel", "Nicole", "Patricia", "Paolo", "Princess",
    "Rachelle", "Ralph", "Raymond", "Rica", "Rodel", "Ronald", "Sean", "Shaira", "Sheila", "Stephanie",
    "Trisha", "Vincent", "Wendell", "Yna", "Zyra",
)

SURNAMES = (
    "Aguilar", "Bautista", "Bondoc", "Calma", "Canlas", "Castro", "Cruz", "Cunanan", "David", "De Guzman",
    "Dela Cruz", "Dizon", "Dungca", "Garcia", "Gomez", "Guevarra", "Gutierrez", "Lacson", "Lansangan", "Layug",
    "Lingad", "Lugtu", "Macapagal", "Mallari", "Manalang", "Manalo", "Manansala", "Mercado", "Miranda", "Navarro",
    "Nunag", "Ocampo", "Pamintuan", "Panlilio", "Pineda", "Quiambao", "Reyes", "Salonga", "Santos", "Sicat",
    "Simbulan", "Soriano", "Sunga", "Tolentino", "Tuazon", "Valdez", "Vergara", "Yabut", "Yalung", "Zabala",
)

# (first name, last name, email local part, school ID, strictness, joined)
INSTRUCTORS = (
    ("Maria Lourdes", "Dizon", "mldizon", "FAC0201134", "moderate", "2019-06-17"),
    ("Ramon", "Mercado", "rmercado", "FAC0201287", "strict", "2017-08-01"),
    ("Kristine Joy", "Manalo", "kjmanalo", "FAC0202415", "moderate", "2021-01-11"),
    ("Jerome", "Lansangan", "jlansangan", "FAC0202561", "moderate", "2022-06-13"),
    ("Angelica", "Pineda", "apineda", "FAC0203078", "lax", "2025-08-04"),
)

# Faculty hired this school year are created by MIS through the admin form.
NEWLY_PROVISIONED_FACULTY = {"apineda"}


@dataclass(frozen=True)
class ClassPlan:
    key: str
    instructor: str  # INSTRUCTORS email local part
    name: str
    subject_code: str
    section: str
    year_level: int  # students' current year level
    size: int
    activities: tuple[str, ...]  # ActivityTemplate keys, in teaching order
    archived: bool = False


CLASSES = (
    ClassPlan("cp1-it-a", "mldizon", "Computer Programming 1", "CC 102", "BSIT 1-A", 1, 34,
              ("hello", "receipt", "grade_equiv", "mult_table", "jeepney", "class_record", "library")),
    ClassPlan("cp1-it-b", "mldizon", "Computer Programming 1", "CC 102", "BSIT 1-B", 1, 32,
              ("hello", "receipt", "grade_equiv", "mult_table", "jeepney", "class_record", "library")),
    ClassPlan("cp1-cs-a", "rmercado", "Computer Programming 1", "CC 102", "BSCS 1-A", 1, 31,
              ("hello", "receipt", "grade_equiv", "mult_table", "jeepney", "class_record")),
    ClassPlan("cp1-is-a", "apineda", "Computer Programming 1", "CC 102", "BSIS 1-A", 1, 27,
              ("hello", "receipt", "grade_equiv", "mult_table", "jeepney", "class_record")),
    ClassPlan("dsa-cs-a", "kjmanalo", "Data Structures and Algorithms", "CC 104", "BSCS 2-A", 2, 30,
              ("brackets", "queue_sim", "binary_search", "bubble_sort", "course_dir")),
    ClassPlan("ipt-it-b", "jlansangan", "Integrative Programming and Technologies", "IT 213", "BSIT 2-B", 2, 29,
              ("csv_parse", "json_record", "validate_input", "inventory_class")),
    # Last semester's class of the current BSCS 2-A students.
    ClassPlan("cp2-cs-a-prev", "rmercado", "Computer Programming 2", "CC 103", "BSCS 1-A", 2, 30,
              ("class_record", "validate_input", "json_record"), archived=True),
)

# Students who will join a class once MIS creates their account.
PENDING_ENROLLEES = {
    "cp1-it-a": ("Rhea", "Sunga"),
    "cp1-is-a": ("Jayson", "Bondoc"),
}


@dataclass(frozen=True)
class Variant:
    quality: str  # correct | structure | wrong | error
    weight: int
    code: str


@dataclass(frozen=True)
class ActivityTemplate:
    key: str
    title: str
    activity_type: str
    difficulty: str
    description: str
    scenario: str
    instructions: str
    starter_code: str
    rules: dict
    expected_output: str
    solution_explanation: str
    variants: tuple[Variant, ...]
    # Values for @@NAME@@ placeholders, chosen per student.
    choices: dict = field(default_factory=dict)


HEADER_CHOICES = ("", "", "# @@TITLE@@\n", "# @@TITLE@@\n# @@SECTION@@\n\n", "# Activity: @@TITLE@@\n\n")


ACTIVITIES: dict[str, ActivityTemplate] = {}


def _add(template: ActivityTemplate) -> None:
    ACTIVITIES[template.key] = template


_add(ActivityTemplate(
    key="hello",
    title="Laboratory 1: Hello, Pampanga State!",
    activity_type="laboratory",
    difficulty="beginner",
    description="Your first Python program: print the welcome message on three lines.",
    scenario=(
        "The College of Computing Studies wants a short welcome message on the lobby screen "
        "for first-year students. Each line must appear exactly as written."
    ),
    instructions=(
        "Write a program that prints these three lines, in this order:\n\n"
        "```\nPampanga State University\nCollege of Computing Studies\nWelcome to Computer Programming 1!\n```\n\n"
        "Use one `print()` call for each line."
    ),
    starter_code="# Print the three lines below this comment.\n",
    rules={"require_print_call": 3},
    expected_output="Pampanga State University\nCollege of Computing Studies\nWelcome to Computer Programming 1!\n",
    solution_explanation=(
        "Each `print()` call writes one line and ends it with a new line, so three calls produce "
        "three lines. The text inside the quotes is printed exactly, including capital letters and "
        "the exclamation mark."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@print("Pampanga State University")\nprint("College of Computing Studies")\nprint("Welcome to Computer Programming 1!")\n'),
        Variant("correct", 3, "@@HEADER@@print('Pampanga State University')\nprint('College of Computing Studies')\nprint('Welcome to Computer Programming 1!')\n"),
        Variant("correct", 2, '@@HEADER@@@@SCHOOL@@ = "Pampanga State University"\ncollege = "College of Computing Studies"\nmessage = "Welcome to Computer Programming 1!"\n\nprint(@@SCHOOL@@)\nprint(college)\nprint(message)\n'),
        Variant("structure", 2, '@@HEADER@@print("Pampanga State University\\nCollege of Computing Studies\\nWelcome to Computer Programming 1!")\n'),
        Variant("wrong", 2, '@@HEADER@@print("Pampanga State Univeristy")\nprint("College of Computing Studies")\nprint("Welcome to Computer Programming 1")\n'),
        Variant("error", 1, '@@HEADER@@print("Pampanga State University"\nprint("College of Computing Studies")\nprint("Welcome to Computer Programming 1!")\n'),
    ),
    choices={"SCHOOL": ("school", "university", "school_name")},
))

_add(ActivityTemplate(
    key="receipt",
    title="Laboratory 2: Canteen Order Receipt",
    activity_type="laboratory",
    difficulty="beginner",
    description="Use variables and arithmetic to print a small order receipt.",
    scenario=(
        "The university canteen wants a quick receipt for group orders: 2 rice meals at PHP 65 each "
        "and 3 iced teas at PHP 20 each."
    ),
    instructions=(
        "Store each price and quantity in a variable, compute the line totals and the grand total, "
        "then print:\n\n"
        "```\nRice meals: 2 x PHP 65 = PHP 130\nIced tea: 3 x PHP 20 = PHP 60\nTotal: PHP 190\n```\n\n"
        "Compute the totals with arithmetic; don't type the answers yourself."
    ),
    starter_code="meal_price = 65\nmeal_count = 2\ntea_price = 20\ntea_count = 3\n\n# Compute and print the receipt\n",
    rules={"require_print_call": 3},
    expected_output="Rice meals: 2 x PHP 65 = PHP 130\nIced tea: 3 x PHP 20 = PHP 60\nTotal: PHP 190\n",
    solution_explanation=(
        "Multiplying each price by its quantity gives the line totals, and adding them gives the "
        "grand total. f-strings place the numbers inside the text, so the receipt stays correct "
        "if a price changes."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@meal_price = 65\nmeal_count = 2\ntea_price = 20\ntea_count = 3\n\n@@MEALS@@ = meal_price * meal_count\n@@TEAS@@ = tea_price * tea_count\ntotal = @@MEALS@@ + @@TEAS@@\n\nprint(f"Rice meals: {meal_count} x PHP {meal_price} = PHP {@@MEALS@@}")\nprint(f"Iced tea: {tea_count} x PHP {tea_price} = PHP {@@TEAS@@}")\nprint(f"Total: PHP {total}")\n'),
        Variant("correct", 3, '@@HEADER@@meal_price = 65\nmeal_count = 2\ntea_price = 20\ntea_count = 3\n\ntotal = meal_price * meal_count + tea_price * tea_count\nprint("Rice meals: " + str(meal_count) + " x PHP " + str(meal_price) + " = PHP " + str(meal_price * meal_count))\nprint("Iced tea: " + str(tea_count) + " x PHP " + str(tea_price) + " = PHP " + str(tea_price * tea_count))\nprint("Total: PHP " + str(total))\n'),
        Variant("correct", 2, '@@HEADER@@meal_price = 65\nmeal_count = 2\ntea_price = 20\ntea_count = 3\n\nprint("Rice meals: {} x PHP {} = PHP {}".format(meal_count, meal_price, meal_price * meal_count))\nprint("Iced tea: {} x PHP {} = PHP {}".format(tea_count, tea_price, tea_price * tea_count))\nprint("Total: PHP {}".format(meal_price * meal_count + tea_price * tea_count))\n'),
        Variant("wrong", 2, '@@HEADER@@meal_price = 65\nmeal_count = 2\ntea_price = 20\ntea_count = 3\n\nprint(f"Rice meals: {meal_count} x PHP {meal_price} = PHP {meal_price * meal_count}")\nprint(f"Iced tea: {tea_count} x PHP {tea_price} = PHP {tea_price * tea_count}")\nprint(f"Total: PHP {meal_price + tea_price}")\n'),
        Variant("error", 1, '@@HEADER@@meal_price = 65\nmeal_count = 2\ntea_price = 20\ntea_count = 3\n\nprint("Rice meals: " + meal_count + " x PHP " + meal_price)\n'),
    ),
    choices={"MEALS": ("meal_total", "meals_total", "rice_total"), "TEAS": ("tea_total", "drinks_total", "iced_tea_total")},
))

_add(ActivityTemplate(
    key="grade_equiv",
    title="Homework 1: Grade Equivalent",
    activity_type="homework",
    difficulty="beginner",
    description="Convert a percentage into the university's grade equivalent with if/elif/else.",
    scenario=(
        "Faculty encode class standing as a percentage, but the registrar records the grade "
        "equivalent (1.00 to 5.00). Automate the conversion for one student."
    ),
    instructions=(
        "Given `percentage = 87`, print the percentage, the grade equivalent and the remarks:\n\n"
        "```\nPercentage: 87\nGrade: 2.00\nRemarks: Passed\n```\n\n"
        "Scale: 97-100 = 1.00, 94-96 = 1.25, 91-93 = 1.50, 88-90 = 1.75, 85-87 = 2.00, 82-84 = 2.25, "
        "79-81 = 2.50, 76-78 = 2.75, 75 = 3.00, below 75 = 5.00 (Failed)."
    ),
    starter_code="percentage = 87\n\n# Decide the grade equivalent\n",
    rules={"require_if_statement": 1},
    expected_output="Percentage: 87\nGrade: 2.00\nRemarks: Passed\n",
    solution_explanation=(
        "Checking the ranges from the highest down means the first true condition is the right "
        "grade, so each elif only needs a lower bound. Anything below 75 falls through to else."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@percentage = 87\n\nif percentage >= 97:\n    @@GRADE@@ = "1.00"\nelif percentage >= 94:\n    @@GRADE@@ = "1.25"\nelif percentage >= 91:\n    @@GRADE@@ = "1.50"\nelif percentage >= 88:\n    @@GRADE@@ = "1.75"\nelif percentage >= 85:\n    @@GRADE@@ = "2.00"\nelif percentage >= 82:\n    @@GRADE@@ = "2.25"\nelif percentage >= 79:\n    @@GRADE@@ = "2.50"\nelif percentage >= 76:\n    @@GRADE@@ = "2.75"\nelif percentage >= 75:\n    @@GRADE@@ = "3.00"\nelse:\n    @@GRADE@@ = "5.00"\n\nremarks = "Passed" if @@GRADE@@ != "5.00" else "Failed"\nprint(f"Percentage: {percentage}")\nprint(f"Grade: {@@GRADE@@}")\nprint(f"Remarks: {remarks}")\n'),
        Variant("correct", 3, '@@HEADER@@percentage = 87\nscale = [(97, 1.00), (94, 1.25), (91, 1.50), (88, 1.75), (85, 2.00), (82, 2.25), (79, 2.50), (76, 2.75), (75, 3.00)]\n\n@@GRADE@@ = 5.00\nfor minimum, equivalent in scale:\n    if percentage >= minimum:\n        @@GRADE@@ = equivalent\n        break\n\nprint("Percentage:", percentage)\nprint(f"Grade: {@@GRADE@@:.2f}")\nif @@GRADE@@ <= 3.00:\n    print("Remarks: Passed")\nelse:\n    print("Remarks: Failed")\n'),
        Variant("wrong", 3, '@@HEADER@@percentage = 87\n\nif percentage >= 75:\n    print("Percentage:", percentage)\n    print("Grade: Passed")\nelse:\n    print("Grade: Failed")\n'),
        Variant("error", 1, '@@HEADER@@percentage = 87\n\nif percentage >= 97\n    grade = "1.00"\nelse:\n    grade = "2.00"\nprint(grade)\n'),
    ),
    choices={"GRADE": ("grade", "equivalent", "final_grade")},
))

_add(ActivityTemplate(
    key="mult_table",
    title="Laboratory 3: Multiplication Table",
    activity_type="laboratory",
    difficulty="beginner",
    description="Print the multiplication table of 7 using a for loop.",
    scenario="A Grade 3 teacher from a partner school asked the class for a printable table of 7.",
    instructions=(
        "Use a `for` loop to print the table of 7 from 1 to 10, one line each:\n\n"
        "```\n7 x 1 = 7\n7 x 2 = 14\n...\n7 x 10 = 70\n```"
    ),
    starter_code="number = 7\n\n# Print the table with a for loop\n",
    rules={"require_for_loop": 1},
    expected_output="".join(f"7 x {i} = {7 * i}\n" for i in range(1, 11)),
    solution_explanation=(
        "`range(1, 11)` produces 1 to 10 (the end value is excluded), and the loop body prints one "
        "line for each value, so the program stays three lines long however long the table is."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@number = 7\n\nfor @@I@@ in range(1, 11):\n    print(f"{number} x {@@I@@} = {number * @@I@@}")\n'),
        Variant("correct", 3, '@@HEADER@@number = 7\nfor @@I@@ in range(1, 11):\n    product = number * @@I@@\n    print(number, "x", @@I@@, "=", product)\n'),
        Variant("structure", 2, '@@HEADER@@number = 7\n@@I@@ = 1\nwhile @@I@@ <= 10:\n    print(f"{number} x {@@I@@} = {number * @@I@@}")\n    @@I@@ += 1\n'),
        Variant("wrong", 2, '@@HEADER@@number = 7\n\nfor @@I@@ in range(1, 10):\n    print(f"{number} x {@@I@@} = {number * @@I@@}")\n'),
        Variant("error", 1, '@@HEADER@@number = 7\nfor i in range(1, 11):\nprint(number * i)\n'),
    ),
    choices={"I": ("i", "multiplier", "n")},
))

_add(ActivityTemplate(
    key="jeepney",
    title="Laboratory 4: Jeepney Fare Calculator",
    activity_type="laboratory",
    difficulty="intermediate",
    description="Write a function that returns a jeepney fare, with the student discount.",
    scenario=(
        "Students commuting to the Bacolor campus want to check their fare. The minimum fare is "
        "PHP 13.00 for the first 4 km, plus PHP 1.80 for every km after that. Students get 20% off."
    ),
    instructions=(
        "Define a function that takes the distance in km and whether the passenger is a student, "
        "and **returns** the fare. Then print the fares for 4 km (regular), 10 km (regular) and "
        "10 km (student):\n\n"
        "```\n4 km (regular): PHP 13.00\n10 km (regular): PHP 23.80\n10 km (student): PHP 19.04\n```"
    ),
    starter_code="def compute_fare(distance_km, is_student):\n    # Return the fare\n    pass\n",
    rules={"require_function_def": 1, "require_return_statement": 1, "require_if_statement": 1},
    expected_output="4 km (regular): PHP 13.00\n10 km (regular): PHP 23.80\n10 km (student): PHP 19.04\n",
    solution_explanation=(
        "The function starts from the minimum fare and adds PHP 1.80 only for the kilometres beyond "
        "4. The discount is applied last, to the whole fare. Returning the value (instead of "
        "printing inside the function) lets the caller format it with two decimals."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@def @@FN@@(distance_km, is_student):\n    fare = 13.00\n    if distance_km > 4:\n        fare += (distance_km - 4) * 1.80\n    if is_student:\n        fare *= 0.80\n    return fare\n\n\ntrips = [(4, False), (10, False), (10, True)]\nfor km, student in trips:\n    label = "student" if student else "regular"\n    print(f"{km} km ({label}): PHP {@@FN@@(km, student):.2f}")\n'),
        Variant("correct", 3, '@@HEADER@@def @@FN@@(distance_km, is_student):\n    extra_km = max(0, distance_km - 4)\n    fare = 13.00 + extra_km * 1.80\n    if is_student:\n        return fare * 0.8\n    return fare\n\n\nprint(f"4 km (regular): PHP {@@FN@@(4, False):.2f}")\nprint(f"10 km (regular): PHP {@@FN@@(10, False):.2f}")\nprint(f"10 km (student): PHP {@@FN@@(10, True):.2f}")\n'),
        Variant("structure", 2, '@@HEADER@@def @@FN@@(distance_km, is_student):\n    fare = 13.00\n    if distance_km > 4:\n        fare += (distance_km - 4) * 1.80\n    if is_student:\n        fare *= 0.80\n    label = "student" if is_student else "regular"\n    print(f"{distance_km} km ({label}): PHP {fare:.2f}")\n\n\n@@FN@@(4, False)\n@@FN@@(10, False)\n@@FN@@(10, True)\n'),
        Variant("wrong", 2, '@@HEADER@@def @@FN@@(distance_km, is_student):\n    fare = 13.00\n    if distance_km > 4:\n        fare += (distance_km - 4) * 1.80\n    return fare\n\n\nfor km, student in [(4, False), (10, False), (10, True)]:\n    label = "student" if student else "regular"\n    print(f"{km} km ({label}): PHP {@@FN@@(km, student):.2f}")\n'),
        Variant("error", 1, '@@HEADER@@def @@FN@@(distance_km, is_student):\n    fare = 13.00\n    if distance_km > 4:\n        fare += (distance_km - 4) * 1.80\n    return fare\n\nprint(f"10 km: PHP {compute(10, False):.2f}")\n'),
    ),
    choices={"FN": ("compute_fare", "get_fare", "calculate_fare")},
))

_add(ActivityTemplate(
    key="class_record",
    title="Homework 2: Class Record Average",
    activity_type="homework",
    difficulty="intermediate",
    description="Use a list and a loop to compute the average, highest and lowest quiz score.",
    scenario=(
        "A class adviser keeps quiz scores in a list and needs the class average, the highest and "
        "the lowest score for the class record."
    ),
    instructions=(
        "Given `scores = [88, 92, 75, 95, 70, 85]`, use a `for` loop (not `sum`, `max` or `min`) "
        "to print:\n\n```\nAverage: 84.17\nHighest: 95\nLowest: 70\n```"
    ),
    starter_code="scores = [88, 92, 75, 95, 70, 85]\n\n# Compute with a for loop\n",
    rules={"require_list": 1, "require_for_loop": 1},
    expected_output="Average: 84.17\nHighest: 95\nLowest: 70\n",
    solution_explanation=(
        "One pass through the list is enough: keep a running total, and replace the highest or "
        "lowest value whenever a score beats it. Starting both from the first score avoids "
        "guessing a starting value."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@scores = [88, 92, 75, 95, 70, 85]\n\n@@TOTAL@@ = 0\nhighest = scores[0]\nlowest = scores[0]\nfor score in scores:\n    @@TOTAL@@ += score\n    if score > highest:\n        highest = score\n    if score < lowest:\n        lowest = score\n\naverage = @@TOTAL@@ / len(scores)\nprint(f"Average: {average:.2f}")\nprint(f"Highest: {highest}")\nprint(f"Lowest: {lowest}")\n'),
        Variant("correct", 3, '@@HEADER@@scores = [88, 92, 75, 95, 70, 85]\n@@TOTAL@@ = 0\ncount = 0\nhighest = lowest = scores[0]\nfor score in scores:\n    @@TOTAL@@ = @@TOTAL@@ + score\n    count = count + 1\n    highest = score if score > highest else highest\n    lowest = score if score < lowest else lowest\nprint("Average:", format(@@TOTAL@@ / count, ".2f"))\nprint("Highest:", highest)\nprint("Lowest:", lowest)\n'),
        Variant("structure", 3, '@@HEADER@@scores = [88, 92, 75, 95, 70, 85]\n\nprint(f"Average: {sum(scores) / len(scores):.2f}")\nprint(f"Highest: {max(scores)}")\nprint(f"Lowest: {min(scores)}")\n'),
        Variant("wrong", 1, '@@HEADER@@scores = [88, 92, 75, 95, 70, 85]\n@@TOTAL@@ = 0\nfor score in scores:\n    @@TOTAL@@ += score\nprint(f"Average: {@@TOTAL@@ / len(scores)}")\nprint(f"Highest: {scores[-1]}")\nprint(f"Lowest: {scores[0]}")\n'),
        Variant("error", 1, '@@HEADER@@scores = [88, 92, 75, 95, 70, 85]\nfor score in scores:\n    total += score\nprint(total / len(scores))\n'),
    ),
    choices={"TOTAL": ("total", "running_total", "score_sum")},
))

_add(ActivityTemplate(
    key="library",
    title="Laboratory 5: Library Book Inventory",
    activity_type="laboratory",
    difficulty="intermediate",
    description="Store book titles and copies in a dictionary and report what is available.",
    scenario=(
        "The university library lends programming books to first-year students and wants a quick "
        "count of the copies on the shelf."
    ),
    instructions=(
        "Store the books in a dictionary (title → copies). Loop over it to print each title with its "
        "copies, then the total:\n\n"
        "```\nPython Crash Course: 4\nThink Python: 2\nAutomate the Boring Stuff: 3\nTotal copies: 9\n```"
    ),
    starter_code="# Create the dictionary of books here\n",
    rules={"require_dict": 1, "require_for_loop": 1},
    expected_output="Python Crash Course: 4\nThink Python: 2\nAutomate the Boring Stuff: 3\nTotal copies: 9\n",
    solution_explanation=(
        "A dictionary keeps each title next to its number of copies. Looping over `items()` gives "
        "both at once, and a running total counts the copies while printing."
    ),
    variants=(
        Variant("correct", 1, 'books = {"Python Crash Course": 4, "Think Python": 2, "Automate the Boring Stuff": 3}\ntotal = 0\nfor title, copies in books.items():\n    print(f"{title}: {copies}")\n    total += copies\nprint(f"Total copies: {total}")\n'),
    ),
))

_add(ActivityTemplate(
    key="brackets",
    title="Laboratory 1: Balanced Brackets Checker",
    activity_type="laboratory",
    difficulty="intermediate",
    description="Use a list as a stack to check whether brackets in an expression are balanced.",
    scenario=(
        "A calculator app for the Mathematics department must reject formulas with unmatched "
        "brackets before evaluating them."
    ),
    instructions=(
        "Write `is_balanced(expression)` that uses a list as a stack and returns `True` or `False`. "
        "Check these three expressions:\n\n"
        "```\n(a + b) * [c - d]: balanced\n{[(])}: not balanced\n((x): not balanced\n```"
    ),
    starter_code="def is_balanced(expression):\n    stack = []\n    # Push opening brackets, pop on closing ones\n",
    rules={"require_function_def": 1, "require_for_loop": 1, "require_return_statement": 1},
    expected_output="(a + b) * [c - d]: balanced\n{[(])}: not balanced\n((x): not balanced\n",
    solution_explanation=(
        "Every opening bracket is pushed; every closing bracket must match the most recent opening "
        "one, which is exactly what popping the stack gives. The expression is balanced only if "
        "nothing is left on the stack at the end."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@def @@FN@@(expression):\n    pairs = {")": "(", "]": "[", "}": "{"}\n    stack = []\n    for ch in expression:\n        if ch in "([{":\n            stack.append(ch)\n        elif ch in pairs:\n            if not stack or stack.pop() != pairs[ch]:\n                return False\n    return not stack\n\n\nfor expr in ["(a + b) * [c - d]", "{[(])}", "((x)"]:\n    result = "balanced" if @@FN@@(expr) else "not balanced"\n    print(f"{expr}: {result}")\n'),
        Variant("correct", 3, '@@HEADER@@def @@FN@@(expression):\n    stack = []\n    for ch in expression:\n        if ch == "(" or ch == "[" or ch == "{":\n            stack.append(ch)\n        elif ch == ")" or ch == "]" or ch == "}":\n            if len(stack) == 0:\n                return False\n            top = stack.pop()\n            if (top, ch) not in [("(", ")"), ("[", "]"), ("{", "}")]:\n                return False\n    return len(stack) == 0\n\n\nexpressions = ["(a + b) * [c - d]", "{[(])}", "((x)"]\nfor expr in expressions:\n    print(expr + ": " + ("balanced" if @@FN@@(expr) else "not balanced"))\n'),
        Variant("wrong", 3, '@@HEADER@@def @@FN@@(expression):\n    return (expression.count("(") == expression.count(")")\n            and expression.count("[") == expression.count("]")\n            and expression.count("{") == expression.count("}"))\n\n\nfor expr in ["(a + b) * [c - d]", "{[(])}", "((x)"]:\n    print(f"{expr}: {\'balanced\' if @@FN@@(expr) else \'not balanced\'}")\n'),
        Variant("error", 1, '@@HEADER@@def @@FN@@(expression):\n    stack = []\n    for ch in expression:\n        if ch in "([{":\n            stack.push(ch)\n    return not stack\n\nprint(@@FN@@("(a)"))\n'),
    ),
    choices={"FN": ("is_balanced", "check_brackets", "balanced")},
))

_add(ActivityTemplate(
    key="queue_sim",
    title="Laboratory 2: Enrollment Line Queue",
    activity_type="laboratory",
    difficulty="intermediate",
    description="Simulate a first-come, first-served queue with collections.deque.",
    scenario=(
        "During enrollment week the Registrar serves students at two windows, alternating between "
        "them, in the order the students arrived."
    ),
    instructions=(
        "Use `collections.deque` and a `while` loop to serve Ana, Ben, Carlo, Dina and Elle, "
        "alternating between Window 1 and Window 2, then print `All students served.`"
    ),
    starter_code="from collections import deque\n\nline = deque([\"Ana\", \"Ben\", \"Carlo\", \"Dina\", \"Elle\"])\n",
    rules={"require_import": 1, "require_while_loop": 1},
    expected_output=(
        "Window 1: now serving Ana\nWindow 2: now serving Ben\nWindow 1: now serving Carlo\n"
        "Window 2: now serving Dina\nWindow 1: now serving Elle\nAll students served.\n"
    ),
    solution_explanation=(
        "A deque removes items from the front in constant time with `popleft()`, which is what a "
        "queue needs. The loop runs while the line is not empty and flips the window number after "
        "each student."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@from collections import deque\n\nline = deque(["Ana", "Ben", "Carlo", "Dina", "Elle"])\n@@WIN@@ = 1\nwhile line:\n    student = line.popleft()\n    print(f"Window {@@WIN@@}: now serving {student}")\n    @@WIN@@ = 2 if @@WIN@@ == 1 else 1\nprint("All students served.")\n'),
        Variant("correct", 3, '@@HEADER@@from collections import deque\n\nline = deque(["Ana", "Ben", "Carlo", "Dina", "Elle"])\nserved = 0\nwhile len(line) > 0:\n    @@WIN@@ = served % 2 + 1\n    print("Window", str(@@WIN@@) + ":", "now serving", line.popleft())\n    served += 1\nprint("All students served.")\n'),
        Variant("structure", 2, '@@HEADER@@line = ["Ana", "Ben", "Carlo", "Dina", "Elle"]\n@@WIN@@ = 1\nwhile line:\n    print(f"Window {@@WIN@@}: now serving {line.pop(0)}")\n    @@WIN@@ = 2 if @@WIN@@ == 1 else 1\nprint("All students served.")\n'),
        Variant("wrong", 2, '@@HEADER@@from collections import deque\n\nline = deque(["Ana", "Ben", "Carlo", "Dina", "Elle"])\nwhile line:\n    print(f"Window 1: now serving {line.pop()}")\nprint("All students served.")\n'),
    ),
    choices={"WIN": ("window", "counter", "win")},
))

_add(ActivityTemplate(
    key="binary_search",
    title="Homework 1: Binary Search on Student Numbers",
    activity_type="homework",
    difficulty="intermediate",
    description="Implement binary search with a while loop on a sorted list of student numbers.",
    scenario=(
        "The OSA keeps a sorted list of student numbers with incomplete clearances and needs a fast "
        "way to look one up."
    ),
    instructions=(
        "Write `binary_search(ids, target)` with a `while` loop that returns the index of `target` or "
        "`-1`. Search for 2025100417 and 2025100500:\n\n"
        "```\n2025100417: found at index 3\n2025100500: not found\n```"
    ),
    starter_code="student_numbers = [2025100112, 2025100245, 2025100398, 2025100417, 2025100583, 2025100691]\n",
    rules={"require_function_def": 1, "require_while_loop": 1, "require_return_statement": 1},
    expected_output="2025100417: found at index 3\n2025100500: not found\n",
    solution_explanation=(
        "Each step compares the middle item and discards the half that cannot contain the target, "
        "so a list of a million numbers needs about 20 comparisons instead of a million."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@def @@FN@@(ids, target):\n    low, high = 0, len(ids) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if ids[mid] == target:\n            return mid\n        if ids[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n\n\nstudent_numbers = [2025100112, 2025100245, 2025100398, 2025100417, 2025100583, 2025100691]\nfor target in [2025100417, 2025100500]:\n    index = @@FN@@(student_numbers, target)\n    if index == -1:\n        print(f"{target}: not found")\n    else:\n        print(f"{target}: found at index {index}")\n'),
        Variant("structure", 3, '@@HEADER@@def @@FN@@(ids, target):\n    for index, value in enumerate(ids):\n        if value == target:\n            return index\n    return -1\n\n\nstudent_numbers = [2025100112, 2025100245, 2025100398, 2025100417, 2025100583, 2025100691]\nfor target in [2025100417, 2025100500]:\n    index = @@FN@@(student_numbers, target)\n    print(f"{target}: found at index {index}" if index != -1 else f"{target}: not found")\n'),
        Variant("wrong", 1, '@@HEADER@@def @@FN@@(ids, target):\n    low, high = 0, len(ids)\n    while low < high:\n        mid = (low + high) // 2\n        if ids[mid] < target:\n            low = mid + 1\n        else:\n            high = mid\n    return low\n\n\nstudent_numbers = [2025100112, 2025100245, 2025100398, 2025100417, 2025100583, 2025100691]\nfor target in [2025100417, 2025100500]:\n    print(f"{target}: found at index {@@FN@@(student_numbers, target)}")\n'),
    ),
    choices={"FN": ("binary_search", "search_id", "find_student")},
))

_add(ActivityTemplate(
    key="bubble_sort",
    title="Laboratory 3: Ranking Exam Scores with Bubble Sort",
    activity_type="laboratory",
    difficulty="intermediate",
    description="Sort exam scores from highest to lowest with nested loops, then print the ranking.",
    scenario="The department ranks midterm scores for the Dean's List shortlist.",
    instructions=(
        "Write `bubble_sort(scores)` with nested `for` loops (no `sort` or `sorted`) and print the "
        "ranking of `[78, 92, 85, 64, 99, 71]` from highest to lowest: `Rank 1: 99` ... `Rank 6: 64`."
    ),
    starter_code="exam_scores = [78, 92, 85, 64, 99, 71]\n",
    rules={"require_function_def": 1, "require_for_loop": 2},
    expected_output="".join(f"Rank {rank}: {score}\n" for rank, score in enumerate([99, 92, 85, 78, 71, 64], start=1)),
    solution_explanation=(
        "After each pass of the inner loop the smallest remaining score has moved to the end, so the "
        "next pass can stop one place earlier. Swapping when the left score is smaller sorts from "
        "highest to lowest."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@def bubble_sort(scores):\n    items = scores[:]\n    n = len(items)\n    for i in range(n - 1):\n        for j in range(n - 1 - i):\n            if items[j] < items[j + 1]:\n                items[j], items[j + 1] = items[j + 1], items[j]\n    return items\n\n\nexam_scores = [78, 92, 85, 64, 99, 71]\nfor rank, score in enumerate(bubble_sort(exam_scores), start=1):\n    print(f"Rank {rank}: {score}")\n'),
        Variant("structure", 3, '@@HEADER@@def bubble_sort(scores):\n    return sorted(scores, reverse=True)\n\n\nexam_scores = [78, 92, 85, 64, 99, 71]\nfor rank, score in enumerate(bubble_sort(exam_scores), start=1):\n    print(f"Rank {rank}: {score}")\n'),
        Variant("wrong", 2, '@@HEADER@@def bubble_sort(scores):\n    items = scores[:]\n    for i in range(len(items)):\n        for j in range(len(items) - 1):\n            if items[j] > items[j + 1]:\n                items[j], items[j + 1] = items[j + 1], items[j]\n    return items\n\n\nexam_scores = [78, 92, 85, 64, 99, 71]\nfor rank, score in enumerate(bubble_sort(exam_scores), start=1):\n    print(f"Rank {rank}: {score}")\n'),
        Variant("error", 1, '@@HEADER@@def bubble_sort(scores):\n    for i in range(len(scores)):\n        for j in range(len(scores) - 1):\n            if scores[j] < scores[j + 1]:\n                scores[j], scores[j + 1] = scores[j + 1], scores[j]\n   return scores\n'),
    ),
))

_add(ActivityTemplate(
    key="course_dir",
    title="Laboratory 4: Course Directory",
    activity_type="laboratory",
    difficulty="intermediate",
    description="Store course codes and titles in a dictionary and print them in order.",
    scenario="The CCS faculty room needs a printed list of course codes and titles for the new term.",
    instructions=(
        "Store the courses in a dictionary (code → title), print them sorted by code, then the total:\n\n"
        "```\nCC 101 - Introduction to Computing\nCC 102 - Computer Programming 1\n"
        "CC 104 - Data Structures and Algorithms\nTotal courses: 3\n```"
    ),
    starter_code="# Course code -> course title\ncourses = {}\n",
    rules={"require_dict": 1, "require_for_loop": 1},
    expected_output=(
        "CC 101 - Introduction to Computing\nCC 102 - Computer Programming 1\n"
        "CC 104 - Data Structures and Algorithms\nTotal courses: 3\n"
    ),
    solution_explanation=(
        "Sorting the dictionary's items orders them by key, the course code. `len()` on a "
        "dictionary counts its keys."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@courses = {\n    "CC 104": "Data Structures and Algorithms",\n    "CC 101": "Introduction to Computing",\n    "CC 102": "Computer Programming 1",\n}\n\nfor code, title in sorted(courses.items()):\n    print(f"{code} - {title}")\nprint(f"Total courses: {len(courses)}")\n'),
        Variant("correct", 3, '@@HEADER@@courses = {"CC 101": "Introduction to Computing", "CC 102": "Computer Programming 1", "CC 104": "Data Structures and Algorithms"}\nfor code in sorted(courses):\n    print(code, "-", courses[code])\nprint("Total courses:", len(courses))\n'),
        Variant("wrong", 2, '@@HEADER@@courses = {"CC 104": "Data Structures and Algorithms", "CC 101": "Introduction to Computing", "CC 102": "Computer Programming 1"}\nfor code in courses:\n    print(f"{code} - {courses[code]}")\nprint(f"Total courses: {len(courses)}")\n'),
    ),
))

_add(ActivityTemplate(
    key="csv_parse",
    title="Laboratory 1: Parsing Enrollment Records",
    activity_type="laboratory",
    difficulty="intermediate",
    description="Read CSV text with the csv module and total the enrolled units.",
    scenario=(
        "The Registrar exports enrollment records as CSV. The department needs each student's load "
        "and the total units of the block section."
    ),
    instructions=(
        "Use the `csv` module to read `DATA`, print each student's name, program and units, then the "
        "total:\n\n"
        "```\nAndrea Dizon (BSIT): 21 units\nMark Lansangan (BSIT): 18 units\nJoy Tuazon (BSIT): 24 units\n"
        "Total units enrolled: 63\n```"
    ),
    starter_code=(
        "import csv\nimport io\n\nDATA = \"\"\"student_no,name,program,units\n2025100112,Andrea Dizon,BSIT,21\n"
        "2025100245,Mark Lansangan,BSIT,18\n2025100398,Joy Tuazon,BSIT,24\n\"\"\"\n"
    ),
    rules={"require_import": 1, "require_for_loop": 1},
    expected_output=(
        "Andrea Dizon (BSIT): 21 units\nMark Lansangan (BSIT): 18 units\nJoy Tuazon (BSIT): 24 units\n"
        "Total units enrolled: 63\n"
    ),
    solution_explanation=(
        "`csv.DictReader` turns each row into a dictionary keyed by the header, so the code reads "
        "`row[\"units\"]` instead of remembering column positions. Units arrive as text and must be "
        "converted with `int()` before adding."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@import csv\nimport io\n\nDATA = """student_no,name,program,units\n2025100112,Andrea Dizon,BSIT,21\n2025100245,Mark Lansangan,BSIT,18\n2025100398,Joy Tuazon,BSIT,24\n"""\n\n@@TOTAL@@ = 0\nfor row in csv.DictReader(io.StringIO(DATA)):\n    units = int(row["units"])\n    @@TOTAL@@ += units\n    print(f"{row[\'name\']} ({row[\'program\']}): {units} units")\nprint(f"Total units enrolled: {@@TOTAL@@}")\n'),
        Variant("correct", 3, '@@HEADER@@import csv\nimport io\n\nDATA = """student_no,name,program,units\n2025100112,Andrea Dizon,BSIT,21\n2025100245,Mark Lansangan,BSIT,18\n2025100398,Joy Tuazon,BSIT,24\n"""\n\nreader = csv.reader(io.StringIO(DATA))\nnext(reader)\n@@TOTAL@@ = 0\nfor student_no, name, program, units in reader:\n    @@TOTAL@@ += int(units)\n    print(name + " (" + program + "): " + units + " units")\nprint("Total units enrolled:", @@TOTAL@@)\n'),
        Variant("structure", 2, '@@HEADER@@DATA = """student_no,name,program,units\n2025100112,Andrea Dizon,BSIT,21\n2025100245,Mark Lansangan,BSIT,18\n2025100398,Joy Tuazon,BSIT,24\n"""\n\n@@TOTAL@@ = 0\nfor line in DATA.strip().splitlines()[1:]:\n    student_no, name, program, units = line.split(",")\n    @@TOTAL@@ += int(units)\n    print(f"{name} ({program}): {units} units")\nprint(f"Total units enrolled: {@@TOTAL@@}")\n'),
        Variant("error", 1, '@@HEADER@@import csv\nimport io\n\nDATA = """student_no,name,program,units\n2025100112,Andrea Dizon,BSIT,21\n"""\n\ntotal = 0\nfor row in csv.DictReader(io.StringIO(DATA)):\n    total += row["units"]\nprint(total)\n'),
    ),
    choices={"TOTAL": ("total_units", "total", "unit_total")},
))

_add(ActivityTemplate(
    key="json_record",
    title="Laboratory 2: Student Record as JSON",
    activity_type="laboratory",
    difficulty="intermediate",
    description="Represent a student record as a dictionary and serialize it with json.dumps.",
    scenario=(
        "The student portal exchanges records with other offices as JSON. Produce one student's "
        "record in the agreed format."
    ),
    instructions=(
        "Build a dictionary with `student_no`, `name`, `program`, `year_level` and `subjects`, then "
        "print it with `json.dumps(record, indent=2)`."
    ),
    starter_code="import json\n\n# Build the record dictionary\n",
    rules={"require_import": 1, "require_dict": 1},
    expected_output=(
        '{\n  "student_no": "2025100112",\n  "name": "Andrea Dizon",\n  "program": "BSIT",\n'
        '  "year_level": 2,\n  "subjects": [\n    "IT 213",\n    "IT 214",\n    "GE 105"\n  ]\n}\n'
    ),
    solution_explanation=(
        "`json.dumps` converts Python values to JSON text: strings get double quotes, the list "
        "becomes a JSON array and the number stays a number. `indent=2` makes it readable."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@import json\n\n@@REC@@ = {\n    "student_no": "2025100112",\n    "name": "Andrea Dizon",\n    "program": "BSIT",\n    "year_level": 2,\n    "subjects": ["IT 213", "IT 214", "GE 105"],\n}\nprint(json.dumps(@@REC@@, indent=2))\n'),
        Variant("structure", 2, '@@HEADER@@import json\n\n@@REC@@ = dict(student_no="2025100112", name="Andrea Dizon", program="BSIT", year_level=2, subjects=["IT 213", "IT 214", "GE 105"])\ntext = json.dumps(@@REC@@, indent=2)\nprint(text)\n'),
        Variant("wrong", 2, '@@HEADER@@import json\n\n@@REC@@ = {"student_no": 2025100112, "name": "Andrea Dizon", "program": "BSIT", "year_level": "2", "subjects": ["IT 213", "IT 214", "GE 105"]}\nprint(json.dumps(@@REC@@, indent=2))\n'),
        Variant("wrong", 1, '@@HEADER@@@@REC@@ = {"student_no": "2025100112", "name": "Andrea Dizon", "program": "BSIT", "year_level": 2, "subjects": ["IT 213", "IT 214", "GE 105"]}\nprint(@@REC@@)\n'),
    ),
    choices={"REC": ("record", "student", "student_record")},
))

_add(ActivityTemplate(
    key="validate_input",
    title="Homework 1: Validating Payment Amounts",
    activity_type="homework",
    difficulty="intermediate",
    description="Use try/except to reject payment amounts that are not valid numbers.",
    scenario=(
        "The cashier's kiosk receives amounts typed by students. Bad entries must be rejected "
        "without crashing the kiosk."
    ),
    instructions=(
        "Write `parse_amount(text)` that returns the amount as a float, or `None` when the text is "
        "not a number or not positive. Use `try`/`except ValueError`. Check '1500', 'abc', '-200' "
        "and '750.50':\n\n"
        "```\n'1500': accepted PHP 1500.00\n'abc': invalid amount\n'-200': invalid amount\n'750.50': accepted PHP 750.50\n```"
    ),
    starter_code="def parse_amount(text):\n    # Return a positive float or None\n    pass\n",
    rules={"require_try_except": 1, "require_function_def": 1},
    expected_output="'1500': accepted PHP 1500.00\n'abc': invalid amount\n'-200': invalid amount\n'750.50': accepted PHP 750.50\n",
    solution_explanation=(
        "`float()` raises `ValueError` for text such as 'abc'; catching it turns a crash into a "
        "normal 'invalid' result. A separate check rejects zero and negative amounts, which are "
        "valid numbers but not valid payments."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@def @@FN@@(text):\n    try:\n        amount = float(text)\n    except ValueError:\n        return None\n    if amount <= 0:\n        return None\n    return amount\n\n\nfor entry in ["1500", "abc", "-200", "750.50"]:\n    amount = @@FN@@(entry)\n    if amount is None:\n        print(f"{entry!r}: invalid amount")\n    else:\n        print(f"{entry!r}: accepted PHP {amount:.2f}")\n'),
        Variant("correct", 3, '@@HEADER@@def @@FN@@(text):\n    try:\n        amount = float(text)\n        return amount if amount > 0 else None\n    except ValueError:\n        return None\n\n\nfor entry in ["1500", "abc", "-200", "750.50"]:\n    amount = @@FN@@(entry)\n    message = "invalid amount" if amount is None else "accepted PHP " + format(amount, ".2f")\n    print(repr(entry) + ": " + message)\n'),
        Variant("wrong", 2, '@@HEADER@@def @@FN@@(text):\n    if text.isdigit():\n        return float(text)\n    return None\n\n\nfor entry in ["1500", "abc", "-200", "750.50"]:\n    amount = @@FN@@(entry)\n    print(f"{entry!r}: invalid amount" if amount is None else f"{entry!r}: accepted PHP {amount:.2f}")\n'),
        Variant("error", 1, '@@HEADER@@def @@FN@@(text):\n    return float(text)\n\n\nfor entry in ["1500", "abc"]:\n    print(@@FN@@(entry))\n'),
    ),
    choices={"FN": ("parse_amount", "to_amount", "read_amount")},
))

_add(ActivityTemplate(
    key="inventory_class",
    title="Laboratory 3: Inventory Item Class",
    activity_type="laboratory",
    difficulty="expert",
    description="Model supply-room items with a class, methods and attributes.",
    scenario="The CCS supply room tracks bond paper and markers and needs the value of its stock.",
    instructions=(
        "Define `InventoryItem` with `name`, `quantity` and `unit_price`, a `total_value()` method and "
        "a `restock(amount)` method. Restock the markers by 10, then print:\n\n"
        "```\nBond paper (ream): 12 pcs, PHP 2940.00\nWhiteboard marker: 40 pcs, PHP 1540.00\n```"
    ),
    starter_code="class InventoryItem:\n    def __init__(self, name, quantity, unit_price):\n        pass\n",
    rules={"require_class_def": 1, "require_function_def": 2},
    expected_output="Bond paper (ream): 12 pcs, PHP 2940.00\nWhiteboard marker: 40 pcs, PHP 1540.00\n",
    solution_explanation=(
        "Keeping the data and the operations together in a class means each item computes its own "
        "value and restocks itself; the loop at the end only asks each object for its values."
    ),
    variants=(
        Variant("correct", 6, '@@HEADER@@class InventoryItem:\n    def __init__(self, name, quantity, unit_price):\n        self.name = name\n        self.quantity = quantity\n        self.unit_price = unit_price\n\n    def total_value(self):\n        return self.quantity * self.unit_price\n\n    def restock(self, amount):\n        self.quantity += amount\n\n\n@@ITEMS@@ = [InventoryItem("Bond paper (ream)", 12, 245.0), InventoryItem("Whiteboard marker", 30, 38.5)]\n@@ITEMS@@[1].restock(10)\nfor item in @@ITEMS@@:\n    print(f"{item.name}: {item.quantity} pcs, PHP {item.total_value():.2f}")\n'),
        Variant("wrong", 2, '@@HEADER@@class InventoryItem:\n    def __init__(self, name, quantity, unit_price):\n        self.name = name\n        self.quantity = quantity\n        self.unit_price = unit_price\n\n    def total_value(self):\n        return self.quantity * self.unit_price\n\n\n@@ITEMS@@ = [InventoryItem("Bond paper (ream)", 12, 245.0), InventoryItem("Whiteboard marker", 30, 38.5)]\nfor item in @@ITEMS@@:\n    print(f"{item.name}: {item.quantity} pcs, PHP {item.total_value():.2f}")\n'),
    ),
    choices={"ITEMS": ("items", "inventory", "stock")},
))


@dataclass(frozen=True)
class PracticeLesson:
    title: str
    instructions: str
    starter_code: str
    expected_output: str
    expected_ast_patterns: dict
    solution: str
    mistake: str  # a typical failed attempt
    mistake_feedback: str


PRACTICE_MODULES = (
    ("Python Basics", "Learn the basic syntax and structure of Python. Master variables and printing.", (
        PracticeLesson(
            "Hello World",
            "# Welcome to Python!\n\nPython reads almost like plain English. By tradition, your first "
            "program prints **\"Hello, World!\"**.\n\nThe `print()` function writes whatever is inside its "
            "parentheses. Text (a **string**) goes inside quotes.\n\n```python\nprint(\"Welcome to PAMSU IDE!\")\n```\n\n"
            "### Activity\nPrint exactly: `Hello, World!`",
            "# Write your code below\n", "Hello, World!\n", {"require_print_call": True},
            'print("Hello, World!")\n', 'print("Hello World")\n',
            "Execution failed or output did not match expected output.",
        ),
        PracticeLesson(
            "Variables",
            "# Variables\n\nA **variable** is a name for a value: `x = 5` stores 5 in `x`. Printing the "
            "variable prints its value.\n\n### Activity\nCreate a variable `x` assigned to 5, then print `x`.",
            "# Create variable x\n", "5\n", {"require_print_call": True},
            "x = 5\nprint(x)\n", 'x = 5\nprint("x")\n',
            "Execution failed or output did not match expected output.",
        ),
    )),
    ("Control Flow", "Make decisions in your code using if, elif, and else statements.", (
        PracticeLesson(
            "If Statements",
            "# Making decisions\n\nAn `if` statement runs its block only when the condition is true. "
            "The block is the indented code under the colon.\n\n### Activity\n`x` is 10. Print `Positive` if "
            "`x` is greater than 0.",
            "x = 10\n# Write your if statement here\n", "Positive\n",
            {"require_if_statement": True, "require_print_call": True},
            'x = 10\nif x > 0:\n    print("Positive")\n', 'x = 10\nif x > 0\n    print("Positive")\n',
            "SyntaxError: expected ':'",
        ),
    )),
    ("Loops", "Automate repetitive tasks using for and while loops.", (
        PracticeLesson(
            "For Loop",
            "# Repeating with for\n\n`for i in range(5):` runs its block five times, with `i` taking "
            "the values 0 to 4.\n\n### Activity\nPrint the numbers 0 to 4, each on its own line.",
            "# Write a for loop\n", "0\n1\n2\n3\n4\n", {"require_for_loop": True, "require_print_call": True},
            "for i in range(5):\n    print(i)\n", "for i in range(1, 5):\n    print(i)\n",
            "Execution failed or output did not match expected output.",
        ),
        PracticeLesson(
            "While Loop",
            "# Repeating with while\n\nA `while` loop repeats as long as its condition is true, so "
            "something inside must eventually make it false.\n\n### Activity\nPrint `Run` exactly 3 times "
            "with a while loop.",
            "count = 0\n# Write a while loop\n", "Run\nRun\nRun\n",
            {"require_while_loop": True, "require_print_call": True},
            'count = 0\nwhile count < 3:\n    print("Run")\n    count += 1\n',
            'count = 0\nwhile count <= 3:\n    print("Run")\n    count += 1\n',
            "Execution failed or output did not match expected output.",
        ),
    )),
    ("Functions", "Organize your code with reusable functions.", (
        PracticeLesson(
            "Defining Functions",
            "# Functions\n\n`def greet():` defines a function; its body runs each time you call "
            "`greet()`.\n\n### Activity\nDefine `greet` that prints `Hello`, then call it.",
            "# Define greet() here\n", "Hello\n", {"require_function_def": True, "require_function_call": True},
            'def greet():\n    print("Hello")\n\ngreet()\n', 'def greet():\n    print("Hello")\n',
            "Execution failed or output did not match expected output.",
        ),
        PracticeLesson(
            "Return Values",
            "# Returning a value\n\n`return` sends a value back to the caller, so the result can be "
            "printed or used in another calculation.\n\n### Activity\nDefine `add(a, b)` that returns the "
            "sum, then print `add(2, 3)`.",
            "# Define add(a, b) here\n", "5\n",
            {"require_function_def": True, "require_return_statement": True, "require_print_call": True},
            "def add(a, b):\n    return a + b\n\nprint(add(2, 3))\n",
            "def add(a, b):\n    print(a + b)\n\nadd(2, 3)\n",
            "Missing Return statement: Use at least 1 return statement.",
        ),
    )),
    ("Data Structures", "Store and manipulate collections of data using Lists and Dictionaries.", (
        PracticeLesson(
            "Lists",
            "# Lists\n\nA list keeps several values in order: `[\"apple\", \"banana\"]`.\n\n### Activity\n"
            "Create `fruits` containing 'apple' and 'banana', then print the list.",
            "# Create your list here\n", "['apple', 'banana']\n", {"require_print_call": True},
            'fruits = ["apple", "banana"]\nprint(fruits)\n', 'fruits = "apple, banana"\nprint(fruits)\n',
            "Execution failed or output did not match expected output.",
        ),
        PracticeLesson(
            "List Comprehension",
            "# List comprehensions\n\n`[n * n for n in range(1, 4)]` builds a list in one line.\n\n"
            "### Activity\nUse a list comprehension to build the squares of 1 to 3 and print `[1, 4, 9]`.",
            "# Write your list comprehension\n", "[1, 4, 9]\n",
            {"require_list_comprehension": True, "require_print_call": True},
            "squares = [n * n for n in range(1, 4)]\nprint(squares)\n", "squares = [1, 4, 9]\nprint(squares)\n",
            "Missing List comprehension: Use at least 1 list comprehension.",
        ),
    )),
    ("Object-Oriented Programming", "Model real-world concepts using Classes and Objects.", (
        PracticeLesson(
            "Classes and Objects",
            "# Classes\n\nA class describes a kind of object; its methods are functions that belong to "
            "it.\n\n### Activity\nDefine `Dog` with a method `bark` that prints `Woof!`. Create a dog and "
            "call `bark()`.",
            "# Define your class here\n", "Woof!\n",
            {"require_class_def": True, "require_function_def": True, "require_print_call": True},
            'class Dog:\n    def bark(self):\n        print("Woof!")\n\nDog().bark()\n',
            'class Dog:\n    def bark():\n        print("Woof!")\n\nDog().bark()\n',
            "TypeError: Dog.bark() takes 0 positional arguments but 1 was given",
        ),
    )),
)

GRADE_FEEDBACK = {
    "correct": (
        "Excellent work! Correct output and clean code.",
        "Good job. Your solution is correct and easy to follow.",
        "Correct. Next time, add a short comment for each step.",
        "Well done! Nice, descriptive variable names.",
        "Very good. Output matches the sample exactly.",
    ),
    "structure": (
        "Your output is correct, but the activity requires a specific structure. Please review the requirements.",
        "Correct result, but you did not use the required construct. Partial credit.",
    ),
    "wrong": (
        "Almost there. Compare your output with the sample line by line.",
        "Your logic is close, but the result does not match. Trace your program with the given values.",
        "Check your formatting and computations against the expected output.",
    ),
    "error": (
        "Your program does not run because of an error. Use Run before submitting.",
        "Error on submission. Read the error message carefully and test again.",
    ),
}
