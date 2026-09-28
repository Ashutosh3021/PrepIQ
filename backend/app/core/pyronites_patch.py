"""Compatibility patches for the installed ``pyronites`` SDK.

pyronites 1.2.0 introduced two process-wide bugs that break any multi-user
FastAPI deployment (see backend/app/core/pyronites_client.py, which hands out a
single shared client):

1. ``HttpTransport.request`` coalesces requests keyed on
   ``METHOD + path + params`` only (the request body is not part of the key) and
   never removes completed entries from ``_inflight``. The first *successful*
   response for a path is therefore replayed forever and the underlying HTTP
   request is never sent again:

     * ``POST /auth/signup`` → every later signup returns user #1's identity
       and creates no account;
     * ``POST /auth/login``  → every later login returns user #1's token;
     * ``POST /tables/<t>``  → every later write returns the first write's
       response while silently persisting nothing.

   pyronites 1.1.0 had no coalescing at all — it simply performed the request.

2. ``AuthClient.user()`` caches the identity for 30s on the shared client, so
   one user's identity can be returned to another user's request.

Both are corrected here. The patches are idempotent, version-aware (they no-op
if a future release fixes the underlying code) and are installed by
``app.core.pyronites_client`` before the shared client is created.

Repository-level reads keep their own short-lived cache/coalescing in
``app.repositories.base`` — that layer keys on the full query and expires, so
it does not inherit this bug.
"""
from __future__ import annotations

import inspect
import logging
import threading

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_applied = False


def _patched_request(self, method, path, *, json=None, params=None, files=None, data=None):
    """Send every request (no response replay).

    Mirrors pyronites 1.1.0 behaviour: normalise the path, then delegate to
    ``_do_request`` which owns retries, rate-limit backoff and error mapping.
    """
    if not path.startswith("/"):
        path = "/" + path
    return self._do_request(method, path, json=json, params=params, files=files, data=data)


def _uncached_user(self):
    """Always resolve the session identity from PyroCore.

    pyronites 1.2.0 returns ``self._user`` when younger than 30s, which on a
    shared client can be a different user's identity. Refresh every time.
    """
    from pyronites.errors import AuthError

    try:
        data = self._http.request("GET", "/auth/me")
    except AuthError:
        self._user = None
        self._user_ts = 0.0
        return None
    self._user = data
    self._user_ts = 0.0
    return data


def apply_pyronites_patches() -> bool:
    """Install the patches. Safe to call repeatedly; returns True when applied."""
    global _applied
    if _applied:
        return True

    with _lock:
        if _applied:
            return True
        try:
            from pyronites.auth import AuthClient
            from pyronites.http import HttpTransport
        except Exception as e:  # pragma: no cover - SDK missing is a config error
            logger.warning("[pyronites-patch] could not import pyronites: %s", e)
            return False

        try:
            request_src = inspect.getsource(HttpTransport.request)
        except Exception:
            request_src = ""
        if "_inflight" in request_src:
            HttpTransport.request = _patched_request  # type: ignore[method-assign]
            logger.info(
                "[pyronites-patch] response-replay bug found in HttpTransport.request "
                "— patched to always send the request"
            )
        else:
            logger.info("[pyronites-patch] HttpTransport.request is clean — no patch needed")

        try:
            user_src = inspect.getsource(AuthClient.user)
        except Exception:
            user_src = ""
        if "_USER_TTL" in user_src:
            AuthClient.user = _uncached_user  # type: ignore[method-assign]
            logger.info(
                "[pyronites-patch] 30s cross-request identity cache found in "
                "AuthClient.user — patched to resolve fresh"
            )
        else:
            logger.info("[pyronites-patch] AuthClient.user is clean — no patch needed")

        _applied = True
        return True
