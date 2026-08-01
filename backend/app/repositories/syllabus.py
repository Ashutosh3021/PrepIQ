"""Syllabus taxonomy (government track). One row per subject."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from app.repositories import base

TABLE = "syllabus"


def get(syllabus_id: str) -> Optional[Dict[str, Any]]:
    return base.get_by_id(TABLE, syllabus_id)


def get_for_subject(subject_id: str) -> Optional[Dict[str, Any]]:
    rows = base.select_eq(TABLE, "subject_id", subject_id)
    if not rows:
        return None

    def _key(r: Dict[str, Any]) -> str:
        return str(r.get("extracted_at") or r.get("created_at") or "")

    rows.sort(key=_key, reverse=True)
    return rows[0]


def create(subject_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    taxonomy = data.get("extracted_taxonomy")
    if taxonomy is None:
        taxonomy = []
    row = {
        "id": str(data.get("id") or uuid.uuid4()),
        "subject_id": subject_id,
        "raw_pdf_ref": data.get("raw_pdf_ref"),
        "extracted_taxonomy": taxonomy,
        "extracted_at": data.get("extracted_at"),
        "created_at": now,
        "updated_at": now,
    }
    return base.insert_row(TABLE, row)


def update(syllabus_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    fields = dict(fields)
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    return base.update_eq(TABLE, "id", syllabus_id, fields)


def upsert_for_subject(subject_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    existing = get_for_subject(subject_id)
    if existing:
        updated = update(str(existing["id"]), data)
        return updated or {**existing, **data}
    return create(subject_id, data)


def list_all() -> List[Dict[str, Any]]:
    return base.select_all(TABLE)
