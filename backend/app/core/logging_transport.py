"""HTTP transport wrapper that logs rate-limit headers and captures Retry-After.

Wraps the pyronites SDK transport so every outbound call to PyroCore has its
response headers logged (X-RateLimit-Remaining, Retry-After, etc.) and the
most recent Retry-After value is stored in a thread-local variable for the
retry logic to consume.
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Thread-local storage for the latest Retry-After value from a 429 response.
_retry_after_tls = threading.local()


def get_last_retry_after() -> Optional[float]:
    """Return the Retry-After value captured by the transport, or None."""
    return getattr(_retry_after_tls, "value", None)


def _set_retry_after(value: float) -> None:
    _retry_after_tls.value = value


def _clear_retry_after() -> None:
    _retry_after_tls.value = None


# Headers we always want to log when present on responses.
_WATCHED_HEADERS = frozenset({
    "retry-after",
    "x-ratelimit-limit",
    "x-ratelimit-remaining",
    "x-ratelimit-reset",
    "x-ratelimit-reset-after",
    "ratelimit-limit",
    "ratelimit-remaining",
    "ratelimit-reset",
})


class LoggingTransport:
    """Transparent proxy that logs response headers and captures Retry-After.

    Usage::

        scoped = _ProjectScopedTransport(client._http, project_id)
        client._http = LoggingTransport(scoped)  # wraps the existing transport
    """

    def __init__(self, wrapped: Any) -> None:
        object.__setattr__(self, "_wrapped", wrapped)

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_wrapped"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(object.__getattribute__(self, "_wrapped"), name, value)

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        wrapped = object.__getattribute__(self, "_wrapped")
        response = wrapped.request(method, path, **kwargs)

        # The pyronites SDK returns a requests/httpx Response-like object.
        # Try to extract headers from it.
        headers = self._extract_headers(response)
        if not headers:
            return response

        status_code = getattr(response, "status_code", None)

        # Log watched headers on every response
        logged = {}
        for h in _WATCHED_HEADERS:
            val = headers.get(h) or headers.get(h.replace("-", "_"))
            if val is not None:
                logged[h] = val

        if logged:
            logger.info(
                "[pyrocore] %s %s → %s headers: %s",
                method, path, status_code, logged,
            )

        # On 429, capture Retry-After for the retry logic
        if status_code == 429 or self._looks_rate_limited(response):
            retry_after = headers.get("retry-after") or headers.get("Retry-After")
            if retry_after is not None:
                try:
                    _set_retry_after(float(retry_after))
                    logger.warning(
                        "[pyrocore] 429 on %s %s — Retry-After: %ss",
                        method, path, retry_after,
                    )
                except (ValueError, TypeError):
                    pass
            else:
                logger.warning(
                    "[pyrocore] 429 on %s %s — no Retry-After header",
                    method, path,
                )

        return response

    def close(self) -> None:
        object.__getattribute__(self, "_wrapped").close()

    @staticmethod
    def _extract_headers(response: Any) -> dict:
        """Pull headers dict from various response object shapes."""
        # requests/httpx Response
        h = getattr(response, "headers", None)
        if h is not None:
            if isinstance(h, dict):
                return h
            # Mapping-like (httpx.Headers, requests.structures.CaseInsensitiveDict)
            if hasattr(h, "items"):
                return dict(h.items())
        # Fallback: try response.request.headers? No, we want response headers.
        return {}

    @staticmethod
    def _looks_rate_limited(response: Any) -> bool:
        """Quick heuristic: does the response look like a 429?"""
        code = getattr(response, "status_code", None)
        if code == 429:
            return True
        body = getattr(response, "text", "") or ""
        if isinstance(body, str) and "too many requests" in body.lower():
            return True
        return False
