"""Shared helpers for Pyronites table repositories (Fix Phase B safer parsing)."""
from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional

from app.core.pyronites_client import get_pyronites_client

logger = logging.getLogger(__name__)

# PyroCore is rate-limited on free-tier hosting (429 Too Many Requests). A single
# wizard step fires several identical user/profile lookups (auth resolution +
# the endpoint handler + get_by_id's get()/select_eq() fallback), and _retry
# amplifies every logical read into multiple HTTP calls. A short-lived,
# process-local read cache plus request coalescing collapses those into ONE
# remote call — exactly the mitigation PyroCore recommends ("don't poll the same
# endpoint repeatedly", "wait for auth before fetching"). Writes invalidate the
# affected key so reads stay fresh. This is a single-process cache (Render free
# runs one worker/instance), which is sufficient for the rate-limit problem.
_READ_CACHE_TTL = float(os.getenv("PYROCORE_READ_CACHE_TTL", "5"))
_FAIL_CACHE_TTL = float(os.getenv("PYROCORE_FAIL_CACHE_TTL", "1"))
_READ_CACHE_MAX = int(os.getenv("PYROCORE_READ_CACHE_MAX", "2000"))

_MISS = object()   # cached marker for a failed (e.g. 429) read
_UNSET = object()  # "no cache entry" sentinel

_read_cache: Dict[str, tuple[float, Any]] = {}
_read_cache_lock = threading.Lock()
_inflight: Dict[str, threading.Event] = {}
_inflight_lock = threading.Lock()


def _cache_get(key: str, fail_ttl: float) -> Any:
    """Return cached value, or _UNSET if missing/expired. _MISS normalises to None."""
    with _read_cache_lock:
        item = _read_cache.get(key)
        if item is None:
            return _UNSET
        ts, val = item
        ttl = fail_ttl if val is _MISS else _READ_CACHE_TTL
        if (time.monotonic() - ts) >= ttl:
            _read_cache.pop(key, None)
            return _UNSET
        return None if val is _MISS else val


def _cache_set(key: str, val: Any) -> None:
    with _read_cache_lock:
        _read_cache[key] = (time.monotonic(), val)
        # Bound the cache so un-read keys can't accumulate into a memory leak.
        # Evict the oldest entries (by insertion timestamp) when over the limit.
        if len(_read_cache) > _READ_CACHE_MAX:
            overflow = len(_read_cache) - _READ_CACHE_MAX
            oldest = sorted(_read_cache.items(), key=lambda kv: kv[1][0])[:overflow]
            for k, _ in oldest:
                _read_cache.pop(k, None)


def _cached(key: str, producer, fail_ttl: float = _FAIL_CACHE_TTL) -> Any:
    """Run `producer()` once per key, coalescing concurrent calls and caching
    the result (or a short-lived failure marker) to avoid repeated remote hits."""
    cached = _cache_get(key, fail_ttl)
    if cached is not _UNSET:
        return cached

    # Wait for an in-flight fetch of the same key, then re-check the cache.
    ev = _inflight.get(key)
    if ev is not None:
        ev.wait()
        cached = _cache_get(key, fail_ttl)
        if cached is not _UNSET:
            return cached

    # Claim the slot so only one producer runs for this key. Re-check the cache
    # after acquiring the lock (whether or not another producer was in-flight)
    # so we never run producer() twice for the same key.
    with _inflight_lock:
        existing = _inflight.get(key)
        if existing is not None:
            existing.wait()
        cached = _cache_get(key, fail_ttl)
        if cached is not _UNSET:
            return cached
        ev = threading.Event()
        _inflight[key] = ev

    try:
        val = producer()
        _cache_set(key, val if val is not None else _MISS)
        return val
    except Exception:
        _cache_set(key, _MISS)
        raise
    finally:
        with _inflight_lock:
            _inflight.pop(key, None)
        ev.set()


def _invalidate(table_name: str, row_id: Any) -> None:
    """Drop cached reads for a row after a successful write."""
    rid = str(row_id)
    prefixes = (
        f"get:{table_name}:{rid}",
        f"select:{table_name}:id:{rid}",
    )
    with _read_cache_lock:
        for k in list(_read_cache.keys()):
            if k in prefixes or k == f"select:{table_name}:id:{rid}":
                _read_cache.pop(k, None)

# PyroCore free-tier rate limits surface as 429 "Too Many Requests". A short,
# bounded retry with backoff lets transient throttling recover instead of
# bubbling up as a 500 to the caller.
_RATE_LIMIT_MAX_RETRIES = 3
_RATE_LIMIT_BACKOFF = 0.5


def _is_rate_limited(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "too many requests" in msg


def _retry(fn):
    """Run fn() with bounded retry on 429 rate-limit errors."""
    last = None
    for attempt in range(_RATE_LIMIT_MAX_RETRIES):
        try:
            return fn()
        except Exception as e:
            if _is_rate_limited(e) and attempt < _RATE_LIMIT_MAX_RETRIES - 1:
                time.sleep(_RATE_LIMIT_BACKOFF * (attempt + 1))
                last = e
                continue
            raise
    raise last


def _as_list(result: Any) -> List[Dict[str, Any]]:
    if result is None:
        return []
    if isinstance(result, list):
        return [r for r in result if isinstance(r, dict)]
    if isinstance(result, dict):
        for key in ("data", "rows", "items", "results"):
            if key in result and isinstance(result[key], list):
                return [r for r in result[key] if isinstance(r, dict)]
        # single row object
        if "id" in result or any(k in result for k in ("email", "name", "subject_id", "user_id")):
            return [result]
        return []
    # object with .data
    data = getattr(result, "data", None)
    if data is not None:
        return _as_list(data)
    return []


def _as_one(result: Any) -> Optional[Dict[str, Any]]:
    rows = _as_list(result)
    return rows[0] if rows else None


def table(name: str) -> Any:
    return get_pyronites_client().table(name)


def select_eq(table_name: str, column: str, value: Any) -> List[Dict[str, Any]]:
    key = f"select:{table_name}:{column}:{value}"

    def _produce() -> List[Dict[str, Any]]:
        try:
            q = table(table_name).select()
            if hasattr(q, "eq"):
                q = q.eq(column, value)
            result = _retry(lambda: q.execute()) if hasattr(q, "execute") else q
            return _as_list(result)
        except Exception as e:
            logger.error("select_eq %s.%s=%s failed: %s", table_name, column, value, e)
            raise

    try:
        return _cached(key, _produce)
    except Exception:
        # Failure was cached briefly; surface empty rather than 500 to caller.
        return []


def select_all(table_name: str) -> List[Dict[str, Any]]:
    try:
        q = table(table_name).select()
        result = _retry(lambda: q.execute()) if hasattr(q, "execute") else q
        return _as_list(result)
    except Exception as e:
        logger.error("select_all %s failed: %s", table_name, e)
        raise


def get_by_id(table_name: str, row_id: str) -> Optional[Dict[str, Any]]:
    key = f"get:{table_name}:{row_id}"

    def _produce() -> Any:
        t = table(table_name)
        if hasattr(t, "get"):
            try:
                return _retry(lambda: t.get(row_id))
            except Exception:
                return None
        return None

    try:
        direct = _cached(key, _produce)
    except Exception:
        direct = None
    one = _as_one(direct)
    if one:
        return one
    try:
        rows = select_eq(table_name, "id", row_id)
        return rows[0] if rows else None
    except Exception as e:
        logger.error("get_by_id %s/%s failed: %s", table_name, row_id, e)
        return None


def insert_row(table_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        t = table(table_name)
        result = t.insert(payload)
        if hasattr(result, "execute"):
            result = _retry(lambda: result.execute())
        row = _as_one(result)
        if row:
            return row
        if isinstance(result, dict):
            # merge so id from server wins if present
            merged = dict(payload)
            merged.update(result)
            _invalidate(table_name, merged.get("id", payload.get("id")))
            return merged
        _invalidate(table_name, payload.get("id"))
        return payload
    except Exception as e:
        logger.error("insert %s failed: %s", table_name, e)
        raise


def update_eq(table_name: str, column: str, value: Any, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        t = table(table_name)
        q = t.update(payload)
        if hasattr(q, "eq"):
            q = q.eq(column, value)
        result = _retry(lambda: q.execute()) if hasattr(q, "execute") else q
        row = _as_one(result)
        if row:
            _invalidate(table_name, value)
            return row
        # fallback read
        if column == "id":
            return get_by_id(table_name, str(value)) or {**payload, column: value}
        return payload
    except Exception as e:
        logger.error("update %s failed: %s", table_name, e)
        raise


def delete_eq(table_name: str, column: str, value: Any) -> bool:
    try:
        t = table(table_name)
        q = t.delete()
        if hasattr(q, "eq"):
            q = q.eq(column, value)
        if hasattr(q, "execute"):
            _retry(lambda: q.execute())
        _invalidate(table_name, value)
        return True
    except Exception as e:
        logger.error("delete %s failed: %s", table_name, e)
        raise
