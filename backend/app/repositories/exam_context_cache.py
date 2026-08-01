"""Shared exam-level context (NEET/JEE). Keyed by exam_name, not user/subject."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from app.repositories import base

TABLE = "exam_context_cache"


def get(row_id: str) -> Optional[Dict[str, Any]]:
    return base.get_by_id(TABLE, row_id)


def get_by_exam_name(exam_name: str) -> Optional[Dict[str, Any]]:
    key = (exam_name or "").strip()
    if not key:
        return None
    rows = base.select_eq(TABLE, "exam_name", key)
    if not rows:
        # case-insensitive fallback
        all_rows = base.select_all(TABLE)
        rows = [r for r in all_rows if str(r.get("exam_name") or "").lower() == key.lower()]
    if not rows:
        return None

    def _key(r: Dict[str, Any]) -> str:
        return str(r.get("fetched_at") or r.get("updated_at") or "")

    rows.sort(key=_key, reverse=True)
    return rows[0]


def list_all() -> List[Dict[str, Any]]:
    return base.select_all(TABLE)


def create(data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": str(data.get("id") or uuid.uuid4()),
        "exam_name": str(data.get("exam_name") or "").strip(),
        "context_summary": data.get("context_summary") or "",
        "fetched_at": data.get("fetched_at") or now,
        "created_at": now,
        "updated_at": now,
    }
    return base.insert_row(TABLE, row)


def update(row_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    fields = dict(fields)
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    return base.update_eq(TABLE, "id", row_id, fields)


def upsert_by_exam_name(exam_name: str, context_summary: str, fetched_at: Optional[str] = None) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    existing = get_by_exam_name(exam_name)
    payload = {
        "exam_name": exam_name.strip(),
        "context_summary": context_summary,
        "fetched_at": fetched_at or now,
    }
    if existing:
        updated = update(str(existing["id"]), payload)
        return updated or {**existing, **payload}
    return create(payload)
