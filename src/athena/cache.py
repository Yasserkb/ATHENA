from __future__ import annotations

import sys
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


@dataclass(frozen=True, slots=True)
class CacheStats:
    hits: int
    misses: int
    entries: int
    max_entries: int
    evictions: int
    invalidations: int
    approximate_bytes: int
    average_time_saved_ms: float

    def to_dict(self) -> dict[str, int | float]:
        requests = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / requests, 4) if requests else 0.0,
            "entries": self.entries,
            "max_entries": self.max_entries,
            "evictions": self.evictions,
            "invalidations": self.invalidations,
            "approximate_bytes": self.approximate_bytes,
            "average_time_saved_ms": round(self.average_time_saved_ms, 4),
        }


@dataclass(slots=True)
class _Entry(Generic[V]):
    value: V
    compute_ms: float
    approximate_bytes: int


class BoundedCache(Generic[K, V]):
    """Small thread-safe LRU with deterministic bounds and lightweight observability."""

    def __init__(self, max_entries: int) -> None:
        self.max_entries = max(0, max_entries)
        self._entries: OrderedDict[K, _Entry[V]] = OrderedDict()
        self._lock = RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._invalidations = 0
        self._saved_ms = 0.0

    def get(self, key: K) -> V | None:
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._misses += 1
                return None
            self._entries.move_to_end(key)
            self._hits += 1
            self._saved_ms += entry.compute_ms
            return entry.value

    def put(self, key: K, value: V, compute_ms: float = 0.0) -> None:
        if self.max_entries == 0:
            return
        approximate_bytes = sys.getsizeof(key) + sys.getsizeof(value)
        with self._lock:
            self._entries[key] = _Entry(value, max(0.0, compute_ms), approximate_bytes)
            self._entries.move_to_end(key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)
                self._evictions += 1

    def get_or_compute(self, key: K, compute: Callable[[], V]) -> V:
        cached = self.get(key)
        if cached is not None:
            return cached
        started = time.perf_counter()
        value = compute()
        self.put(key, value, (time.perf_counter() - started) * 1000)
        return value

    def invalidate(self) -> None:
        with self._lock:
            if self._entries:
                self._entries.clear()
                self._invalidations += 1

    def stats(self) -> CacheStats:
        with self._lock:
            approximate_bytes = sum(entry.approximate_bytes for entry in self._entries.values())
            return CacheStats(
                self._hits,
                self._misses,
                len(self._entries),
                self.max_entries,
                self._evictions,
                self._invalidations,
                approximate_bytes,
                self._saved_ms / self._hits if self._hits else 0.0,
            )
