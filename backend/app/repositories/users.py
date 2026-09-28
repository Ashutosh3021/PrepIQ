"""User-profile + wizard targeting store backed by PyroCore ``user_profiles``.

History: this repository used to write to PyroCore's ``users`` table (reserved
server-side, so every write 404'd) and then moved to a local SQLite file. The
SQLite file lives on Render's ephemeral disk, so every redeploy silently
wiped profiles and wizard state. Profiles now live alongside the rest of the
application data on the PyroCore project — durable across deploys.

Failure policy (deliberate):
  * reads  — degrade to ``None``/empty so a PyroCore hiccup never 500s auth;
  * writes — raise. A wizard step or signup that cannot persist must surface
    instead of pretending it succeeded.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.repositories import base

logger = logging.getLogger(__name__)

TABLE = "user_profiles"

_BOOL_FIELDS = ("wizard_completed",)
_INT_FIELDS = (
    "year_of_study",
    "days_until_exam",
    "study_hours_per_day",
    "target_score",
)
_JSON_FIELDS = ("focus_subjects",)

_ALLOWED = (
    "email",
    "full_name",
    "college_name",
    "program",
    "year_of_study",
    "exam_type",
    "exam_name",
    "university_name",
    "days_until_exam",
    "exam_date",
    "focus_subjects",
    "study_hours_per_day",
    "target_score",
    "preparation_level",
    "wizard_completed",
)

# Targeting parameters captured by the setup wizard. Clearing these fully resets
# the user's exam targeting so the wizard can be replayed without stale data.
_TARGETING_FIELDS = (
    "exam_type",
    "exam_name",
    "university_name",
    "days_until_exam",
    "exam_date",
    "focus_subjects",
    "study_hours_per_day",
    "target_score",
    "preparation_level",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_jsonish(value: Any) -> Any:
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


def _coerce(row: Dict[str, Any], key: str, value: Any) -> Any:
    if key in _BOOL_FIELDS:
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)
    if key in _INT_FIELDS:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    if key in _JSON_FIELDS:
        parsed = _parse_jsonish(value)
        return parsed if isinstance(parsed, list) else []
    return value


def _normalise(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not row:
        return row
    out = dict(row)
    for key in list(out.keys()):
        if key in _BOOL_FIELDS or key in _INT_FIELDS or key in _JSON_FIELDS:
            out[key] = _coerce(out, key, out[key])
    out.setdefault("focus_subjects", [])
    out["wizard_completed"] = bool(out.get("wizard_completed"))
    if not out.get("program"):
        out["program"] = "BTech"
    if out.get("year_of_study") in (None, 0):
        out["year_of_study"] = 1
    if out.get("email"):
        out["email"] = str(out["email"]).strip().lower()
    return out


def get(user_id: str) -> Optional[Dict[str, Any]]:
    if not user_id:
        return None
    try:
        return _normalise(base.get_by_id(TABLE, str(user_id)))
    except Exception as e:
        if base.is_auth_error(e):
            raise
        logger.warning("user_profiles.get failed for %s (continuing): %s", user_id, e)
        return None


def get_by_email(email: str) -> Optional[Dict[str, Any]]:
    if not email:
        return None
    try:
        rows = base.select_eq(TABLE, "email", str(email).strip().lower())
    except Exception as e:
        if base.is_auth_error(e):
            raise
        logger.warning("user_profiles.get_by_email failed (continuing): %s", e)
        return None
    return _normalise(rows[0]) if rows else None


def _write_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
    """Filter to writable columns and stamp the timestamp."""
    payload = {k: v for k, v in fields.items() if k in _ALLOWED}
    payload["updated_at"] = _now()
    return payload


def upsert_profile(user_id: str, email: str, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create or refresh the application profile after auth signup/login."""
    profile = profile or {}
    uid = str(user_id)
    clean_email = (email or "").strip().lower() or None

    # Booleans are written whenever the key is present (False must stick);
    # other fields only overwrite when a value is supplied.
    incoming = {
        k: v
        for k, v in profile.items()
        if k in _ALLOWED and (k in _BOOL_FIELDS or (v is not None and v != ""))
    }

    existing = get(uid)
    if existing is None:
        payload = {
            "id": uid,
            "email": clean_email,
            "program": "BTech",
            "year_of_study": 1,
            "wizard_completed": False,
            **incoming,
            "created_at": _now(),
        }
        payload["updated_at"] = _now()
        row = base.insert_row(TABLE, {k: v for k, v in payload.items() if v is not None or k in _BOOL_FIELDS})
        logger.info("user_profiles created row for %s", uid)
        return _normalise(row) or _normalise(payload) or {"id": uid}

    if clean_email and clean_email != existing.get("email"):
        incoming["email"] = clean_email
    if not incoming:
        return existing

    row = base.update_eq(TABLE, "id", uid, _write_fields(incoming))
    return _normalise(row) or _normalise({**existing, **incoming}) or {"id": uid}


def update(user_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Persist wizard/profile fields. Raises when the write cannot be made."""
    uid = str(user_id)
    payload = _write_fields(fields)
    if not payload:
        return get(uid)

    existing = get(uid)
    if existing is None:
        payload = {
            "id": uid,
            "program": "BTech",
            "year_of_study": 1,
            **payload,
        }
        row = base.insert_row(TABLE, payload)
    else:
        row = base.update_eq(TABLE, "id", uid, payload)

    merged = _normalise(row) or _normalise({**(existing or {}), **payload, "id": uid})
    return merged


def reset_targeting(user_id: str) -> Optional[Dict[str, Any]]:
    """Wipe all previously saved targeting information for the user.

    Sets every wizard/targeting column back to NULL (or False for the
    completion flag) so a re-triggered wizard starts from a clean slate and
    cannot conflict with the previous exam configuration.
    """
    fields: Dict[str, Any] = {key: None for key in _TARGETING_FIELDS}
    fields["wizard_completed"] = False
    return update(user_id, fields)
