from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import json
import uuid

from app.repositories import base

TABLE = "predictions"


def list_for_user_subject(user_id: str, subject_id: str) -> List[Dict[str, Any]]:
    rows = base.select_eq(TABLE, "subject_id", subject_id)
    return [r for r in rows if str(r.get("user_id")) == str(user_id)]


def get(prediction_id: str) -> Optional[Dict[str, Any]]:
    return base.get_by_id(TABLE, prediction_id)


def get_latest(user_id: str, subject_id: str) -> Optional[Dict[str, Any]]:
    rows = list_for_user_subject(user_id, subject_id)
    if not rows:
        return None

    def _key(r: Dict[str, Any]) -> str:
        return str(r.get("created_at") or "")

    rows.sort(key=_key, reverse=True)
    return rows[0]


def create(user_id: str, subject_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    preds = data.get("predictions") or data.get("predicted_questions") or []
    if not isinstance(preds, str):
        preds_json = json.dumps(preds)
    else:
        preds_json = preds
    row = {
        "id": str(data.get("id") or uuid.uuid4()),
        "user_id": user_id,
        "subject_id": subject_id,
        "predicted_questions_json": preds_json,
        "total_questions": data.get("total_questions") or (len(preds) if isinstance(preds, list) else None),
        "total_predicted_marks": data.get("total_marks") or data.get("total_predicted_marks"),
        "unit_coverage_json": data.get("unit_coverage") or data.get("unit_coverage_json") or {},
        "ml_analysis_json": data.get("ml_analysis_json")
        if isinstance(data.get("ml_analysis_json"), str)
        else json.dumps(data.get("ml_analysis_json") or {}),
        "prediction_accuracy_score": data.get("prediction_accuracy_score") or data.get("accuracy_score") or 0,
        "created_at": now,
        "updated_at": now,
    }
    return base.insert_row(TABLE, row)


def update(prediction_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    fields = dict(fields)
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    if "predictions" in fields and not isinstance(fields.get("predicted_questions_json"), str):
        fields["predicted_questions_json"] = json.dumps(fields.pop("predictions"))
    return base.update_eq(TABLE, "id", prediction_id, fields)
