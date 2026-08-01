from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from app.repositories import base
from app.repositories import papers as papers_repo

TABLE = "questions"


def list_for_paper(paper_id: str) -> List[Dict[str, Any]]:
    return base.select_eq(TABLE, "paper_id", paper_id)


def list_for_subject(subject_id: str) -> List[Dict[str, Any]]:
    paper_ids = {str(p["id"]) for p in papers_repo.list_for_subject(subject_id)}
    if not paper_ids:
        return []
    # Prefer server-side filter when available; else filter client-side
    try:
        rows = base.select_eq(TABLE, "subject_id", subject_id)
        if rows:
            return rows
    except Exception:
        pass
    all_rows: List[Dict[str, Any]] = []
    for pid in paper_ids:
        all_rows.extend(list_for_paper(pid))
    return all_rows


def get(question_id: str) -> Optional[Dict[str, Any]]:
    return base.get_by_id(TABLE, question_id)


def create_many(paper_id: str, subject_id: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    created: List[Dict[str, Any]] = []
    for item in items:
        row = {
            "id": str(item.get("id") or uuid.uuid4()),
            "paper_id": paper_id,
            "subject_id": subject_id,
            "question_text": item.get("text") or item.get("question_text") or "",
            "question_number": item.get("number") or item.get("question_number"),
            "marks": int(item.get("marks") or 0),
            "unit_name": item.get("unit") or item.get("unit_name") or "Unknown",
            "question_type": item.get("question_type") or "unknown",
            "difficulty": (item.get("difficulty") or "medium"),
            "correct_answer": item.get("correct_answer"),
            "topics_json": item.get("topics_json"),
            "text_length": item.get("length") or len(str(item.get("text") or "")),
            # Government-track syllabus tagging (filled in a later phase)
            "tagged_unit": item.get("tagged_unit"),
            "tagging_confidence": item.get("tagging_confidence"),
            "created_at": now,
        }
        created.append(base.insert_row(TABLE, row))
    return created


def update(question_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Patch fields (e.g. tagged_unit / tagging_confidence after LLM tagging)."""
    return base.update_eq(TABLE, "id", question_id, fields)
