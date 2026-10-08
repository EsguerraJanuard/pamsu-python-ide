import os
import re

filepath = "backend/app/main.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

import_str = "import redis.asyncio as redis\nfrom fastapi_limiter import FastAPILimiter\n\n"
content = import_str + content

startup_replacement = """@app.on_event("startup")
async def startup_event():
    import anyio.to_thread
    try:
        limiter = anyio.to_thread.current_default_thread_limiter()
        limiter.total_tokens = 200
    except Exception:
        pass
        
    try:
        redis_client = redis.from_url("redis://redis:6379/0", encoding="utf8", decode_responses=True)
        await FastAPILimiter.init(redis_client)
    except Exception as e:
        print("Could not initialize FastAPILimiter:", e)
"""

pattern = r"@app\.on_event\(\"startup\"\)\nasync def startup_event\(\):\n    import anyio\.to_thread\n    try:\n        limiter = anyio\.to_thread\.current_default_thread_limiter\(\)\n        limiter\.total_tokens = 200\n    except Exception:\n        pass\n"
content = re.sub(pattern, startup_replacement, content, flags=re.MULTILINE)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Injected FastAPILimiter into main.py")
