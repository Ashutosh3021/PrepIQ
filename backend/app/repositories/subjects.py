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
_PHASE0_KEYS = ("exam_type", "exam_name", "university_name")


def _native_track_columns() -> bool:
    # Default ON — columns confirmed present after ALTER on production PyroCore.
    raw = (os.getenv("PREPIQ_SUBJECTS_HAS_TRACK_COLUMNS") or "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


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


def _drop_nones(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in payload.items() if v is not None}


def create(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert subject using the same shape that succeeds via direct PyroCore POST."""
    now = datetime.now(timezone.utc).isoformat()
    payload: Dict[str, Any] = {
        "id": str(data.get("id") or uuid.uuid4()),
        "user_id": user_id,
        "name": data.get("name") or "Untitled",
        "code": data.get("code"),
        "semester": data.get("semester") if data.get("semester") is not None else 1,
        "academic_year": data.get("academic_year") or str(datetime.now().year),
        "created_at": now,
        "updated_at": now,
    }
    # Native track columns (do NOT send nested syllabus_json — causes 500 on some PyroCore builds)
    if _native_track_columns():
        for k in _PHASE0_KEYS:
            if data.get(k) is not None:
                payload[k] = data.get(k)

    for opt in (
        "total_marks",
        "exam_date",
        "exam_duration_minutes",
        "papers_uploaded",
        "predictions_generated",
        "mock_tests_created",
    ):
        if data.get(opt) is not None:
            payload[opt] = data.get(opt)

    payload = _drop_nones(payload)
    logger.info("subjects.create payload keys=%s", sorted(payload.keys()))
    try:
        return normalize_subject(base.insert_row(TABLE, payload)) or payload
    except Exception as e:
        logger.error("subjects.create failed: %s", e)
        # Last-resort bare insert, then PATCH track fields
        bare = {
            "id": payload["id"],
            "user_id": user_id,
            "name": payload["name"],
            "code": payload.get("code"),
            "semester": payload.get("semester", 1),
            "academic_year": payload.get("academic_year"),
            "created_at": now,
            "updated_at": now,
        }
        bare = _drop_nones(bare)
        row = base.insert_row(TABLE, bare)
        track = {k: data.get(k) for k in _PHASE0_KEYS if data.get(k) is not None}
        if track:
            try:
                updated = base.update_eq(TABLE, "id", payload["id"], track)
                if updated:
                    row = updated
            except Exception as e2:
                logger.warning("subjects track field patch failed: %s", e2)
        merged = {**(row or bare), **track}
        return normalize_subject(merged) or merged


def update(subject_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    fields = dict(fields)
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    # Avoid nested syllabus_json writes unless explicitly provided as already-safe value
    if "syllabus_json" in fields and isinstance(fields["syllabus_json"], dict):
        # leave as dict — some clients accept it; if it fails caller can retry without
        pass
    try:
        return normalize_subject(base.update_eq(TABLE, "id", subject_id, _drop_nones(fields)))
    except Exception as e:
        msg = str(e)
        if "syllabus_json" in fields:
            logger.warning("subjects update without syllabus_json: %s", e)
            fallback = {k: v for k, v in fields.items() if k != "syllabus_json"}
            return normalize_subject(base.update_eq(TABLE, "id", subject_id, _drop_nones(fallback)))
        raise


def delete(subject_id: str) -> bool:
    return base.delete_eq(TABLE, "id", subject_id)
