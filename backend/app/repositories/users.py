from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from app.repositories import base

logger = logging.getLogger(__name__)

TABLE = "users"


def get(user_id: str) -> Optional[Dict[str, Any]]:
    return base.get_by_id(TABLE, user_id)


def get_by_email(email: str) -> Optional[Dict[str, Any]]:
    rows = base.select_eq(TABLE, "email", email.strip().lower())
    return rows[0] if rows else None


def upsert_profile(user_id: str, email: str, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create or refresh application user row after auth signup/login."""
    profile = profile or {}
    existing = get(user_id)
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "id": user_id,
        "email": email.strip().lower(),
        "full_name": profile.get("full_name") or (existing or {}).get("full_name"),
        "college_name": profile.get("college_name") or (existing or {}).get("college_name"),
        "program": profile.get("program") or (existing or {}).get("program") or "BTech",
        "year_of_study": profile.get("year_of_study") or (existing or {}).get("year_of_study") or 1,
        "wizard_completed": profile.get("wizard_completed", (existing or {}).get("wizard_completed", False)),
        "updated_at": now,
    }
    if existing:
        return base.update_eq(TABLE, "id", user_id, payload) or payload
    payload["created_at"] = now
    return base.insert_row(TABLE, payload)


def update(user_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        fields = dict(fields)
        fields["updated_at"] = datetime.now(timezone.utc).isoformat()
        return base.update_eq(TABLE, "id", user_id, fields)
    except Exception as e:
        # PyroCore can be rate-limited (429) or the users table may be
        # un-migrated; the wizard steps and reset must not 500 on that.
        # Return the attempted fields (augmented with id) as a best-effort
        # result so callers that don't depend on the persisted row proceed.
        logger.warning("users.update failed for %s (continuing): %s", user_id, e)
        fields = dict(fields)
        fields.pop("updated_at", None)
        fields["id"] = user_id
        return fields


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


def reset_targeting(user_id: str) -> Optional[Dict[str, Any]]:
    """Wipe all previously saved targeting information for the user.

    Sets every wizard/targeting column back to NULL (or False for the
    completion flag) so a re-triggered wizard starts from a clean slate and
    cannot conflict with the previous exam configuration.
    """
    fields = {key: None for key in _TARGETING_FIELDS}
    fields["wizard_completed"] = False
    return update(user_id, fields)
