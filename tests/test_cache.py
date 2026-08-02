from athena.cache import BoundedCache


def test_bounded_cache_tracks_hits_misses_evictions_and_invalidations() -> None:
    cache: BoundedCache[str, str] = BoundedCache(2)

    assert cache.get("missing") is None
    cache.put("one", "1", compute_ms=4.0)
    cache.put("two", "2", compute_ms=2.0)
    assert cache.get("one") == "1"
    cache.put("three", "3")

    assert cache.get("two") is None
    stats = cache.stats()
    assert stats.entries == 2
    assert stats.hits == 1
    assert stats.misses == 2
    assert stats.evictions == 1
    assert stats.average_time_saved_ms == 4.0

    cache.invalidate()
    assert cache.stats().entries == 0
    assert cache.stats().invalidations == 1


def test_zero_capacity_cache_is_deterministically_disabled() -> None:
    cache: BoundedCache[str, int] = BoundedCache(0)
    assert cache.get_or_compute("value", lambda: 42) == 42
    assert cache.get_or_compute("value", lambda: 43) == 43
    assert cache.stats().entries == 0
    assert cache.stats().misses == 2
