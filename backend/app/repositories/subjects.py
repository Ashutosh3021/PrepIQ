from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import json
import logging
import os
import uuid

from app.repositories import base

logger = logging.getLogger(__name__)

TABLE = "subjects"

# Track metadata (Phase 0). Prefer syllabus_json until PyroCore has native columns.
_PHASE0_KEYS = ("exam_type", "exam_name", "university_name")

# Set PREPIQ_SUBJECTS_HAS_TRACK_COLUMNS=1 after ALTER TABLE adds the three columns.
def _native_track_columns() -> bool:
    return (os.getenv("PREPIQ_SUBJECTS_HAS_TRACK_COLUMNS") or "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _parse_jsonish(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            return value
    return value


def normalize_subject(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Surface exam_type / exam_name / university_name from syllabus_json if needed."""
    if not row:
        return row
    out = dict(row)
    sj = _parse_jsonish(out.get("syllabus_json"))
    if not isinstance(sj, dict):
        sj = {}
    for key in _PHASE0_KEYS:
        if out.get(key) is None and key in sj:
            out[key] = sj.get(key)
    if sj:
        out["syllabus_json"] = sj
    return out


def list_for_user(user_id: str) -> List[Dict[str, Any]]:
    return [normalize_subject(r) or r for r in base.select_eq(TABLE, "user_id", user_id)]


def get(subject_id: str) -> Optional[Dict[str, Any]]:
    return normalize_subject(base.get_by_id(TABLE, subject_id))


def get_for_user(subject_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    row = get(subject_id)
    if row and str(row.get("user_id")) == str(user_id):
        return row
    return None


def _merge_phase0_into_syllabus_json(data: Dict[str, Any]) -> Any:
    sj = _parse_jsonish(data.get("syllabus_json"))
    if not isinstance(sj, dict):
        sj = {}
    for key in _PHASE0_KEYS:
        if data.get(key) is not None:
            sj[key] = data.get(key)
    return sj or None


def _drop_nones(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in payload.items() if v is not None}


def create(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    base_payload: Dict[str, Any] = {
        "id": str(data.get("id") or uuid.uuid4()),
        "user_id": user_id,
        "name": data.get("name") or "Untitled",
        "code": data.get("code"),
        "semester": data.get("semester"),
        "academic_year": data.get("academic_year"),
        "total_marks": data.get("total_marks"),
        "exam_date": data.get("exam_date"),
        "exam_duration_minutes": data.get("exam_duration_minutes"),
        "papers_uploaded": data.get("papers_uploaded", 0),
        "predictions_generated": data.get("predictions_generated", 0),
        "mock_tests_created": data.get("mock_tests_created", 0),
        "created_at": now,
        "updated_at": now,
    }

    track = {k: data.get(k) for k in _PHASE0_KEYS if data.get(k) is not None}
    sj = _merge_phase0_into_syllabus_json({**data, **track})
    base_payload["syllabus_json"] = sj

    if _native_track_columns():
        for k, v in track.items():
            base_payload[k] = v

    payload = _drop_nones(base_payload)
    try:
        return normalize_subject(base.insert_row(TABLE, payload)) or payload
    except Exception as e:
        # If native columns were enabled but still missing, strip and retry once.
        msg = str(e)
        if any(k in msg for k in _PHASE0_KEYS) or "Identifier" in msg:
            logger.warning("subjects insert retry without track columns: %s", e)
            fallback = {k: v for k, v in payload.items() if k not in _PHASE0_KEYS}
            fallback["syllabus_json"] = sj
            return normalize_subject(base.insert_row(TABLE, _drop_nones(fallback))) or fallback
        raise


def update(subject_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    fields = dict(fields)
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    existing = get(subject_id) or {}
    merged = {**existing, **fields}
    if any(k in fields for k in _PHASE0_KEYS) or "syllabus_json" in fields:
        fields["syllabus_json"] = _merge_phase0_into_syllabus_json(merged)

    if not _native_track_columns():
        for k in _PHASE0_KEYS:
            fields.pop(k, None)

    try:
        return normalize_subject(base.update_eq(TABLE, "id", subject_id, _drop_nones(fields)))
    except Exception as e:
        msg = str(e)
        if any(k in msg for k in _PHASE0_KEYS) or "Identifier" in msg:
            logger.warning("subjects update retry without track columns: %s", e)
            fallback = {k: v for k, v in fields.items() if k not in _PHASE0_KEYS}
            return normalize_subject(base.update_eq(TABLE, "id", subject_id, _drop_nones(fallback)))
        raise


def delete(subject_id: str) -> bool:
    return base.delete_eq(TABLE, "id", subject_id)
