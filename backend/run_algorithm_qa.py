"""
Algorithm QA for the thesis: AST structure detection and Jaccard similarity.

Run from the backend folder with the project virtualenv:

    venv\\Scripts\\python.exe run_algorithm_qa.py

The script imports the production functions directly (no database, no
network), runs two test suites and writes algorithm_qa_results.md next to
this file. It exits with code 1 if any algorithm check fails.

Part 1 checks evaluate_ast_details() against hand-written structure counts,
and its pass/fail verdicts against the strictness modes as the instructor UI
describes them.

Part 2 measures calculate_jaccard_score(a, b, shingle_size=3) on five base
programs and seven kinds of variant.

The Part 2 test programs are run here once (with exec) only to confirm that
each "same task" variant prints the same output as its base program. They are
fixed programs written in this file, never student code.
"""

from __future__ import annotations

import builtins
import contextlib
import io
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from statistics import mean
from textwrap import dedent

from app.services.ast_evaluator import evaluate_ast_details
from app.services.ast_fingerprinter import generate_ast_fingerprint
from app.services.jaccard import calculate_jaccard_details, calculate_jaccard_score

BACKEND_DIR = Path(__file__).resolve().parent
REPORT_PATH = BACKEND_DIR / "algorithm_qa_results.md"

# The shingle size evaluation_service.py uses in production.
SHINGLE_SIZE = 3


def src(text: str) -> str:
    """Remove the indentation used to keep the test programs readable here."""
    return dedent(text).strip("\n") + "\n"


def percent(matched: int, total: int) -> str:
    if total == 0:
        return "n/a"
    text = f"{100 * matched / total:.1f}".rstrip("0").rstrip(".")
    return f"{text}%"


def ratio(matched: int, total: int) -> str:
    return f"{matched} of {total} checks matched ({percent(matched, total)})"


@dataclass
class Tally:
    matched: int = 0
    total: int = 0

    def add(self, ok: bool) -> None:
        self.total += 1
        self.matched += int(ok)

    @property
    def failed(self) -> int:
        return self.total - self.matched

    def __add__(self, other: "Tally") -> "Tally":
        return Tally(self.matched + other.matched, self.total + other.total)

    def __str__(self) -> str:
        return ratio(self.matched, self.total)


# ---------------------------------------------------------------------------
# Part 1: AST test cases
# ---------------------------------------------------------------------------

# Report label -> rule id stored on a task (backend/app/services/ast_evaluator.py).
AST_RULES = {
    "for loop": "require_for_loop",
    "while loop": "require_while_loop",
    "if statement": "require_if_statement",
    "function definition": "require_function_def",
    "list comprehension": "require_list_comprehension",
    "return statement": "require_return_statement",
    "print call": "require_print_call",
}

SHORT_HEADERS = {
    "for loop": "for",
    "while loop": "while",
    "if statement": "if",
    "function definition": "def",
    "list comprehension": "listcomp",
    "return statement": "return",
    "print call": "print()",
}

STRICTNESS_MODES = ("strict", "moderate", "lax")

# Every program is checked against a required count of 1 and of 2. With 1,
# strict and moderate differ whenever a structure appears two or more times.
# With 2, moderate and lax differ whenever it appears exactly once.
REQUIRED_COUNTS = (1, 2)


def expect(**counts: int) -> dict[str, int]:
    """Expected count for every rule. Rules not named are expected to be 0."""
    expected = {label: 0 for label in AST_RULES}
    for key, value in counts.items():
        label = key.replace("_", " ")
        if label not in expected:
            raise KeyError(f"Unknown rule label: {key}")
        expected[label] = value
    return expected


def rules_for(required: int) -> dict[str, dict[str, object]]:
    """Rules in the shape ActivityEditor.jsx saves on a task."""
    return {
        rule_id: {"required": True, "min_count": required}
        for rule_id in AST_RULES.values()
    }


def spec_verdict(count: int, required: int, mode: str) -> bool:
    """
    Pass or fail as the instructor UI describes each mode
    (frontend/src/utils/astRules.js, AST_STRICTNESS_LEVELS):
      strict   - "must appear exactly as many times as you set"
      moderate - "must appear at least as many times as you set"
      lax      - "passes once it appears at least once, whatever count you set"
    """
    if mode == "strict":
        return count == required
    if mode == "moderate":
        return count >= required
    return count >= 1


@dataclass(frozen=True)
class AstCase:
    case_id: str
    title: str
    code: str
    expected: dict[str, int] | None = None
    syntax_error_line: int | None = None


AST_CASES: list[AstCase] = [
    AstCase(
        "A01",
        "Single for loop",
        src("""
            for i in range(5):
                print(i)
        """),
        expect(for_loop=1, print_call=1),
    ),
    AstCase(
        "A02",
        "if / elif / else: elif counts as a second if statement",
        src("""
            score = 85
            if score >= 90:
                print("A")
            elif score >= 80:
                print("B")
            else:
                print("C")
        """),
        expect(if_statement=2, print_call=3),
    ),
    AstCase(
        "A03",
        "if with two elif clauses",
        src("""
            n = 0
            if n > 0:
                print("positive")
            elif n < 0:
                print("negative")
            elif n == 0:
                print("zero")
        """),
        expect(if_statement=3, print_call=3),
    ),
    AstCase(
        "A04",
        "Conditional expression only (not an if statement)",
        src("""
            a = True
            x = 1 if a else 2
            print(x)
        """),
        expect(print_call=1),
    ),
    AstCase(
        "A05",
        "Conditional expression next to a real if statement",
        src("""
            age = 20
            label = "adult" if age >= 18 else "minor"
            if label == "adult":
                print("Welcome")
        """),
        expect(if_statement=1, print_call=1),
    ),
    AstCase(
        "A06",
        "Nested for loops",
        src("""
            for i in range(3):
                for j in range(3):
                    print(i * j)
        """),
        expect(for_loop=2, print_call=1),
    ),
    AstCase(
        "A07",
        "for loop inside a while loop",
        src("""
            i = 0
            while i < 3:
                for j in range(i):
                    print(j)
                i += 1
        """),
        expect(for_loop=1, while_loop=1, print_call=1),
    ),
    AstCase(
        "A08",
        "Loop inside a function",
        src("""
            def total(numbers):
                result = 0
                for n in numbers:
                    result += n
                return result

            print(total([1, 2, 3]))
        """),
        expect(for_loop=1, function_definition=1, return_statement=1, print_call=1),
    ),
    AstCase(
        "A09",
        "List comprehension (not a for loop)",
        src("""
            squares = [x * x for x in range(10)]
            print(squares)
        """),
        expect(list_comprehension=1, print_call=1),
    ),
    AstCase(
        "A10",
        "List comprehension with an if filter (not a for loop, not an if statement)",
        src("""
            evens = [x for x in range(20) if x % 2 == 0]
            print(evens)
        """),
        expect(list_comprehension=1, print_call=1),
    ),
    AstCase(
        "A11",
        "Nested list comprehension",
        src("""
            grid = [[r * c for c in range(3)] for r in range(3)]
            print(grid)
        """),
        expect(list_comprehension=2, print_call=1),
    ),
    AstCase(
        "A12",
        "Generator expression, set and dict comprehensions (none are for loops or list comprehensions)",
        src("""
            data = [1, 2, 3, 4]
            total = sum(x for x in data)
            unique = {x % 2 for x in data}
            lookup = {x: x * x for x in data}
            print(total, unique, lookup)
        """),
        expect(print_call=1),
    ),
    AstCase(
        "A13",
        "for loop that contains a list comprehension",
        src("""
            rows = [[1, 2], [3, 4]]
            for row in rows:
                doubled = [v * 2 for v in row]
                print(doubled)
        """),
        expect(for_loop=1, list_comprehension=1, print_call=1),
    ),
    AstCase(
        "A14",
        "while True with if and break",
        src("""
            count = 0
            while True:
                count += 1
                if count == 5:
                    break
            print(count)
        """),
        expect(while_loop=1, if_statement=1, print_call=1),
    ),
    AstCase(
        "A15",
        "for-else (the else does not add a loop)",
        src("""
            for n in range(2, 10):
                if n % 7 == 0:
                    print("found", n)
                    break
            else:
                print("none")
        """),
        expect(for_loop=1, if_statement=1, print_call=2),
    ),
    AstCase(
        "A16",
        "if nested inside else (same tree as elif)",
        src("""
            x = 5
            if x > 10:
                print("big")
            else:
                if x > 3:
                    print("medium")
                else:
                    print("small")
        """),
        expect(if_statement=2, print_call=3),
    ),
    AstCase(
        "A17",
        "Nested function definitions",
        src("""
            def outer():
                def inner():
                    return 1
                return inner()

            print(outer())
        """),
        expect(function_definition=2, return_statement=2, print_call=1),
    ),
    AstCase(
        "A18",
        "Lambda (not a function definition, no return statement)",
        src("""
            square = lambda n: n * n
            print(square(4))
        """),
        expect(print_call=1),
    ),
    AstCase(
        "A19",
        "Methods inside a class",
        src("""
            class Counter:
                def __init__(self):
                    self.value = 0

                def increment(self):
                    self.value += 1
                    return self.value

            c = Counter()
            print(c.increment())
        """),
        expect(function_definition=2, return_statement=1, print_call=1),
    ),
    AstCase(
        "A20",
        "async def and async for",
        src("""
            async def read_all(stream):
                items = []
                async for item in stream:
                    items.append(item)
                return items
        """),
        expect(for_loop=1, function_definition=1, return_statement=1),
    ),
    AstCase(
        "A21",
        "Keywords inside a comment and a string",
        src("""
            # for i in range(10): if i: print(i)
            message = "for each item, if needed, def ine and return"
            print(message)
        """),
        expect(print_call=1),
    ),
    AstCase(
        "A22",
        "Keywords inside a docstring",
        src('''
            def greet(name):
                """Use a for loop and an if statement here, then return."""
                return "Hello " + name

            print(greet("Ana"))
        '''),
        expect(function_definition=1, return_statement=1, print_call=1),
    ),
    AstCase(
        "A23",
        "Recursive function with two return statements",
        src("""
            def factorial(n):
                if n <= 1:
                    return 1
                return n * factorial(n - 1)

            print(factorial(5))
        """),
        expect(if_statement=1, function_definition=1, return_statement=2, print_call=1),
    ),
    AstCase(
        "A24",
        "match statement with a case guard (the guard is not an if statement)",
        src("""
            value = 7
            match value:
                case 0:
                    print("zero")
                case n if n > 0:
                    print("positive")
                case _:
                    print("negative")
        """),
        expect(print_call=3),
    ),
    AstCase(
        "A25",
        "try/except followed by an if statement",
        src("""
            try:
                number = int("42")
            except ValueError:
                number = 0
            if number:
                print(number)
        """),
        expect(if_statement=1, print_call=1),
    ),
    AstCase(
        "A26",
        "Several statements on one line (counts structures, not lines)",
        src("""
            for i in range(3): print(i); print(i * 2)
            print("done")
        """),
        expect(for_loop=1, print_call=3),
    ),
    AstCase(
        "A27",
        "while loop only (not counted as a for loop)",
        src("""
            n = 10
            while n > 0:
                n -= 3
            print(n)
        """),
        expect(while_loop=1, print_call=1),
    ),
    AstCase(
        "A28",
        "while loop with an assignment expression inside an if",
        src("""
            values = [3, 1, 4, 1, 5]
            index = 0
            while index < len(values):
                if (v := values[index]) > 2:
                    print(v)
                index += 1
        """),
        expect(while_loop=1, if_statement=1, print_call=1),
    ),
    AstCase(
        "A29",
        "Combined: nested loops in a function, elif, conditional expression in a comprehension",
        src("""
            def classify(matrix):
                labels = []
                for row in matrix:
                    for value in row:
                        if value > 0:
                            labels.append("pos")
                        elif value < 0:
                            labels.append("neg")
                        else:
                            labels.append("zero")
                flags = [1 if l == "pos" else 0 for l in labels]
                return labels, flags

            result = classify([[1, -1], [0, 2]])
            print(result)
        """),
        expect(
            for_loop=2,
            if_statement=2,
            function_definition=1,
            list_comprehension=1,
            return_statement=1,
            print_call=1,
        ),
    ),
    AstCase(
        "A30",
        "Decorator with a nested function, and an early return inside a loop",
        src("""
            def log(fn):
                def wrapper(*args):
                    print("calling")
                    return fn(*args)
                return wrapper

            @log
            def find_first_even(items):
                for item in items:
                    if item % 2 == 0:
                        return item
                return None

            print(find_first_even([1, 3, 4]))
        """),
        expect(
            for_loop=1,
            if_statement=1,
            function_definition=3,
            return_statement=4,
            print_call=2,
        ),
    ),
    AstCase(
        "A31",
        "Syntax error: missing colon after for",
        src("""
            for i in range(3)
                print(i)
        """),
        syntax_error_line=1,
    ),
    AstCase(
        "A32",
        "Syntax error: function body not indented",
        src("""
            def broken():
            print("no indent")
        """),
        syntax_error_line=2,
    ),
    AstCase(
        "A33",
        "Syntax error: 'else if' instead of 'elif'",
        src("""
            x = 3
            if x > 5:
                print("big")
            else if x > 1:
                print("medium")
        """),
        syntax_error_line=4,
    ),
]


@dataclass
class AstSuiteResult:
    count_by_rule: dict[str, Tally]
    verdict_by_rule: dict[str, Tally]
    verdict_by_mode: dict[str, Tally]
    verdict_by_rule_mode: dict[tuple[str, str], Tally]
    syntax: Tally
    count_rows: list[tuple[AstCase, dict[str, tuple[int, set]]]]
    syntax_rows: list[dict]
    failures: list[str]
    combinations: int
    combinations_where_modes_differ: int

    @property
    def counts(self) -> Tally:
        return sum(self.count_by_rule.values(), Tally())

    @property
    def verdicts(self) -> Tally:
        return sum(self.verdict_by_mode.values(), Tally())

    @property
    def overall(self) -> Tally:
        return self.counts + self.verdicts + self.syntax


def run_ast_suite() -> AstSuiteResult:
    count_by_rule = {label: Tally() for label in AST_RULES}
    verdict_by_rule = {label: Tally() for label in AST_RULES}
    verdict_by_mode = {mode: Tally() for mode in STRICTNESS_MODES}
    verdict_by_rule_mode = {
        (label, mode): Tally() for label in AST_RULES for mode in STRICTNESS_MODES
    }
    syntax = Tally()
    count_rows = []
    syntax_rows = []
    failures: list[str] = []
    combinations = 0
    combinations_where_modes_differ = 0

    for case in AST_CASES:
        if case.syntax_error_line is not None:
            row = {"case": case, "modes": {}, "line": None, "message": None}
            for mode in STRICTNESS_MODES:
                result = evaluate_ast_details(case.code, rules_for(1), strictness_level=mode)
                error = result["syntax_error"]
                ok = error is not None and result["passed"] is False and result["findings"] == []
                syntax.add(ok)
                row["modes"][mode] = ok
                if error:
                    row["line"] = error["line"]
                    row["message"] = error["message"]
                if not ok:
                    failures.append(
                        f"{case.case_id} ({mode}): syntax error not reported as a failed "
                        f"evaluation with no findings."
                    )
            row["line_ok"] = row["line"] == case.syntax_error_line
            syntax.add(row["line_ok"])
            if not row["line_ok"]:
                failures.append(
                    f"{case.case_id}: syntax error reported on line {row['line']}, "
                    f"expected line {case.syntax_error_line}."
                )
            syntax_rows.append(row)
            continue

        detected_seen: dict[str, set] = {label: set() for label in AST_RULES}
        expected_verdicts: dict[tuple[str, int], set[bool]] = {}

        for required in REQUIRED_COUNTS:
            for mode in STRICTNESS_MODES:
                result = evaluate_ast_details(case.code, rules_for(required), strictness_level=mode)
                findings = {finding["rule"]: finding for finding in result["findings"]}

                for label, rule_id in AST_RULES.items():
                    finding = findings.get(rule_id)
                    want = spec_verdict(case.expected[label], required, mode)
                    got = finding["passed"] if finding else None
                    detected_seen[label].add(finding["detected_count"] if finding else None)
                    expected_verdicts.setdefault((label, required), set()).add(want)

                    ok = got is want
                    verdict_by_rule[label].add(ok)
                    verdict_by_mode[mode].add(ok)
                    verdict_by_rule_mode[(label, mode)].add(ok)
                    if not ok:
                        failures.append(
                            f"{case.case_id} {label}, {mode}, required {required}: "
                            f"expected {'pass' if want else 'fail'}, got "
                            f"{'pass' if got else 'fail' if got is False else 'no finding'}."
                        )

        for wants in expected_verdicts.values():
            combinations += 1
            combinations_where_modes_differ += int(len(wants) > 1)

        cells = {}
        for label in AST_RULES:
            expected_count = case.expected[label]
            seen = detected_seen[label]
            # One check per program and rule: every one of the six runs
            # (2 required counts x 3 modes) must report the hand count.
            ok = seen == {expected_count}
            count_by_rule[label].add(ok)
            cells[label] = (expected_count, seen)
            if not ok:
                failures.append(
                    f"{case.case_id} {label}: expected {expected_count}, "
                    f"detected {sorted(seen, key=str)}."
                )
        count_rows.append((case, cells))

    return AstSuiteResult(
        count_by_rule=count_by_rule,
        verdict_by_rule=verdict_by_rule,
        verdict_by_mode=verdict_by_mode,
        verdict_by_rule_mode=verdict_by_rule_mode,
        syntax=syntax,
        count_rows=count_rows,
        syntax_rows=syntax_rows,
        failures=failures,
        combinations=combinations,
        combinations_where_modes_differ=combinations_where_modes_differ,
    )


# ---------------------------------------------------------------------------
# Part 2: Jaccard test programs
# ---------------------------------------------------------------------------

JACCARD_CATEGORIES = (
    ("exact", "Exact copy"),
    ("renamed", "Variables renamed"),
    ("cosmetic", "Comments, spacing, literal values changed"),
    ("reordered", "Statements reordered"),
    ("while_loop", "for loop rewritten as while loop"),
    ("independent", "Independent solution, same task"),
    ("different_task", "Program for a different task"),
)
CATEGORY_LABELS = dict(JACCARD_CATEGORIES)

# Supplementary measurement only: the same comparisons at other shingle sizes,
# to show why the order of statements matters at size 3.
SUPPLEMENTARY_SHINGLE_SIZES = (1, 2, 3, 4)

# Lexical changes: the structural fingerprint must not change at all.
MUST_BE_100 = ("exact", "renamed", "cosmetic")

# Variants that must print the same output as the base (test data check).
SAME_OUTPUT = ("exact", "renamed", "reordered", "while_loop", "independent")


@dataclass(frozen=True)
class JaccardTask:
    task_id: str
    title: str
    base: str
    variants: dict[str, str]
    reorder_note: str
    independent_note: str
    different_note: str
    sample_inputs: tuple[str, ...] = field(default=("",))


def jaccard_task(task_id, title, base, *, reorder_note, independent_note,
                 different_note, sample_inputs, **variants) -> JaccardTask:
    return JaccardTask(
        task_id=task_id,
        title=title,
        base=base,
        variants={"exact": base, **variants},
        reorder_note=reorder_note,
        independent_note=independent_note,
        different_note=different_note,
        sample_inputs=sample_inputs,
    )


JACCARD_TASKS: list[JaccardTask] = [
    jaccard_task(
        "J1",
        "Sum of even numbers from 1 to n",
        src("""
            n = int(input("Enter n: "))
            total = 0
            for number in range(1, n + 1):
                if number % 2 == 0:
                    total += number
            print("Sum of even numbers:", total)
        """),
        renamed=src("""
            limit = int(input("Enter n: "))
            running_sum = 0
            for k in range(1, limit + 1):
                if k % 2 == 0:
                    running_sum += k
            print("Sum of even numbers:", running_sum)
        """),
        cosmetic=src("""
            # Read the upper limit from the user
            n=int(input( "Upper limit? " ))
            total=0      # running sum


            for number in range(0,  n+1):   # start at zero instead of one
                if number%2==0 :
                    total+=number   # add the even number
            print( "Total of the even numbers =" , total )
        """),
        reordered=src("""
            total = 0
            n = int(input("Enter n: "))
            for number in range(1, n + 1):
                if number % 2 == 0:
                    total += number
            print("Sum of even numbers:", total)
        """),
        while_loop=src("""
            n = int(input("Enter n: "))
            total = 0
            number = 1
            while number <= n:
                if number % 2 == 0:
                    total += number
                number += 1
            print("Sum of even numbers:", total)
        """),
        independent=src("""
            n = int(input("Enter n: "))
            print("Sum of even numbers:", sum(range(2, n + 1, 2)))
        """),
        different_task=src("""
            celsius = float(input("Temperature in Celsius: "))
            fahrenheit = celsius * 9 / 5 + 32
            print("Temperature in Fahrenheit:", fahrenheit)
        """),
        reorder_note="`total = 0` moved above the input line.",
        independent_note="`sum(range(2, n + 1, 2))` with no loop.",
        different_note="Celsius to Fahrenheit conversion.",
        sample_inputs=("10", "7"),
    ),
    jaccard_task(
        "J2",
        "Factorial of n",
        src("""
            n = int(input("Enter a number: "))
            result = 1
            for i in range(1, n + 1):
                result *= i
            print("Factorial:", result)
        """),
        renamed=src("""
            num = int(input("Enter a number: "))
            product = 1
            for factor in range(1, num + 1):
                product *= factor
            print("Factorial:", product)
        """),
        cosmetic=src("""
            # Factorial of a whole number
            n = int( input("Number please: ") )

            result = 1   # the empty product
            for i in range(1,n+1):
                result*=i

            print("n! =",result)
        """),
        reordered=src("""
            result = 1
            n = int(input("Enter a number: "))
            for i in range(1, n + 1):
                result *= i
            print("Factorial:", result)
        """),
        while_loop=src("""
            n = int(input("Enter a number: "))
            result = 1
            i = 1
            while i <= n:
                result *= i
                i += 1
            print("Factorial:", result)
        """),
        independent=src("""
            def factorial(n):
                if n <= 1:
                    return 1
                return n * factorial(n - 1)


            print("Factorial:", factorial(int(input("Enter a number: "))))
        """),
        different_task=src("""
            sentence = input("Type a sentence: ")
            words = sentence.split()
            print("Number of words:", len(words))
        """),
        reorder_note="`result = 1` moved above the input line.",
        independent_note="Recursive function instead of a loop.",
        different_note="Word count of a sentence.",
        sample_inputs=("5", "0"),
    ),
    jaccard_task(
        "J3",
        "Count the vowels in a text",
        src("""
            text = input("Enter text: ")
            count = 0
            for ch in text.lower():
                if ch in "aeiou":
                    count += 1
            print("Vowels:", count)
        """),
        renamed=src("""
            sentence = input("Enter text: ")
            vowel_total = 0
            for letter in sentence.lower():
                if letter in "aeiou":
                    vowel_total += 1
            print("Vowels:", vowel_total)
        """),
        cosmetic=src("""
            text = input( "Type something: " )   # read one line

            count = 0
            # look at every character
            for ch in text.lower() :
                if ch in "uoiea" :
                    count += 1
            print( "Number of vowels ->" , count )
        """),
        reordered=src("""
            count = 0
            text = input("Enter text: ")
            for ch in text.lower():
                if ch in "aeiou":
                    count += 1
            print("Vowels:", count)
        """),
        while_loop=src("""
            text = input("Enter text: ")
            count = 0
            index = 0
            while index < len(text):
                if text[index].lower() in "aeiou":
                    count += 1
                index += 1
            print("Vowels:", count)
        """),
        independent=src("""
            text = input("Enter text: ")
            vowels = [ch for ch in text.lower() if ch in "aeiou"]
            print("Vowels:", len(vowels))
        """),
        different_task=src("""
            width = float(input("Width: "))
            height = float(input("Height: "))
            area = width * height
            print("Area of the rectangle:", area)
        """),
        reorder_note="`count = 0` moved above the input line.",
        independent_note="List comprehension with a filter, then `len()`.",
        different_note="Area of a rectangle.",
        sample_inputs=("Programming in Python", "rhythm"),
    ),
    jaccard_task(
        "J4",
        "Largest number in a list",
        src("""
            numbers = [12, 45, 7, 23, 56, 89, 34]
            size = len(numbers)
            largest = numbers[0]
            for value in numbers:
                if value > largest:
                    largest = value
            print("Largest of", size, "numbers:", largest)
        """),
        renamed=src("""
            data = [12, 45, 7, 23, 56, 89, 34]
            length = len(data)
            biggest = data[0]
            for item in data:
                if item > biggest:
                    biggest = item
            print("Largest of", length, "numbers:", biggest)
        """),
        cosmetic=src("""
            # a fixed list of test scores
            numbers = [3, 99, 14, 2, 61, 8, 40]
            size = len( numbers )
            largest = numbers[ 0 ]

            for value in numbers :
                if value>largest :   # found a bigger one
                    largest = value
            print( "Maximum among" , size , "values:" , largest )
        """),
        reordered=src("""
            numbers = [12, 45, 7, 23, 56, 89, 34]
            largest = numbers[0]
            for value in numbers:
                if value > largest:
                    largest = value
            size = len(numbers)
            print("Largest of", size, "numbers:", largest)
        """),
        while_loop=src("""
            numbers = [12, 45, 7, 23, 56, 89, 34]
            size = len(numbers)
            largest = numbers[0]
            index = 0
            while index < size:
                if numbers[index] > largest:
                    largest = numbers[index]
                index += 1
            print("Largest of", size, "numbers:", largest)
        """),
        independent=src("""
            numbers = [12, 45, 7, 23, 56, 89, 34]
            print("Largest of", len(numbers), "numbers:", max(numbers))
        """),
        different_task=src("""
            year = int(input("Year: "))
            if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0:
                print(year, "is a leap year")
            else:
                print(year, "is not a leap year")
        """),
        reorder_note="`size = len(numbers)` moved from before the loop to after it.",
        independent_note="Built-in `max()` with no loop.",
        different_note="Leap year check.",
        sample_inputs=("",),
    ),
    jaccard_task(
        "J5",
        "Check whether n is prime",
        src("""
            is_prime = True
            n = int(input("Enter a number: "))
            if n < 2:
                is_prime = False
            for divisor in range(2, n):
                if n % divisor == 0:
                    is_prime = False
                    break
            print(n, "is prime" if is_prime else "is not prime")
        """),
        renamed=src("""
            prime_flag = True
            value = int(input("Enter a number: "))
            if value < 2:
                prime_flag = False
            for d in range(2, value):
                if value % d == 0:
                    prime_flag = False
                    break
            print(value, "is prime" if prime_flag else "is not prime")
        """),
        cosmetic=src("""
            is_prime = True   # assume prime until proven otherwise
            n = int(input("Number to test: "))

            if n < 2 :
                is_prime = False
            # try every possible divisor
            for divisor in range( 2 , n ):
                if n%divisor==0:
                    is_prime = False
                    break
            print(n, "-> prime" if is_prime else "-> not prime")
        """),
        reordered=src("""
            is_prime = True
            n = int(input("Enter a number: "))
            for divisor in range(2, n):
                if n % divisor == 0:
                    is_prime = False
                    break
            if n < 2:
                is_prime = False
            print(n, "is prime" if is_prime else "is not prime")
        """),
        while_loop=src("""
            is_prime = True
            n = int(input("Enter a number: "))
            if n < 2:
                is_prime = False
            divisor = 2
            while divisor < n:
                if n % divisor == 0:
                    is_prime = False
                    break
                divisor += 1
            print(n, "is prime" if is_prime else "is not prime")
        """),
        independent=src("""
            def is_prime(n):
                if n < 2:
                    return False
                return all(n % d != 0 for d in range(2, int(n ** 0.5) + 1))


            n = int(input("Enter a number: "))
            print(n, "is prime" if is_prime(n) else "is not prime")
        """),
        different_task=src("""
            number = int(input("Number: "))
            for i in range(1, 11):
                print(number, "x", i, "=", number * i)
        """),
        reorder_note="The `if n < 2` block moved from before the loop to after it.",
        independent_note="Function with `all()` over divisors up to the square root.",
        different_note="Multiplication table (uses the same constructs: input, for, range, print).",
        sample_inputs=("29", "15", "1"),
    ),
]

# Extra probes that document how the fingerprint behaves. They are measured
# and reported, not scored as pass/fail.
JACCARD_PROBES = [
    (
        "Second student, working alone, writes the standard loop for J1",
        JACCARD_TASKS[0].base,
        src("""
            upper = int(input("Upper bound: "))
            even_sum = 0
            for value in range(2, upper + 1):
                if value % 2 == 0:
                    even_sum += value
            print("The sum is", even_sum)
        """),
        "The usual way to write the task has one shape. An honest student who "
        "picks the same approach produces the same structure as a copy.",
    ),
    (
        "Docstring added to the factorial program",
        JACCARD_TASKS[1].base,
        '"""Compute the factorial of a number."""\n' + JACCARD_TASKS[1].base,
        "A docstring is a string statement in the syntax tree, not a comment, "
        "so it adds one node to the fingerprint.",
    ),
    (
        "Different built-in function, same shape (`sum` vs `len`)",
        src("""
            values = [4, 8, 15, 16, 23, 42]
            result = sum(values)
            print("Result:", result)
        """),
        src("""
            values = [4, 8, 15, 16, 23, 42]
            result = len(values)
            print("Result:", result)
        """),
        "Function names are ignored like variable names, so two programs that "
        "call different functions in the same shape look identical.",
    ),
    (
        "One operator changed in the factorial program (`*=` to `+=`)",
        JACCARD_TASKS[1].base,
        JACCARD_TASKS[1].base.replace("result *= i", "result += i"),
        "Operators are kept in the fingerprint, so changing one operator "
        "changes the shingles around it.",
    ),
]


def run_program(code: str, input_value: str) -> str:
    """Run one fixed test program with input() answered by input_value."""
    buffer = io.StringIO()
    namespace = {
        "__name__": "__qa_program__",
        "__builtins__": builtins,
        "input": lambda prompt="": input_value,
    }
    with contextlib.redirect_stdout(buffer):
        exec(compile(code, "<qa-program>", "exec"), namespace)
    return buffer.getvalue()


@dataclass
class JaccardSuiteResult:
    scores: dict[tuple[str, str], float]
    details: dict[tuple[str, str], dict]
    lexical: Tally
    symmetry: Tally
    parsed: Tally
    same_output: Tally
    probes: list[tuple[str, float, dict, str]]
    size_means: dict[tuple[str, int], float]
    failures: list[str]
    data_failures: list[str]

    @property
    def overall(self) -> Tally:
        return self.lexical + self.symmetry


def run_jaccard_suite() -> JaccardSuiteResult:
    scores: dict[tuple[str, str], float] = {}
    details: dict[tuple[str, str], dict] = {}
    lexical = Tally()
    symmetry = Tally()
    parsed = Tally()
    same_output = Tally()
    failures: list[str] = []
    data_failures: list[str] = []

    for task in JACCARD_TASKS:
        # Test data check 1: every program parses, so the score comes from the
        # AST fingerprint and not from the token fallback in jaccard.py.
        programs = {"base": task.base, **task.variants}
        for name, code in programs.items():
            if name == "exact":
                continue
            try:
                generate_ast_fingerprint(code)
                parsed.add(True)
            except SyntaxError as error:
                parsed.add(False)
                data_failures.append(f"{task.task_id} {name}: does not parse ({error.msg}).")

        # Test data check 2: same-task variants print the same output.
        for category in SAME_OUTPUT:
            for value in task.sample_inputs:
                try:
                    ok = run_program(task.base, value) == run_program(task.variants[category], value)
                except Exception as error:  # report, do not stop the suite
                    ok = False
                    data_failures.append(f"{task.task_id} {category}: raised {error!r}.")
                same_output.add(ok)
                if not ok:
                    data_failures.append(
                        f"{task.task_id} {category}: output differs from the base for input {value!r}."
                    )

        for category, _ in JACCARD_CATEGORIES:
            variant = task.variants[category]
            score = calculate_jaccard_score(task.base, variant, shingle_size=SHINGLE_SIZE)
            reverse = calculate_jaccard_score(variant, task.base, shingle_size=SHINGLE_SIZE)
            scores[(task.task_id, category)] = score
            details[(task.task_id, category)] = calculate_jaccard_details(
                task.base, variant, shingle_size=SHINGLE_SIZE
            )

            symmetry.add(score == reverse)
            if score != reverse:
                failures.append(
                    f"{task.task_id} {category}: score {score} one way, {reverse} the other way."
                )

            if category in MUST_BE_100:
                ok = score == 100.0
                lexical.add(ok)
                if not ok:
                    failures.append(
                        f"{task.task_id} {CATEGORY_LABELS[category]}: expected 100%, got {score}%."
                    )

    probes = []
    for title, a, b, note in JACCARD_PROBES:
        probe_score = calculate_jaccard_score(a, b, shingle_size=SHINGLE_SIZE)
        probes.append(
            (title, probe_score, calculate_jaccard_details(a, b, shingle_size=SHINGLE_SIZE), note)
        )

    size_means = {
        (category, size): mean(
            calculate_jaccard_score(task.base, task.variants[category], shingle_size=size)
            for task in JACCARD_TASKS
        )
        for category, _ in JACCARD_CATEGORIES
        for size in SUPPLEMENTARY_SHINGLE_SIZES
    }

    return JaccardSuiteResult(
        scores=scores,
        details=details,
        lexical=lexical,
        symmetry=symmetry,
        parsed=parsed,
        same_output=same_output,
        probes=probes,
        size_means=size_means,
        failures=failures,
        data_failures=data_failures,
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def environment_lines() -> list[str]:
    def git(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], cwd=BACKEND_DIR, capture_output=True, text=True, check=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return ""

    commit = git("rev-parse", "--short", "HEAD") or "unknown"
    changed = git(
        "status",
        "--porcelain",
        "--",
        "app/services/ast_evaluator.py",
        "app/services/ast_fingerprinter.py",
        "app/services/ast_safety.py",
        "app/services/jaccard.py",
    )
    # Porcelain lines are "XY path"; split instead of slicing (stdout was stripped).
    changed_files = [line.split(maxsplit=1)[1] for line in changed.splitlines() if line.strip()]
    tree_state = (
        "plus uncommitted changes to " + ", ".join(f"`{path}`" for path in changed_files)
        if changed_files
        else "no uncommitted changes in the tested service files"
    )
    return [
        f"- Generated: {date.today().isoformat()}",
        f"- Python: {platform.python_version()} ({platform.system()})",
        f"- Code under test: commit `{commit}` {tree_state}",
        "- Functions: `evaluate_ast_details` (`app/services/ast_evaluator.py`), "
        f"`calculate_jaccard_score(a, b, shingle_size={SHINGLE_SIZE})` (`app/services/jaccard.py`)",
        "- Re-run: `venv\\Scripts\\python.exe run_algorithm_qa.py` from the `backend` folder",
    ]


def fmt_score(value: float) -> str:
    return f"{value:.2f}%"


def detected_text(seen: set) -> str:
    values = sorted(seen, key=str)
    if len(values) == 1:
        return "none" if values[0] is None else str(values[0])
    return "/".join("none" if v is None else str(v) for v in values)


def code_block(code: str) -> list[str]:
    return ["```python", code.rstrip("\n"), "```"]


def build_report(ast_result: AstSuiteResult, jaccard_result: JaccardSuiteResult) -> str:
    lines: list[str] = []
    add = lines.append
    algorithm_total = ast_result.overall + jaccard_result.overall
    all_failures = ast_result.failures + jaccard_result.failures

    add("# Algorithm QA results: AST evaluation and Jaccard similarity")
    add("")
    add("Generated by `backend/run_algorithm_qa.py`. Every number below comes from running the "
        "production functions; nothing is typed in by hand.")
    add("")
    lines.extend(environment_lines())
    add("")

    # Summary ---------------------------------------------------------------
    add("## Summary")
    add("")
    add("| Suite | Result |")
    add("|---|---|")
    add(f"| Part 1: AST structure counts | {ast_result.counts} |")
    add(f"| Part 1: strict / moderate / lax verdicts | {ast_result.verdicts} |")
    add(f"| Part 1: syntax-error handling | {ast_result.syntax} |")
    add(f"| **Part 1 total** | **{ast_result.overall}** |")
    add(f"| Part 2: lexical changes score 100% | {jaccard_result.lexical} |")
    add(f"| Part 2: same score in both directions | {jaccard_result.symmetry} |")
    add(f"| **Part 2 total** | **{jaccard_result.overall}** |")
    add(f"| **All algorithm checks** | **{algorithm_total}** |")
    add("")
    if all_failures:
        add(f"**Result: {len(all_failures)} algorithm check(s) failed.** See *Failures* below.")
    else:
        add("**Result: every algorithm check passed.**")
    add("")
    add("Test data checks (these validate the test programs, not the algorithms): "
        f"Part 2 programs parse: {jaccard_result.parsed}; same-task variants print the same "
        f"output as their base: {jaccard_result.same_output}.")
    add("")
    if all_failures or jaccard_result.data_failures:
        add("### Failures")
        add("")
        for failure in all_failures:
            add(f"- {failure}")
        for failure in jaccard_result.data_failures:
            add(f"- Test data: {failure}")
        add("")

    # Part 1 ----------------------------------------------------------------
    add("## Part 1: AST evaluation (`evaluate_ast_details`)")
    add("")
    add("### How the checks work")
    add("")
    valid_cases = len(ast_result.count_rows)
    add(f"- {len(AST_CASES)} programs: {valid_cases} valid programs and "
        f"{len(ast_result.syntax_rows)} with a deliberate syntax error.")
    add(f"- Each valid program is checked for {len(AST_RULES)} rules. The expected count for every "
        "rule was written by hand from the Python language rules, not taken from the evaluator. "
        "A zero is a check too: it catches false positives.")
    add("- Rules are passed in the shape the activity editor saves: "
        "`{rule_id: {\"required\": True, \"min_count\": n}}`.")
    add(f"- Each valid program runs {len(REQUIRED_COUNTS) * len(STRICTNESS_MODES)} times: required "
        f"count {' and '.join(map(str, REQUIRED_COUNTS))}, under strict, moderate and lax.")
    add("- **Count check** (one per program and rule): all of those runs must report "
        "`detected_count` equal to the hand count.")
    add("- **Verdict check** (one per program, rule, required count and mode): the finding's "
        "`passed` value must match the mode's meaning as the instructor screen describes it "
        "(`frontend/src/utils/astRules.js`): strict = exactly the required count; moderate = at "
        "least the required count; lax = at least once, whatever count is set. The expected "
        "verdict is computed from the hand count, so a counting error would also show up here.")
    add(f"- In {ast_result.combinations_where_modes_differ} of {ast_result.combinations} "
        "(program, rule, required count) combinations the three modes should give different "
        "verdicts, so the test exercises the differences between the modes, not only cases where "
        "they agree.")
    add("- **Syntax-error check**: for each broken program and each mode, the result must report "
        "`syntax_error`, `passed = False` and no findings; and the reported line must match.")
    add("")

    add("### Structure counts per rule")
    add("")
    add("| Rule | Rule id | Result |")
    add("|---|---|---|")
    for label, rule_id in AST_RULES.items():
        add(f"| {label} | `{rule_id}` | {ast_result.count_by_rule[label]} |")
    add(f"| **All rules** | | **{ast_result.counts}** |")
    add("")

    add("### Strict / moderate / lax verdicts per rule")
    add("")
    add("| Rule | strict | moderate | lax | Result |")
    add("|---|---|---|---|---|")
    for label in AST_RULES:
        cells = [
            f"{t.matched}/{t.total}"
            for t in (ast_result.verdict_by_rule_mode[(label, mode)] for mode in STRICTNESS_MODES)
        ]
        add(f"| {label} | {' | '.join(cells)} | {ast_result.verdict_by_rule[label]} |")
    mode_cells = [
        f"{ast_result.verdict_by_mode[m].matched}/{ast_result.verdict_by_mode[m].total}"
        for m in STRICTNESS_MODES
    ]
    add(f"| **All rules** | {' | '.join(mode_cells)} | **{ast_result.verdicts}** |")
    add("")
    for mode in STRICTNESS_MODES:
        add(f"- {mode}: {ast_result.verdict_by_mode[mode]}")
    add("")

    add("### Expected vs detected counts per program")
    add("")
    add("Each cell shows the expected count. A mismatch shows **expected → detected**.")
    add("")
    header = " | ".join(SHORT_HEADERS[label] for label in AST_RULES)
    add(f"| ID | Program | {header} | Counts |")
    add("|---|---|" + "---|" * len(AST_RULES) + "---|")
    for case, cells in ast_result.count_rows:
        rendered = []
        all_ok = True
        for label in AST_RULES:
            expected_count, seen = cells[label]
            if seen == {expected_count}:
                rendered.append(str(expected_count))
            else:
                all_ok = False
                rendered.append(f"**{expected_count} → {detected_text(seen)}**")
        add(f"| {case.case_id} | {case.title} | {' | '.join(rendered)} | "
            f"{'match' if all_ok else '**mismatch**'} |")
    add("")

    add("### Syntax-error programs")
    add("")
    add("| ID | Program | Expected line | Reported line | Message | strict | moderate | lax |")
    add("|---|---|---|---|---|---|---|---|")
    for row in ast_result.syntax_rows:
        case = row["case"]
        modes = " | ".join("ok" if row["modes"][m] else "**wrong**" for m in STRICTNESS_MODES)
        line = str(row["line"]) if row["line_ok"] else f"**{row['line']}**"
        add(f"| {case.case_id} | {case.title} | {case.syntax_error_line} | {line} | "
            f"{row['message']} | {modes} |")
    add("")

    add("### Notes on the AST results")
    add("")
    if ast_result.failures:
        add("Some AST checks failed (see *Failures*). The notes below describe the intended "
            "behavior.")
        add("")
    add("- `elif` is stored by Python as an `if` nested in the `else` branch, so an "
        "`if / elif / else` chain counts as 2 if statements (A02), the same as an `if` written "
        "inside `else` (A16). In **strict** mode with a required count of 1, such a chain "
        "therefore fails. This is the intended counting, but instructors who use strict mode "
        "should set the count to the number of `if` plus `elif` branches.")
    add("- Conditional expressions (`x = 1 if a else 2`), comprehension filters "
        "(`[x for x in y if x > 0]`) and `match` case guards are different syntax nodes, so they "
        "are not counted as if statements (A04, A05, A10, A24, A29).")
    add("- The `for` inside a list, set or dict comprehension or a generator expression is not "
        "a for loop (A09 to A13, A29). `async for` and `async def` do count as a for loop and a "
        "function definition (A20).")
    add("- Keywords inside comments, strings and docstrings are not counted (A21, A22), because "
        "the evaluator reads the syntax tree, not the text.")
    add("- Lax mode ignores the required count once a structure appears at least once. With a "
        "required count of 2, a program with one for loop passes in lax and fails in moderate "
        "and strict, as the instructor screen says.")
    add("")

    # Part 2 ----------------------------------------------------------------
    add(f"## Part 2: Jaccard similarity (`calculate_jaccard_score`, shingle size {SHINGLE_SIZE})")
    add("")
    add("### How the score works")
    add("")
    add("Both programs are parsed into syntax trees and reduced to a sequence of node types and "
        "operators (`app/services/ast_fingerprinter.py`). Variable names, function names and "
        "literal values are dropped; comments and spacing never reach the tree. The sequence is "
        f"cut into overlapping runs of {SHINGLE_SIZE} node types (shingles), and the score is "
        "|shared shingles| / |all shingles| x 100. For example, `total = a + b` becomes "
        f"`{' '.join(generate_ast_fingerprint('total = a + b'))}`. The platform shows this score to the "
        "instructor as a review indicator; it has no automatic threshold and never flags "
        "plagiarism by itself.")
    add("")
    add("Each base program was compared with seven variants. Same-task variants were run with "
        "fixed inputs to confirm they print the same output as their base "
        f"({jaccard_result.same_output}).")
    add("")

    add("### Similarity by variant category")
    add("")
    task_headers = " | ".join(f"{t.task_id}" for t in JACCARD_TASKS)
    add(f"| Category | {task_headers} | Mean | Min | Max | Requirement |")
    add("|---|" + "---|" * len(JACCARD_TASKS) + "---|---|---|---|")
    category_stats: dict[str, tuple[float, float, float]] = {}
    for category, label in JACCARD_CATEGORIES:
        values = [jaccard_result.scores[(t.task_id, category)] for t in JACCARD_TASKS]
        stats = (mean(values), min(values), max(values))
        category_stats[category] = stats
        if category in MUST_BE_100:
            met = sum(v == 100.0 for v in values)
            requirement = f"Must be 100%: {ratio(met, len(values))}"
        else:
            requirement = "Measured"
        cells = " | ".join(fmt_score(v) for v in values)
        add(f"| {label} | {cells} | {fmt_score(stats[0])} | {fmt_score(stats[1])} | "
            f"{fmt_score(stats[2])} | {requirement} |")
    add("")
    add("Tasks: " + "; ".join(f"{t.task_id} = {t.title}" for t in JACCARD_TASKS) + ".")
    add("")

    add("### Shingle counts per comparison")
    add("")
    add("| Task | Category | Shared shingles | All shingles | Score | What changed |")
    add("|---|---|---|---|---|---|")
    for task in JACCARD_TASKS:
        notes = {
            "exact": "Nothing.",
            "renamed": "Every variable renamed.",
            "cosmetic": "Comments added, spacing changed, literal values changed.",
            "reordered": task.reorder_note,
            "while_loop": "The for loop rewritten as a while loop with a counter.",
            "independent": task.independent_note,
            "different_task": task.different_note,
        }
        for category, label in JACCARD_CATEGORIES:
            d = jaccard_result.details[(task.task_id, category)]
            add(f"| {task.task_id} | {label} | {d['intersection_count']} | {d['union_count']} | "
                f"{fmt_score(d['score'])} | {notes[category]} |")
    add("")

    # Interpretation (every number is computed above)
    def scores_of(category: str) -> dict[str, float]:
        return {t.task_id: jaccard_result.scores[(t.task_id, category)] for t in JACCARD_TASKS}

    reorder_mean, reorder_min, reorder_max = category_stats["reordered"]
    while_mean, while_min, while_max = category_stats["while_loop"]
    indep_mean, indep_min, indep_max = category_stats["independent"]
    diff_mean, diff_min, diff_max = category_stats["different_task"]
    while_scores = scores_of("while_loop")
    indep_scores = scores_of("independent")
    diff_scores = scores_of("different_task")
    top_indep = max(indep_scores, key=indep_scores.get)
    top_diff = max(diff_scores, key=diff_scores.get)
    low_while = min(while_scores, key=while_scores.get)
    size_means = jaccard_result.size_means

    j1 = JACCARD_TASKS[0]
    j1_reorder = jaccard_result.details[(j1.task_id, "reordered")]
    j1_length = len(generate_ast_fingerprint(j1.base))
    j1_changed = j1_reorder["union_count"] - j1_reorder["intersection_count"]
    same_approach_score = jaccard_result.probes[0][1]

    add("### Interpretation")
    add("")
    add(f"- **Lexical changes** (exact copy, renamed variables, comments, spacing, literal values): "
        f"{jaccard_result.lexical}. Renaming and reformatting a program does not lower the score.")
    add(f"- **Reordered statements** scored {fmt_score(reorder_min)} to {fmt_score(reorder_max)} "
        f"(mean {fmt_score(reorder_mean)}). The score compares runs of {SHINGLE_SIZE} consecutive "
        f"node types, so statement order matters. In {j1.task_id}, two lines swap places, but "
        f"the fingerprint is only {j1_length} node types long, so {j1_changed} of the "
        f"{j1_reorder['union_count']} distinct shingles across the two programs are not shared. With order ignored (shingle size "
        f"1) the same reordered copies average {fmt_score(size_means[('reordered', 1)])}.")
    add(f"- **for rewritten as while** scored {fmt_score(while_min)} to {fmt_score(while_max)} "
        f"(mean {fmt_score(while_mean)}). The loop node changes from `For` to `While`, and the "
        "counter adds an assignment and an update.")
    add(f"- **Independent solutions** scored {fmt_score(indep_min)} to {fmt_score(indep_max)} "
        f"(mean {fmt_score(indep_mean)}; highest {top_indep}). Each one takes a different "
        "approach (a built-in function, recursion or a comprehension), which gives a different "
        "syntax tree.")
    add(f"- **Different tasks** scored {fmt_score(diff_min)} to {fmt_score(diff_max)} "
        f"(mean {fmt_score(diff_mean)}; highest {top_diff}). At shingle size {SHINGLE_SIZE}, "
        "unrelated short programs share little structure.")
    if reorder_min > max(indep_max, diff_max):
        add(f"- Every reordered copy (lowest {fmt_score(reorder_min)}) still scored above every "
            f"independent solution (highest {fmt_score(indep_max)}) and every different-task "
            f"program (highest {fmt_score(diff_max)}), so a reordered copy still stands out when "
            "the instructor compares submissions.")
    if while_min <= indep_max:
        add(f"- The ranges for while rewrites and independent solutions overlap: the lowest "
            f"rewrite ({low_while}, {fmt_score(while_scores[low_while])}) scored no higher than "
            f"the highest independent solution ({top_indep}, {fmt_score(indep_scores[top_indep])}).")
    add("")

    add("### Shingle size comparison (supplementary)")
    add("")
    add("Mean score per category over the five tasks at other shingle sizes. Production uses "
        f"size {SHINGLE_SIZE}; the other columns only explain the trade-off.")
    add("")
    size_headers = " | ".join(
        f"size {s}{' (production)' if s == SHINGLE_SIZE else ''}" for s in SUPPLEMENTARY_SHINGLE_SIZES
    )
    add(f"| Category | {size_headers} |")
    add("|---|" + "---|" * len(SUPPLEMENTARY_SHINGLE_SIZES))
    for category, label in JACCARD_CATEGORIES:
        cells = " | ".join(fmt_score(size_means[(category, s)]) for s in SUPPLEMENTARY_SHINGLE_SIZES)
        add(f"| {label} | {cells} |")
    add("")
    add("A larger shingle size makes the score more sensitive to statement order and loop "
        "rewrites. A smaller one ignores order, but independent and unrelated programs then "
        "score higher too.")
    add("")

    add("### Documented limitations")
    add("")
    add(f"1. **Independent work with the same approach looks like a copy.** The independent "
        f"solutions above scored at most {fmt_score(indep_max)} only because each takes a "
        "different approach. A second student who writes the standard loop for J1 on their "
        f"own scores **{fmt_score(same_approach_score)}** (first probe below). Short tasks have "
        "few natural solutions, so honest students often produce the same structure. This is "
        "the main reason the platform shows the score to the instructor as a review indicator "
        "and never as an automatic verdict.")
    add(f"2. **Reordering statements lowers the score sharply on short programs** "
        f"({fmt_score(reorder_min)} to {fmt_score(reorder_max)} here), because each moved "
        "statement changes a large share of a short program's shingles.")
    if while_min <= indep_max:
        add("3. **Rewriting a for loop as a while loop can push a copy down into the range of "
            f"independent solutions** (lowest rewrite {fmt_score(while_min)}, highest independent "
            f"solution {fmt_score(indep_max)}).")
    else:
        add(f"3. **Rewriting a for loop as a while loop lowers the score substantially** "
            f"({fmt_score(while_min)} to {fmt_score(while_max)}).")
    add("4. **Names are fully ignored, including function names.** This is what makes renaming "
        "score 100%, but it also means `sum(values)` and `len(values)` look the same "
        "(probe below).")
    add("5. **Docstrings count as statements.** Unlike `#` comments, a docstring is a string "
        "expression in the syntax tree, so adding one lowers the score slightly (probe below).")
    add("6. **Programs with syntax errors are compared differently.** If either program does not "
        "parse, `jaccard.py` falls back to comparing normalized tokens. That path is not "
        f"measured here: all Part 2 programs parse ({jaccard_result.parsed}).")
    add("")

    add("### Probes")
    add("")
    add("| Probe | Shared shingles | All shingles | Score | Why |")
    add("|---|---|---|---|---|")
    for title, score, d, note in jaccard_result.probes:
        add(f"| {title} | {d['intersection_count']} | {d['union_count']} | {fmt_score(score)} | {note} |")
    add("")

    operator_sample = "total = a + b\n"
    operator_fingerprint = generate_ast_fingerprint(operator_sample)
    if operator_fingerprint.count("Add") > 1:
        add("### Observation: operators appear twice in the fingerprint")
        add("")
        add(f"`{operator_sample.strip()}` produces the fingerprint "
            f"`{' '.join(operator_fingerprint)}`. `ASTFingerprinter.generic_visit` "
            "(`app/services/ast_fingerprinter.py`) appends the operator name itself, then visits "
            "the operator node, which is not in its skip list, so the name is appended again. "
            "Identical programs still produce identical fingerprints, so no check above is "
            "affected, but operators carry double weight in the shingles. Every score in this "
            "report was measured with this behavior.")
        add("")

    # Appendix --------------------------------------------------------------
    add("## Appendix A: AST test programs")
    add("")
    for case in AST_CASES:
        if case.expected is not None:
            nonzero = ", ".join(f"{label} = {n}" for label, n in case.expected.items() if n)
            summary = f"expected: {nonzero or 'all zero'}"
        else:
            summary = f"expected: syntax error on line {case.syntax_error_line}"
        add("<details>")
        add(f"<summary>{case.case_id}: {case.title} ({summary})</summary>")
        add("")
        lines.extend(code_block(case.code))
        add("")
        add("</details>")
        add("")

    add("## Appendix B: Jaccard test programs")
    add("")
    for task in JACCARD_TASKS:
        add(f"### {task.task_id}: {task.title}")
        add("")
        add("<details>")
        add("<summary>Base program</summary>")
        add("")
        lines.extend(code_block(task.base))
        add("")
        add("</details>")
        add("")
        for category, label in JACCARD_CATEGORIES:
            if category == "exact":
                continue
            add("<details>")
            add(f"<summary>{label} ({fmt_score(jaccard_result.scores[(task.task_id, category)])})</summary>")
            add("")
            lines.extend(code_block(task.variants[category]))
            add("")
            add("</details>")
            add("")

    return "\n".join(lines).rstrip("\n") + "\n"


def main() -> int:
    ast_result = run_ast_suite()
    jaccard_result = run_jaccard_suite()

    REPORT_PATH.write_text(build_report(ast_result, jaccard_result), encoding="utf-8")

    print("Part 1: AST evaluation")
    print(f"  Structure counts: {ast_result.counts}")
    for label in AST_RULES:
        print(f"    {label}: {ast_result.count_by_rule[label]}")
    print(f"  Strictness verdicts: {ast_result.verdicts}")
    for mode in STRICTNESS_MODES:
        print(f"    {mode}: {ast_result.verdict_by_mode[mode]}")
    for label in AST_RULES:
        print(f"    {label}: {ast_result.verdict_by_rule[label]}")
    print(f"  Syntax-error handling: {ast_result.syntax}")
    print(f"  Part 1 total: {ast_result.overall}")
    print()
    print(f"Part 2: Jaccard similarity (shingle size {SHINGLE_SIZE})")
    for category, label in JACCARD_CATEGORIES:
        values = [jaccard_result.scores[(t.task_id, category)] for t in JACCARD_TASKS]
        print(f"  {label}: " + ", ".join(f"{v:.2f}%" for v in values) + f" (mean {mean(values):.2f}%)")
    print(f"  Lexical changes score 100%: {jaccard_result.lexical}")
    print(f"  Same score both directions: {jaccard_result.symmetry}")
    print(f"  Test data - programs parse: {jaccard_result.parsed}")
    print(f"  Test data - same output as base: {jaccard_result.same_output}")
    print(f"  Part 2 total: {jaccard_result.overall}")
    print()
    total = ast_result.overall + jaccard_result.overall
    print(f"All algorithm checks: {total}")

    failures = ast_result.failures + jaccard_result.failures + jaccard_result.data_failures
    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"  - {failure}")

    print(f"\nReport written to {REPORT_PATH}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
