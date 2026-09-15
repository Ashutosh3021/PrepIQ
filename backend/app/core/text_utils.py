"""Shared text helpers used across PrepIQ services."""
from __future__ import annotations

import re


def strip_fences(raw: str) -> str:
    """Remove markdown code fences wrapping a string (e.g. LLM JSON output)."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()
