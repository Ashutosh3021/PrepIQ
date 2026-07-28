"""
Pyronites client factory (Phase 2).

Env:
  PYRONITES_URL
  PYRONITES_KEY

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


def get_pyronites_client() -> Any:
    """
    Return a process-wide Pyronites client (lazy singleton).

    Thread-safe for FastAPI sync routes. Raises RuntimeError if env is missing.
    """
    global _client
    if _client is not None:
        return _client
    with _lock:
        if _client is not None:
            return _client
        url, key = _require_env()
        try:
            from pyronites import create_client
        except ImportError as e:
            raise RuntimeError(
                "pyronites package is not installed. Add 'pyronites' to requirements."
            ) from e
        _client = create_client(url, key)
        logger.info("Pyronites client initialised (url=%s)", url[:48])
        return _client


def reset_pyronites_client() -> None:
    """Test helper: drop cached client."""
    global _client
    with _lock:
        _client = None


def pyronites_configured() -> bool:
    return bool((os.getenv("PYRONITES_URL") or "").strip() and (os.getenv("PYRONITES_KEY") or "").strip())
