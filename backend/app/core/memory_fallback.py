"""
In-process stand-in for Redis keys while Redis is unreachable.

Rate limits and token revocation fall back to this store instead of failing
open. Render runs the API as a single process, so counts kept here are the
real counts for the whole deployment; they reset when the process restarts.

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
        self._entries: OrderedDict[str, tuple[int, float]] = OrderedDict()
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

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def _live_entry(self, key: str, now: float) -> tuple[int, float] | None:
        entry = self._entries.get(key)

        if entry is not None and entry[1] <= now:
            del self._entries[key]
            return None

        return entry

    def _insert(self, key: str, entry: tuple[int, float], now: float) -> None:
        if len(self._entries) >= self._max_entries:
            for expired_key in [k for k, (_, expires) in self._entries.items() if expires <= now]:
                del self._entries[expired_key]

        while len(self._entries) >= self._max_entries:
            self._entries.popitem(last=False)

        self._entries[key] = entry
