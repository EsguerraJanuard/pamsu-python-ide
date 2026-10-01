import os

filepath = "backend/app/routers/submissions.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

retake_code = """
@router.post("/{submission_id}/retake-request")
async def request_retake(submission_id: str, db: AsyncSession = Depends(get_db)):
    query = select(Submission).where(Submission.id == submission_id)
    result = await db.execute(query)
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    # Set status or add a flag
    submission.status = "retake_requested"
    await db.commit()
    return {"message": "Retake requested successfully"}
"""

if "retake-request" not in content:
    content += retake_code

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Added Retake Request API")
