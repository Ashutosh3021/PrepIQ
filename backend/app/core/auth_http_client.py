"""Direct httpx client for PyroCore auth endpoints.

Bypasses the pyronites SDK to give full control over timeouts, response
header inspection, and rate-limit observability. Used as a fallback when
the SDK's exception-based error handling loses header context.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

_PYROCORE_URL = (os.getenv("PYRONITES_URL") or "").rstrip("/")
_PYROCORE_KEY = os.getenv("PYRONITES_KEY", "")

# Longer timeout for auth calls — PyroCore cold-starts can be slow
_AUTH_TIMEOUT = float(os.getenv("AUTH_HTTP_TIMEOUT", "15"))


def _auth_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_PYROCORE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


class AuthHttpClient:
    """Thin wrapper around httpx for PyroCore auth calls with full header logging.

    Every call logs:
      - Request method + path
      - Response status code
      - All rate-limit headers (Retry-After, X-Ratelimit-*, etc.)
      - Response body on error
    """

    def __init__(self) -> None:
        self._base_url = _PYROCORE_URL
        self._client = httpx.Client(
            base_url=self._base_url,
            headers=_auth_headers(),
            timeout=_AUTH_TIMEOUT,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "AuthHttpClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ── auth endpoints ──────────────────────────────────────────────────

    def signup(self, email: str, password: str) -> Tuple[Dict[str, Any], int]:
        """POST /auth/signup → (response_json, status_code)."""
        return self._post("/auth/signup", {"email": email, "password": password})

    def login(self, email: str, password: str) -> Tuple[Dict[str, Any], int]:
        """POST /auth/login → (response_json, status_code)."""
        return self._post("/auth/login", {"email": email, "password": password})

    def me(self, session_token: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
        """GET /auth/me → (response_json, status_code)."""
        headers = {}
        if session_token:
            headers["Cookie"] = f"session_token={session_token}"
        return self._get("/auth/me", headers=headers)

    # ── internals ───────────────────────────────────────────────────────

    def _post(self, path: str, body: Dict[str, Any], extra_headers: Optional[Dict] = None) -> Tuple[Dict[str, Any], int]:
        try:
            response = self._client.post(path, json=body, headers=extra_headers or {})
            self._log_response("POST", path, response)
            return self._parse(response), response.status_code
        except httpx.TimeoutException as e:
            logger.error("[pyrocore-auth] POST %s timed out: %s", path, e)
            raise
        except httpx.HTTPError as e:
            logger.error("[pyrocore-auth] POST %s failed: %s", path, e)
            raise

    def _get(self, path: str, extra_headers: Optional[Dict] = None) -> Tuple[Dict[str, Any], int]:
        try:
            response = self._client.get(path, headers=extra_headers or {})
            self._log_response("GET", path, response)
            return self._parse(response), response.status_code
        except httpx.TimeoutException as e:
            logger.error("[pyrocore-auth] GET %s timed out: %s", path, e)
            raise
        except httpx.HTTPError as e:
            logger.error("[pyrocore-auth] GET %s failed: %s", path, e)
            raise

    def _log_response(self, method: str, path: str, response: httpx.Response) -> None:
        """Log response with all rate-limit headers."""
        watched = {}
        for h in ("retry-after", "x-ratelimit-limit", "x-ratelimit-remaining",
                   "x-ratelimit-reset", "ratelimit-limit", "ratelimit-remaining",
                   "ratelimit-reset"):
            val = response.headers.get(h)
            if val is not None:
                watched[h] = val

        if watched:
            logger.info(
                "[pyrocore-auth] %s %s → %s (headers: %s)",
                method, path, response.status_code, watched,
            )
        else:
            logger.info(
                "[pyrocore-auth] %s %s → %s",
                method, path, response.status_code,
            )

    @staticmethod
    def _parse(response: httpx.Response) -> Dict[str, Any]:
        try:
            return response.json()
        except Exception:
            return {"_raw": response.text, "_status": response.status_code}


# Module-level convenience singleton
_auth_client: Optional[AuthHttpClient] = None


def get_auth_http_client() -> AuthHttpClient:
    global _auth_client
    if _auth_client is None:
        _auth_client = AuthHttpClient()
    return _auth_client
