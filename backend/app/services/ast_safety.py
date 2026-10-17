"""
Bounded parsing for static analysis of untrusted Python source.

ast.parse() and the recursive visitors built on it can raise MemoryError
or RecursionError, or run for seconds, on small pathological inputs such
as "-" * 99_999 + "1" or "a+" * 50_000 + "a". Every analysis of student or
instructor code goes through parse_python_source() so those inputs are
reported as a syntax-style error instead of crashing the request or
pinning the CPU.

SourceAnalysisLimitError subclasses SyntaxError, so existing
"except SyntaxError" handlers report it like any other syntax error.
"""

import ast

MAX_ANALYZED_SOURCE_LENGTH = 100_000

# Real classroom programs stay far below these limits. The depth limit keeps
# recursive NodeVisitor subclasses well inside Python's recursion limit.
MAX_AST_NODES = 20_000
MAX_AST_DEPTH = 100


class SourceAnalysisLimitError(SyntaxError):
    """The source is too large or too deeply nested to analyze safely."""


def _check_tree_size(tree: ast.AST) -> None:
    node_count = 0
    stack: list[tuple[ast.AST, int]] = [(tree, 1)]

    while stack:
        node, depth = stack.pop()
        node_count += 1

        if node_count > MAX_AST_NODES:
            raise SourceAnalysisLimitError(
                "The code is too long to analyze. Simplify it and try again."
            )

        if depth > MAX_AST_DEPTH:
            raise SourceAnalysisLimitError(
                "The code is nested too deeply to analyze. Simplify it and try again."
            )

        for child in ast.iter_child_nodes(node):
            stack.append((child, depth + 1))


def parse_python_source(source: str) -> ast.Module:
    """Parse source for static analysis within fixed size and depth limits."""

    if len(source) > MAX_ANALYZED_SOURCE_LENGTH:
        raise SourceAnalysisLimitError(
            "The code is too long to analyze. Simplify it and try again."
        )

    try:
        tree = ast.parse(source)
    except SyntaxError:
        raise
    except (MemoryError, RecursionError, ValueError) as error:
        raise SourceAnalysisLimitError(
            "The code is nested too deeply to analyze. Simplify it and try again."
        ) from error

    _check_tree_size(tree)

    return tree
