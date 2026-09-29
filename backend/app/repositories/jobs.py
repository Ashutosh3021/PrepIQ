"""jobs repository — background queue for family assignment / rubric backfill.

Single-worker claim model: the only claimant is the daemon thread started in
job_queue.py (Render runs --workers 1), so a read-then-update claim is safe.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json
import uuid

from app.repositories import base

TABLE = "jobs"

STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_FAILED = "failed"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def enqueue(kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    row = {
        "id": str(uuid.uuid4()),
        "kind": str(kind),
        "payload_json": payload or {},
        "status": STATUS_QUEUED,
        "attempts": 0,
        "created_at": _now(),
        "updated_at": _now(),
    }
    return base.insert_row(TABLE, row)


def list_by_status(status: str, limit: int = 20) -> List[Dict[str, Any]]:
    rows = base.select_eq(TABLE, "status", status)
    rows.sort(key=lambda r: str(r.get("created_at") or ""))
    return rows[:limit]


def claim_next() -> Optional[Dict[str, Any]]:
    """Claim the oldest queued job by flipping it to running."""
    for job in list_by_status(STATUS_QUEUED, limit=1):
        job_id = str(job.get("id"))
        updated = update(
            job_id,
            {"status": STATUS_RUNNING, "updated_at": _now()},
        )
        if updated and str(updated.get("status") or "") == STATUS_RUNNING:
            return updated
        # Someone else claimed it (or update was rejected) — try nothing more;
        # the next drain cycle will pick the following job.
        return None
    return None


def update(job_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # last_error is allowed to be explicitly cleared (None) on mark_done.
    payload = {k: v for k, v in fields.items() if v is not None or k == "last_error"}
    payload["updated_at"] = _now()
    return base.update_eq(TABLE, "id", job_id, payload)


def mark_done(job_id: str) -> Optional[Dict[str, Any]]:
    return update(job_id, {"status": STATUS_DONE, "last_error": None})


def mark_failed(job_id: str, error: str) -> Optional[Dict[str, Any]]:
    return update(job_id, {"status": STATUS_FAILED, "last_error": str(error)[:1000]})


def requeue(job_id: str, attempts: int, error: str) -> Optional[Dict[str, Any]]:
    return update(
        job_id,
        {
            "status": STATUS_QUEUED,
            "attempts": attempts,
            "last_error": str(error)[:1000],
        },
    )


def parse_payload(job: Dict[str, Any]) -> Dict[str, Any]:
    raw = job.get("payload_json")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}
