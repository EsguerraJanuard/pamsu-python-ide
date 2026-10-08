import os
import re

filepath = "backend/app/routers/auth.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

import_str = "from fastapi_limiter.depends import RateLimiter\n"
content = content.replace("from fastapi import APIRouter", import_str + "from fastapi import APIRouter")

content = content.replace("@router.post(\"/login\", response_model=TokenResponse)", "@router.post(\"/login\", response_model=TokenResponse, dependencies=[Depends(RateLimiter(times=5, seconds=60))])")
content = content.replace("@router.post(\"/guest\", response_model=TokenResponse)", "@router.post(\"/guest\", response_model=TokenResponse, dependencies=[Depends(RateLimiter(times=2, seconds=60))])")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Injected FastAPILimiter into auth.py")
