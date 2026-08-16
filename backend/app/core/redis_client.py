import os
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Connection pool for synchronous Redis client
redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True
)
