"""Local user-profile store for wizard/account data.

Historically this repository wrote to the Pyronites ``users`` *data* table.
That table is the Pyronites auth table and is not provisioned as a writable
data table on the PyroCore backend, so every write returned
``404 table_not_found`` and was silently swallowed — which made
``/wizard/complete`` fail with ``422 Missing: ...`` because none of the
targeting fields were ever persisted.

We now persist profile + wizard data in a self-contained local SQLite store.
No external provisioning or environment variables are required, and the data
survives restarts, so the wizard can read back what the steps wrote.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    JSON,
    DateTime,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

# ── Local SQLite engine (one file, no external service required) ──────────────
_BASE = declarative_base()

_DB_PATH = None
_ENGINE = None
_SESSION = None
_INIT_LOCK = threading.Lock()


def _ensure_initialised() -> bool:
    """Lazily create the engine + table. Returns True on success.

    Failures are logged but never raised — the callers already treat a missing
    profile as "empty", so a broken local store degrades to the previous
    (best-effort) behaviour instead of 500-ing the request.
    """
    global _DB_PATH, _ENGINE, _SESSION
    if _SESSION is not None:
        return True
    with _INIT_LOCK:
        if _SESSION is not None:
            return True
        try:
            import os
            from pathlib import Path

            data_dir = Path(__file__).resolve().parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            _DB_PATH = str(data_dir / "prepiq_users.db")
            _ENGINE = create_engine(
                f"sqlite:///{_DB_PATH}",
                connect_args={"check_same_thread": False},
                pool_pre_ping=True,
            )
            _BASE.metadata.create_all(_ENGINE)
            _SESSION = sessionmaker(bind=_ENGINE, expire_on_commit=False)
            logger.info("Local user store initialised at %s", _DB_PATH)
            return True
        except Exception as e:  # pragma: no cover - defensive
            logger.error("Local user store init failed (continuing): %s", e)
            _SESSION = None
            return False


class _LocalUser(_BASE):
    __tablename__ = "local_users"

    id = Column(String(64), primary_key=True)
    email = Column(String(320), unique=True, index=True, nullable=True)

    full_name = Column(String(255), nullable=True)
    college_name = Column(String(255), nullable=True)
    program = Column(String(100), nullable=True)
    year_of_study = Column(Integer, nullable=True)

    exam_type = Column(String(50), nullable=True)
    exam_name = Column(String(255), nullable=True)
    university_name = Column(String(255), nullable=True)
    days_until_exam = Column(Integer, nullable=True)
    exam_date = Column(String(64), nullable=True)

    focus_subjects = Column(JSON, nullable=True)
    study_hours_per_day = Column(Integer, nullable=True)
    target_score = Column(Integer, nullable=True)
    preparation_level = Column(String(50), nullable=True)

    wizard_completed = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_public(row: Optional[_LocalUser]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return {
        "id": row.id,
        "email": row.email,
        "full_name": row.full_name,
        "college_name": row.college_name,
        "program": row.program,
        "year_of_study": row.year_of_study,
        "exam_type": row.exam_type,
        "exam_name": row.exam_name,
        "university_name": row.university_name,
        "days_until_exam": row.days_until_exam,
        "exam_date": row.exam_date,
        "focus_subjects": row.focus_subjects or [],
        "study_hours_per_day": row.study_hours_per_day,
        "target_score": row.target_score,
        "preparation_level": row.preparation_level,
        "wizard_completed": bool(row.wizard_completed),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def get(user_id: str) -> Optional[Dict[str, Any]]:
    if not _ensure_initialised():
        return None
    try:
        with _SESSION() as s:
            row = s.get(_LocalUser, str(user_id))
            return _to_public(row)
    except Exception as e:
        logger.warning("local users.get failed for %s (continuing): %s", user_id, e)
        return None


def get_by_email(email: str) -> Optional[Dict[str, Any]]:
    if not email or not _ensure_initialised():
        return None
    try:
        with _SESSION() as s:
            row = (
                s.query(_LocalUser)
                .filter(_LocalUser.email == str(email).strip().lower())
                .first()
            )
            return _to_public(row)
    except Exception as e:
        logger.warning("local users.get_by_email failed (continuing): %s", e)
        return None


def upsert_profile(user_id: str, email: str, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create or refresh the application user row after auth signup/login."""
    profile = profile or {}
    uid = str(user_id)
    now = _now()
    if not _ensure_initialised():
        return {
            "id": uid,
            "email": (email or "").strip().lower(),
            **{k: profile.get(k) for k in (
                "full_name", "college_name", "program", "year_of_study",
                "wizard_completed",
            )},
        }
    try:
        with _SESSION() as s:
            row = s.get(_LocalUser, uid)
            if row is None:
                row = _LocalUser(id=uid)
                row.created_at = now
                s.add(row)
            row.email = (email or "").strip().lower() or row.email
            row.full_name = profile.get("full_name") or row.full_name
            row.college_name = profile.get("college_name") or row.college_name
            row.program = profile.get("program") or row.program or "BTech"
            row.year_of_study = profile.get("year_of_study") or row.year_of_study or 1
            if "wizard_completed" in profile:
                row.wizard_completed = bool(profile["wizard_completed"])
            row.updated_at = now
            s.commit()
            return _to_public(row) or {"id": uid}
    except Exception as e:
        logger.error("local users.upsert_profile failed for %s (continuing): %s", uid, e)
        return {"id": uid, "email": (email or "").strip().lower()}


def update(user_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    uid = str(user_id)
    if not _ensure_initialised():
        # Mirror the previous best-effort behaviour so callers that don't depend
        # on a persisted row still proceed.
        out = dict(fields)
        out["id"] = uid
        return out
    try:
        with _SESSION() as s:
            row = s.get(_LocalUser, uid)
            if row is None:
                row = _LocalUser(id=uid)
                row.created_at = _now()
                s.add(row)
            allowed = {
                "email", "full_name", "college_name", "program", "year_of_study",
                "exam_type", "exam_name", "university_name", "days_until_exam",
                "exam_date", "focus_subjects", "study_hours_per_day",
                "target_score", "preparation_level", "wizard_completed",
            }
            for key, val in fields.items():
                if key in allowed:
                    setattr(row, key, val)
            row.updated_at = _now()
            s.commit()
            return _to_public(row) or {"id": uid}
    except Exception as e:
        logger.error("local users.update failed for %s (continuing): %s", uid, e)
        out = dict(fields)
        out["id"] = uid
        return out


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
