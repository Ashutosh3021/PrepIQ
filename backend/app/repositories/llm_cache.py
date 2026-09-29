"""llm_cache repository — free-tier LLM response cache (implementation-plan.md 0.3).

Rows are keyed by (capability, prompt_hash) where prompt_hash is a sha256 of
capability+namespace+prompt, so a lookup by prompt_hash alone is unique. One
LLM call is ever paid per distinct prompt (family assignment, rubrics, S/T/C).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

from app.repositories import base

TABLE = "llm_cache"


def get(capability: str, prompt_hash: str) -> Optional[Dict[str, Any]]:
    rows = base.select_eq(TABLE, "prompt_hash", prompt_hash)
    for row in rows:
        if str(row.get("capability") or "") == capability:
            return row
    return None


def put(capability: str, prompt_hash: str, response: Any) -> Dict[str, Any]:
    row = {
        "id": str(uuid.uuid4()),
        "capability": capability,
        "prompt_hash": prompt_hash,
        "response_json": response,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return base.insert_row(TABLE, row)
