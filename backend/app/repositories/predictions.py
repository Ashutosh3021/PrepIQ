from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import json
import logging
import uuid

from app.repositories import base

logger = logging.getLogger(__name__)

TABLE = "predictions"

# source_type: "government_ml" | "university_llm" (nullable until two-track ships)
# model_version: government track only — which trained model produced the row


def _as_json_value(value: Any, default: Any) -> Any:
    """Normalize to a JSON-serializable object for PyroCore JSON columns.

    Do NOT pre-stringify: double-encoded strings can cause 500s on insert.
    """
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        try:
            parsed = json.loads(text)
            if isinstance(parsed, (dict, list)):
                return parsed
        except Exception:
            pass
        return default
    return default


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
    preds = _as_json_value(preds, [])
    if not isinstance(preds, list):
        preds = []

    unit_coverage = _as_json_value(
        data.get("unit_coverage") if data.get("unit_coverage") is not None else data.get("unit_coverage_json"),
        {},
    )
    if not isinstance(unit_coverage, dict):
        unit_coverage = {}

    ml_analysis = _as_json_value(data.get("ml_analysis_json"), {})
    if not isinstance(ml_analysis, dict):
        ml_analysis = {}

    row: Dict[str, Any] = {
        "id": str(data.get("id") or uuid.uuid4()),
        "user_id": user_id,
        "subject_id": subject_id,
        "predicted_questions_json": preds,
        "total_questions": data.get("total_questions")
        if data.get("total_questions") is not None
        else len(preds),
        "total_predicted_marks": data.get("total_marks") or data.get("total_predicted_marks") or 0,
        "unit_coverage_json": unit_coverage,
        "ml_analysis_json": ml_analysis,
        "prediction_accuracy_score": float(
            data.get("prediction_accuracy_score") or data.get("accuracy_score") or 0
        ),
        "created_at": now,
        "updated_at": now,
    }
    # Only send optional Phase 0 columns when present — avoids
    # "Identifier 'source_type' not found" on older PyroCore schemas.
    if data.get("source_type") is not None:
        row["source_type"] = data.get("source_type")
    if data.get("model_version") is not None:
        row["model_version"] = data.get("model_version")

    try:
        return base.insert_row(TABLE, row)
    except Exception as e:
        msg = str(e)
        if "source_type" in msg or "model_version" in msg or "Identifier" in msg:
            logger.warning("predictions insert retry without track columns: %s", e)
            row.pop("source_type", None)
            row.pop("model_version", None)
            return base.insert_row(TABLE, row)
        raise


def update(prediction_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    fields = dict(fields)
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    if "predictions" in fields:
        fields["predicted_questions_json"] = _as_json_value(fields.pop("predictions"), [])
    if "predicted_questions_json" in fields:
        fields["predicted_questions_json"] = _as_json_value(fields["predicted_questions_json"], [])
    if "unit_coverage_json" in fields:
        fields["unit_coverage_json"] = _as_json_value(fields["unit_coverage_json"], {})
    if "ml_analysis_json" in fields:
        fields["ml_analysis_json"] = _as_json_value(fields["ml_analysis_json"], {})
    return base.update_eq(TABLE, "id", prediction_id, fields)
