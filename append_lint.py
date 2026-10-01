import os

filepath = "backend/app/routers/execution.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

lint_code = """
from app.schemas.lint_schema import LintRequest, LintResult
from app.services.lint_service import lint_python_code

@router.post("/lint", response_model=LintResult)
async def lint_endpoint(request: LintRequest):
    return lint_python_code(request.code)
"""
content += lint_code

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Lint endpoint added.")
