"""
Pyronites client factory (Phase 3 — project-scoped routing).

Env:
  PYRONITES_URL
  PYRONITES_KEY
  PYRONITES_PROJECT_ID   (optional — when set, routes through project-scoped API)

Usage:
  from app.core.pyronites_client import get_pyronites_client
  client = get_pyronites_client()
  client.table("subjects").select()...
  client.auth.sign_in(email, password)
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Any, Optional

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_client: Any = None


def _require_env() -> tuple[str, str]:
    url = (os.getenv("PYRONITES_URL") or "").strip()
    key = (os.getenv("PYRONITES_KEY") or "").strip()
    if not url or not key:
        raise RuntimeError(
            "Pyronites is not configured. Set PYRONITES_URL and PYRONITES_KEY."
        )
    return url, key


def _get_project_id() -> Optional[str]:
    return (os.getenv("PYRONITES_PROJECT_ID") or "").strip() or None


class _ProjectScopedTransport:
    """Wraps pyronites HttpTransport to rewrite unscoped paths into
    project-scoped paths (e.g. /tables/foo -> /api/projects/{pid}/tables/foo).

    Auth is still handled by the underlying HttpTransport via the Bearer header.
    """

    def __init__(self, wrapped: Any, project_id: str) -> None:
        # Expose inner transport for pyronites internals (config, close, etc.)
        object.__setattr__(self, "_wrapped", wrapped)
        object.__setattr__(self, "_project_id", project_id)
        object.__setattr__(self, "_prefix", f"/api/projects/{project_id}")

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_wrapped"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(object.__getattribute__(self, "_wrapped"), name, value)

    def _rewrite_path(self, path: str) -> str:
        prefix = object.__getattribute__(self, "_prefix")
        # SQL execution: /sql/execute -> /api/projects/{pid}/sql/execute
        if path.startswith("/sql/"):
            return prefix + path
        # Table operations: /tables[...] -> /api/projects/{pid}/tables[...]
        if path.startswith("/tables"):
            return prefix + path
        return path

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        wrapped = object.__getattribute__(self, "_wrapped")
        rewritten = self._rewrite_path(path)
        return wrapped.request(method, rewritten, **kwargs)

    def close(self) -> None:
        object.__getattribute__(self, "_wrapped").close()


def get_pyronites_client() -> Any:
    """
    Return a process-wide Pyronites client (lazy singleton).

    When PYRONITES_PROJECT_ID is set, all table/SQL calls are routed through
    project-scoped endpoints.  Otherwise falls back to legacy unscoped paths.

    Thread-safe for FastAPI sync routes. Raises RuntimeError if env is missing.
    """
    global _client
    if _client is not None:
        return _client
    with _lock:
        if _client is not None:
            return _client
        url, key = _require_env()
        project_id = _get_project_id()
        try:
            from pyronites import create_client
        except ImportError as e:
            raise RuntimeError(
                "pyronites package is not installed. Add 'pyronites' to requirements."
            ) from e
        _client = create_client(url, key)
        if project_id:
            # Swap the HttpTransport for a project-scoped wrapper
            scoped = _ProjectScopedTransport(_client._http, project_id)
            _client._http = scoped
            logger.info(
                "Pyronites client initialised (url=%s, project=%s)",
                url[:48], project_id,
            )
        else:
            logger.info("Pyronites client initialised (url=%s, legacy unscoped)", url[:48])
        return _client


def reset_pyronites_client() -> None:
    """Test helper: drop cached client."""
    global _client
    with _lock:
        _client = None


def pyronites_configured() -> bool:
    return bool((os.getenv("PYRONITES_URL") or "").strip() and (os.getenv("PYRONITES_KEY") or "").strip())
