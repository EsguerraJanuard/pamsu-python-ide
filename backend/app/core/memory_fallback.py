"""
In-process stand-in for Redis keys while Redis is unreachable.

Rate limits, token revocation and AI Tutor hints fall back to this store
instead of failing open. Render runs the API as a single process, so counts
kept here are the real counts for the whole deployment; they reset when the
process restarts.

Every entry expires, and the store never holds more than `max_entries`
keys: when it is full, expired keys are dropped first, then the oldest.
This bounds memory even if a client sends many distinct identifiers.
"""

import threading
import time
from collections import OrderedDict
from collections.abc import Callable

DEFAULT_MAX_ENTRIES = 100_000


class ExpiringMemoryStore:
    def __init__(
        self,
        *,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        clock: Callable[[], float] = time.monotonic,
    ):
        # (count or stored value, expiry time)
        self._entries: OrderedDict[str, tuple[int | str, float]] = OrderedDict()
        self._lock = threading.Lock()
        self._max_entries = max_entries
        self._clock = clock

    def incr(self, key: str, window_seconds: int) -> tuple[int, int]:
        """Count one hit in a fixed window; return (count, seconds left)."""

        with self._lock:
            now = self._clock()
            entry = self._live_entry(key, now)

            if entry is None:
                entry = (1, now + window_seconds)
                self._insert(key, entry, now)
            else:
                entry = (entry[0] + 1, entry[1])
                self._entries[key] = entry

            return entry[0], max(1, int(entry[1] - now))

    def set(self, key: str, ttl_seconds: int) -> None:
        with self._lock:
            now = self._clock()
            self._entries.pop(key, None)
            self._insert(key, (1, now + ttl_seconds), now)

    def contains(self, key: str) -> bool:
        with self._lock:
            return self._live_entry(key, self._clock()) is not None

    def put(self, key: str, value: str, ttl_seconds: int) -> None:
        """Store a value, as Redis SET with EX does."""

        with self._lock:
            now = self._clock()
            self._entries.pop(key, None)
            self._insert(key, (value, now + ttl_seconds), now)

    def get(self, key: str) -> str | None:
        with self._lock:
            entry = self._live_entry(key, self._clock())
            return None if entry is None else entry[0]

    def add(self, key: str, ttl_seconds: int) -> bool:
        """Redis SET NX: store the key unless it is live; True if stored."""

        with self._lock:
            now = self._clock()
            if self._live_entry(key, now) is not None:
                return False
            self._insert(key, (1, now + ttl_seconds), now)
            return True

    def discard(self, key: str) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def _live_entry(self, key: str, now: float) -> tuple[int | str, float] | None:
        entry = self._entries.get(key)

        if entry is not None and entry[1] <= now:
            del self._entries[key]
            return None

        return entry

    def _insert(self, key: str, entry: tuple[int | str, float], now: float) -> None:
        if len(self._entries) >= self._max_entries:
            for expired_key in [k for k, (_, expires) in self._entries.items() if expires <= now]:
                del self._entries[expired_key]

        while len(self._entries) >= self._max_entries:
            self._entries.popitem(last=False)

        self._entries[key] = entry
