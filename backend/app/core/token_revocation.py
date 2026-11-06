"""
Revoked access tokens (logout), kept in Redis by token id (jti).

Every revocation is also kept in this process's memory until the token
expires, so a token logged out before or during a Redis outage stays
rejected while Redis is unreachable. Render runs the API as one process, so
that covers the whole deployment until it restarts. Password resets and
deactivation do not depend on this: they are checked in the database.
"""

import logging

import redis

from app.core.memory_fallback import ExpiringMemoryStore
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

REVOKED_TOKEN_KEY_PREFIX = "blacklist"

revoked_in_memory = ExpiringMemoryStore()


def _key(jti: str) -> str:
    return f"{REVOKED_TOKEN_KEY_PREFIX}:{jti}"


def revoke_token(jti: str, ttl_seconds: int) -> None:
    revoked_in_memory.set(_key(jti), ttl_seconds)

    try:
        redis_client.setex(_key(jti), ttl_seconds, "revoked")
    except redis.exceptions.RedisError:
        logger.warning("Could not record a revoked token in Redis; it is kept in memory only.")


def is_token_revoked(jti: str) -> bool:
    if revoked_in_memory.contains(_key(jti)):
        return True

    try:
        return bool(redis_client.get(_key(jti)))
    except redis.exceptions.RedisError:
        logger.warning("Token revocation list unavailable in Redis; only this server's memory was checked.")
        return False
