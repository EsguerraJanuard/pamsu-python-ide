import os

import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
if "?" in REDIS_URL:
    REDIS_URL = REDIS_URL.split("?")[0]

# Same connect-phase bound as the synchronous client (see redis_client.py).
REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS = float(
    os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS", "1.0")
)

kwargs = {
    "decode_responses": True,
    "socket_connect_timeout": REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS,
}
if REDIS_URL.startswith("rediss://"):
    kwargs["ssl_cert_reqs"] = "none"

# Connection pool for asynchronous Redis client (used for WebSockets Pub/Sub
# and the fastapi-limiter rate limiter)
async_redis_client = aioredis.from_url(
    REDIS_URL,
    **kwargs
)
