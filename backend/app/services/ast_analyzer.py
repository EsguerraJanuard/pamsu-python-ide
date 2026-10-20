import re
from typing import Any

from app.services.ast_evaluator import SUPPORTED_AST_RULES
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

# Constructs suggested from a reference solution. Constructs that almost every
# program contains (any call, print, literals, pass, import) would only add
# noise, so the instructor adds those by hand when they matter.
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
    "require_dict",
    "require_list_comprehension",
    "require_dict_comprehension",
    "require_open_call",
    "require_class_def",
    "require_try_except",
    "require_lambda",
    "require_yield",
    "require_raise_statement",
    "require_decorator",
    "require_match_statement",
)

# Phrases in a problem description that point to a construct. Matching is
# case-insensitive on whole words; every match is reported so the instructor
# can see why a rule was suggested.
DESCRIPTION_PATTERNS: dict[str, tuple[str, ...]] = {
    "require_input_call": (
        r"input", r"ask(?:s)? the user", r"prompt(?:s)? the user", r"user enters?",
        r"enter (?:a|an|the|their|his|her|two|three)",
    ),
    "require_print_call": (r"print", r"display", r"output"),
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
    "require_function_def": (
        r"function", r"functions", r"define a", r"def",
    ),
    "require_return_statement": (r"return", r"returns"),
    "require_list": (r"list", r"lists", r"array", r"arrays"),
    "require_dict": (r"dictionary", r"dictionaries", r"dict", r"key-value", r"key value pairs?"),
    "require_list_comprehension": (r"list comprehension",),
    "require_dict_comprehension": (r"dictionary comprehension", r"dict comprehension"),
    "require_open_call": (
        r"file", r"files", r"read from a", r"write to a", r"\.txt", r"\.csv", r"csv",
    ),
    "require_class_def": (
        r"(?:create|define|write|design) (?:a|the) class", r"class named",
        r"object-oriented", r"oop", r"inherit(?:s|ance)?", r"constructor",
    ),
    "require_try_except": (
        r"exceptions?", r"error handling", r"handle (?:the )?errors?",
        r"invalid input", r"try/except", r"try-except", r"without crashing",
    ),
    "require_lambda": (r"lambda", r"anonymous function"),
    "require_import": (r"import", r"module", r"library"),
    "require_raise_statement": (r"raise", r"raises"),
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


def _level_of(rule: str) -> str:
    return RULE_LEVELS.get(rule, "beginner")


def _highest_level(rules: list[str]) -> str:
    if not rules:
        return "beginner"

    return max((_level_of(rule) for rule in rules), key=DIFFICULTY_ORDER.index)


def _label_of(rule: str) -> str:
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
                "label": _label_of(rule),
                "level": _level_of(rule),
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
    difficulty = _highest_level(basis)
    deciding = [rule for rule in basis if _level_of(rule) == difficulty]

    if deciding:
        difficulty_reason = (
            f"{difficulty.capitalize()}: uses "
            + ", ".join(_label_of(rule).lower() for rule in deciding[:3])
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
