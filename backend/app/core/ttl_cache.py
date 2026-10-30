"""
A small in-process cache whose entries expire after a fixed time.

Zero-budget alternative to a Redis query cache: values live in this
process's memory only. Render runs one API process (start.sh), so a write
that invalidates the cache here takes effect at once; any other process
(the Celery worker) sees the change when its own entry expires. Keep TTLs
short and cache only small values that are read far more often than they
change.

functools.lru_cache is not used for database values: it never expires, so
a value changed in the database (or by another process) would be served
forever.
"""

import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Hashable

_MISSING = object()

# Every cache, so tests can start each case empty (tests/conftest.py).
_all_caches: list["TTLCache"] = []


class TTLCache:
    def __init__(self, *, ttl_seconds: float, max_entries: int = 128) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive.")
        if max_entries <= 0:
            raise ValueError("max_entries must be positive.")
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: OrderedDict[Hashable, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()
        _all_caches.append(self)

    def get(self, key: Hashable, default: Any = None) -> Any:
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return default
            expires_at, value = entry
            if expires_at <= time.monotonic():
                del self._entries[key]
                return default
            self._entries.move_to_end(key)
            return value

    def set(self, key: Hashable, value: Any) -> None:
        with self._lock:
            self._entries[key] = (time.monotonic() + self.ttl_seconds, value)
            self._entries.move_to_end(key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)

    def get_or_load(self, key: Hashable, loader: Callable[[], Any]) -> Any:
        """
        The cached value, or loader()'s result (which is then cached).

        If loader() raises, nothing is cached and the error propagates.
        Two threads that miss at the same moment may both load; the value
        is the same, so that is cheaper than holding the lock during I/O.
        """
        value = self.get(key, _MISSING)
        if value is not _MISSING:
            return value
        value = loader()
        self.set(key, value)
        return value

    def invalidate(self, key: Hashable) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


def clear_all_caches() -> None:
    for cache in _all_caches:
        cache.clear()
