from app.services.ast_evaluator import evaluate_ast, evaluate_ast_details


def test_ast_passes_when_required_nodes_exist():
    raw_code = """
def solve():
    for number in range(5):
        print(number)

solve()
"""

    rules = {
        "require_for_loop": True,
        "require_function_def": True,
        "require_while_loop": False,
    }

    result = evaluate_ast_details(raw_code, rules)

    assert result["passed"] is True
    assert result["syntax_error"] is None
    assert result["missing_requirements"] == []
    assert evaluate_ast(raw_code, rules) is True


def test_ast_fails_when_required_node_is_missing():
    raw_code = """
def solve():
    print("No loop")

solve()
"""

    rules = {
        "require_for_loop": True,
        "require_function_def": True,
    }

    result = evaluate_ast_details(raw_code, rules)

    assert result["passed"] is False
    assert "require_for_loop" in result["missing_requirements"]


def test_ast_handles_syntax_error():
    raw_code = "def solve(:"

    rules = {
        "require_function_def": True,
    }

    result = evaluate_ast_details(raw_code, rules)

    assert result["passed"] is False
    assert result["syntax_error"] is not None
    assert result["syntax_error"]["message"] == "invalid syntax"
    assert result["syntax_error"]["line"] == 1
    assert result["syntax_error"]["column"] == 11
