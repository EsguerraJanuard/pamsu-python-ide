import ast
import json
from typing import Any


SUPPORTED_AST_RULES: dict[str, tuple[type[ast.AST], ...]] = {
    "require_for_loop": (ast.For, ast.AsyncFor),
    "require_while_loop": (ast.While,),
    "require_function_def": (ast.FunctionDef, ast.AsyncFunctionDef),
    "require_if_statement": (ast.If,),
    "require_class_def": (ast.ClassDef,),
    "require_return_statement": (ast.Return,),
    "require_try_except": (ast.Try,),
    "require_import": (ast.Import, ast.ImportFrom),
    "require_list_comprehension": (ast.ListComp,),
    "require_dict_comprehension": (ast.DictComp,),
    "require_lambda": (ast.Lambda,),
}

if hasattr(ast, "Match"):
    SUPPORTED_AST_RULES["require_match_statement"] = (ast.Match,)


def evaluate_ast_details(raw_code: str, rules: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "passed": False,
        "syntax_error": None,
        "missing_requirements": [],
        "unsupported_rules": [],
        "detected_nodes": {},
    }

    if not isinstance(raw_code, str):
        result["syntax_error"] = "raw_code must be a string."
        return result

    if not isinstance(rules, dict):
        result["syntax_error"] = "rules must be a dictionary."
        return result

    try:
        syntax_tree = ast.parse(raw_code)
    except SyntaxError as error:
        result["syntax_error"] = f"SyntaxError: {error.msg} at line {error.lineno}"
        return result

    all_nodes = list(ast.walk(syntax_tree))

    for rule_name, node_types in SUPPORTED_AST_RULES.items():
        result["detected_nodes"][rule_name] = sum(
            1 for node in all_nodes if isinstance(node, node_types)
        )

    for rule_name, is_required in rules.items():
        if is_required is not True:
            continue

        if rule_name not in SUPPORTED_AST_RULES:
            result["unsupported_rules"].append(rule_name)
            continue

        if result["detected_nodes"].get(rule_name, 0) == 0:
            result["missing_requirements"].append(rule_name)

    result["passed"] = (
        not result["syntax_error"]
        and not result["missing_requirements"]
        and not result["unsupported_rules"]
    )

    return result


def evaluate_ast(raw_code: str, rules: dict[str, Any]) -> bool:
    evaluation = evaluate_ast_details(raw_code, rules)
    return bool(evaluation["passed"])


if __name__ == "__main__":
    sample_raw_code = """
def solve():
    for i in range(5):
        print(i)

solve()
"""

    sample_rules = {
        "require_for_loop": True,
        "require_while_loop": True,
        "require_function_def": True,
    }

    sample_result = evaluate_ast_details(sample_raw_code, sample_rules)

    print(json.dumps(sample_result, indent=4))
