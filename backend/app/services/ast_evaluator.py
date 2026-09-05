import ast
from collections.abc import Callable
from typing import Any, TypedDict


class ASTRuleDefinition(TypedDict):
    label: str
    detector: Callable[[ast.AST], list[ast.AST]]


def _find_nodes(
    syntax_tree: ast.AST,
    node_types: tuple[type[ast.AST], ...],
) -> list[ast.AST]:
    return [node for node in ast.walk(syntax_tree) if isinstance(node, node_types)]


def _find_named_calls(
    syntax_tree: ast.AST,
    function_name: str,
) -> list[ast.AST]:
    matches: list[ast.AST] = []

    for node in ast.walk(syntax_tree):
        if not isinstance(node, ast.Call):
            continue

        if isinstance(node.func, ast.Name) and node.func.id == function_name:
            matches.append(node)

    return matches


SUPPORTED_AST_RULES: dict[str, ASTRuleDefinition] = {
    "require_for_loop": {
        "label": "For loop",
        "detector": lambda tree: _find_nodes(
            tree,
            (ast.For, ast.AsyncFor),
        ),
    },
    "require_while_loop": {
        "label": "While loop",
        "detector": lambda tree: _find_nodes(
            tree,
            (ast.While,),
        ),
    },
    "require_function_def": {
        "label": "Function definition",
        "detector": lambda tree: _find_nodes(
            tree,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ),
    },
    "require_function_call": {
        "label": "Function call",
        "detector": lambda tree: _find_nodes(
            tree,
            (ast.Call,),
        ),
    },
    "require_input_call": {
        "label": "Input call",
        "detector": lambda tree: _find_named_calls(
            tree,
            "input",
        ),
    },
    "require_print_call": {
        "label": "Print call",
        "detector": lambda tree: _find_named_calls(
            tree,
            "print",
        ),
    },
    "require_if_statement": {
        "label": "If statement",
        "detector": lambda tree: _find_nodes(
            tree,
            (ast.If,),
        ),
    },
    "require_class_def": {
        "label": "Class definition",
        "detector": lambda tree: _find_nodes(
            tree,
            (ast.ClassDef,),
        ),
    },
    "require_return_statement": {
        "label": "Return statement",
        "detector": lambda tree: _find_nodes(
            tree,
            (ast.Return,),
        ),
    },
    "require_try_except": {
        "label": "Try/except statement",
        "detector": lambda tree: _find_nodes(
            tree,
            (ast.Try,),
        ),
    },
    "require_import": {
        "label": "Import statement",
        "detector": lambda tree: _find_nodes(
            tree,
            (ast.Import, ast.ImportFrom),
        ),
    },
    "require_list_comprehension": {
        "label": "List comprehension",
        "detector": lambda tree: _find_nodes(
            tree,
            (ast.ListComp,),
        ),
    },
    "require_dict_comprehension": {
        "label": "Dictionary comprehension",
        "detector": lambda tree: _find_nodes(
            tree,
            (ast.DictComp,),
        ),
    },
    "require_lambda": {
        "label": "Lambda expression",
        "detector": lambda tree: _find_nodes(
            tree,
            (ast.Lambda,),
        ),
    },
}

if hasattr(ast, "Match"):
    SUPPORTED_AST_RULES["require_match_statement"] = {
        "label": "Match statement",
        "detector": lambda tree: _find_nodes(
            tree,
            (ast.Match,),
        ),
    }


def _is_rule_enabled(configuration: Any) -> bool:
    if isinstance(configuration, bool):
        return configuration

    if isinstance(configuration, int):
        return configuration > 0

    if isinstance(configuration, dict):
        return configuration.get("required", True) is True

    return True


def _normalize_rule_configuration(
    configuration: Any,
) -> tuple[bool, int, str | None]:
    if isinstance(configuration, bool):
        return configuration, 1 if configuration else 0, None

    if isinstance(configuration, int):
        if configuration < 0:
            raise ValueError("Minimum count cannot be negative.")

        return configuration > 0, configuration, None

    if isinstance(configuration, dict):
        required = configuration.get("required", True)
        minimum_count = configuration.get("min_count", 1)
        custom_label = configuration.get("label")

        if not isinstance(required, bool):
            raise ValueError("'required' must be a boolean.")

        if (
            isinstance(minimum_count, bool)
            or not isinstance(minimum_count, int)
            or minimum_count < 0
        ):
            raise ValueError("'min_count' must be a non-negative integer.")

        if custom_label is not None and (
            not isinstance(custom_label, str) or not custom_label.strip()
        ):
            raise ValueError("'label' must be a non-empty string.")

        if required and minimum_count == 0:
            minimum_count = 1

        return (
            required,
            minimum_count if required else 0,
            custom_label.strip() if custom_label else None,
        )

    raise ValueError("Rule configuration must be a boolean, integer, or dictionary.")


def evaluate_ast_details(
    raw_code: str,
    rules: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "passed": False,
        "syntax_error": None,
        "configuration_errors": [],
        "missing_requirements": [],
        "unsupported_rules": [],
        "detected_nodes": {},
        "detected_lines": {},
        "findings": [],
    }

    if not isinstance(raw_code, str):
        result["configuration_errors"].append("raw_code must be a string.")
        return result

    if not raw_code.strip():
        result["configuration_errors"].append("raw_code cannot be empty.")
        return result

    if not isinstance(rules, dict):
        result["configuration_errors"].append("rules must be a dictionary.")
        return result

    try:
        syntax_tree = ast.parse(raw_code)
    except SyntaxError as error:
        result["syntax_error"] = {
            "message": error.msg,
            "line": error.lineno,
            "column": error.offset,
            "end_line": error.end_lineno,
            "end_column": error.end_offset,
        }
        return result

    detected_by_rule: dict[str, list[ast.AST]] = {}

    for rule_name, definition in SUPPORTED_AST_RULES.items():
        detected_nodes = definition["detector"](syntax_tree)
        detected_by_rule[rule_name] = detected_nodes

        result["detected_nodes"][rule_name] = len(detected_nodes)
        result["detected_lines"][rule_name] = sorted(
            {node.lineno for node in detected_nodes if hasattr(node, "lineno")}
        )

    for rule_name, configuration in rules.items():
        if rule_name not in SUPPORTED_AST_RULES:
            if _is_rule_enabled(configuration):
                result["unsupported_rules"].append(rule_name)
            continue

        try:
            required, minimum_count, custom_label = _normalize_rule_configuration(
                configuration
            )
        except ValueError as error:
            result["configuration_errors"].append(
                {
                    "rule": rule_name,
                    "message": str(error),
                }
            )
            continue

        if not required:
            continue

        definition = SUPPORTED_AST_RULES[rule_name]
        detected_nodes = detected_by_rule[rule_name]
        detected_count = len(detected_nodes)
        passed = detected_count >= minimum_count

        finding = {
            "rule": rule_name,
            "label": custom_label or definition["label"],
            "required_count": minimum_count,
            "detected_count": detected_count,
            "passed": passed,
            "line_numbers": result["detected_lines"][rule_name],
            "message": (
                f"Detected {detected_count}; required at least {minimum_count}."
            ),
        }

        result["findings"].append(finding)

        if not passed:
            result["missing_requirements"].append(rule_name)

    result["passed"] = not any(
        (
            result["syntax_error"],
            result["configuration_errors"],
            result["missing_requirements"],
            result["unsupported_rules"],
        )
    )

    return result


def evaluate_ast(
    raw_code: str,
    rules: dict[str, Any],
) -> bool:
    return bool(
        evaluate_ast_details(
            raw_code=raw_code,
            rules=rules,
        )["passed"]
    )


# ANALYSIS BOUNDARY:
# This module performs static parsing only. It must never execute submitted
# source code through exec(), eval(), subprocess, or another local runtime.

# REVIEW BOUNDARY:
# AST findings are learning and instructor-review indicators only. They must
# never automatically calculate the official grade.

# PARTNER INTEGRATION:
# Actual Python execution remains the responsibility of the partner-owned
# isolated worker and its CPU, memory, time, process, output, filesystem,
# and network limits.
