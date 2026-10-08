import os
import re

filepath = "backend/app/services/evaluation_service.py"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Find where ast_analysis is added and insert the auto-grading logic before _commit_evaluation_transaction
    pattern = r'(    if highest_match_sub_id is not None:.*?        db\.add\(similarity_result\)\n)'
    
    auto_grade_logic = """
    # Panel Requirement: AST-Based Auto-Grading
    # If the code satisfies all required AST rules, automatically award full score for the structural portion.
    if ast_pass_fail:
        existing_grade = (
            db.query(InstructorGrade)
            .filter(InstructorGrade.submission_id == submission.sub_id)
            .first()
        )
        if not existing_grade:
            auto_grade = InstructorGrade(
                submission_id=submission.sub_id,
                instructor_id=task.instructor_id,
                score=100.0,
                max_score=100.0,
                feedback="Auto-graded: Passed all structural (AST) requirements.",
                is_released=True
            )
            db.add(auto_grade)
            submission.status = "graded"
"""
    
    # We will inject the logic right before _commit_evaluation_transaction
    content = re.sub(pattern, r'\1' + auto_grade_logic, content, flags=re.DOTALL)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed AST auto-grading")
