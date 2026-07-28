from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from app.repositories import base

TABLE = "mock_tests"


def list_for_user(user_id: str) -> List[Dict[str, Any]]:
    return base.select_eq(TABLE, "user_id", user_id)


def get(test_id: str) -> Optional[Dict[str, Any]]:
    return base.get_by_id(TABLE, test_id)


def get_for_user(test_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    row = get(test_id)
    if row and str(row.get("user_id")) == str(user_id):
        return row
    return None


def create(user_id: str, subject_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": str(data.get("id") or uuid.uuid4()),
        "user_id": user_id,
        "subject_id": subject_id,
        "total_questions": data.get("total_questions") or 0,
        "total_marks": data.get("total_marks"),
        "duration_minutes": data.get("duration_minutes") or data.get("time_limit_minutes"),
        "difficulty_level": data.get("difficulty_level") or data.get("difficulty"),
        "questions_json": data.get("questions_json") or data.get("questions") or [],
        "start_time": data.get("start_time") or now,
        "end_time": data.get("end_time"),
        "is_completed": data.get("is_completed", False),
        "user_answers_json": data.get("user_answers_json"),
        "score": data.get("score"),
        "percentage": data.get("percentage"),
        "correct_count": data.get("correct_count"),
        "incorrect_count": data.get("incorrect_count"),
        "skipped_count": data.get("skipped_count"),
        "weak_topics_json": data.get("weak_topics_json"),
        "strong_topics_json": data.get("strong_topics_json"),
        "created_at": now,
    }
    return base.insert_row(TABLE, row)


def update(test_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return base.update_eq(TABLE, "id", test_id, fields)
