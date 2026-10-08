import os
import re

filepath = "backend/app/routers/practice.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

if "RateLimiter" not in content:
    content = content.replace("from fastapi import APIRouter", "from fastapi_limiter.depends import RateLimiter\nfrom fastapi import APIRouter")

content = content.replace("@router.post(\"/tasks/{task_id}/submit\", response_model=PracticeSubmissionResponse)", "@router.post(\"/tasks/{task_id}/submit\", response_model=PracticeSubmissionResponse, dependencies=[Depends(RateLimiter(times=3, seconds=10))])")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Injected FastAPILimiter into practice.py")
