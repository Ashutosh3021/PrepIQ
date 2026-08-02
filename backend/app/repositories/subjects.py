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

# After successful ALTER on PyroCore, default to native columns.
# Set PREPIQ_SUBJECTS_HAS_TRACK_COLUMNS=0 to force syllabus_json-only mode.
def _native_track_columns() -> bool:
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


def _merge_phase0_into_syllabus_json(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
    track = {k: data.get(k) for k in _PHASE0_KEYS if data.get(k) is not None}
    sj = _merge_phase0_into_syllabus_json({**data, **track})

    # Minimal core set that has worked on this project historically
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
    if sj is not None:
        payload["syllabus_json"] = sj

    if _native_track_columns():
        payload.update(track)

    # Optional counters only if caller provided them (avoid unknown-column 500s)
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
        msg = str(e)
        logger.error("subjects.create failed: %s", e)
        # Progressive strip: track cols → syllabus_json → bare minimum
        attempts = [
            {k: v for k, v in payload.items() if k not in _PHASE0_KEYS},
            {
                k: v
                for k, v in payload.items()
                if k not in _PHASE0_KEYS and k != "syllabus_json"
            },
            {
                "id": payload["id"],
                "user_id": user_id,
                "name": payload["name"],
                "created_at": now,
                "updated_at": now,
            },
        ]
        last_err = e
        for attempt in attempts:
            try:
                logger.warning("subjects.create retry keys=%s", sorted(attempt.keys()))
                row = base.insert_row(TABLE, _drop_nones(attempt))
                # If we stripped track cols, patch syllabus_json in a second update if possible
                if sj and "syllabus_json" not in attempt:
                    try:
                        base.update_eq(TABLE, "id", payload["id"], {"syllabus_json": sj})
                    except Exception:
                        pass
                # Reflect track fields in returned object for gate logic
                merged = {**(row or attempt), **track, "syllabus_json": sj}
                return normalize_subject(merged) or merged
            except Exception as e2:
                last_err = e2
                continue
        raise last_err


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
            fallback = {k: v for k, v in fields.items() if k not in _PHASE0_KEYS}
            return normalize_subject(base.update_eq(TABLE, "id", subject_id, _drop_nones(fallback)))
        raise


def delete(subject_id: str) -> bool:
    return base.delete_eq(TABLE, "id", subject_id)
