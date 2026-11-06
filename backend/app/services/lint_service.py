import pyflakes.api
import pyflakes.reporter
from app.schemas.lint_schema import LintMarker, LintResult
from app.services.ast_safety import (SourceAnalysisLimitError,
                                     parse_python_source)


class LintReporter(pyflakes.reporter.Reporter):
    def __init__(self):
        self.markers = []

    def unexpectedError(self, filename, msg):
        self.markers.append(LintMarker(line=1, column=1, message=msg, severity="error"))

    def syntaxError(self, filename, msg, lineno, offset, text):
        self.markers.append(LintMarker(line=lineno or 1, column=(offset or 0) + 1, message=msg, severity="error"))

    def flake(self, msg):
        # msg is an instance of pyflakes.messages.Message
        # It has attributes lineno, col, and message
        col = getattr(msg, "col", 0) + 1
        self.markers.append(LintMarker(line=msg.lineno, column=col, message=msg.message % msg.message_args, severity="warning"))

def lint_python_code(code: str) -> LintResult:
    try:
        parse_python_source(code)
    except SourceAnalysisLimitError as error:
        return LintResult(markers=[LintMarker(line=1, column=1, message=error.msg, severity="error")])
    except SyntaxError:
        # pyflakes reports ordinary syntax errors with their position.
        pass

    reporter = LintReporter()
    pyflakes.api.check(code, filename="code.py", reporter=reporter)
    return LintResult(markers=reporter.markers)
