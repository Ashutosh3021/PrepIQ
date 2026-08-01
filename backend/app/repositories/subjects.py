from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from app.repositories import base

TABLE = "subjects"

# exam_type: "government" | "university" (nullable until wizard sets it)
# exam_name: "NEET" | "JEE" for government; free text for university
# university_name: university track only (nullable)


def list_for_user(user_id: str) -> List[Dict[str, Any]]:
    return base.select_eq(TABLE, "user_id", user_id)


def get(subject_id: str) -> Optional[Dict[str, Any]]:
    return base.get_by_id(TABLE, subject_id)


def get_for_user(subject_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    row = get(subject_id)
    if row and str(row.get("user_id")) == str(user_id):
        return row
    return None


def create(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "id": str(data.get("id") or uuid.uuid4()),
        "user_id": user_id,
        "name": data.get("name") or "Untitled",
        "code": data.get("code"),
        "semester": data.get("semester"),
        "academic_year": data.get("academic_year"),
        "total_marks": data.get("total_marks"),
        "exam_date": data.get("exam_date"),
        "exam_duration_minutes": data.get("exam_duration_minutes"),
        "syllabus_json": data.get("syllabus_json"),
        "exam_type": data.get("exam_type"),
        "exam_name": data.get("exam_name"),
        "university_name": data.get("university_name"),
        "papers_uploaded": data.get("papers_uploaded", 0),
        "predictions_generated": data.get("predictions_generated", 0),
        "mock_tests_created": data.get("mock_tests_created", 0),
        "created_at": now,
        "updated_at": now,
    }
    return base.insert_row(TABLE, payload)


def update(subject_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    fields = dict(fields)
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    return base.update_eq(TABLE, "id", subject_id, fields)


def delete(subject_id: str) -> bool:
    return base.delete_eq(TABLE, "id", subject_id)
