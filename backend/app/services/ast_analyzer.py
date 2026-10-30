import re
from collections.abc import Iterable
from typing import Any

from app.services.ast_evaluator import SUPPORTED_AST_RULES, is_rule_enabled
from app.services.ast_safety import parse_python_source

# Activity-creation assistant. It only suggests a difficulty level and AST
# requirements; the instructor reviews and saves them. It never grades.

DIFFICULTY_ORDER = ("beginner", "intermediate", "expert")

# Lowest difficulty at which each rule may be required. This mirrors the
# rule categories in the frontend activity editor (frontend/src/utils/astRules.js):
# Output & Input and Control Flow are beginner; Functions, Data Structures and
# File Handling are intermediate; OOP & Advanced is expert.
RULE_LEVELS: dict[str, str] = {
    "require_print_call": "beginner",
    "require_input_call": "beginner",
    "require_if_statement": "beginner",
    "require_for_loop": "beginner",
    "require_while_loop": "beginner",
    "require_break_statement": "beginner",
    "require_continue_statement": "beginner",
    "require_with_statement": "beginner",
    "require_pass_statement": "beginner",
    "require_function_def": "intermediate",
    "require_function_call": "intermediate",
    "require_return_statement": "intermediate",
    "require_global": "intermediate",
    "require_nonlocal": "intermediate",
    "require_list": "intermediate",
    "require_dict": "intermediate",
    "require_tuple": "intermediate",
    "require_set": "intermediate",
    "require_list_comprehension": "intermediate",
    "require_dict_comprehension": "intermediate",
    "require_del_statement": "intermediate",
    "require_open_call": "intermediate",
    "require_class_def": "expert",
    "require_try_except": "expert",
    "require_lambda": "expert",
    "require_import": "expert",
    "require_match_statement": "expert",
    "require_yield": "expert",
    "require_assert_statement": "expert",
    "require_raise_statement": "expert",
    "require_decorator": "expert",
    "require_async_function": "expert",
    "require_await": "expert",
}

# Older activities may still use these rule names (see ast_evaluator.py).
LEGACY_RULE_NAMES = {
    "require_function": "require_function_def",
    "require_class": "require_class_def",
}

# Constructs read from a reference solution. They are suggested as
# requirements and set the difficulty. Left out because they appear in
# programs of every level and would only add noise: any call (print() is a
# call), print, tuples (a, b = b, a), pass, and import (import math or
# import random is common in beginner work). The instructor adds those by
# hand when they matter.
SOLUTION_SUGGESTIBLE_RULES = (
    "require_input_call",
    "require_if_statement",
    "require_for_loop",
    "require_while_loop",
    "require_break_statement",
    "require_continue_statement",
    "require_with_statement",
    "require_function_def",
    "require_return_statement",
    "require_global",
    "require_nonlocal",
    "require_list",
    "require_dict",
    "require_set",
    "require_list_comprehension",
    "require_dict_comprehension",
    "require_del_statement",
    "require_open_call",
    "require_class_def",
    "require_try_except",
    "require_lambda",
    "require_yield",
    "require_assert_statement",
    "require_raise_statement",
    "require_decorator",
    "require_async_function",
    "require_await",
    "require_match_statement",
)

# Standard-library modules named in problem text ("use the math module").
_MODULE_NAMES = r"(?:math|random|datetime|time|os|sys|statistics|string|json|csv|collections|itertools|functools)"

# Phrases in a problem description that point to a construct. Matching is
# case-insensitive on whole words; every match is reported so the instructor
# can see why a rule was suggested.
DESCRIPTION_PATTERNS: dict[str, tuple[str, ...]] = {
    "require_input_call": (
        r"input", r"ask(?:s)? the user", r"prompt(?:s)? the user", r"user enters?",
        r"enter (?:a|an|the|their|his|her|two|three)",
    ),
    "require_print_call": (r"prints?", r"displays?", r"outputs?"),
    "require_if_statement": (
        r"if", r"otherwise", r"condition(?:al|s)?", r"check (?:if|whether)",
        r"determine (?:if|whether)",
    ),
    "require_for_loop": (
        r"for loop", r"for each", r"for every", r"loop(?:s|ing)? (?:through|over)",
        r"iterat(?:e|es|ing|ion)", r"repeat(?:s|edly)? \w+ times",
    ),
    "require_while_loop": (
        r"while loop", r"while", r"until", r"keep asking", r"repeatedly ask",
    ),
    "require_break_statement": (r"break", r"stop the loop", r"exit the loop"),
    # Not "define a": beginner problems say "define a variable".
    "require_function_def": (r"function", r"functions", r"def"),
    "require_return_statement": (r"return", r"returns"),
    "require_list": (r"list", r"lists", r"array", r"arrays"),
    "require_dict": (r"dictionary", r"dictionaries", r"dict", r"key-value", r"key value pairs?"),
    "require_list_comprehension": (r"list comprehension",),
    "require_dict_comprehension": (r"dictionary comprehension", r"dict comprehension"),
    # Reading or writing a file, not "save your file as lab3.py".
    "require_open_call": (
        r"text files?",
        r"file (?:handling|input|output|operations?)",
        r"(?:read|reads|reading|write|writes|writing|append|appends|appending|save|saves|saving"
        r"|store|stores|storing|load|loads|loading)(?: \w+){0,3} (?:to|from|into) (?:a|an|the) (?:\w+ )?files?",
        r"open(?:s|ing)? (?:a|an|the) (?:\w+ )?files?",
        r"\.txt", r"\.csv", r"csv",
    ),
    "require_class_def": (
        r"(?:create|define|write|design) (?:a|the) class", r"class named",
        r"object-oriented", r"oop", r"inherit(?:s|ance)?", r"constructor",
    ),
    # Not "invalid input": beginner problems print "Invalid input" from an if.
    "require_try_except": (
        r"exceptions?", r"error handling", r"handle (?:the )?errors?",
        r"try/except", r"try-except", r"without crashing",
    ),
    "require_lambda": (r"lambda", r"anonymous function"),
    # Not a bare "module" or "library" ("In this module", "Library fines").
    "require_import": (
        r"import statements?",
        r"imports? (?:a|an|the) (?:\w+ )?(?:module|library)",
        r"import " + _MODULE_NAMES,
        _MODULE_NAMES + r" (?:module|library)",
    ),
    # Raising an error, not "raise a number to the power of 2".
    "require_raise_statement": (r"raises? (?:an? |the )?\w*(?:error|exception)s?",),
}

def _compile_phrase(pattern: str) -> re.Pattern[str]:
    # Whole words only; a pattern that starts with punctuation (".txt")
    # may follow a word character, as in "data.txt".
    prefix = "" if pattern.startswith("\\") else r"(?<![\w-])"
    return re.compile(rf"{prefix}{pattern}(?![\w-])", re.IGNORECASE)


_COMPILED_DESCRIPTION_PATTERNS = {
    rule: [_compile_phrase(pattern) for pattern in patterns]
    for rule, patterns in DESCRIPTION_PATTERNS.items()
}

DIFFICULTY_DEFINITIONS = {
    "beginner": "input/output, conditionals and loops only",
    "intermediate": "functions, data structures or file handling",
    "expert": "classes, exception handling, lambdas or other advanced constructs",
}


class SolutionParseError(ValueError):
    pass


def rule_level(rule: str) -> str:
    """Lowest difficulty at which a rule may be required."""
    return RULE_LEVELS.get(LEGACY_RULE_NAMES.get(rule, rule), "beginner")


def highest_level(rules: Iterable[str]) -> str:
    """Highest level among the rules; beginner when there are none."""
    return max((rule_level(rule) for rule in rules), key=DIFFICULTY_ORDER.index, default="beginner")


def required_rule_names(rules: dict[str, Any] | None) -> list[str]:
    """Rule names a stored rule map actually requires (see ast_evaluator)."""
    return [rule for rule, configuration in (rules or {}).items() if is_rule_enabled(configuration)]


def rules_above_level(difficulty: str, rules: dict[str, Any] | None) -> list[str]:
    """Required rules that need a higher difficulty than the given one."""
    limit = DIFFICULTY_ORDER.index(difficulty)
    return [rule for rule in required_rule_names(rules) if DIFFICULTY_ORDER.index(rule_level(rule)) > limit]


def rule_label(rule: str) -> str:
    definition = SUPPORTED_AST_RULES.get(rule)
    return definition["label"] if definition else rule


def detect_solution_constructs(code: str) -> dict[str, int]:
    """Count the suggestible constructs in a reference solution.

    The counts come from the evaluator's own detectors, so a suggested
    requirement is measured exactly as a student submission will be.
    """
    try:
        tree = parse_python_source(code)
    except SyntaxError as error:
        raise SolutionParseError(f"SyntaxError: {error}") from error

    counts: dict[str, int] = {}

    for rule in SOLUTION_SUGGESTIBLE_RULES:
        definition = SUPPORTED_AST_RULES.get(rule)
        if definition is None:
            continue

        count = len(definition["detector"](tree))
        if count > 0:
            counts[rule] = count

    return counts


def detect_description_constructs(text: str) -> dict[str, list[str]]:
    """Find phrases in a problem description that point to constructs."""
    matches: dict[str, list[str]] = {}

    for rule, patterns in _COMPILED_DESCRIPTION_PATTERNS.items():
        if rule not in SUPPORTED_AST_RULES:
            continue

        terms: list[str] = []
        for pattern in patterns:
            for match in pattern.finditer(text):
                term = match.group(0).lower()
                if term not in terms:
                    terms.append(term)

        if terms:
            matches[rule] = terms[:5]

    return matches


def analyze_activity(
    reference_code: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Suggest a difficulty level and AST requirements for a new activity.

    Raises SolutionParseError when the reference solution does not parse.
    """
    has_solution = bool(reference_code and reference_code.strip())
    solution_counts = detect_solution_constructs(reference_code) if has_solution else {}
    description_terms = (
        detect_description_constructs(description)
        if description and description.strip()
        else {}
    )

    ordered_rules = [rule for rule in RULE_LEVELS if rule in solution_counts or rule in description_terms]

    constructs = []
    for rule in ordered_rules:
        in_solution = rule in solution_counts
        in_description = rule in description_terms
        constructs.append(
            {
                "rule": rule,
                "label": rule_label(rule),
                "level": rule_level(rule),
                "source": (
                    "both" if in_solution and in_description
                    else "solution" if in_solution
                    else "description"
                ),
                "solution_count": solution_counts.get(rule, 0),
                "description_terms": description_terms.get(rule, []),
            }
        )

    # A reference solution is evidence; description phrases are hints. When a
    # solution is given, it alone sets the difficulty.
    basis = list(solution_counts) if has_solution else list(description_terms)
    difficulty = highest_level(basis)
    deciding = [rule for rule in basis if rule_level(rule) == difficulty]

    if deciding:
        difficulty_reason = (
            f"{difficulty.capitalize()}: uses "
            + ", ".join(rule_label(rule).lower() for rule in deciding[:3])
            + f" ({DIFFICULTY_DEFINITIONS[difficulty]})."
        )
    else:
        difficulty_reason = f"Beginner: no constructs beyond basic statements were found ({DIFFICULTY_DEFINITIONS['beginner']})."

    # Presence is suggested (at least one). The instructor can raise a count.
    suggested_rules = {
        rule: {"required": True, "min_count": 1}
        for rule in ordered_rules
    }

    return {
        "success": True,
        "difficulty_level": difficulty,
        "difficulty_reason": difficulty_reason,
        "suggested_ast_rules": suggested_rules,
        "constructs": constructs,
    }


def analyze_reference_solution(code: str) -> dict[str, Any]:
    """Analyze a reference solution only (kept for existing callers)."""
    try:
        return analyze_activity(reference_code=code)
    except SolutionParseError as error:
        return {
            "success": False,
            "error": str(error),
            "difficulty_level": "beginner",
            "suggested_ast_rules": {},
            "constructs": [],
        }
