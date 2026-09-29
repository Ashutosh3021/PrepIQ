"""question_rubrics repository — gradeability artifacts per question.

Row shape (migration.py _TABLES):
  id, question_id, family_id, mode (mcq|descriptive), model_answer,
  rubric_json, keywords_json, options_json, needs_review, generated_at, created_at

One row per question; family-level LLM reuse copies artifacts into new rows
(services/rubric_generation.py) so grading always looks up by question_id.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import logging
import uuid

from app.repositories import base

logger = logging.getLogger(__name__)

TABLE = "question_rubrics"


def find_by_question(question_id: str) -> Optional[Dict[str, Any]]:
    rows = base.select_eq(TABLE, "question_id", str(question_id))
    return rows[0] if rows else None


def find_by_family(family_id: str) -> Optional[Dict[str, Any]]:
    if not family_id:
        return None
    rows = base.select_eq(TABLE, "family_id", str(family_id))
    return rows[0] if rows else None


def get(rubric_id: str) -> Optional[Dict[str, Any]]:
    return base.get_by_id(TABLE, rubric_id)


def create(data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": str(data.get("id") or uuid.uuid4()),
        "question_id": str(data.get("question_id") or ""),
        "family_id": data.get("family_id"),
        "mode": data.get("mode") or "descriptive",
        "model_answer": data.get("model_answer"),
        "rubric_json": data.get("rubric_json"),
        "keywords_json": data.get("keywords_json"),
        "options_json": data.get("options_json"),
        "needs_review": bool(data.get("needs_review", True)),
        "generated_at": data.get("generated_at") or now,
        "created_at": data.get("created_at") or now,
    }
    return base.insert_row(TABLE, row)


def update(rubric_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return base.update_eq(TABLE, "id", rubric_id, fields)


def list_for_questions(question_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Map question_id -> rubric row (small N; one select per id)."""
    out: Dict[str, Dict[str, Any]] = {}
    for qid in question_ids:
        row = find_by_question(qid)
        if row:
            out[str(qid)] = row
    return out
