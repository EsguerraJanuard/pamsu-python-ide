import ast
from typing import Any, Dict


class SolutionAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.stats = {
            "For": 0,
            "While": 0,
            "FunctionDef": 0,
            "ClassDef": 0,
            "With": 0,
            "ListComp": 0,
            "DictComp": 0,
            "Try": 0,
            "Lambda": 0
        }

    def visit_For(self, node):
        self.stats["For"] += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.stats["While"] += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.stats["FunctionDef"] += 1
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.stats["ClassDef"] += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.stats["With"] += 1
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self.stats["ListComp"] += 1
        self.generic_visit(node)
        
    def visit_DictComp(self, node):
        self.stats["DictComp"] += 1
        self.generic_visit(node)
        
    def visit_Try(self, node):
        self.stats["Try"] += 1
        self.generic_visit(node)

    def visit_Lambda(self, node):
        self.stats["Lambda"] += 1
        self.generic_visit(node)

def analyze_reference_solution(code: str) -> Dict[str, Any]:
    """
    Parses the provided Python code, analyzes its AST, and determines
    the activity difficulty and recommended AST validation rules.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {
            "success": False,
            "error": f"SyntaxError: {str(e)}",
            "difficulty_level": "beginner",
            "suggested_ast_rules": {}
        }

    analyzer = SolutionAnalyzer()
    analyzer.visit(tree)
    stats = analyzer.stats

    # Determine Difficulty
    if stats["ClassDef"] > 0 or stats["With"] > 0 or stats["Try"] > 0:
        difficulty = "expert"
    elif stats["For"] > 0 or stats["While"] > 0 or stats["FunctionDef"] > 0 or stats["ListComp"] > 0 or stats["DictComp"] > 0 or stats["Lambda"] > 0:
        difficulty = "intermediate"
    else:
        difficulty = "beginner"

    # Map detected features to frontend AST Rule IDs
    # Based on the typical frontend requirements mapping (e.g. ActivityEditor.jsx checkboxes)
    suggested_rules = {}
    
    if stats["For"] > 0:
        suggested_rules["require_for_loop"] = {"required": True, "min_count": stats["For"]}
    if stats["While"] > 0:
        suggested_rules["require_while_loop"] = {"required": True, "min_count": stats["While"]}
    if stats["FunctionDef"] > 0:
        suggested_rules["require_function"] = {"required": True, "min_count": stats["FunctionDef"]}
    if stats["ClassDef"] > 0:
        suggested_rules["require_class"] = {"required": True, "min_count": stats["ClassDef"]}
    if stats["ListComp"] > 0:
        suggested_rules["require_list_comprehension"] = {"required": True, "min_count": stats["ListComp"]}
    if stats["DictComp"] > 0:
        suggested_rules["require_dict_comprehension"] = {"required": True, "min_count": stats["DictComp"]}

    return {
        "success": True,
        "difficulty_level": difficulty,
        "suggested_ast_rules": suggested_rules,
        "raw_stats": stats
    }
