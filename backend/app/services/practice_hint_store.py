"""
Where AI Tutor hints for failed solo practice attempts are kept.

Hints live in Redis, keyed by attempt id, for HINT_TTL_SECONDS; there is no
database column for them. An expired hint is generated again on the next
request (the endpoint's rate limit still applies).

While Redis is unreachable the same keys are kept in this process's memory
(core/memory_fallback.py), so the tutor keeps working. Render runs the API
and its background tasks in one process, so the in-memory copy is the one
every request sees until the process restarts.
"""

import logging

from app.core.memory_fallback import ExpiringMemoryStore
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

HINT_TTL_SECONDS = 24 * 60 * 60
# A failed generation is kept briefly, so asking again soon retries Gemini.
UNAVAILABLE_TTL_SECONDS = 60
# Longer than one Gemini call (ai_tutor_service.REQUEST_TIMEOUT_MS).
GENERATION_LOCK_SECONDS = 60

# Used only while Redis is unreachable. Hints are a few hundred bytes and
# the rate limit bounds how many are made, so a small cap is enough.
memory_store = ExpiringMemoryStore(max_entries=2_000)


def _hint_key(attempt_id: int) -> str:
    return f"practice_ai_hint:{attempt_id}"


def _lock_key(attempt_id: int) -> str:
    return f"ai_hint_generating:{attempt_id}"


def get_hint(attempt_id: int) -> str | None:
    key = _hint_key(attempt_id)

    try:
        hint = redis_client.get(key)
    except Exception:
        logger.warning("AI hint store: Redis unavailable; reading from memory.")
        hint = None

    # A hint saved while Redis was down exists only in memory.
    return hint or memory_store.get(key)


def save_hint(attempt_id: int, hint: str, *, ttl_seconds: int = HINT_TTL_SECONDS) -> None:
    key = _hint_key(attempt_id)

    try:
        redis_client.set(key, hint, ex=ttl_seconds)
    except Exception:
        logger.warning("AI hint store: Redis unavailable; keeping the hint in memory.")
        memory_store.put(key, hint, ttl_seconds)


def claim_generation(attempt_id: int) -> bool:
    """SET NX: True only for the caller that should start a generation."""

    key = _lock_key(attempt_id)

    try:
        return bool(redis_client.set(key, "1", ex=GENERATION_LOCK_SECONDS, nx=True))
    except Exception:
        # If Redis returns mid-generation a second Gemini call can start;
        # it is rate-limited and saves the same kind of hint.
        logger.warning("AI hint lock: Redis unavailable; locking in memory.")
        return memory_store.add(key, GENERATION_LOCK_SECONDS)


def release_generation(attempt_id: int) -> None:
    key = _lock_key(attempt_id)
    memory_store.discard(key)

    try:
        redis_client.delete(key)
    except Exception:
        # The lock expires on its own after GENERATION_LOCK_SECONDS.
        logger.warning("AI hint lock: Redis unavailable; could not release it early.")
