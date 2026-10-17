import os

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# Remove leftover query params to avoid parsing conflicts
if "?" in REDIS_URL:
    REDIS_URL = REDIS_URL.split("?")[0]

# Bound only the TCP connect phase. Without it an unreachable Redis host
# blocks every caller for the OS connect timeout (tens of seconds); read
# timeouts are intentionally left unchanged.
REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS = float(
    os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS", "1.0")
)

kwargs = {
    "decode_responses": True,
    "socket_connect_timeout": REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS,
}
if REDIS_URL.startswith("rediss://"):
    kwargs["ssl_cert_reqs"] = "none"

# Connection pool for synchronous Redis client
redis_client = redis.Redis.from_url(
    REDIS_URL,
    **kwargs
)
