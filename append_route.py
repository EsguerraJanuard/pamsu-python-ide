import os

ROUTER_PATH = "backend/app/routers/instructor.py"

with open(ROUTER_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Make sure we don't add it twice
if "analyze-solution" not in content:
    # Add imports if missing
    if "from pydantic import BaseModel" not in content:
        content = content.replace("from fastapi import", "from pydantic import BaseModel\nfrom fastapi import")
    
    if "from app.services.ast_analyzer import analyze_reference_solution" not in content:
        content = "from app.services.ast_analyzer import analyze_reference_solution\n" + content

    new_route = """

class SolutionAnalysisRequest(BaseModel):
    reference_code: str

@router.post("/tasks/analyze-solution", status_code=status.HTTP_200_OK)
def analyze_solution(
    request: SolutionAnalysisRequest,
    current_user: User = Depends(get_current_active_user)
):
    \"\"\"
    Analyzes the instructor's reference solution using AST 
    to auto-detect the difficulty and required Python constructs.
    \"\"\"
    if current_user.role != UserRole.INSTRUCTOR:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    analysis_result = analyze_reference_solution(request.reference_code)
    
    if not analysis_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=analysis_result.get("error", "Failed to parse code.")
        )
        
    return analysis_result
"""
    content += new_route

    with open(ROUTER_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("Added /tasks/analyze-solution to instructor.py")
else:
    print("Route already exists.")
