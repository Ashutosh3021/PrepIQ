from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from app.repositories import base

TABLE = "question_papers"


def list_for_subject(subject_id: str) -> List[Dict[str, Any]]:
    return base.select_eq(TABLE, "subject_id", subject_id)


def list_completed_for_subject(subject_id: str) -> List[Dict[str, Any]]:
    rows = list_for_subject(subject_id)
    return [r for r in rows if r.get("processing_status") == "completed"]


def get(paper_id: str) -> Optional[Dict[str, Any]]:
    return base.get_by_id(TABLE, paper_id)


def create(payload: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": str(payload.get("id") or uuid.uuid4()),
        "subject_id": payload["subject_id"],
        "file_name": payload.get("file_name") or "upload",
        "file_path": payload.get("file_path"),  # relative path under UPLOAD_ROOT
        "file_size_bytes": payload.get("file_size_bytes"),
        "exam_year": payload.get("exam_year"),
        "exam_semester": payload.get("exam_semester"),
        "total_marks": payload.get("total_marks"),
        "duration_minutes": payload.get("duration_minutes"),
        "raw_text": payload.get("raw_text"),
        "metadata_json": payload.get("metadata_json"),
        "extraction_confidence": payload.get("extraction_confidence"),
        "extraction_method": payload.get("extraction_method"),
        "processing_status": payload.get("processing_status") or "pending",
        "error_message": payload.get("error_message"),
        "processed_at": payload.get("processed_at"),
        "created_at": now,
        "updated_at": now,
    }
    return base.insert_row(TABLE, row)


def update(paper_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    fields = dict(fields)
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    return base.update_eq(TABLE, "id", paper_id, fields)


def count_completed(subject_id: str) -> int:
    return len(list_completed_for_subject(subject_id))
