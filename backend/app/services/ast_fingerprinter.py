import ast

from app.services.ast_safety import parse_python_source


# Names, constants and load/store contexts carry no structure. Operator nodes
# are recorded by their parent through `op` / `ops` below, so recording them
# again when they are visited as children would count each operator twice.
SKIPPED_NODE_TYPES = (
    ast.Name,
    ast.Constant,
    ast.arg,
    ast.alias,
    ast.Load,
    ast.Store,
    ast.Del,
    ast.operator,
    ast.boolop,
    ast.unaryop,
    ast.cmpop,
)


class ASTFingerprinter(ast.NodeVisitor):
    def __init__(self):
        self.fingerprint = []

    def generic_visit(self, node):
        # We explicitly ignore nodes that represent names, constants, and basic
        # syntax sugar that doesn't change logic, to focus purely on structural flow.
        if isinstance(node, SKIPPED_NODE_TYPES):
            super().generic_visit(node)
            return

        # Add the structural class name
        node_type = type(node).__name__
        self.fingerprint.append(node_type)
        
        # If the node has an operator (like Add, Sub, Eq, Not), append the operator type too
        if hasattr(node, 'op'):
            self.fingerprint.append(type(node.op).__name__)
        if hasattr(node, 'ops'):
            for op in node.ops:
                self.fingerprint.append(type(op).__name__)

        super().generic_visit(node)

def generate_ast_fingerprint(raw_code: str) -> list[str]:
    """
    Parses Python code into an AST and generates a structural fingerprint.
    Returns a sequence of structural tokens. Raises SyntaxError if parsing fails.
    """
    if not isinstance(raw_code, str) or not raw_code.strip():
        return []
        
    tree = parse_python_source(raw_code)
    fingerprinter = ASTFingerprinter()
    fingerprinter.visit(tree)
    return fingerprinter.fingerprint
