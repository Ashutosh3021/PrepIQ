"""
Pyronites-backed prediction pipeline (Fix Phase A).

No SQLAlchemy. LLM via Phase 1 provider capability=\"prediction\".
"""
from __future__ import annotations

import json
import logging
import os
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.llm_provider import get_llm_client
from app.repositories import papers as papers_repo
from app.repositories import predictions as predictions_repo
from app.repositories import questions as questions_repo
from app.repositories import subjects as subjects_repo

logger = logging.getLogger(__name__)

MIN_PAPERS_FULL = int(os.getenv("PREDICTION_MIN_PAPERS_FULL", "3") or "3")
MAX_ITEMS = int(os.getenv("PREDICTION_MAX_ITEMS", "10") or "10")
CONTEXT_CHARS = int(os.getenv("PREDICTION_CONTEXT_CHARS", "12000") or "12000")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_item(raw: Dict[str, Any], index: int, source: str) -> Dict[str, Any]:
    text = str(raw.get("text") or raw.get("question_text") or "").strip()
    topic = str(raw.get("topic") or raw.get("unit") or "General")
    try:
        marks = int(raw.get("marks") or 5)
    except (TypeError, ValueError):
        marks = 5
    try:
        conf = float(raw.get("confidence_score") if raw.get("confidence_score") is not None else 0.5)
    except (TypeError, ValueError):
        conf = 0.5
    conf = max(0.0, min(1.0, conf))
    prob = str(raw.get("probability") or "moderate").lower()
    if conf >= 0.8:
        prob = "very_high"
    elif conf >= 0.65:
        prob = "high"
    elif conf >= 0.4:
        prob = "moderate"
    else:
        prob = "low"
    return {
        "question_number": int(raw.get("question_number") or index),
        "text": text,
        "topic": topic,
        "unit": topic,
        "marks": marks,
        "probability": prob,
        "confidence_score": conf,
        "reasoning": str(raw.get("reasoning") or ""),
        "source": source,
    }


def _build_stats(question_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    units: Counter = Counter()
    marks: Counter = Counter()
    samples: List[str] = []
    for q in question_rows:
        unit = str(q.get("unit_name") or q.get("unit") or "General")
        units[unit] += 1
        try:
            m = int(q.get("marks") or 0)
        except (TypeError, ValueError):
            m = 0
        if m:
            marks[m] += 1
        text = str(q.get("question_text") or q.get("text") or "").strip()
        if text and len(samples) < 40:
            samples.append(text[:400])
    return {
        "unit_frequency": dict(units),
        "marks_distribution": {str(k): v for k, v in marks.items()},
        "total_questions": len(question_rows),
        "sample_questions": samples,
    }


def _stats_fallback_predictions(stats: Dict[str, Any], source: str) -> List[Dict[str, Any]]:
    units = stats.get("unit_frequency") or {}
    ranked = sorted(units.items(), key=lambda x: x[1], reverse=True)
    out: List[Dict[str, Any]] = []
    for i, (unit, count) in enumerate(ranked[:MAX_ITEMS], start=1):
        total = max(int(stats.get("total_questions") or 1), 1)
        conf = min(0.35 + (count / total) * 0.4, 0.75)
        out.append(
            _normalize_item(
                {
                    "question_number": i,
                    "text": f"Focus revision on unit/topic: {unit} (appeared {count} times in uploaded papers).",
                    "topic": unit,
                    "unit": unit,
                    "marks": 5,
                    "confidence_score": conf,
                    "reasoning": "Derived from frequency statistics only (LLM unavailable or parse failed).",
                },
                i,
                source,
            )
        )
    return out


def _call_llm(prompt: str) -> List[Dict[str, Any]]:
    client = get_llm_client("prediction")
    if not client.is_available:
        return []
    try:
        parsed = client.generate_json(prompt, expect_list=False)
        raw_list = parsed.get("predictions") if isinstance(parsed, dict) else None
        if raw_list is None and isinstance(parsed, dict) and "items" in parsed:
            raw_list = parsed["items"]
        if not isinstance(raw_list, list):
            # try free text JSON
            text = client.generate_text(prompt)
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            data = json.loads(cleaned)
            raw_list = data.get("predictions") if isinstance(data, dict) else data
        if not isinstance(raw_list, list):
            return []
        out = []
        for i, item in enumerate(raw_list[:MAX_ITEMS], start=1):
            if not isinstance(item, dict):
                continue
            norm = _normalize_item(item, i, "llm")
            if norm["text"]:
                out.append(norm)
        return out
    except Exception as e:
        logger.warning("Prediction LLM failed: %s", e)
        return []


def generate_predictions(user_id: str, subject_id: str) -> Dict[str, Any]:
    subject = subjects_repo.get_for_user(subject_id, user_id)
    if not subject:
        raise ValueError("Subject not found")

    completed = papers_repo.list_completed_for_subject(subject_id)
    paper_count = len(completed)
    question_rows = questions_repo.list_for_subject(subject_id)
    # Prefer questions only from completed papers when possible
    completed_ids = {str(p.get("id")) for p in completed}
    if completed_ids:
        filtered = [q for q in question_rows if str(q.get("paper_id")) in completed_ids]
        if filtered:
            question_rows = filtered

    # Tier 0
    if paper_count == 0 or not question_rows:
        return {
            "id": None,
            "subject_id": subject_id,
            "predictions": [],
            "predicted_questions": [],
            "total_marks": 0,
            "coverage_percentage": 0,
            "unit_coverage": {},
            "generated_at": _now(),
            "fallback_used": True,
            "fallback_reason": "no_papers" if paper_count == 0 else "no_questions",
            "message": (
                "Upload at least one past paper and wait for extraction to get predictions. "
                f"Add {MIN_PAPERS_FULL}+ papers for fuller AI-powered predictions."
            ),
            "source": "no_data",
            "warning": None,
        }

    stats = _build_stats(question_rows)
    subject_name = str(subject.get("name") or "Subject")
    syllabus = subject.get("syllabus_json")
    syllabus_text = ""
    if syllabus:
        syllabus_text = json.dumps(syllabus) if isinstance(syllabus, (dict, list)) else str(syllabus)

    cold = paper_count < MIN_PAPERS_FULL
    source_tag = "cold_start" if cold else "full"
    warning = (
        "Generated with limited papers — treat as guidance, not a full historical pattern analysis."
        if cold
        else None
    )

    samples = stats.get("sample_questions") or []
    sample_block = "\n".join(f"- {s}" for s in samples)[:CONTEXT_CHARS]
    prompt = f"""You are an exam prediction engine for engineering students.
Subject: {subject_name}
Papers analyzed: {paper_count}
Question count: {stats.get('total_questions')}
Unit frequency: {json.dumps(stats.get('unit_frequency') or {})}
Marks distribution: {json.dumps(stats.get('marks_distribution') or {})}
Syllabus (optional): {syllabus_text[:2000]}

Sample extracted questions:
{sample_block}

Return JSON only with this shape:
{{"predictions":[{{"question_number":1,"text":"...","topic":"...","unit":"...","marks":5,"probability":"high","confidence_score":0.0,"reasoning":"..."}}],"total_marks":0,"coverage_percentage":0,"unit_coverage":{{}},"generated_at":"ISO"}}

Rules:
- Ground topics in the provided samples and unit frequencies.
- Do not invent university-specific past papers you were not given.
- confidence_score between 0 and 1.
- At most {MAX_ITEMS} predictions, ranked by likelihood.
"""

    llm_preds = _call_llm(prompt)
    fallback_used = False
    if not llm_preds:
        llm_preds = _stats_fallback_predictions(stats, "stats")
        fallback_used = True
        source_tag = "stats" if not cold else "cold_start"

    llm_preds.sort(key=lambda x: float(x.get("confidence_score") or 0), reverse=True)
    final = llm_preds[:MAX_ITEMS]
    for i, p in enumerate(final, start=1):
        p["question_number"] = i
        p["source"] = source_tag if p.get("source") == "llm" else p.get("source") or source_tag

    unit_coverage: Dict[str, int] = {}
    for p in final:
        u = p.get("unit") or "General"
        unit_coverage[u] = unit_coverage.get(u, 0) + 1
    total_marks = sum(int(p.get("marks") or 0) for p in final)

    record = predictions_repo.create(
        user_id,
        subject_id,
        {
            "predictions": final,
            "total_questions": len(final),
            "total_marks": total_marks,
            "unit_coverage": unit_coverage,
            "ml_analysis_json": {
                "source": source_tag,
                "fallback_used": fallback_used,
                "paper_count": paper_count,
                "stats": {
                    "unit_frequency": stats.get("unit_frequency"),
                    "total_questions": stats.get("total_questions"),
                },
            },
            "prediction_accuracy_score": 0.0,
        },
    )

    return {
        "id": str(record.get("id")),
        "subject_id": subject_id,
        "predictions": final,
        "predicted_questions": final,
        "total_marks": total_marks,
        "coverage_percentage": int(round(100 * len(unit_coverage) / max(len(unit_coverage), 1))) if final else 0,
        "unit_coverage": unit_coverage,
        "generated_at": _now(),
        "fallback_used": fallback_used or cold,
        "fallback_reason": "llm_unavailable" if fallback_used else ("limited_papers" if cold else None),
        "message": None,
        "warning": warning,
        "source": source_tag,
    }


def get_prediction(prediction_id: str, user_id: str) -> Dict[str, Any]:
    row = predictions_repo.get(prediction_id)
    if not row or str(row.get("user_id")) != str(user_id):
        raise ValueError("Prediction not found")
    return _row_to_response(row)


def get_latest_prediction(subject_id: str, user_id: str) -> Dict[str, Any]:
    subject = subjects_repo.get_for_user(subject_id, user_id)
    if not subject:
        raise ValueError("Subject not found")
    row = predictions_repo.get_latest(user_id, subject_id)
    if not row:
        raise ValueError("No predictions found for this subject")
    return _row_to_response(row)


def _row_to_response(row: Dict[str, Any]) -> Dict[str, Any]:
    raw = row.get("predicted_questions_json") or []
    if isinstance(raw, str):
        try:
            preds = json.loads(raw)
        except Exception:
            preds = []
    else:
        preds = raw if isinstance(raw, list) else []
    unit_coverage = row.get("unit_coverage_json") or {}
    if isinstance(unit_coverage, str):
        try:
            unit_coverage = json.loads(unit_coverage)
        except Exception:
            unit_coverage = {}
    return {
        "id": str(row.get("id")),
        "subject_id": str(row.get("subject_id")),
        "predictions": preds,
        "predicted_questions": preds,
        "total_marks": int(row.get("total_predicted_marks") or 0),
        "coverage_percentage": 0,
        "unit_coverage": unit_coverage if isinstance(unit_coverage, dict) else {},
        "generated_at": row.get("created_at") or _now(),
        "fallback_used": False,
        "source": "stored",
        "accuracy_score": row.get("prediction_accuracy_score"),
    }
