"""question_families repository (implementation-plan.md 0.4).

A family is the generative template behind question variants. Visibility rules
honor expert decision D2 (Phase 1 = isolated user data):
  - scope "seed": expert/LLM-drafted from public syllabus content, user_id NULL
    -> visible to every user (shared knowledge, not user data).
  - scope "user": derived from a user's uploaded paper, user_id set
    -> visible only to that user (no cross-tenant pooling in Phase 1).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from app.repositories import base

TABLE = "question_families"


def get(family_id: str) -> Optional[Dict[str, Any]]:
    return base.get_by_id(TABLE, family_id)


def _visible_to(row: Dict[str, Any], user_id: str) -> bool:
    owner = str(row.get("user_id") or "")
    if not owner:
        return True  # seed families are shared
    return owner == str(user_id)


def list_seeds() -> List[Dict[str, Any]]:
    return [r for r in base.select_eq(TABLE, "scope", "seed") if not r.get("user_id")]


def list_for_user(user_id: str) -> List[Dict[str, Any]]:
    """Families this user may see: all seeds + their own derived families."""
    seen: Dict[str, Dict[str, Any]] = {}
    for row in base.select_eq(TABLE, "scope", "seed"):
        if row.get("id"):
            seen[str(row["id"])] = row
    for row in base.select_eq(TABLE, "user_id", user_id):
        if row.get("id") and _visible_to(row, user_id):
            seen[str(row["id"])] = row
    return list(seen.values())


def find_by_hash(normalized_hash: str, user_id: str) -> Optional[Dict[str, Any]]:
    """First family with this normalized hash that the user may see."""
    for row in base.select_eq(TABLE, "normalized_hash", normalized_hash):
        if _visible_to(row, user_id):
            return row
    return None


def seed_exists(normalized_hash: str) -> bool:
    for row in base.select_eq(TABLE, "normalized_hash", normalized_hash):
        if str(row.get("scope") or "") == "seed" and not row.get("user_id"):
            return True
    return False


def create(data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": str(data.get("id") or uuid.uuid4()),
        "scope": data.get("scope") or "user",
        "canonical_text": data.get("canonical_text") or "",
        "normalized_hash": data.get("normalized_hash") or "",
        "topic": data.get("topic"),
        "bloom_level": data.get("bloom_level"),
        "command_verb": data.get("command_verb"),
        "marks_typical": data.get("marks_typical"),
        "difficulty": data.get("difficulty"),
        "seed_source": data.get("seed_source"),
        "created_at": now,
    }
    # Optional scoping keys — only sent when present so PyroCore never sees
    # unknown null columns on older rows.
    for key in ("user_id", "subject_id", "branch"):
        if data.get(key) is not None:
            row[key] = data[key]
    for key in ("solvability", "transfer", "study_cost", "stc_cached_at"):
        if data.get(key) is not None:
            row[key] = data[key]
    return base.insert_row(TABLE, row)


def update(family_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in fields.items() if v is not None}
    return base.update_eq(TABLE, "id", family_id, payload)
