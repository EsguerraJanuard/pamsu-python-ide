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
# A failed generation is remembered this long: polls stop and the student
# may ask again (practice router, retry=true).
FAILURE_TTL_SECONDS = 60
# Longer than every Gemini attempt and the waits between them
# (ai_tutor_service.worst_case_generation_seconds()).
GENERATION_LOCK_SECONDS = 90

# Used only while Redis is unreachable. Hints are a few hundred bytes and
# the rate limit bounds how many are made, so a small cap is enough.
memory_store = ExpiringMemoryStore(max_entries=2_000)


def _hint_key(attempt_id: int) -> str:
    return f"practice_ai_hint:{attempt_id}"


def _failure_key(attempt_id: int) -> str:
    return f"practice_ai_hint_failed:{attempt_id}"


def _lock_key(attempt_id: int) -> str:
    return f"ai_hint_generating:{attempt_id}"


def _get(key: str) -> str | None:
    try:
        value = redis_client.get(key)
    except Exception:
        logger.warning("AI hint store: Redis unavailable; reading from memory.")
        value = None

    # A value saved while Redis was down exists only in memory.
    return value or memory_store.get(key)


def _put(key: str, value: str, ttl_seconds: int) -> None:
    try:
        redis_client.set(key, value, ex=ttl_seconds)
    except Exception:
        logger.warning("AI hint store: Redis unavailable; keeping the value in memory.")
        memory_store.put(key, value, ttl_seconds)


def _delete(key: str) -> None:
    memory_store.discard(key)

    try:
        redis_client.delete(key)
    except Exception:
        logger.warning("AI hint store: Redis unavailable; the key will expire on its own.")


def get_hint(attempt_id: int) -> str | None:
    return _get(_hint_key(attempt_id))


def save_hint(attempt_id: int, hint: str) -> None:
    _put(_hint_key(attempt_id), hint, HINT_TTL_SECONDS)


def generation_failed(attempt_id: int) -> bool:
    return _get(_failure_key(attempt_id)) is not None


def save_failure(attempt_id: int) -> None:
    _put(_failure_key(attempt_id), "1", FAILURE_TTL_SECONDS)


def clear_failure(attempt_id: int) -> None:
    _delete(_failure_key(attempt_id))


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
    _delete(_lock_key(attempt_id))
