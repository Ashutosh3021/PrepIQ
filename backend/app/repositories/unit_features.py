"""Per-unit feature vectors (government track feature engineering core output).

marks_trend representation: float slope-style signal
  > 0  marks allocation increasing over years
  = 0  flat / insufficient data
  < 0  decreasing
Exact computation lives in a later phase; storage is float only.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from app.repositories import base

TABLE = "unit_features"


def list_for_subject(subject_id: str) -> List[Dict[str, Any]]:
    return base.select_eq(TABLE, "subject_id", subject_id)


def get(row_id: str) -> Optional[Dict[str, Any]]:
    return base.get_by_id(TABLE, row_id)


def get_for_subject_unit(subject_id: str, unit_name: str) -> Optional[Dict[str, Any]]:
    rows = list_for_subject(subject_id)
    for r in rows:
        if str(r.get("unit_name") or "") == str(unit_name):
            return r
    return None


def create(subject_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": str(data.get("id") or uuid.uuid4()),
        "subject_id": subject_id,
        "unit_name": data.get("unit_name") or "Unknown",
        "recurrence_count": int(data.get("recurrence_count") or 0),
        "recency_weight": float(data.get("recency_weight") or 0.0),
        "marks_trend": float(data.get("marks_trend") or 0.0),
        "last_asked_gap": int(data.get("last_asked_gap") or 0),
        "computed_at": data.get("computed_at") or now,
        "created_at": now,
        "updated_at": now,
    }
    return base.insert_row(TABLE, row)


def update(row_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    fields = dict(fields)
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    return base.update_eq(TABLE, "id", row_id, fields)


def upsert_for_subject_unit(subject_id: str, unit_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    existing = get_for_subject_unit(subject_id, unit_name)
    payload = {**data, "unit_name": unit_name}
    if existing:
        updated = update(str(existing["id"]), payload)
        return updated or {**existing, **payload}
    return create(subject_id, payload)


def replace_for_subject(subject_id: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Delete existing feature rows for subject and insert the new set (best-effort)."""
    for old in list_for_subject(subject_id):
        try:
            base.delete_eq(TABLE, "id", str(old.get("id")))
        except Exception:
            pass
    created: List[Dict[str, Any]] = []
    for r in rows:
        created.append(create(subject_id, r))
    return created
