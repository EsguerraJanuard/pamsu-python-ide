import os
import re

filepath = "backend/app/routers/evaluation.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

import_str = "from fastapi_limiter.depends import RateLimiter\n"
content = import_str + content

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed evaluation.py import")
