import os
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
if "?" in REDIS_URL:
    REDIS_URL = REDIS_URL.split("?")[0]

kwargs = {"decode_responses": True}
if REDIS_URL.startswith("rediss://"):
    kwargs["ssl_cert_reqs"] = "none"

# Connection pool for asynchronous Redis client (used for WebSockets Pub/Sub)
async_redis_client = aioredis.from_url(
    REDIS_URL,
    **kwargs
)
