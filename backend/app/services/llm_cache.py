"""Cached LLM JSON calls — the free-tier spend guard (implementation-plan.md 0.3).

Every Phase 0/1 LLM call (family assignment, rubric/distractor generation,
later S/T/C estimation) goes through :func:`cached_json` so the same prompt is
ever only paid once:

    result = cached_json("family", question_id, prompt, lambda: llm(prompt))

On a cache miss ``fn`` is called and its dict/list result is persisted to the
``llm_cache`` table; on a hit the stored response is returned with zero API
usage. ``fn`` returning None/raising is never cached, so transient failures
retry on the next call.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Callable

from app.repositories import llm_cache as llm_cache_repo

logger = logging.getLogger(__name__)


def _coerce(value: Any) -> Any:
    """PyroCore JSON columns come back as dict/list or as a JSON string."""
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except Exception:
            return None
        if isinstance(parsed, (dict, list)):
            return parsed
    return None


def prompt_hash(capability: str, namespace: str, prompt: str) -> str:
    raw = f"{capability}\x00{namespace}\x00{prompt}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def cached_json(
    capability: str,
    namespace: str,
    prompt: str,
    fn: Callable[[], Any],
) -> Any:
    """Return the cached response for this prompt, or compute and store it."""
    key = prompt_hash(capability, namespace, prompt)

    try:
        row = llm_cache_repo.get(capability, key)
    except Exception as e:
        # A cache read failure must not block the call — pay the LLM instead.
        logger.warning("llm_cache read failed (capability=%s): %s", capability, e)
        row = None

    if row is not None:
        cached = _coerce(row.get("response_json"))
        if cached is not None:
            return cached

    response = fn()
    if response is None or not isinstance(response, (dict, list)):
        return response

    try:
        llm_cache_repo.put(capability, key, response)
    except Exception as e:
        # Persist failure still returns the live response — never lose work.
        logger.warning("llm_cache write failed (capability=%s): %s", capability, e)

    return response
