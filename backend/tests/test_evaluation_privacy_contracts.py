from app.services.ast_evaluator import evaluate_ast_details

# --- AST Evaluator Contract Tests ---


def test_ast_evaluator_catches_syntax_errors():
    """
    Contract: The evaluator must gracefully catch syntax errors
    without crashing the main API thread.
    """
    raw_code = "print('missing closing quote)"
    rules = {"require_print_call": True}

    result = evaluate_ast_details(raw_code, rules)

    assert result["passed"] is False
    assert result["syntax_error"] is not None
    assert result["syntax_error"]["line"] is not None


def test_ast_evaluator_validates_required_rules():
    """
    Contract: The evaluator must correctly identify if specific AST nodes
    (like loops or print statements) are present based on the rules.
    """
    raw_code = "for i in range(5):\n    print(i)"
    rules = {
        "require_for_loop": {"required": True, "min_count": 1},
        "require_print_call": True,
    }

    result = evaluate_ast_details(raw_code, rules)

    assert result["passed"] is True
    assert len(result["missing_requirements"]) == 0
    assert result["detected_nodes"]["require_for_loop"] >= 1


def test_ast_evaluator_never_executes_code():
    """
    Contract: As stated in the boundary comments, this module must only
    perform static parsing. Malicious code should be parsed safely without execution.
    """
    # This code would wipe files if executed, but ast.parse only reads it.
    malicious_code = "import os\nos.system('rm -rf /')"
    rules = {"require_import": True}

    result = evaluate_ast_details(malicious_code, rules)

    # It passes the static check for having an 'import', but does not execute.
    assert result["passed"] is True
    assert result["syntax_error"] is None


def test_ast_evaluator_handles_configuration_errors():
    """
    Contract: Invalid rule configurations passed to the evaluator must be
    caught and appended to configuration_errors.
    """
    raw_code = "print('hello')"
    # Passing a string instead of a bool/dict/int is invalid
    rules = {"require_print_call": "invalid_config"}

    result = evaluate_ast_details(raw_code, rules)

    assert result["passed"] is False
    assert len(result["configuration_errors"]) > 0
