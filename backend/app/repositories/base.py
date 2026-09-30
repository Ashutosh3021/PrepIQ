"""Shared helpers for Pyronites table repositories (Fix Phase B safer parsing)."""
from __future__ import annotations

import logging
import os
import re
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


class CachedReadFailed(RuntimeError):
    """A recent read of the same key failed and its failure marker is still live.

    Raised (rather than returning ``None``) so callers keep their normal
    empty-result contract — returning ``None`` from a ``List``-typed helper is
    what turned one PyroCore hiccup into a 500 on ``/dashboard/stats`` and
    ``/subjects``.
    """


def is_auth_error(exc: BaseException) -> bool:
    """True when PyroCore rejected our credentials/scope — a configuration
    problem, not a data problem.

    Auth failures must never degrade to an empty result: a dead PYRONITES_KEY
    that turns every list into ``[]`` looks exactly like "user has no data"
    and produces no error anywhere. Transient failures (429/5xx/timeouts) still
    degrade as before; only rejected credentials surface loudly.
    """
    if type(exc).__name__ in ("AuthError", "AuthenticationError"):
        return True
    text = str(exc).lower()
    if "missing or invalid authentication" in text:
        return True
    if "unauthorized" in text or "forbidden" in text:
        return True
    return bool(re.search(r"\b(?:401|403)\b", text))


def _cache_get(key: str, fail_ttl: float) -> Any:
    """Return cached value, _MISS for a live failure marker, or _UNSET if absent."""
    with _read_cache_lock:
        item = _read_cache.get(key)
        if item is None:
            return _UNSET
        ts, val = item
        ttl = fail_ttl if val is _MISS else _READ_CACHE_TTL
        if (time.monotonic() - ts) >= ttl:
            _read_cache.pop(key, None)
            return _UNSET
        return val


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
    the result (or a short-lived failure marker) to avoid repeated remote hits.

    A cached failure marker raises :class:`CachedReadFailed` so callers can
    apply their own empty/fallback semantics instead of receiving ``None``.
    """
    cached = _cache_get(key, fail_ttl)
    if cached is _MISS:
        raise CachedReadFailed(key)
    if cached is not _UNSET:
        return cached

    # Wait for an in-flight fetch of the same key, then re-check the cache.
    ev = _inflight.get(key)
    if ev is not None:
        ev.wait()
        cached = _cache_get(key, fail_ttl)
        if cached is _MISS:
            raise CachedReadFailed(key)
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
        if cached is _MISS:
            raise CachedReadFailed(key)
        if cached is not _UNSET:
            return cached
        ev = threading.Event()
        _inflight[key] = ev

    try:
        val = producer()
        _cache_set(key, val)
        return val
    except Exception as e:
        # Never cache rejected credentials: a failure marker would turn a
        # config error into a short run of silently-empty results.
        if not is_auth_error(e):
            _cache_set(key, _MISS)
        raise
    finally:
        with _inflight_lock:
            _inflight.pop(key, None)
        ev.set()


def _invalidate(table_name: str, row_id: Any = None) -> None:
    """Drop every cached read for a table after a successful write.

    Clearing by table (rather than by row id) also catches lookups keyed on
    non-id columns — e.g. ``select:user_profiles:email:...`` would otherwise
    keep serving the pre-write row for the rest of the read TTL.
    """
    prefixes = (f"get:{table_name}:", f"select:{table_name}:")
    with _read_cache_lock:
        for k in list(_read_cache.keys()):
            if k.startswith(prefixes):
                _read_cache.pop(k, None)

# The pyronites SDK (v1.2.0+) handles 429 retries and Retry-After internally.
# We do NOT add another retry layer — that would double the request count.
# The circuit breaker is the only additional protection we layer on top.
_RATE_LIMIT_MAX_RETRIES = 3  # kept for reference, not used in retry logic


def _is_rate_limited(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "too many requests" in msg


def _retry(fn):
    """Call fn() with circuit breaker protection.

    The pyronites SDK handles 429 retries internally. This wrapper only
    checks the circuit breaker and records success/failure.

    Returns None (not a row) when the breaker is open — callers must treat
    that as "no data", never as a successful write. Use :func:`_retry_write`
    on write paths so an open breaker raises instead of pretending to succeed.
    """
    from app.core.circuit_breaker import pyrocore_breaker

    if pyrocore_breaker.is_open:
        return None  # caller gets None/empty, consistent with failure path

    try:
        result = fn()
        pyrocore_breaker.record_success()
        return result
    except Exception as e:
        if _is_rate_limited(e):
            pyrocore_breaker.record_failure()
        raise


def _retry_write(fn):
    """Like :func:`_retry`, but an open circuit breaker raises.

    Writes must never report success without reaching PyroCore — that is how
    "saved" wizard steps and profiles went missing.
    """
    from app.core.circuit_breaker import pyrocore_breaker

    if pyrocore_breaker.is_open:
        raise RuntimeError("PyroCore circuit breaker is open — write not attempted")

    try:
        result = fn()
        pyrocore_breaker.record_success()
        return result
    except Exception as e:
        if _is_rate_limited(e):
            pyrocore_breaker.record_failure()
        raise


def _is_error_shape(row: Dict[str, Any]) -> bool:
    """True for an API error payload rather than a data row.

    Errors look like ``{"code": 404, "message": "..."}`` (or ``{"error": ...}``)
    and never carry row identity. Data rows do — and some legitimately carry
    their own ``code``/``message`` columns (``subjects.code``, chat messages),
    which the old ``"code" not in row`` heuristic silently dropped, making
    freshly created rows vanish from list results.
    """
    if any(k in row for k in ("id", "email", "name", "subject_id", "user_id", "created_at")):
        return False
    return any(k in row for k in ("message", "error", "code", "status"))


def _as_list(result: Any) -> List[Dict[str, Any]]:
    if result is None:
        return []
    if isinstance(result, list):
        return [r for r in result if isinstance(r, dict) and not _is_error_shape(r)]
    if isinstance(result, dict):
        for key in ("data", "rows", "items", "results"):
            if key in result and isinstance(result[key], list):
                return [
                    r for r in result[key] if isinstance(r, dict) and not _is_error_shape(r)
                ]
        # single row object — but reject error shapes
        if _is_error_shape(result):
            return []
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


# PyroCore's REST backend pages results at 50 rows by default and rejects
# query.limit > 200 (422). A paper with 110 questions, a user with >50 mocks or
# predictions, etc. was therefore silently truncated on every read. All selects
# now paginate in 200-row pages until a short page comes back.
_PAGE_SIZE = 200
_MAX_PAGES = 50  # safety valve: 10k rows per logical read


def _select_pages(build_query, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
    """Execute a select, following offset/limit pages until exhaustion.

    ``build_query()`` must return a fresh TableQuery each call (offset and
    limit are set on it). Returns [] when the circuit breaker is open —
    matching the old single-shot behaviour.
    """
    rows: List[Dict[str, Any]] = []
    offset = 0
    while offset < _PAGE_SIZE * _MAX_PAGES:
        q = build_query()
        if hasattr(q, "limit"):
            q = q.limit(_PAGE_SIZE)
        if offset and hasattr(q, "offset"):
            q = q.offset(offset)
        chunk = _retry(lambda: q.execute()) if hasattr(q, "execute") else q
        chunk = _as_list(chunk)
        rows.extend(chunk)
        if len(chunk) < _PAGE_SIZE:
            break
        offset += _PAGE_SIZE
    else:
        logger.warning(
            "_select_pages: hit page cap (%d rows) — results may be truncated",
            _PAGE_SIZE * _MAX_PAGES,
        )
    if max_rows is not None:
        return rows[:max_rows]
    return rows


def select_eq(table_name: str, column: str, value: Any) -> List[Dict[str, Any]]:
    key = f"select:{table_name}:{column}:{value}"

    def _produce() -> List[Dict[str, Any]]:
        try:
            def _build():
                q = table(table_name).select()
                if hasattr(q, "eq"):
                    q = q.eq(column, value)
                return q
            return _select_pages(_build)
        except Exception as e:
            logger.error("select_eq %s.%s=%s failed: %s", table_name, column, value, e)
            raise

    try:
        return _cached(key, _produce)
    except Exception as e:
        if is_auth_error(e):
            raise
        # Failure was cached briefly; surface empty rather than 500 to caller.
        return []


def select_all(table_name: str, limit: int = 500) -> List[Dict[str, Any]]:
    try:
        return _select_pages(lambda: table(table_name).select(), max_rows=limit)
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
            except Exception as e:
                if is_auth_error(e):
                    raise
                return None
        return None

    try:
        direct = _cached(key, _produce)
    except Exception as e:
        if is_auth_error(e):
            raise
        direct = None
    one = _as_one(direct)
    if one:
        return one
    try:
        rows = select_eq(table_name, "id", row_id)
        return rows[0] if rows else None
    except Exception as e:
        if is_auth_error(e):
            raise
        logger.error("get_by_id %s/%s failed: %s", table_name, row_id, e)
        return None


def insert_row(table_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        t = table(table_name)
        result = t.insert(payload)
        if hasattr(result, "execute"):
            result = _retry_write(lambda: result.execute())
        row = _as_one(result)
        # Always drop cached reads for this id: a stale "row absent" entry is
        # what makes a fresh insert look like it never happened.
        _invalidate(table_name, (row or {}).get("id") or payload.get("id"))
        if row:
            return row
        if isinstance(result, dict):
            # merge so id from server wins if present
            merged = dict(payload)
            merged.update(result)
            return merged
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
        result = _retry_write(lambda: q.execute()) if hasattr(q, "execute") else q
        row = _as_one(result)
        _invalidate(table_name, (row or {}).get("id") or value)
        if row:
            return row
        # fallback read — invalidate first so it cannot serve the pre-write row
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
            _retry_write(lambda: q.execute())
        _invalidate(table_name, value)
        return True
    except Exception as e:
        logger.error("delete %s failed: %s", table_name, e)
        raise
