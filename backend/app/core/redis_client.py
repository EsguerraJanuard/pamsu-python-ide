import os
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# Remove leftover query params to avoid parsing conflicts
if "?" in REDIS_URL:
    REDIS_URL = REDIS_URL.split("?")[0]

kwargs = {"decode_responses": True}
if REDIS_URL.startswith("rediss://"):
    kwargs["ssl_cert_reqs"] = "none"

# Connection pool for synchronous Redis client
redis_client = redis.Redis.from_url(
    REDIS_URL,
    **kwargs
)
