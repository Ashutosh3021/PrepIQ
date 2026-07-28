from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timezone

from app.repositories import base

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
    fields = dict(fields)
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    return base.update_eq(TABLE, "id", user_id, fields)
