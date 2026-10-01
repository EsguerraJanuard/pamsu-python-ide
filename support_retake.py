import os

filepath = "frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add badge mapping
content = content.replace(
    "} else if (sub.status === 'late') {",
    "} else if (sub.status === 'retake_requested') {\n                  badgeText = 'Retake Req';\n                  badgeColor = 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20';\n                } else if (sub.status === 'late') {"
)

# Add "Approve Retake" button in grading panel
button_html = """
                {detailedSub?.status === 'retake_requested' && (
                  <button
                    onClick={async () => {
                      try {
                        await api.post(`/submissions/${detailedSub.id}/approve-retake`);
                        setNotice("Retake approved! Student can now resubmit.");
                        fetchSubmissions();
                      } catch (err) {
                        setNotice("Failed to approve retake.");
                      }
                    }}
                    className="flex-1 rounded-lg bg-amber-500/10 border border-amber-500/20 py-2.5 text-sm font-semibold text-amber-600 dark:text-amber-400 transition-all hover:bg-amber-500/20"
                  >
                    Approve Retake
                  </button>
                )}
"""

content = content.replace(
    '<button\n                  onClick={handleGradeSubmit}',
    button_html + '\n                <button\n                  onClick={handleGradeSubmit}'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

# We also need the backend API for approve-retake
api_filepath = "backend/app/routers/submissions.py"
with open(api_filepath, "r", encoding="utf-8") as f:
    api_content = f.read()

approve_code = """
@router.post("/{submission_id}/approve-retake")
async def approve_retake(submission_id: str, db: AsyncSession = Depends(get_db)):
    query = select(Submission).where(Submission.id == submission_id)
    result = await db.execute(query)
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    submission.status = "in_progress" # Or soft delete to let them submit again
    # Usually approving retake means deleting the submission or resetting it
    # We will reset status to in_progress
    submission.grade_score = None
    submission.has_manual_grade = False
    await db.commit()
    return {"message": "Retake approved"}
"""

if "approve-retake" not in api_content:
    api_content += approve_code

with open(api_filepath, "w", encoding="utf-8") as f:
    f.write(api_content)

print("Added Retake Support to Workspace and Backend API")
